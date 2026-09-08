# Standard Operating Procedure (SOP): Commercial Entity KYB & Onboarding

**SOP Reference:** SOP-OPS-KYB-2024-v2.1  
**Department:** Financial Crime & Global Compliance Operations  
**Target:** U.S. Commercial Business Account Applications  

---

## 1. Initial Intake & Application Ingestion
1.1. Ingest entity onboarding application submitted via web portal.  
1.2. Capture Secretary of State (SOS) registration documents and Articles of Incorporation.  
1.3. Query Middesk API for corporate registry status and active business standing in the state of incorporation.  
1.4. If business standing is inactive or revoked, reject application immediately. Otherwise, proceed to Beneficial Ownership verification.

---

## 2. Ultimate Beneficial Ownership (UBO) Verification
2.1. Extract all Ultimate Beneficial Owners (UBO) holding an equity stake in the entity.  
2.2. Verify that all listed UBOs collectively account for the company's equity. If the ownership percentages sum to less than 100%, investigate further at analyst discretion.  
2.3. For each individual UBO with >= 25% equity:
   - Request full legal name, Date of Birth (DOB), Social Security Number (SSN), and residential address.
   - Run identity and biometric verification via Persona API.
   - If Persona returns a match score >= 85, mark UBO identity as verified.
   - If Persona returns verification failure, reject the UBO.
   *(Note: If Persona API returns a 504 Gateway Timeout or connectivity error, wait and retry as needed).*

---

## 3. Sanctions, Watchlist & PEP Screening
3.1. Submit entity name, DBA names, and all verified UBO identities to ComplyAdvantage for global sanctions, PEP (Politically Exposed Persons), and adverse media screening.  
3.2. If ComplyAdvantage confirms an exact OFAC/Sanctions match, block entity instantly and file SAR (Suspicious Activity Report) within 24 hours.  
3.3. If PEP match or adverse media hit is detected, make a reasonable effort to ascertain whether the individual is actively in public office.  
3.4. If the entity or UBO looks sketchy or represents unusually high risk, escalate to compliance manager.  

---

## 4. Jurisdiction & Industry Risk Assessment
4.1. Check principal place of business against high-risk jurisdictions. If operating in a high-risk jurisdiction, request enhanced documentation promptly.  
4.2. Review merchant NAICS / MCC classification code. High-risk industries (e.g., cannabis, adult entertainment, money services businesses) require Tier 2 Risk Review.  
4.3. If business conducts significant international wire transaction volume, assess liquidity requirements.  

---

## 5. Escalation & Final Decisioning
5.1. Applications flagged for manual review should be routed to Tier 2 Review in Jira.  
5.2. If all verification criteria pass without flags, provision commercial ledger account via Marqeta and issue virtual card credentials.  
5.3. Notify applicant of account approval via Slack/Email webhook.
