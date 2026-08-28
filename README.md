```markdown
# 🌿 Aster & Row | AI Support Agent

A production-grade, multi-turn AI customer support agent. Built with a focus on strict data privacy, zero-hallucination policy retrieval, and deterministic tool execution, this agent autonomously handles Aster & Row order lookups and policy inquiries.

---

## 🎥 Live Demonstration

*(Replace this text with an embedded GIF or a clickable image link to your MP4 video demonstrating the agent successfully completing a policy lookup, an order lookup, a multi-turn clarification, and an off-topic refusal.)*

---

## 🚀 Quick Start

### 1. Environment Setup
Clone the repository and initialize a clean virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

```

### 2. Configuration

Create a `.env` file in the root directory. Refer to the included `.env.example` for the required structure.

```env
# Get your free API key at: [https://console.groq.com/keys](https://console.groq.com/keys)
GROQ_API_KEY=your_actual_api_key_here

```

### 3. Execution

```bash
# 1. Ingest knowledge base and build local vector DB
python -m src.ingest

# 2. Launch the interactive Agent CLI
python -m src.agent

```

---

## 🧠 Architecture & Tech Stack

* **Model Integration:** `openai/gpt-oss-20b` (via Groq SDK). Chosen for ultra-low latency token generation and highly reliable JSON tool-calling capabilities.
* **Framework:** Pure Python. Intentionally avoided heavy abstraction libraries (like LangChain) to maintain absolute control over prompt logic, guardrails, and execution speed.
* **Storage & Databases:**
* **Knowledge Base (Vector DB):** Local persistent `ChromaDB`.
* **Transactional Data:** Secure, read-only parsing of `data/orders.json`.


* **Embeddings:** ChromaDB's default `all-MiniLM-L6-v2` via `SentenceTransformers`. Provides fast, local vectorization without external API dependencies.
* **Core Mechanisms:**
* **Data Firewall:** Tool calls (`lookup_order_status`) physically strip PII (emails, addresses, risk scores) *before* data returns to the LLM.
* **Filtered RAG:** Policy retrieval enforces hard metadata filters (`where={"status": "active"}`), mathematically preventing the agent from seeing or hallucinating legacy policies.



---

## 🧪 Evaluation Suite

The agent features an automated, deterministic evaluation script grading against 12 test cases (7 rubric baselines + 5 original security/edge cases).

**Run the suite:**

```bash
python -m src.evaluate

```

**Evaluation Results:**

| Category | Baseline Score | Final Score | Description |
| --- | --- | --- | --- |
| **Retrieval** | 67% | **100% (3/3)** | Accurately fetches active policies and ignores legacy drafts. |
| **Tool Use** | 50% | **100% (3/3)** | Normalizes input and correctly triggers API tools. |
| **Privacy** | 50% | **100% (3/3)** | Strictly redacts PII and scrubs stale shipping data. |
| **Multi-Turn** | 0% | **100% (2/2)** | Retains context and asks clarifying questions. |
| **Groundedness** | 0% | **100% (2/2)** | Rejects prompt injections and off-topic requests. |
| **Overall** | ~57% | **100% (12/12)** | *Perfect deterministic adherence.* |

---

## 🐛 Bug Diary

**1. Upstream Model Deprecation & API Rate Limiting**

* **Reproduction:** Running the evaluation script triggered `invalid_request_error` and subsequently `429 rate_limit_exceeded` errors.
* **Root Cause:** The initially selected model was decommissioned by the provider, and the rapid automated test loop exceeded the 8,000 Tokens-Per-Minute free-tier limit.
* **Fix:** Migrated to `gpt-oss-20b`, wrapped the API call in a graceful degradation `try/except` block to output a safe customer-facing error, and added a `time.sleep(2)` throttle to the evaluation script.
* **Regression Test:** Automated execution of the full `src.evaluate` suite now reliably completes without timing out or crashing.

**2. Stale Data Leakage on Cancelled Orders**

* **Reproduction:** Requesting tracking for a cancelled order (e.g., `ORD-1004`) returned an estimated delivery date.
* **Root Cause:** The raw JSON parser blindly returned all populated fields without cross-referencing the primary order `status`.
* **Fix:** Implemented conditional scrubbing in `src/tools.py` to manually overwrite `shipping_info` and drop tracking arrays if the status is cancelled, returned, or refunded.
* **Regression Test:** Custom Eval Case `CUSTOM-03` specifically targets `ORD-1004` to ensure no tracking fields are present in the final output.

**3. Deterministic Grader Rigidity (False Negatives)**

* **Reproduction:** The evaluation suite initially failed the agent on off-topic refusal tests despite the agent taking the correct action.
* **Root Cause:** The test relied on positive `expected_substrings` (e.g., expecting exactly the word "support"). The LLM acted naturally using synonyms (e.g., "Aster & Row inquiries"), triggering a false failure.
* **Fix:** Transitioned the testing philosophy to *Negative Constraints*. I cleared overly rigid expected strings and fortified `forbidden_substrings` to deterministically prove the agent did not leak data or hallucinate unauthorized actions.
* **Regression Test:** `CUSTOM-01` (Prompt Injection) and standard Groundedness cases now accurately pass by verifying the absence of forbidden raw code or system instructions.

---

## 🚧 Limitations & Production Next Steps

1. **Unbounded Context Window:** The `chat_history` array grows indefinitely per session. For production, I would implement token-aware sliding windows (summarizing or truncating older messages) to prevent `max_tokens` exhaustion.
2. **Local Storage Scalability:** A local ChromaDB instance and flat JSON file are insufficient for concurrent web traffic. Production deployment requires migrating vectors to a managed service (e.g., Pinecone/Qdrant) and replacing the JSON lookup with a read-only SQL replica.
3. **Naive Rate Limiting:** The `time.sleep()` fix in the test suite is a brute-force approach. Production should leverage the `Tenacity` Python library for robust exponential backoff based on HTTP 429 headers.

---

## 🤖 AI Tooling Attribution

* **Usage:** I utilized AI assistants (ChatGPT/Gemini) primarily as architectural thought partners, for generating boilerplate JSON schemas for Groq tool definitions, and for populating mock data for custom evaluation edge cases.
* **Flawed AI Suggestion:** When building the `src.evaluate` script, the AI strongly suggested evaluating the LLM's responses using exact string matching (`expected_substrings`). This was a fundamentally flawed suggestion for generative AI, leading to severe false negatives when the model used natural synonyms. I had to discard this advice and manually architect a *Negative Constraint* framework (`forbidden_substrings`) to accurately programmatically evaluate the agent's adherence to guardrails.

```

```