"""Deterministic rule definitions and heuristic patterns for SOP linting."""
import re
from typing import List, Dict, Any

# Ambiguity & Subjectivity Heuristic Rules
AMBIGUITY_RULES: List[Dict[str, Any]] = [
    {
        "id": "AMB_001_SKETCHY",
        "pattern": r"\b(looks?\s+sketchy|feels?\s+suspicious|suspicious\s+looking)\b",
        "title": "Subjective Heuristic: 'Looks Sketchy / Suspicious'",
        "category": "AMBIGUITY_SUBJECTIVITY",
        "severity": "CRITICAL",
        "description": "Human gut-feeling terms ('sketchy', 'suspicious') cannot be evaluated by deterministic execution engines. Requires quantifiable risk indicators.",
        "proposed_codification": "risk_engine.score > 75 OR sanctions_match == True OR negative_news_count >= 1"
    },
    {
        "id": "AMB_002_DISCRETION",
        "pattern": r"\b(analyst\s+discretion|at\s+discretion|use\s+discretion|officer\s+discretion|judgement\s+call)\b",
        "title": "Unbounded Human Discretion",
        "category": "AMBIGUITY_SUBJECTIVITY",
        "severity": "CRITICAL",
        "description": "Unbounded human discretion without deterministic bounding parameters halts automated DAG progression and creates compliance audit risks.",
        "proposed_codification": "HITL_Gate(role='L2_ANALYST', timeout=86400, checklist=['DOC_VALIDITY', 'UBO_AFFIDAVIT'], fallback='AUTO_ESCALATE_DIRECTOR')"
    },
    {
        "id": "AMB_003_REASONABLE_EFFORT",
        "pattern": r"\b(reasonable\s+effort|best\s+efforts?|reasonable\s+diligence|endeavour|attempt\s+to)\b",
        "title": "Vague Compliance Standard: 'Reasonable Effort'",
        "category": "AMBIGUITY_SUBJECTIVITY",
        "severity": "WARNING",
        "description": "'Reasonable effort' is legally vague and computationally non-deterministic. Must specify explicit attempt count, timeout, and fallback policy.",
        "proposed_codification": "retry_policy(max_attempts=3, backoff_sec=5, on_exhaust='ROUTE_TO_EDD_QUEUE')"
    },
    {
        "id": "AMB_004_PROMPTLY",
        "pattern": r"\b(promptly|asap|as\s+soon\s+as\s+possible|in\s+due\s+time|timely\s+manner)\b",
        "title": "Undefined Time Constraint: 'Promptly'",
        "category": "AMBIGUITY_SUBJECTIVITY",
        "severity": "WARNING",
        "description": "Temporal terms like 'promptly' lack an enforceable SLA. Deterministic state machines require explicit timeout durations in seconds.",
        "proposed_codification": "sla_timeout_seconds = 3600 # Explicit 1-hour SLA with alert triggers"
    },
    {
        "id": "AMB_005_AS_NEEDED",
        "pattern": r"\b(as\s+needed|if\s+applicable|when\s+necessary|at\s+times|from\s+time\s+to\s+time)\b",
        "title": "Conditional Vagueness: 'As Needed'",
        "category": "AMBIGUITY_SUBJECTIVITY",
        "severity": "WARNING",
        "description": "'As needed' obscures the predicate condition. The trigger condition must be a formal boolean expression.",
        "proposed_codification": "if (retry_count < 3 AND http_status in [500, 502, 503, 504]): retry() else: raise VendorUnavailableException()"
    },
    {
        "id": "AMB_006_HIGH_RISK_JURISDICTION",
        "pattern": r"\b(high[- ]risk\s+jurisdictions?|sanctioned\s+countries|restricted\s+geographies)\b",
        "title": "Undefined Jurisdictional Variable Set",
        "category": "UNDEFINED_VARIABLE_STATE",
        "severity": "CRITICAL",
        "description": "Mentions 'high-risk jurisdiction' without referencing a deterministic ISO 3166-1 alpha-3 code list or dynamic OFAC risk tier.",
        "proposed_codification": "country_iso in ['IRN', 'PRK', 'RUS', 'SYR', 'CUB', 'MMR'] # FATF & OFAC High-Risk Blacklist"
    },
    {
        "id": "AMB_007_SIGNIFICANT_VOLUME",
        "pattern": r"\b(significant\s+(?:transaction\s+)?volume|large\s+transactions?|unusual\s+activity)\b",
        "title": "Undefined Numeric Threshold: 'Significant Volume'",
        "category": "UNDEFINED_VARIABLE_STATE",
        "severity": "WARNING",
        "description": "Lacks quantitative bounds for volume or frequency. Financial state machines must evaluate exact dollar amounts or standard deviation z-scores.",
        "proposed_codification": "monthly_wire_volume_usd > 250000.00 OR single_wire_amount_usd > 50000.00"
    },
    {
        "id": "AMB_008_HIGH_RISK_ENTITY",
        "pattern": r"\b(unusually\s+high\s+risk|high\s+risk\s+entity|elevated\s+risk)\b",
        "title": "Unquantified Risk Level",
        "category": "AMBIGUITY_SUBJECTIVITY",
        "severity": "WARNING",
        "description": "'High risk' must be mapped to a deterministic risk scoring matrix or ML model classification boundary.",
        "proposed_codification": "composite_risk_score >= 80 (where score = 0.4*geo_risk + 0.3*mcc_risk + 0.3*ubo_risk)"
    },
    {
        "id": "AMB_009_EQUITY_SUM_LESS_THAN_100",
        "pattern": r"(?:ownership|equity|percentages?).*?(?:sum\s+(?:to\s+)?less\s+than\s+100%|< ?100%|less\s+than\s+100%)",
        "title": "Unhandled Equity Discrepancy",
        "category": "UNHANDLED_EXCEPTION_PATH",
        "severity": "CRITICAL",
        "description": "If beneficial ownership equity totals < 100%, routing to subjective investigation rather than an automated validation rejection breaks invariant rules.",
        "proposed_codification": "assert sum(ubo.equity_pct for ubo in declared_ubos) == 100.0, else: transition(STATE_REJECT_EQUITY_MISMATCH)"
    }
]

# Known Financial Back-Office API Vendors & Expected Specs
VENDOR_SIGNATURES: Dict[str, Dict[str, Any]] = {
    "Persona": {
        "pattern": r"\b(persona|persona\s+api|persona\s+kyc|persona\s+inquiry)\b",
        "type": "api_call",
        "domain": "Identity Verification & Biometrics",
        "required_timeout_seconds": 30,
        "required_error_codes": ["400", "401", "404", "429", "500", "504"],
        "recommended_payload": {"inquiry_id": "string", "fields": ["name", "dob", "ssn", "id_photo", "selfie"]},
        "default_fallback": "HITL_MANUAL_KYC_REVIEW(reason='PERSONA_GATEWAY_TIMEOUT')"
    },
    "ComplyAdvantage": {
        "pattern": r"\b(complyadvantage|comply\s+advantage|ofac\s+screening|sanctions\s+screening)\b",
        "type": "api_call",
        "domain": "AML, PEP & Sanctions Screening",
        "required_timeout_seconds": 20,
        "required_error_codes": ["400", "403", "429", "500", "503"],
        "recommended_payload": {"search_term": "string", "filters": ["sanctions", "pep", "adverse_media"]},
        "default_fallback": "HITL_COMPLIANCE_EDD_GATE(reason='COMPLYADVANTAGE_ERROR')"
    },
    "Middesk": {
        "pattern": r"\b(middesk|middesk\s+api|sos\s+verification|secretary\s+of\s+state)\b",
        "type": "api_call",
        "domain": "Corporate Entity & Secretary of State Verification",
        "required_timeout_seconds": 15,
        "required_error_codes": ["400", "404", "500", "502"],
        "recommended_payload": {"business_name": "string", "tin": "string", "state": "string"},
        "default_fallback": "STEP_SYS_ALERT_FALLBACK(reason='MIDDESK_SERVICE_UNAVAILABLE')"
    },
    "Marqeta": {
        "pattern": r"\b(marqeta|marqeta\s+api|ledger|card\s+issuance|card\s+program)\b",
        "type": "api_call",
        "domain": "Core Banking Ledger & Card Provisioning",
        "required_timeout_seconds": 15,
        "required_error_codes": ["400", "409", "500"],
        "recommended_payload": {"user_token": "string", "card_product_token": "string"},
        "default_fallback": "STATE_ALERT_DEV_OPS(reason='MARQETA_PROVISIONING_FAILURE')"
    },
    "Jira": {
        "pattern": r"\b(jira|jira\s+ticket|tier\s+2\s+review|tier\s+2\s+risk\s+review|manual\s+review|compliance\s+queue)\b",
        "type": "human_in_the_loop_gate",
        "domain": "Human-in-the-Loop Compliance Ticketing",
        "required_timeout_seconds": 86400,
        "required_error_codes": [],
        "recommended_payload": {"issue_type": "KYB_ESCALATION", "priority": "HIGH", "sla_seconds": 86400},
        "default_fallback": "STATE_ESCALATE_DIRECTOR_REVIEW(reason='JIRA_SLA_BREACHED')"
    },
    "Slack": {
        "pattern": r"\b(slack|slack\s+webhook|slack\s+channel|slack\/email)\b",
        "type": "api_call",
        "domain": "Operational Notifications & Webhooks",
        "required_timeout_seconds": 10,
        "required_error_codes": ["500"],
        "recommended_payload": {"channel": "#compliance-feed", "text": "string"},
        "default_fallback": "LOG_NOTIFICATION_FALLBACK()"
    }
}
