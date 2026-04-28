\# ⚙️ System Design — Dual-Layer Sports Media Protection System (MVP)

\#\# 🧠 System Overview  
The system is a lightweight, AI-powered video verification platform designed to detect whether a given video is a pirated or modified version of an original sports broadcast. 

It follows a dual-layer detection architecture:  
\* \*\*⚡ Fast Path (pHash)\*\* → detects near-identical copies instantly  
\* \*\*🧠 Deep Path (CLIP)\*\* → detects modified, cropped, or filtered videos

The system is optimized for:  
\* ✅ Hackathon development speed  
\* ✅ Reliable demo execution  
\* ✅ Clear detection output

\---

\#\# 🏗️ High-Level Architecture

\`\`\`text  
User Interface (Next.js)  
        ↓  
Upload API (FastAPI)  
        ↓  
Processing Pipeline  
   ├── Frame Extraction  
   ├── pHash Engine (Fast Path)  
   ├── CLIP Engine (Deep Path)  
        ↓  
Storage Layer  
   ├── Firebase (metadata \+ logs)  
   ├── Upstash Vector (embeddings)  
        ↓  
Verification Engine  
        ↓  
Result Dashboard (Frontend)  
