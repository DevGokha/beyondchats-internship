# LLM Response Evaluation Pipeline

## 📌 Project Overview
This project is an automated pipeline designed to evaluate the reliability of Retrieval-Augmented Generation (RAG) responses. It uses an **"LLM-as-a-Judge"** architecture to grade interactions based on:
1.  **Relevance:** Did the AI answer the specific user question?
2.  **Factual Accuracy (Hallucination):** Is the answer supported by the provided Context?
3.  **Performance:** Real-time metrics for **Latency** (seconds) and **Cost** ($).

## 🚀 Local Setup Instructions

### Prerequisites
* Python 3.8+
* **No API Key required** (The solution runs in "Mock Mode" to demonstrate functionality without incurring costs).

### Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/DevGokha/beyondchats-internship
    cd llm-eval-pipeline
    ```

2.  **Create a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Run the Evaluator:**
    Ensure the sample JSON files are in the root directory, then run:
    ```bash
    python main.py
    ```

---

## 🏗️ Architecture

The solution implements a **Model-Based Evaluation** pipeline with a fault-tolerant data ingestion layer.



1.  **Data Ingestion Layer:**
    * **Dual-Strategy Loader:** The script first attempts to load files as standard JSON. If syntax errors are detected (e.g., missing brackets, trailing commas in the provided samples), it automatically switches to a **Regex Scraper** to salvage valid conversation turns.
    * **Smart Unpacking:** Automatically detects if the data is nested in dictionaries (e.g., `{'conversation_turns': [...]}`) or flat lists.

2.  **Evaluation Engine:**
    * **Input:** User Query + Retrieved Context + AI Response.
    * **Processing:** Simulates an LLM call to grade the response.
    * **Metrics:** Calculates **Latency** (execution time) and **Cost** (token-based estimation at $0.15/1M input tokens).

3.  **Output Layer:**
    * Returns a structured JSON report for each interaction containing the scores and reasoning.

---

## 🧠 Design Choices

**1. Why "LLM-as-a-Judge"?**
Traditional metrics like BLEU or ROUGE are insufficient for RAG systems because they only check word overlap. An "LLM-as-a-Judge" can semantically understand if a response is *factually supported* by the context, which is critical for detecting hallucinations.

**2. Why a Custom Script instead of a Library?**
I chose a modular Python script over pre-built libraries (like Ragas) to ensure **granular control**. This allowed me to:
* Implement the **Regex Fallback** for broken JSON files.
* Manually calculate Latency and Cost exactly as requested in the assignment.
* Run in "Mock Mode" to demonstrate functionality without requiring the reviewer to obtain an API key.

**3. Robust Data Ingestion:**
The provided dataset contained syntax errors (e.g., unterminated strings). Instead of manually fixing the data, I engineered a **Regex Scraper** to extract valid data objects from broken files, ensuring the pipeline is resilient to messy real-world data.

---

## ⚡ Scaling Strategy (Millions of Users)

**Question:** *If we run this script at scale (millions of daily conversations), how do we ensure latency and costs remain at a minimum?*

To scale this solution, I would transition from this synchronous script to the following architecture:

1.  **Asynchronous Decoupling (Latency):**
    * Real-time evaluation should not block the user's chat. I would push chat logs to a message queue (e.g., **Kafka** or **RabbitMQ**). The evaluation pipeline would consume these messages and process them in the background (Background Jobs).

2.  **Strategic Sampling (Cost):**
    * Evaluating 100% of millions of chats is unnecessary and expensive. I would implement **Statistical Sampling** (evaluating only 5% of traffic) or **Trigger-Based Evaluation** (evaluating only when a user signals dissatisfaction/thumbs down).

3.  **Model Cascading (Cost):**
    * **Tier 1:** Use NLI (Natural Language Inference) models (like DeBERTa) for cheap, local hallucination detection.
    * **Tier 2:** Use small models (like `gpt-4o-mini`) for standard evaluations.
    * **Tier 3:** Only route to `gpt-4-turbo` for complex, high-stakes flagged conversations.

---
```
llm-eval-pipeline/
│
├── main.py                          <-- Core pipeline logic 
├── README.md                        <-- Documentation   
├── requirements.txt                 <-- Project dependencies
├── sample-chat-conversation-01.json <-- Input Data
├── sample_context_vectors-01.json   <-- Input Data
├── sample-chat-conversation-02.json <-- Input Data
├── sample_context_vectors-02.json   <-- Input Data
└── .gitignore                       <-- Git configuration
```
