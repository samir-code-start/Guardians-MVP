# Frontend Architecture Research: Dual-Layer Digital Asset Protection

**TARGET AUDIENCE**: AI Coding Agent / Frontend Developer
**CONTEXT**: Hackathon MVP (Speed, Demo-ability, Impact)
**STACK FOCUS**: React/Next.js (implied for modern frontend), WebSocket/SSE, Canvas/Video APIs.

---

## 1. Multi-Stage Pipelines & Complex AI Systems
**Goal**: Represent `Ingestion -> Layer 1 (C2PA) -> Layer 2 (AI) -> Result` clearly.
* **Component Pattern**: `Vertical/Horizontal Stepper` or `DAG (Directed Acyclic Graph) View`.
* **Agent Implementation Notes**:
    * Maintain a global state machine: `IDLE` -> `UPLOADING` -> `VERIFYING_C2PA` -> `EXTRACTING_FRAMES` -> `COMPUTING_PHASH` -> `ANALYZING_CLIP` -> `COMPLETE`.
    * **UI/UX**: Use pulsing animations on the active step. Previous steps show checkmarks (green/red based on pass/fail).
    * **Simplification**: Do not show raw logs by default. Use an accordion or "View Details" toggle for the console output of each step.

## 2. Real-Time Dashboards & Event Streams
**Goal**: Handle continuous data updates (threat logs, detection results).
* **Component Pattern**: `Activity Feed` / `Triage Queue`.
* **Agent Implementation Notes**:
    * **Data Handling**: Use WebSockets or Server-Sent Events (SSE). Keep a fixed-size array (e.g., `max 100 items`) in state to prevent memory leaks from continuous event streams.
    * **UI/UX**: New items should animate in from the top (`Framer Motion` or CSS transitions). Use a "Pause Feed" button if events exceed 5 per second so users can read them.
    * **Hierarchy**: Highlight the `timestamp`, `event_type` (e.g., 'Tamper Detected'), and `asset_id`.

## 3. AI/ML Outputs (Confidence Scores & Similarity)
**Goal**: Visualize pHash/CLIP metrics and hybrid confidence scores.
* **Component Pattern**: `Gauge Charts`, `Progress Bars with Threshold Markers`, `Diff Viewers`.
* **Agent Implementation Notes**:
    * **Data Visualization**:
        * Confidence Score: Radial gauge (0-100%).
        * Thresholding: Strictly map values to semantic colors. `< 50 = Red (Fake/Tampered)`, `50-75 = Yellow (Suspicious)`, `> 75 = Green (Authentic)`.
    * **Explainability (Crucial for AI)**: Next to the final hybrid score, display a breakdown visualization (e.g., a stacked bar or radar chart showing weight of pHash vs. CLIP vs. C2PA).

## 4. Digital Media Authenticity (Trust & Provenance)
**Goal**: Present C2PA metadata and cryptographic tampering.
* **Component Pattern**: `Verification Badges`, `Cryptographic Hash Displays`, `Metadata Tree`.
* **Agent Implementation Notes**:
    * **UI/UX**: Use universally recognized trust icons (Shields, Checkmarks).
    * **Data Display**: Truncate long cryptographic hashes (e.g., `0x1a2b...9f8d`) using monospace fonts with a one-click "Copy" clipboard icon.
    * **State**: If C2PA is missing or broken, immediately flag the UI with a "Provenance Broken" warning banner. Do not hide this in a menu.

## 5. Video Analysis & Frame-Level Processing
**Goal**: Show frame extraction and comparisons.
* **Component Pattern**: `Filmstrip`, `Side-by-side Video Diffing`, `Canvas Overlays`.
* **Agent Implementation Notes**:
    * **Video Player**: Build a custom wrapper around the HTML5 `<video>` element to sync playback with an array of extracted frames.
    * **Frame Display**: Show a horizontal scrollable "Filmstrip" below the video. Highlight the specific frame currently being analyzed by the AI.
    * **Comparison**: For similarity checks, use a side-by-side view (Original vs. Uploaded) with synchronous scrubbing (moving the timeline on one moves the other).

## 6. Cybersecurity & Threat Intelligence Dashboards
**Goal**: Structure and prioritize system threats.
* **Component Pattern**: `KPI Cards`, `Severity Matrix`, `Dark Mode High-Contrast UI`.
* **Agent Implementation Notes**:
    * **Hierarchy**: Top row must contain aggregate KPI cards (`Total Ingested`, `Threats Blocked`, `Avg Confidence`).
    * **Prioritization**: Implement a `Severity Level` enum (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`). Sort all incoming events by severity first, timestamp second.
    * **Color Palette**: Default to a dark theme (standard for SecOps/NOC dashboards) with neon accent colors for alerts (Red/Orange) to create high visual impact.

## 7. Interaction Design (Flow & Processing States)
**Goal**: Communicate data flow without overwhelming the user.
* **Component Pattern**: `Skeleton Loaders`, `Micro-interactions`, `Toast Notifications`.
* **Agent Implementation Notes**:
    * **Transitions**: Use layout animations when an asset moves from the "Pending" column to the "Analyzed" column.
    * **Processing States**: Instead of a generic spinner, use text-changing loaders (e.g., "Extracting audio..." -> "Hashing frames..." -> "Querying vector DB..."). This proves to judges the backend is doing real work.

## 8. Hackathon/Demo-Focused Frontend Patterns
**Goal**: Maximize clarity and "wow" factor for a 2-3 minute presentation.
* **Component Pattern**: `Bento Box Layout`, `Hero Component`, `Mock Fallbacks`.
* **Agent Implementation Notes**:
    * **Layout**: Use a CSS Grid "Bento Box" layout. It keeps all vital information above the fold. No scrolling should be required during the core demo.
    * **The "Aha" Moment**: The UI must clearly show a "Before and After" or a "Clean vs. Malicious" state side-by-side.
    * **Safety (Hackathon specific)**: Implement a hidden keyboard shortcut (e.g., `Ctrl+Shift+D`) to load pre-computed JSON mock data in case the live FastAPI/Firebase backend goes down during the pitch.
