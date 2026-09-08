# Rapidfolio SOP Pre-Flight Linter & Deterministic Graph Compiler

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.5+-orange.svg)](https://networkx.org/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-purple.svg)](https://docs.pydantic.dev/)
[![Tests](https://img.shields.io/badge/tests-16%20passed-brightgreen.svg)]()

An enterprise-grade POC tool for **Rapidfolio** that ingests raw banking & fintech Standard Operating Procedures (SOPs), performs deterministic static & semantic linting, flags human-judgment ambiguities and unhandled edge cases, and compiles compliant procedural workflows into executable **Rapidfolio DAG State-Machine Specifications (JSON)**.

---


---

## 📸 Application Showcase

### 1. The "Messy" Audit Failure (The Problem)
Rapidfolio instantly identifies subjective language, unbounded human discretion, and missing SLAs in standard compliance documents that would cause automated pipelines to crash.
![Deterministic Linter catching subjective human language](assets/media_1788871106756.png)

### 2. The "Clean" Score & Vendor Extraction (The Solution)
Once ambiguities are resolved, the engine validates the workflow and automatically extracts 3rd-party API dependencies, fallback paths, and strict SLA timeouts.
![100% Execution Readiness with extracted SLA timeouts](assets/media_1788871118955.png)

### 3. The Generated DAG Visualization
The validated text is compiled into a Directed Acyclic Graph (DAG), mapping every API call, rule evaluation, and human-in-the-loop checkpoint.
![Automated Graph Compilation](assets/media_1788871161916.png)

### 4. The Machine-Readable Output
The final output is a strict, Pydantic-validated state-machine JSON payload, ready to be deployed directly into execution engines like Temporal or AWS Step Functions.
![Compiled State-Machine JSON](assets/media_1788871197831.png)


## âš¡ Problem Context
Financial institutions frequently have messy, contradictory back-office SOPs filled with subjective human judgment calls (*"flag if entity looks sketchy"*, *"review at analyst discretion"*) and unhandled edge cases (e.g., API gateway timeouts, unlinked escalations, beneficial ownership discrepancies). When onboarding new banks onto Rapidfolio, engineers must manually audit and codify these SOPs before turning them into 99.9%+ deterministic DAG workflows.

This tool automates that pre-flight audit and compilation pipeline.

---

## ðŸ—ï¸ Architecture & Core Components

```
rapidflow/
â”œâ”€â”€ README.md
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ run.py                          # Server launcher (FastAPI + Uvicorn)
â”œâ”€â”€ sample_sops/                    # Built-in sample SOPs for rapid demonstration
â”‚   â”œâ”€â”€ messy_kyb_sop.md            # Realistic messy U.S. Bank KYB manual (50-60% score)
â”‚   â””â”€â”€ clean_kyb_sop.md            # Fully codified, deterministic KYB SOP (100% score)
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ api/                        # FastAPI REST API & SPA host
â”‚   â”‚   â”œâ”€â”€ app.py
â”‚   â”‚   â””â”€â”€ routes.py
â”‚   â”œâ”€â”€ compiler/                   # Rapidfolio DAG Compiler & Graph Builder
â”‚   â”‚   â”œâ”€â”€ dag_exporter.py
â”‚   â”‚   â””â”€â”€ graph_builder.py
â”‚   â”œâ”€â”€ linter/                     # Static & Semantic Analysis Engine
â”‚   â”‚   â”œâ”€â”€ ambiguity_scanner.py    # Subjectivity & vague terms heuristic scanner
â”‚   â”‚   â”œâ”€â”€ graph_analyzer.py       # NetworkX DiGraph topology & dead-end validator
â”‚   â”‚   â”œâ”€â”€ rules.py                # Regex rules & programmatic boolean codifications
â”‚   â”‚   â”œâ”€â”€ scoring.py              # 0-100% Deterministic Readiness Score calculator
â”‚   â”‚   â””â”€â”€ vendor_tagger.py        # Financial API tagger (Persona, Middesk, Marqeta, etc.)
â”‚   â”œâ”€â”€ llm/                        # Optional LiteLLM/Gemini refinement with offline fallback
â”‚   â”‚   â””â”€â”€ client.py
â”‚   â””â”€â”€ schemas/                    # Strict Pydantic v2 data models
â”‚       â”œâ”€â”€ audit.py
â”‚       â”œâ”€â”€ dag.py
â”‚       â””â”€â”€ sop.py
â”œâ”€â”€ static/                         # Modern Dark-Mode SPA
â”‚   â”œâ”€â”€ css/styles.css
â”‚   â”œâ”€â”€ js/app.js
â”‚   â””â”€â”€ index.html
â””â”€â”€ tests/                          # 16 Pytest unit & integration tests
    â”œâ”€â”€ test_ambiguity_scanner.py
    â”œâ”€â”€ test_api.py
    â”œâ”€â”€ test_compiler.py
    â”œâ”€â”€ test_extended.py
    â”œâ”€â”€ test_graph_analyzer.py
    â”œâ”€â”€ test_scoring.py
    â””â”€â”€ test_vendor_tagger.py
```

---

## ðŸ” Key Features

1. **Ambiguity & Subjectivity Scanner (`src/linter/ambiguity_scanner.py`)**:
   - Flags non-deterministic phrases (`"looks sketchy"`, `"analyst discretion"`, `"reasonable effort"`, `"promptly"`, `"as needed"`).
   - Proposes concrete boolean/programmatic replacements (e.g. `risk_engine.score > 75 OR sanctions_match == True`).

2. **NetworkX Graph Topology & Edge-Case Analyzer (`src/linter/graph_analyzer.py`)**:
   - Converts procedural steps into directed graph (`DiGraph`).
   - Discovers **dead-end steps** (e.g., routing to "Tier 2 Review" with no downstream transition or timeout).
   - Identifies **infinite loops and circular logic** using `nx.simple_cycles()`.
   - Flags **unhandled API exceptions** (e.g., HTTP 504 gateway timeouts on Persona KYC checks).

3. **Vendor Integration Tagger (`src/linter/vendor_tagger.py`)**:
   - Detects financial back-office APIs (*Persona*, *ComplyAdvantage*, *Middesk*, *Marqeta*, *Jira*, *Slack*).
   - Validates SLA timeout declarations, network error recovery policies, and input/output payload schemas.

4. **Deterministic Readiness Scoring (`src/linter/scoring.py`)**:
   - Calculates a weighted score from 0 to 100%.
   - Status classifications: `READY_FOR_COMPILATION` (Green), `REQUIRES_REMEDIATION` (Amber), `CRITICAL_BLOCKERS` (Red).

5. **Rapidfolio DAG State-Machine Exporter (`src/compiler/dag_exporter.py`)**:
   - Compiles validated SOPs into Rapidfolio-compliant JSON state-machines (`workflow_id`, `nodes`, `edges`, conditional expressions, `hitl_checkpoints`).

6. **Interactive Dark-Mode UI (`static/index.html`)**:
   - Side-by-side view with Markdown editor, presets, and live line count.
   - Interactive Cytoscape.js DAG visualizer with node payload/SLA inspector.
   - Expandable audit issue cards with one-click **"Copy Rule"** and **"Apply Codification"** actions.
   - One-click JSON DAG export and download.

---

## ðŸš€ Getting Started

### 1. Prerequisites
- Python 3.11+

### 2. Installation
```bash
# Clone or open directory
cd d:/Rapidflow

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python run.py
```
Open your browser and navigate to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## ðŸ§ª Running Automated Tests
Run the deterministic Pytest suite:
```bash
python -m pytest -v
```
All 16 tests assert exact readiness scores, NetworkX graph integrity, vendor spec detection, and API payload contracts.

---

## ðŸ“‘ REST API Documentation
Once running, explore interactive Swagger docs at:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### Key Endpoints:
- `POST /api/audit`: Runs full static & semantic linting on raw SOP text, returning `AuditReport`.
- `POST /api/compile`: Audits and compiles SOP text into `RapidfolioDAG` JSON.
- `GET /api/samples`: Lists available sample SOP files (`messy_kyb_sop.md`, `clean_kyb_sop.md`).
- `GET /api/samples/{filename}`: Fetches raw content of a sample SOP.
- `GET /api/health`: Health status.

