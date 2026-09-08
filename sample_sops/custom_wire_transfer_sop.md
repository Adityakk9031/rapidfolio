# Standard Operating Procedure (SOP): High-Value International Wire Transfer Operations

**SOP Reference:** SOP-OPS-WIRE-2024-v1.4  
**Department:** Treasury Operations & Anti-Money Laundering (AML)  
**Target:** Outbound Cross-Border SWIFT & Fedwire Transactions >= $50,000  

---

## 1. Wire Initiation & Balance Check
1.1. Ingest outbound international wire transfer request submitted via corporate banking portal.  
1.2. Verify that sending account has sufficient available ledger balance. If funds are insufficient, cancel transaction immediately.  
1.3. If account balance is sufficient, hold wire amount and proceed to screening.  

---

## 2. AML Watchlist & OFAC Screening
2.1. Submit beneficiary name, beneficiary bank BIC/SWIFT code, and intermediary routing info to ComplyAdvantage screening API.  
2.2. If ComplyAdvantage returns an exact OFAC or sanctioned jurisdiction hit, place immediate freeze on the transfer and alert BSA compliance officer.  
2.3. If screening detects a potential PEP match or negative news hit, use reasonable effort to determine whether beneficiary is a high-ranking public official.  
2.4. If the beneficiary looks suspicious or exhibits unusual transaction velocity, escalate to senior investigator.  

---

## 3. Fraud Anomaly & Biometric Step-Up Gate
3.1. Calculate behavioral risk score via Sardine API.  
3.2. If Sardine score is elevated or represents unusually high risk, trigger biometric selfie step-up via Persona API.  
*(Note: If Persona API returns a 504 Gateway Timeout, wait and retry as needed).*  
3.3. If biometric verification succeeds, proceed to dual-authorization gate.  

---

## 4. Dual Approval & Exception Routing
4.1. If wire amount exceeds $250,000, route transaction to Tier 2 Risk Review in Jira for executive approval.  
4.2. If transaction involves a high-risk jurisdiction, request enhanced documentation promptly.  
4.3. Review business wire justification at analyst discretion.  

---

## 5. Settlement & SWIFT Dispatch
5.1. Transmit finalized payment order to Federal Reserve Fedwire / SWIFT Gateway.  
5.2. Upon receiving settlement confirmation from Fedwire, debit customer ledger and generate MT103 confirmation receipt.  
5.3. Send real-time confirmation notification to customer via Slack/Email webhook.  
