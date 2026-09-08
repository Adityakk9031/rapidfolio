# Standard Operating Procedure (SOP): Codified Deterministic KYB Workflow

**SOP Reference:** SOP-OPS-KYB-2024-v3.0-DETERMINISTIC  
**Department:** Financial Crime & Global Compliance Operations  
**Target:** Automated & HITL-Gated U.S. Commercial Business Onboarding  

---

## 1. Initial Intake & Corporate Verification
1.1. `[Step: INTAKE_01 | Type: rule_evaluation]` Ingest entity registration JSON payload from customer portal. Validate required schema fields: `ein`, `legal_name`, `state_of_inc`, `address`, and `ubo_list`.
   - If validation fails (`payload.valid == false`), transition to `STATE_REJECT_INVALID_PAYLOAD`.  
   - If validation succeeds (`payload.valid == true`), transition to `MIDDESK_VERIFY`.
1.2. `[Step: MIDDESK_VERIFY | Type: api_call | Vendor: Middesk | Timeout: 15s]` Call Middesk SOS Verification API (`POST /v1/businesses/verify`).
   - If `middesk.status == "ACTIVE" AND middesk.standing == "GOOD"`, transition to `STEP_UBO_PARSE`.
   - If `middesk.status in ["REVOKED", "INACTIVE", "DISSOLVED"]`, transition to `STATE_REJECT_INACTIVE_ENTITY`.
   - If `middesk.http_status in [500, 502, 503, 504]` (API Failure), execute retry with exponential backoff (max 3 retries, delay 2s). If retries exhausted, route to `STEP_SYS_ALERT_FALLBACK`.

---

## 2. Ultimate Beneficial Ownership (UBO) Calculation & KYC
2.1. `[Step: STEP_UBO_PARSE | Type: rule_evaluation]` Calculate total equity sum across all declared UBO entries:
   - If `sum(ubo.equity_pct) != 100.0`, transition to `STATE_REJECT_EQUITY_MISMATCH`.
   - For all UBOs where `ubo.equity_pct >= 25.0`, enqueue each UBO record into array `eligible_ubos` and transition to `STEP_PERSONA_KYC`.  
2.2. `[Step: STEP_PERSONA_KYC | Type: api_call | Vendor: Persona | Timeout: 30s]` Dispatch batch biometric & identity verification via Persona Inquiry API (`POST /v1/inquiries`).
   - If all `ubo.persona_score >= 85 AND ubo.id_verified == true`, transition to `STEP_COMPLYADVANTAGE_SCREEN`.
   - If any `ubo.persona_score < 85 OR ubo.id_verified == false`, transition to `HITL_MANUAL_KYC_REVIEW`.
   - If `persona.timeout == true OR persona.http_status >= 500`, trigger circuitbreaker retry (max 3 attempts) and on failure fallback route to `HITL_MANUAL_KYC_REVIEW`.

---

## 3. Sanctions, Watchlist & PEP Screening
3.1. `[Step: STEP_COMPLYADVANTAGE_SCREEN | Type: api_call | Vendor: ComplyAdvantage | Timeout: 20s]` Submit entity payload and verified UBO list to ComplyAdvantage Search API (`POST /v2/searches`).
   - If `screening.ofac_sanctions_match == true`, transition to `STATE_BLOCK_OFAC_SAR_FILING`.
   - If `screening.pep_match == true OR screening.adverse_media_match == true`, transition to `HITL_COMPLIANCE_EDD_GATE`.
   - If `screening.matches_count == 0`, transition to `STEP_JURISDICTION_RISK_EVAL`.
   - If `complyadvantage.http_status >= 500`, execute retry (max 3) or fallback route to `HITL_COMPLIANCE_EDD_GATE`.

---

## 4. Jurisdiction & Merchant Industry Evaluation
4.1. `[Step: STEP_JURISDICTION_RISK_EVAL | Type: rule_evaluation]` Check entity country against FATF High-Risk & Non-Cooperative Jurisdiction ISO List `["IRN", "PRK", "MMR", "RUS", "SYR", "CUB"]`.
   - If `entity.country_iso in FATF_HIGH_RISK_LIST`, transition to `STATE_REJECT_PROHIBITED_JURISDICTION`.
   - If `entity.country_iso not in FATF_HIGH_RISK_LIST`, transition to `STEP_MCC_EVAL`.
4.2. `[Step: STEP_MCC_EVAL | Type: rule_evaluation]` Check merchant category code `mcc_code` against Prohibited MCC list `[7995, 5993, 6051, 7800, 7801, 7802]`.
   - If `entity.mcc_code in PROHIBITED_MCC_LIST`, transition to `STATE_REJECT_PROHIBITED_INDUSTRY`.
   - If `entity.mcc_code not in PROHIBITED_MCC_LIST`, transition to `STEP_MARQETA_PROVISION`.

---

## 5. Decisioning, Provisioning & Human-in-the-Loop Gates
5.1. `[Step: HITL_MANUAL_KYC_REVIEW | Type: human_in_the_loop_gate | Vendor: Jira | Timeout: 86400s]` Enqueue task to Jira Compliance Queue with SLA timeout of 86400 seconds (24 hours).
   - If `compliance_officer.decision == "APPROVED"`, transition to `STEP_COMPLYADVANTAGE_SCREEN`.
   - If `compliance_officer.decision == "REJECTED"`, transition to `STATE_FINAL_REJECT`.
   - If SLA timeout (86400s) elapses with no action, transition to `STATE_ESCALATE_DIRECTOR_REVIEW`.
5.2. `[Step: HITL_COMPLIANCE_EDD_GATE | Type: human_in_the_loop_gate | Vendor: Jira | Timeout: 86400s]` Enqueue Enhanced Due Diligence (EDD) task in Jira with SLA timeout of 86400s.
   - If `edd_analyst.risk_override == "APPROVE_LOW_RISK"`, transition to `STEP_JURISDICTION_RISK_EVAL`.
   - If `edd_analyst.risk_override == "REJECT"`, transition to `STATE_FINAL_REJECT`.
   - If SLA timeout expires, transition to `STATE_ESCALATE_DIRECTOR_REVIEW`.
5.3. `[Step: STEP_MARQETA_PROVISION | Type: api_call | Vendor: Marqeta | Timeout: 15s]` Call Marqeta Card Program API (`POST /v3/users` and `POST /v3/cardproducts`).
   - If `marqeta.status == "ACTIVE"`, transition to `STEP_SLACK_NOTIFY_SUCCESS`.
   - If `marqeta.status == "FAILED" or marqeta.http_status >= 500`, route to `STATE_ALERT_DEV_OPS`.
5.4. `[Step: STEP_SLACK_NOTIFY_SUCCESS | Type: api_call | Vendor: Slack | Timeout: 10s]` Send success webhook notification payload (`POST /services/webhook`) to `#customer-onboarding-feed` (retry on 500) and transition to `STATE_WORKFLOW_COMPLETE`.

---

## 6. Terminal States & System Handlers
6.1. `[Step: STATE_WORKFLOW_COMPLETE | Type: terminal_state]` Terminal state: Return HTTP 200 with onboarding token and account ID.  
6.2. `[Step: STATE_FINAL_REJECT | Type: terminal_state]` Terminal state: Send adverse action notice email to applicant and archive audit logs.  
6.3. `[Step: STATE_BLOCK_OFAC_SAR_FILING | Type: terminal_state]` Terminal state: Place immediate account freeze, log FinCEN SAR payload, and alert Compliance Officer.  
6.4. `[Step: STEP_SYS_ALERT_FALLBACK | Type: terminal_state]` Terminal state: Dispatch PagerDuty critical incident for system connectivity failure and pause ingestion.  
6.5. `[Step: STATE_ESCALATE_DIRECTOR_REVIEW | Type: terminal_state]` Terminal state: Reassign compliance ticket directly to Managing Director Compliance Queue.  
6.6. `[Step: STATE_ALERT_DEV_OPS | Type: terminal_state]` Terminal state: Dispatch telemetry alert to Core Ledger DevOps team.  
6.7. `[Step: STATE_REJECT_INVALID_PAYLOAD | Type: terminal_state]` Terminal state: Return HTTP 400 Bad Request with schema validation error details.  
6.8. `[Step: STATE_REJECT_INACTIVE_ENTITY | Type: terminal_state]` Terminal state: Issue automatic rejection notice citing Secretary of State inactive status.  
6.9. `[Step: STATE_REJECT_EQUITY_MISMATCH | Type: terminal_state]` Terminal state: Reject application due to beneficial ownership sum != 100%.  
6.10. `[Step: STATE_REJECT_PROHIBITED_JURISDICTION | Type: terminal_state]` Terminal state: Issue adverse action for prohibited jurisdiction.  
6.11. `[Step: STATE_REJECT_PROHIBITED_INDUSTRY | Type: terminal_state]` Terminal state: Issue adverse action for prohibited MCC industry code.  
