# HYBRID REAL MODE: Refactoring Implementation Plan

## 🎯 Objective
Refactor the "Dual-Layer Sports Media Protection System" into a hybrid state for a stable, high-performance hackathon demonstration. 
The system will rely exclusively on **pHash (Fast Path)** as the active detection layer, while safely disabling all heavy machine learning and vector database modules (Deep Path) without deleting their code or breaking the existing frontend.

## ⚙️ Phase 1: Dependency & Initialization Refactoring
- **Goal:** Prevent the server from loading heavy ML libraries or attempting external DB connections at startup.
- **Actions:**
  - In `services/deep_path.py` and `services/vector_db.py`, guard or comment out heavy imports (like `torch`, `transformers`, vector SDKs) so they are not evaluated at runtime.
  - Add clear internal comments: `"# Reserved for future semantic layer - DISABLED FOR HYBRID MVP"`.
  - Ensure `main.py` (or the FastAPI app setup) does not fail on startup by removing or bypassing the vector database initialization.

## 🏎️ Phase 2: Fortify the Primary Layer (pHash)
- **Goal:** Ensure the Fast Path is robust, deterministic, and returns results in under 2 seconds.
- **Actions:**
  - Ensure `services/fast_path.py` and `services/media_processor.py` successfully extract 2-3 keyframes using OpenCV/ffmpeg.
  - Generate pHash via `imagehash` and compute the Hamming distance.
  - Guarantee confidence conversion: `confidence = 1 - (distance / 64)`.

## 🧠 Phase 3: Disable Deep Layer Execution
- **Goal:** Stop the verification endpoint from executing the deep analysis layer.
- **Actions:**
  - In `api/v1/verify.py` (or the main verification orchestrator), bypass the call to `deep_path`.
  - Keep the logical block present but inactive (e.g., wrap in `if False: # deep analysis (DISABLED)`).

## 🌉 Phase 4: API Contract Preservation
- **Goal:** Maintain 100% compatibility with the React frontend so no UI changes are needed.
- **Actions:**
  - The verification endpoint MUST continue returning the exact JSON structure expected by `frontend/src/app/page.tsx`.
  - **Required JSON Structure:**
    ```json
    {
      "decision": "AUTHENTIC" | "TAMPERED",
      "hybrid_confidence": <float based entirely on fast_path>,
      "fast_path": {
        "match": <boolean>,
        "min_distance": <int>,
        "matches_count": <int>,
        "confidence": <float>
      },
      "deep_path": {
        "match": false,
        "max_similarity": 0.0,
        "matches_count": 0,
        "confidence": 0
      }
    }
    ```
  - The final `decision` and `hybrid_confidence` will be calculated solely using the pHash results, while the `deep_path` block serves as a static placeholder to keep the UI happy.

## 🏁 Success Criteria
- [ ] Backend runs fully locally with zero reliance on cloud vector databases or ML model downloads.
- [ ] Zero initialization delay (starts instantly without loading PyTorch weights).
- [ ] Total processing time per video comparison is under 2 seconds.
- [ ] Frontend dashboard functions perfectly and renders results successfully.
