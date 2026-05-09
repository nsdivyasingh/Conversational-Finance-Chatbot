# 💼 Payroll Chatbot Assistant

AI-powered conversational chatbot designed to handle payroll, tax, and HR-related queries with high precision. The system combines a **deterministic reasoning engine** with **LLM-based semantic understanding** to provide accurate, data-backed responses while maintaining strict security and privacy standards.

## 🏗️ Architecture Overview

The system is built on a hybrid architecture that balances the creative reasoning of Large Language Models with the rigid accuracy required for financial data.

### 🏗️ Architecture Diagram

```mermaid
graph TD
    User([User]) <--> UI[Streamlit / FastAPI]
    UI <--> Guard[Security Guardrails]
    Guard <--> Router{Hybrid Intent Router}
    
    Router -- FAQ --> FAQ[FAQ Semantic Retrieval]
    Router -- Payroll --> Tools[Deterministic Tool Engine]
    
    FAQ --- Model[all-MiniLM-L6-v2]
    FAQ --- Data[(FAQ JSON)]
    
    Tools --- Meta[Metadata Registry]
    Tools --- SQL[(PostgreSQL)]
    
    FAQ --> Reasoning[Gemini Flash Reasoning]
    Tools --> Reasoning
    
    Reasoning --> Response[Final Answer]
```

> [!NOTE]
> Detailed architecture documentation can be found in the `docs/` folder.
> ![Architecture](docs/architecture.png)

## 🔄 System Workflow

The following workflow ensures every query is handled with maximum accuracy and security:

| Step | Action | Description |
| :--- | :--- | :--- |
| 1 | **Authentication** | Employee ID is validated and stored in session context. |
| 2 | **Validation** | User queries pass through security and guardrail validation. |
| 3 | **Routing** | Queries are classified using hybrid deterministic + semantic routing. |
| 4 | **Retrieval** | FAQ queries use semantic retrieval with **all-MiniLM-L6-v2** embeddings; Payroll queries route to SQL tools. |
| 5 | **Execution** | Structured payroll data is retrieved from PostgreSQL using metadata-driven queries. |
| 6 | **Reasoning** | Gemini Flash is selectively used for semantic reasoning and natural language explanation. |
| 7 | **Delivery** | Final responses are delivered via Streamlit or FastAPI endpoints. |

## 🧠 Hybrid AI Design

The system follows a core philosophy of **"Verifiable Reasoning"**:

- **Deterministic Precision**: Financial values (salary, tax, LOP) are retrieved using strict SQL-backed tools. The LLM never "hallucinates" numbers.
- **Semantic Understanding**: Gemini Flash provides intent classification, query rewriting, and analytical reasoning for complex "Why" questions.
- **Vector Search**: FAQ retrieval uses semantic embeddings and vector similarity search for high-accuracy policy matching.
- **Security-First**: Sensitive payroll values are processed in a sandbox; the LLM only sees the data it needs to explain the result.

## ⚙️ Metadata-Driven Query Understanding

The chatbot utilizes centralized metadata registries to decouple logic from data:
- **Field Aliases**: Maps natural language (e.g., "take home") to DB columns (`total_netpay`).
- **Semantic Mappings**: Links intents to specific tool configurations.
- **Policy Rules**: Defines access control and data visibility at the field level.
- **Schema Relationships**: Manages joins and dependencies between payroll tables.

This enables both deterministic query processing and sophisticated semantic tool orchestration using Gemini.

## 🌟 Key Features

- **Hybrid Intelligence**: Combines deterministic logic for financial accuracy with Gemini Flash models for natural language understanding.
- **Detailed Analysis**:
  - Full salary breakdowns (Earnings vs. Deductions).
  - Month-on-month salary comparisons with reason analysis.
  - Tax liability and deduction tracking.
  - Overtime and reimbursement details.
- **Intelligent FAQ**: Vector-based search using **all-MiniLM-L6-v2** to answer common HR and policy questions.
- **Semantic Query Parsing**: Intelligently handles ambiguous or indirect queries by normalizing them for the payroll engine.
- **Multi-Interface Support**: Includes both a professional **Streamlit UI** and a robust **FastAPI** backend.

## 🏗️ Technical Architecture

- **Frontend**: [Streamlit](https://streamlit.io/) for an interactive, user-friendly chat interface.
- **API Framework**: [FastAPI](https://fastapi.tiangolo.com/) for high-performance service delivery.
- **LLM**: [Google Gemini Flash (gemini-flash-latest)](https://ai.google.dev/) for intent classification, query rewriting, and explanation generation.
- **Database**: PostgreSQL with [SQLAlchemy](https://www.sqlalchemy.org/) ORM.
- **NLP / FAQ**: [Sentence Transformers](https://www.sbert.net/) (`all-MiniLM-L6-v2`) and Scikit-learn.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL Database
- Google Gemini API Key

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/nsdivyasingh/Payroll_Chatbot.git
   cd Payroll_Chatbot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   DATABASE_URL=postgresql://user:password@localhost:5432/payroll_db
   ```

4. **Initialize the FAQ Knowledge Base**:
   ```bash
   python build_faq_kb.py
   ```

### Running the Application

- **Start the Chat Interface (Streamlit)**:
  ```bash
  streamlit run app.py
  ```

- **Start the API Server (FastAPI)**:
  ```bash
  uvicorn api:app --reload
  ```

## 🛠️ Project Structure

- `agents/`: AI agents for FAQ, Payroll logic, and reasoning.
- `services/`: Core logic for query processing, intent routing, and database interaction.
- `tools/`: Deterministic tools for fetching specific payroll components.
- `guardrails/`: Security and privacy layers to prevent unauthorized data access.
- `router/`: Intent classification logic (Hybrid: Deterministic + Semantic).
- `data/`: FAQ source data and generated vector indices.

## 🔒 Security & Privacy

This application implements strict security guardrails:
- **Employee-Level Isolation**: No employee can query data belonging to another user.
- **Deterministic Validation**: Financial figures are always sourced directly from the database, never hallucinated by the LLM.
- **Input Sanitization**: Queries are screened for security violations before processing.

---
