# AI ISO 27001 Compliance Assistant

An enterprise-ready AI assistant designed to automate and accelerate ISO/IEC 27001:2022 compliance readiness, policy gap assessments, and risk register management using Python, SQLite, and Streamlit.

---

## 1. Project Overview

Achieving and maintaining ISO/IEC 27001:2022 compliance requires analyzing extensive organizational policies, procedures, and evidence against the standard's mandatory management system clauses (Clauses 4–10) and 93 Annex A information security controls.

The **AI ISO 27001 Compliance Assistant** streamlines this process:
1. Ingests and parses compliance artifacts (PDF, DOCX, XLSX).
2. Performs automated Gap Analysis mapped to ISO/IEC 27001:2022 requirements.
3. Identifies organizational information security risks and generates an actionable Risk Register.
4. Provides an intuitive Streamlit interface for compliance officers, auditors, and CISOs.
5. Persists all audit trails, findings, and configurations in a lightweight SQLite database.

---

## 2. System Architecture

The project follows a modular, layered architecture ensuring clean separation of concerns between presentation, business services, AI orchestration, data extraction, and persistence.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Streamlit Presentation                          │
│   (Upload Dashboard | Gap Analysis Matrix | Risk Register | Reports)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           Service Layer                                │
│   ┌───────────────────────┬──────────────────────┬─────────────────┐   │
│   │   Document Service    │ Gap Analysis Service │  Risk Service   │   │
│   │ (Ingestion & Storage) │  (Audit Evaluation)  │ (Matrix & SoA)  │   │
│   └───────────┬───────────┴──────────┬───────────┴────────┬────────┘   │
└───────────────┼──────────────────────┼────────────────────┼────────────┘
                │                      │                    │
                ▼                      ▼                    ▼
┌─────────────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│    Extractor Engine     │  │  AI Orchestrator │  │ Persistence (SQLite)│
│ ┌─────────────────────┐ │  │ ┌──────────────┐ │  │ ┌─────────────────┐ │
│ │ PDF (pdfplumber)    │ │  │ │ LiteLLM / LLM│ │  │ │ SQLAlchemy 2.0  │ │
│ ├─────────────────────┤ │  │ │ Client Layer │ │  │ ├─────────────────┤ │
│ │ DOCX (python-docx)  │ │  │ ├──────────────┤ │  │ │ SQLite DB Engine│ │
│ ├─────────────────────┤ │  │ │ Prompt Engine│ │  │ ├─────────────────┤ │
│ │ XLSX (openpyxl)     │ │  │ ├──────────────┤ │  │ │ Data Models &   │ │
│ └─────────────────────┘ │  │ │ Pydantic v2  │ │  │ │ Audit Logs      │ │
│                         │  │ │ Schemas      │ │  │ └─────────────────┘ │
└─────────────────────────┘  └──────────────────┘  └─────────────────────┘
                                       │
                                       ▼
                             ┌───────────────────┐
                             │ ISO 27001:2022 KB │
                             │ 93 Annex A + Cls  │
                             └───────────────────┘
```

---

## 3. Technology Stack & Rationale

| Category | Technology | Rationale |
| :--- | :--- | :--- |
| **Language** | Python 3.12 / 3.13 | Optimal balance of modern language features, ecosystem stability, and library compatibility on Windows. |
| **Web Interface** | Streamlit | Rapid interactive dashboard development, built-in state management, native support for data tables, metrics, and file upload components. |
| **Database & ORM** | SQLite + SQLAlchemy 2.0 | Zero-configuration, file-based relational storage with full ACID compliance; SQLAlchemy 2.0 provides type-safe, declarative models and seamless migration paths to PostgreSQL if scaled. |
| **Document Parsing** | `pdfplumber`, `python-docx`, `openpyxl` | Robust extraction for enterprise document formats: text, hierarchy, tables, and multi-sheet workbooks without requiring external non-Python binaries. |
| **Data Validation** | Pydantic v2 | High-performance schema validation, settings management, and structured output parsing for AI responses. |
| **AI Orchestration** | LiteLLM / Custom Provider Client | Provider-agnostic abstraction supporting OpenAI, Azure OpenAI, Anthropic, Google Gemini, and local models (e.g., Ollama) with structured JSON enforcement. |
| **Analytics & Export** | Pandas, XlsxWriter, WeasyPrint/ReportLab | Structured tabular processing and export of Gap Analysis and Risk Register into Excel and executive PDF formats. |
| **Quality & Testing** | Ruff, Pytest, MyPy | Fast linting, static type verification, and comprehensive unit/integration test coverage. |

---

## 4. Proposed Project Structure

```
AI-ISO27001/
├── .env.example                     # Sample environment variables (API keys, settings)
├── .gitignore                       # Git ignore configuration
├── pyproject.toml                   # Project metadata, dependencies, and tool settings
├── README.md                        # Project documentation and roadmap
├── requirements.txt                 # Application dependencies
├── requirements-dev.txt             # Development and testing dependencies
│
├── data/                            # Local application data storage (gitignored)
│   ├── app.db                       # SQLite database
│   ├── standards/
│   │   └── iso27001_2022.json       # ISO 27001:2022 reference catalog (Clauses + Annex A)
│   └── uploads/                     # Secure local store for uploaded compliance docs
│
├── src/
│   └── iso_assistant/
│       ├── __init__.py
│       ├── config.py                # Pydantic BaseSettings for application configuration
│       ├── constants.py             # ISO control definitions, status enums, risk matrices
│       │
│       ├── db/                      # Persistence layer
│       │   ├── __init__.py
│       │   ├── connection.py        # SQLite engine, sessionmaker, database initialization
│       │   ├── models.py            # SQLAlchemy declarative database entities
│       │   └── repository.py        # Data access objects (CRUD operations)
│       │
│       ├── security/                # File validation & audit logging
│       │   ├── __init__.py
│       │   ├── file_validator.py    # Strict MIME/magic byte validation & sanitization
│       │   └── audit_logger.py      # Tamper-evident change history & approval logs
│       │
│       ├── extractors/              # Document extraction module
│       │   ├── __init__.py
│       │   ├── base.py              # AbstractBaseExtractor interface
│       │   ├── factory.py           # File-type detection and extractor factory
│       │   ├── pdf_extractor.py     # PDF text and table extraction (pdfplumber)
│       │   ├── docx_extractor.py    # DOCX paragraph and table extraction (python-docx)
│       │   └── xlsx_extractor.py    # Spreadsheet sheets and data parsing (openpyxl)
│       │
│       ├── ai/                      # AI orchestration and prompt management
│       │   ├── __init__.py
│       │   ├── provider_base.py     # Abstract base provider interface
│       │   ├── client.py            # Unified LLM provider client wrapper & Mock fallback
│       │   ├── prompts.py           # Domain prompts for Gap Analysis and Risk Register
│       │   └── schemas.py           # Pydantic schemas for LLM structured outputs
│       │
│       ├── soa/                     # Dedicated Statement of Applicability module
│       │   ├── __init__.py
│       │   ├── models.py            # SoA entry schemas and justification enums
│       │   └── service.py           # 93-control applicability lifecycle & auditor sign-off
│       │
│       ├── services/                # Core business logic
│       │   ├── __init__.py
│       │   ├── document_service.py  # Ingestion workflow, hashing, chunking, storage
│       │   ├── gap_analysis.py      # Clause & Annex A evaluation (AI draft vs Human review)
│       │   ├── risk_service.py      # Risk calculation (5x5 matrix), treatment, SoA mapping
│       │   └── report_service.py    # Excel / PDF export generators
│       │
│       └── utils/                   # Shared utility functions
│           ├── __init__.py
│           ├── logger.py            # Structured logging setup
│           └── text.py              # Text cleaning, normalization, chunking
│
├── ui/                              # Streamlit Frontend
│   ├── __init__.py
│   ├── app.py                       # Main application entry point & dashboard overview
│   ├── state.py                     # Session state management
│   ├── components/                  # Reusable UI widgets
│   │   ├── __init__.py
│   │   ├── charts.py                # Plotly compliance gauges and risk heatmaps
│   │   ├── metrics.py               # Key metric cards
│   │   └── tables.py                # Interactive styled data tables
│   │
│   └── pages/                       # Multi-page application structure
│       ├── 1_📁_Document_Upload.py  # File upload, parsing status, text preview
│       ├── 2_📊_Gap_Analysis.py     # Clause & control gap matrix with AI audit
│       ├── 3_🛡️_Risk_Register.py    # Risk identification, 5x5 heatmap, treatment plans
│       ├── 4_📋_Statement_of_Applicability.py # SoA management (93 Annex A controls)
│       ├── 5_📑_Reports_Export.py   # Executive summary, XLSX/PDF report downloads
│       └── 6_⚙️_Settings.py         # API keys, model configuration, standards browser
│
└── tests/                           # Automated testing suite
    ├── __init__.py
    ├── conftest.py                  # Pytest fixtures (in-memory SQLite, sample docs)
    ├── unit/
    │   ├── __init__.py
    │   ├── test_security.py         # File validation and audit logging unit tests
    │   ├── test_extractors.py       # Unit tests for PDF, DOCX, XLSX parsers
    │   ├── test_db.py               # Unit tests for models and repository CRUD
    │   ├── test_gap_analysis.py     # Unit tests for AI draft vs human review separation
    │   ├── test_risk_service.py     # Unit tests for risk scoring and matrix
    │   └── test_soa.py              # Unit tests for Statement of Applicability models
    └── integration/
        ├── __init__.py
        └── test_pipeline.py         # End-to-end ingestion and analysis flow
```

---

## 5. ISO/IEC 27001:2022 Domain Model

The assistant incorporates the complete 2022 standard specification:

### Mandatory Management System Clauses
- **Clause 4**: Context of the organization (4.1–4.4)
- **Clause 5**: Leadership (5.1–5.3)
- **Clause 6**: Planning & Risk Assessment (6.1–6.3)
- **Clause 7**: Support & Competence (7.1–7.5)
- **Clause 8**: Operation (8.1–8.3)
- **Clause 9**: Performance Evaluation (9.1–9.3)
- **Clause 10**: Improvement (10.1–10.2)

### Annex A Controls (93 controls across 4 domains)
1. **Organizational Controls** (A.5.1 – A.5.37) — Policies, governance, asset management, supplier relationships.
2. **People Controls** (A.6.1 – A.6.8) — Screening, awareness, remote working, disciplinary process.
3. **Physical Controls** (A.7.1 – A.7.14) — Physical security perimeter, equipment protection, clear desk/screen.
4. **Technological Controls** (A.8.1 – A.8.34) — Access control, cryptography, secure coding, network security, vulnerability management.

---

## 6. Database Schema Design (SQLite)

```sql
-- Organization / Compliance Project
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    organization_name TEXT NOT NULL,
    scope_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingested Documents
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL, -- PDF, DOCX, XLSX
    file_hash TEXT NOT NULL, -- SHA-256 for deduplication
    file_size_bytes INTEGER NOT NULL,
    raw_text TEXT,
    extracted_metadata JSON,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- ISO 27001:2022 Control Baseline Reference
CREATE TABLE iso_controls (
    id TEXT PRIMARY KEY,       -- e.g., "A.5.1" or "Clause.6.1.2"
    category TEXT NOT NULL,    -- "Clause" or "Annex A"
    theme TEXT NOT NULL,       -- "Organizational", "People", "Physical", "Technological"
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    guidance TEXT
);

-- Gap Analysis Assessment Records (AI Draft vs Human Approved Separation)
CREATE TABLE gap_assessments (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    control_id TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'AI Draft', -- "AI Draft", "Under Review", "Human Approved", "Human Rejected"
    -- AI Generated Evaluation
    ai_status TEXT, -- "Compliant", "Partially Compliant", "Non-Compliant", "Not Applicable"
    ai_compliance_score REAL,
    ai_evidence_found TEXT,
    ai_identified_gaps TEXT,
    ai_remediation_plan TEXT,
    ai_confidence_score REAL,
    ai_model_name TEXT,
    ai_assessed_at TIMESTAMP,
    -- Human Auditor Review & Override
    human_status TEXT,
    human_compliance_score REAL,
    human_notes TEXT,
    approved_by TEXT,
    approved_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (control_id) REFERENCES iso_controls(id)
);

-- Statement of Applicability (SoA)
CREATE TABLE soa_items (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    control_id TEXT NOT NULL,
    is_applicable BOOLEAN NOT NULL DEFAULT 1,
    justification TEXT NOT NULL, -- Mandatory justification for inclusion or exclusion
    implementation_status TEXT NOT NULL DEFAULT 'Planned', -- "Implemented", "In Progress", "Planned", "Not Implemented"
    responsible_role TEXT,
    target_date TEXT,
    auditor_verified BOOLEAN NOT NULL DEFAULT 0,
    verified_by TEXT,
    verified_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (control_id) REFERENCES iso_controls(id)
);

-- Information Security Risk Register
CREATE TABLE risk_items (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    risk_title TEXT NOT NULL,
    asset_or_process TEXT NOT NULL,
    threat TEXT NOT NULL,
    vulnerability TEXT NOT NULL,
    impacted_cia TEXT NOT NULL, -- "Confidentiality", "Integrity", "Availability" or combination
    inherent_likelihood INTEGER CHECK(inherent_likelihood BETWEEN 1 AND 5),
    inherent_impact INTEGER CHECK(inherent_impact BETWEEN 1 AND 5),
    inherent_risk_score INTEGER, -- Likelihood * Impact (1-25)
    inherent_risk_level TEXT NOT NULL,
    treatment_strategy TEXT NOT NULL, -- "Mitigate", "Avoid", "Transfer", "Accept"
    mapped_controls TEXT, -- JSON array of ISO control IDs (e.g. ["A.8.2", "A.8.24"])
    treatment_details TEXT,
    residual_likelihood INTEGER CHECK(residual_likelihood BETWEEN 1 AND 5),
    residual_impact INTEGER CHECK(residual_impact BETWEEN 1 AND 5),
    residual_risk_score INTEGER,
    residual_risk_level TEXT,
    risk_owner TEXT,
    status TEXT NOT NULL DEFAULT 'Open', -- "Open", "In Progress", "Mitigated", "Accepted"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Tamper-Evident Audit Trail
CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    performed_by TEXT NOT NULL,
    previous_state TEXT, -- JSON snapshot
    new_state TEXT,      -- JSON snapshot
    comment TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

---

## 7. Development Roadmap

### Phase 1: Foundation, Data Models & Document Ingestion
- [ ] Initialize repository structure, configurations (`pyproject.toml`, `.env.example`).
- [ ] Create SQLite database schema and SQLAlchemy ORM models.
- [ ] Implement ISO 27001:2022 reference knowledge base (Clauses 4-10 + 93 Annex A controls).
- [ ] Build file parsers (`pdfplumber` for PDF, `python-docx` for DOCX, `openpyxl` for XLSX).
- [ ] Implement document deduplication (SHA-256) and text chunking utilities.
- [ ] Unit tests for parsers and database repository.

### Phase 2: AI Orchestration & Gap Analysis Engine
- [ ] Build LLM client integration supporting flexible providers and structured outputs.
- [ ] Design ISO 27001 evaluation prompt pipelines with context injection.
- [ ] Implement the Gap Analysis engine: compliance status classification, evidence mapping, and remediation guidance.
- [ ] Implement scoring logic (compliance percentage by domain and overall).
- [ ] Unit tests for gap assessment services.

### Phase 3: Risk Assessment & Risk Register Generation
- [ ] Design threat and vulnerability identification engine based on uploaded documentation.
- [ ] Implement ISO 27005 / ISO 31000 aligned 5x5 Likelihood/Impact risk scoring engine.
- [ ] Auto-map risks to corresponding ISO 27001:2022 Annex A controls.
- [ ] Implement residual risk calculation post-treatment.
- [ ] Unit tests for risk calculation and matrix mapping.

### Phase 4: Streamlit Interactive Interface
- [ ] Build Streamlit core application shell and navigation state.
- [ ] Implement **Document Upload page**: multi-file dropzone, parsing feedback, and extracted text inspector.
- [ ] Implement **Gap Analysis page**: interactive matrix filtering by theme, compliance status filters, and detailed finding modals.
- [ ] Implement **Risk Register page**: editable risk table, 5x5 Plotly risk heatmap, and treatment management.
- [ ] Implement **Settings & Knowledge Base page**: API key management and control reference explorer.

### Phase 5: Reporting, Export & Production Readiness
- [ ] Implement XLSX and PDF export generators (Gap Analysis Report, Statement of Applicability - SoA, and Risk Register).
- [ ] End-to-end integration testing with realistic compliance documents.
- [ ] Performance optimization (caching extracted texts, batched database operations).
- [ ] Final documentation and user guide.

---

## 8. Getting Started & Setup Guide

### Prerequisites
- **Python:** Python 3.12 or 3.13 recommended (64-bit).
- **Git:** Git 2.40+ installed.

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/your-org/AI-ISO27001.git
cd AI-ISO27001

# Create and activate Python 3.13 virtual environment
py -3.13 -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

### 3. Environment Configuration
```bash
# Copy example environment configuration
cp .env.example .env
```
*Note: By default, `LLM_PROVIDER="mock"` is enabled. The application runs 100% offline without requiring paid API keys or external network connections.*

### 4. Run Test Suite & Linter
```bash
# Run automated tests
pytest -v

# Run code style and lint checks
ruff check .
```

### 5. Launch Streamlit Application
```bash
streamlit run ui/app.py
```

---

## 9. Security & Compliance Safeguards

- **Offline-by-Default:** Operates with a local deterministic `MockLLMProvider` for zero-leakage local compliance evaluation.
- **Strict Ingestion Validation:** Multi-layer file security with path sanitization, 25 MB file size limit, and MIME magic-byte verification against header spoofing.
- **Tamper-Evident Audit Trail:** Every assessment modification, risk rating, and auditor approval is timestamped and recorded in the SQLite audit log.
- **Copyright Compliance:** Adheres to ISO copyright protections by utilizing only structural clause numbers, standard control codes, and non-copyrighted metadata summaries.


