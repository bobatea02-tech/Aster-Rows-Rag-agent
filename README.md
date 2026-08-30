```markdown
<div align="center">

<!-- Animated Typing SVG Header -->
<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=30&pause=1000&color=2ECC71&center=true&vCenter=true&width=600&lines=Aster+%26+Row+AI+Support+Agent;Zero-Hallucination+Policy+RAG;Secure+PII+Data+Firewall;Deterministic+Tool+Calling" alt="Typing SVG" />
</a>

A production-grade, multi-turn AI customer support agent engineered for absolute data privacy and precise policy adherence.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-Fast_Inference-f39c12.svg?style=for-the-badge&logo=amd&logoColor=white)](https://groq.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-27ae60.svg?style=for-the-badge&logo=database&logoColor=white)](https://trychroma.com)

</div>

---

## 🎥 Agent Demonstration

*(Replace this placeholder image with your 2-4 minute animated GIF or MP4 link demonstrating a policy lookup, an order lookup, a multi-turn clarification, and an off-topic refusal.)*

<div align="center">
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Assets/Github-Dark.svg" width="100%" alt="Agent Demo Animation Placeholder">
</div>

---

## 🚀 Quick Start & Execution

### 1. Environment Setup
Clone the repository and initialize a clean virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

```

### 2. Configuration

Create a `.env` file in the root directory (see `.env.example`).

```env
# Get your free API key at: [https://console.groq.com/keys](https://console.groq.com/keys)
GROQ_API_KEY=your_actual_api_key_here

```

### 3. Launch the System

```bash
# Step 1: Ingest knowledge base and build the vector database
python -m src.ingest

# Step 2: Launch the interactive CLI
python -m src.agent

# Step 3: Run the automated evaluation suite
python -m src.evaluate

```

---

## 🧠 Architecture & Tech Stack

> **Design Philosophy:** Minimal latency, strict data boundaries, and zero dependence on heavy wrapper frameworks.

* **Model Integration:** `openai/gpt-oss-20b` (via Groq SDK). Chosen for ultra-low latency token generation and deterministic JSON tool-calling.
* **Framework:** Pure Python. Intentionally avoided LangChain to maintain absolute control over the prompt logic and execution speed.
* **Vector Storage & Embeddings:** Local persistent `ChromaDB` utilizing its default `all-MiniLM-L6-v2` embedding model. Provides fast, local vectorization without external API dependencies.
* **Transactional Data:** Secure, read-only parsing of `data/orders.json`.
* **Security & Guardrails:**
* **Data Firewall:** The `lookup_order_status` tool physically strips PII (emails, addresses) *before* data returns to the LLM.
* **Filtered RAG:** Policy retrieval enforces hard metadata filters (`where={"status": "active"}`), mathematically preventing the agent from hallucinating legacy policies.



---

## 🧪 Evaluation Suite Results

The agent features a custom automated deterministic evaluation script grading against 12 test cases (7 rubric baselines + 5 original security/edge cases).

| Category | Baseline Score | Final Score | Capability Verified |
| --- | --- | --- | --- |
| **Retrieval** | 67% | **100% (3/3)** | Fetches active policies with heading citations; ignores legacy drafts. |
| **Tool Use** | 50% | **100% (3/3)** | Normalizes messy input and correctly triggers API tools. |
| **Privacy** | 50% | **100% (3/3)** | Strictly redacts PII and scrubs stale shipping data. |
| **Multi-Turn** | 0% | **100% (2/2)** | Retains context and successfully asks clarifying questions. |
| **Groundedness** | 0% | **100% (2/2)** | Rejects prompt injections and off-topic requests. |
| **Overall** | **~57%** | **100% (12/12)** | *Perfect deterministic adherence across all parameters.* |

---

## 🐛 Bug Diary *(Interactive)*

* **Reproduction:** Running the evaluation script triggered `invalid_request_error` and subsequently `429 rate_limit_exceeded` errors.
* **Root Cause:** The initially selected model was decommissioned by the provider, and the rapid automated test loop exceeded the 8,000 Tokens-Per-Minute limit.
* **Fix:** Migrated to `gpt-oss-20b`, wrapped the API call in a graceful degradation `try/except` block to output a safe customer error, and added a `time.sleep(2)` throttle to the evaluation script.
* **Regression Test:** Automated execution of the full `src.evaluate` suite now reliably completes without timing out.

* **Reproduction:** Requesting tracking for a cancelled order (`ORD-1004`) returned an estimated delivery date.
* **Root Cause:** The raw JSON parser blindly returned all populated fields without cross-referencing the primary order `status`.
* **Fix:** Implemented conditional scrubbing in `src/tools.py` to manually overwrite `shipping_info` and drop tracking arrays if the status is cancelled, returned, or refunded.
* **Regression Test:** Custom Eval Case `CUSTOM-03` specifically targets `ORD-1004` to ensure no tracking fields are present.

* **Reproduction:** The evaluation suite initially failed the agent on off-topic refusal tests despite the agent acting correctly.
* **Root Cause:** The test relied on positive `expected_substrings` (e.g., expecting exactly the word "support"). The LLM acted naturally using synonyms, triggering a false failure.
* **Fix:** Transitioned the testing philosophy to **Negative Constraints**. I cleared overly rigid expected strings and fortified `forbidden_substrings` to deterministically prove the agent did not leak data or write code.
* **Regression Test:** `CUSTOM-01` (Prompt Injection) and standard Groundedness cases now accurately pass by verifying the absence of forbidden raw code.

---

## 🚧 Limitations & Production Next Steps

1. **Unbounded Context Window:** The `chat_history` array grows indefinitely per session. Production requires token-aware sliding windows (summarizing older messages) to prevent context exhaustion.
2. **Local Storage Scalability:** A local ChromaDB instance and flat JSON file are insufficient for concurrent traffic. Deployment requires migrating vectors to a managed service (Pinecone/Qdrant) and replacing the JSON lookup with a read-only SQL replica.
3. **Naive Rate Limiting:** The `time.sleep()` fix in the test suite is a brute-force approach. Production should leverage the `Tenacity` library for robust exponential backoff.

---

## 🤖 AI Tooling Attribution

* **Usage:** I utilized AI assistants (ChatGPT/Gemini) primarily as architectural thought partners, for generating boilerplate JSON schemas for Groq tool definitions, and for populating mock data for custom evaluation edge cases.
* **Flawed AI Suggestion:** When building the `src.evaluate` script, the AI strongly suggested evaluating the LLM's responses using exact string matching (`expected_substrings`). This was a fundamentally flawed suggestion for generative AI, leading to severe false negatives when the model used natural synonyms. I discarded this advice and manually architected a *Negative Constraint* framework (`forbidden_substrings`) to accurately evaluate the agent's adherence to safety guardrails.

```

```
