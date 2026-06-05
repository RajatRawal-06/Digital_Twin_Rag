# Data Ingestion & Guardrail Strategy
**Project:** RAG Pipeline & Safety Systems

To build a RAG pipeline over papers, articles, and lectures [cite: 53], handling massive 500-page physics PDFs requires an advanced, layout-aware loading strategy. Blindly splitting text will destroy the semantic meaning of mathematical proofs.

---

## 1. Advanced Data Loading (The Parsers)

### A. The Knowledge Folder (6 Deep Physics PDFs)
- **The Problem:** Standard loaders (`PyPDF2`) read text left-to-right, destroying multi-column academic layouts and equations.
- **The Solution (LlamaParse/Unstructured):** We will deploy an AI-native document parser. This tool visually analyzes the PDF structure first. 
- **Execution:** It identifies a block of text as a "Paragraph", a "Header", or a "Table". It converts complex mathematical equations into clean LaTeX format. This ensures that when Feynman retrieves an equation, the syntax is flawless.

### B. The Persona Folder (6 Text/Transcript PDFs & `yt.txt`)
- **The Solution:** Since these are largely conversational transcripts, we utilize a standard Markdown/Text loader. 
- **Metadata Tagging:** During loading, every file is injected with metadata: `{"source": "BBC_Interview_1981", "type": "persona", "format": "video_transcript"}`.

---

## 2. Intelligent Text Splitting (Chunking)

### A. Semantic Chunking (For Knowledge PDFs)
Instead of splitting blindly every 1,000 tokens, we use **Semantic Text Splitting**. 
- **How it works:** A lightweight embedding model reads the sentences. It only places a "split" when the semantic cosine similarity between sentence $A$ and sentence $B$ drops significantly—indicating a change in topic.
- **Result:** An entire sub-chapter explaining the "Double-Slit Experiment" remains together in one cohesive chunk.

### B. Dialogue-Level Chunking (For Persona Transcripts)
- **How it works:** We use a regex-based splitter that breaks chunks strictly at the end of a paragraph or speaker turn. 
- **Result:** This preserves Feynman's distinct speech rhythm. His entire thought process—from setting up a premise to delivering the punchline—is kept intact for the few-shot prompt injection.

---

## 3. The Guardrail Architecture

To ensure technical accuracy [cite: 61] and strict persona adherence, output passes through algorithmic safety checks before reaching the frontend.

### A. Jargon Filtering & Self-Correction
- **Mechanism:** A post-processing LLM node acts as an editor. 
- **Rule:** If the generated text contains heavy modern corporate jargon (e.g., "synergy", "utilize", "leverage") or violates the Feynman Technique by using undefined complex terms, the node automatically rewrites the sentence into plain, first-year college English.

### B. Anomaly Detection (Hallucination Prevention)
- **Mechanism:** We establish a baseline vector embedding of Feynman's verified vocabulary and historical domain.
- **Rule:** If the output generation vector drifts too far from this baseline (e.g., the model begins explaining modern String Theory frameworks invented after 1988), the guardrail detects an anomaly. It forces the generation engine to fallback and state: *"I haven't the slightest idea about that, it must be something you young folks came up with after my time."*
