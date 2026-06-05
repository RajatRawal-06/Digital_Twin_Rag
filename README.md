# Digital Twin RAG: Richard Feynman

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-cyan)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-green)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange)

An advanced Retrieval-Augmented Generation (RAG) system engineered to simulate a digital twin of Richard Feynman. By fusing his technical brilliance with his distinctive rhythm and humor, this project delivers a highly realistic, responsive, and educational AI interaction platform. 

This repository was created as part of the AIMS DTU Summer Project 2026.

---

## 🌟 Features
- **Cognitive Memory Architecture:** Dynamically profiles user knowledge utilizing K-Means and retains context with short-term buffers.
- **Tri-Retriever Engine:** Employs an intelligent intent router to query GraphRAG (for rigorous physics facts) or a Vector Rhythm Base (for persona anecdotes), or both via MMR.
- **Advanced Data Parsing:** Integrates LlamaParse for structure-aware parsing of dense physics PDFs and complex LaTeX equations.
- **Spectrogram TTS Integration:** Real-time integration with ElevenLabs to deliver authentic, synthesized voice outputs mapped to the custom frontend.
- **Industrial Sci-Fi UI:** An immersive React/Vite 3D scrollytelling frontend designed for dynamic interaction.

---

## 🏗️ System Architecture

### 1. The Core Retrieval & Generation Pipeline

This workflow illustrates how a user's query is processed, routed, retrieved, and finally generated into an authentic audio-visual response.

```mermaid
flowchart TD
    A[User Query] --> B(1. Pre-Processing & Cognitive Memory)
    
    subgraph PreProcessing [Pre-Processing]
        B1[Lightweight LLM: Orthographic Check]
        B2[Memory Fetch: Short-Term Context]
        B3[K-Means Profiling: User Knowledge Level]
        B --> B1 & B2 & B3
    end
    
    B1 & B2 & B3 --> C{2. Intent Router LLM}
    
    C -->|Technical / Physics| D1[(Knowledge Graph\nGraphRAG)]
    C -->|Life / Philosophy| D2[(Rhythm Base\nVector DB)]
    C -->|Blended / Both| D3[(Hybrid Engine\nGraph + Vector)]
    
    D1 & D2 & D3 --> E(3. Post-Retrieval Compression)
    
    subgraph Compression [Compression & Augmentation]
        E1[MMR / Diversity Check]
        E2[Contextual Compressor: Discard Noise]
        E1 --> E2
        E2 --> F[4. Persona Augmentation Layer]
    end
    
    E --> E1
    
    F --> G(5. Generation Engine: Gemini 2.5 Flash)
    
    G --> H{6. Anomaly Detection Guardrail}
    H -->|Hallucination Detected| G
    H -->|Passed| I(7. Async Ops & Evaluation)
    
    subgraph AsyncOps [Post-Generation Ops]
        I1[K-Means Update]
        I2[Ragas Metrics Evaluation]
        I3[LangSmith Latency Tracing]
        I --> I1 & I2 & I3
    end
    
    I1 & I2 & I3 --> J[Output to User + ElevenLabs TTS]
```

### 2. Smart Data Ingestion & Chunking

To handle complex 500-page academic physics PDFs and conversational transcripts accurately, the ingestion pipeline relies on advanced semantic chunking rather than blind token splits.

```mermaid
flowchart TD
    subgraph Raw Data
        R1[Knowledge Folder\nDeep Physics PDFs]
        R2[Persona Folder\nInterviews & Books]
    end
    
    R1 --> P1[1. Smart Parsing\nLlamaParse: Extracts Math/Tables]
    R2 --> P2[1. Standard Parsing\nMarkdown/Text Loader]
    
    P1 --> C1[2. Dynamic Chunking\nSemantic Chunking on Topic Change]
    P2 --> C2[2. Dynamic Chunking\nParagraph/Dialogue Chunking]
    
    C1 & C2 --> E[3. Embedding Layer\ntext-embedding-3-large / BGE-M3]
    
    E --> DB[(4. Hybrid Vector Store / Graph DB)]
    
    note[Store chunks with Metadata:\nSource, Page #, Type] --> DB
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- API Keys: Gemini, ElevenLabs

### 1. Setup the Backend
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
# source venv/bin/activate

pip install -r requirements.txt

# Configure your environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and ELEVENLABS_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

### 2. Setup the Frontend
Open a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173` in your browser.

---

## 🛡️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
