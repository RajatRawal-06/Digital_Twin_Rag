# System Architecture: Feynman Digital Twin
**Project**: AIMS DTU Summer Project 2026 - Digital Twin of a Scientist [cite: 39, 40]

## 1. High-Level System Flow
The architecture is designed to accurately emulate Richard Feynman's knowledge, reasoning style, and communication style, so that talking to the agent feels like talking to him [cite: 44]. The system is built around a routing mechanism that directs user queries to specialized databases before augmenting the generation model (Gemini 2.5 Flash) [cite: 57].

### The Core Pipeline
1. **Input & Memory Fetch:** User submits a query. The system fetches Short-Term (recent session) and Long-Term (persistent cross-session) memory context [cite: 52].
2. **Intent Routing:** A lightweight LLM classifies the user's intent into one of three categories:
   - *Technical/Educational* (e.g., "Explain quantum electrodynamics")
   - *Personal/Philosophical* (e.g., "What was Los Alamos like?")
   - *Blended* (e.g., "How did you feel when you figured out the path integral?")
3. **Retrieval & Compression:** The router triggers one of three retrieval paths. Retrieved chunks are compressed using Contextual Compression to remove noise.
4. **Generation & Guardrails:** Gemini 2.5 Flash generates the response, which is run through safety and persona guardrails before being returned to the user alongside the TTS voice stream.

---

## 2. Dual Storage System

To maintain facts and persona independently, the data is isolated into two primary stores.

### A. The Knowledge Graph (Scientific Domain)
- **Content:** Physics papers, *The Feynman Lectures on Physics*, teacher's notes.
- **Structure:** Instead of flat vectors, this is implemented as a GraphRAG. Concepts (Nodes) like "Quantum Mechanics" are linked via relationships (Edges) to "Manhattan Project" or "Path Integrals". 
- **Purpose:** Ensures the agent gets the facts right and frames problems the way Feynman would [cite: 45]. 

### B. The Rhythm Base (Persona & Style)
- **Content:** *Surely You're Joking, Mr. Feynman!*, interview transcripts, and personal views.
- **Structure:** A standard Vector Database (e.g., Qdrant or Pinecone) optimized for fast semantic similarity.
- **Purpose:** Stores exactly *how* he spoke, providing few-shot examples of his rhythm, humor, and use of analogies.

---

## 3. The Tri-Retriever Engine

Based on the Router's decision, the system utilizes one of three specialized retrievers:

### Path 1: The Technical Retriever (Graph Search)
Activated for hard science queries. It traverses the Knowledge Graph to pull accurate physical constants, formulas, and textbook explanations. It prioritizes depth and accuracy.

### Path 2: The Persona Retriever (Vector Search)
Activated for queries about his life or opinions. It searches the Rhythm Base for relevant anecdotes, maintaining consistency with his personality [cite: 55].

### Path 3: The Hybrid Retriever (Maximal Marginal Relevance)
Activated for complex questions. It fires searches to *both* databases. It uses Maximal Marginal Relevance (MMR) to re-rank the results, guaranteeing that the context window contains exactly one accurate scientific explanation *plus* one personal stylistic anecdote, avoiding duplicate information.

---

## 4. Short-Term and Long-Term Memory
To fulfill the requirement of supporting multi-turn conversations [cite: 56], the system implements:
- **Short-Term Context Window:** Appends the last $k$ interactions (e.g., 5 turns) directly into the query context to handle pronouns and follow-up questions.
- **Long-Term K-Means Profiling:** An asynchronous background process clusters the user's past queries to build a profile. This profile is injected into the system prompt, allowing Feynman to tailor analogies across sessions [cite: 52].
