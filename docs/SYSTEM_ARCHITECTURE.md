# NETRAVA — End-to-End System Architecture

**Document Version:** 1.0.0  
**Authority:** Senior Software Architect & Lead Multi-Agent Coordinator  
**System Title:** Explainable AI-Based Diabetic Retinopathy Screening System

---

## 1. High-Level Distributed Architecture

NETRAVA is organized as a decoupled, four-tier microservices architecture engineered for high availability, sub-second inference latency, and strict healthcare compliance:

```mermaid
graph TB
    subgraph ClientTier["Client Presentation Tier (Mobile / Web)"]
        FlutterApp["Flutter Mobile Application\n(Field Technician / Ophthalmologist)"]
        WebAdmin["Admin Portal\n(Clinic Administrator)"]
    end

    subgraph GatewayTier["API Gateway & Application Tier"]
        FastAPI["FastAPI Orchestration Microservice\n(Uvicorn / Asynchronous Python)"]
        AuthMiddleware["JWT Auth & Role Guard\n(Technician | Doctor | Admin)"]
        QCEngine["Image QC Filter\n(Laplacian Blur / Luminance)"]
    end

    subgraph MLTier["Deep Learning Inference Tier"]
        PyTorch["PyTorch Vision Pipeline\n(EfficientNet-B3 Engine)"]
        GradCAM["Grad-CAM Explainability Engine\n(Target: conv_head)"]
    end

    subgraph DataTier["Persistence & Cloud Tier (Supabase)"]
        Postgres["Supabase PostgreSQL 15+\n(10 Relational Tables + RLS)"]
        Storage["Private S3 Storage Buckets\n(fundus-images | heatmaps | reports)"]
        AuthService["Supabase GoTrue Auth\n(Identity & Session Management)"]
    end

    FlutterApp -->|HTTPS / REST API / TLS 1.3| FastAPI
    WebAdmin -->|HTTPS / REST API| FastAPI
    
    FastAPI --> AuthMiddleware
    AuthMiddleware --> AuthService
    FastAPI --> QCEngine
    
    FastAPI -->|In-Memory Tensor Pipeline| PyTorch
    PyTorch --> GradCAM
    
    FastAPI -->|SQLAlchemy / Supabase SDK| Postgres
    FastAPI -->|Encrypted Signed Uploads| Storage
    FastAPI -.->|Temporary Signed Media URLs| FlutterApp
```

---

## 2. Architectural Tiers Breakdown

### 2.1 Client Presentation Tier
- **Technology:** Flutter 3.x with Dart ^3.12.
- **Responsibilities:**
  - Hardware camera management and optical reticle HUD display.
  - Client-side validation of patient intake demographics and vitals.
  - Interactive dual-layer image viewing (Original Fundus + Grad-CAM Heatmap overlay).
  - Offline local caching (SQLite) with background request queueing.

### 2.2 Gateway & Application Tier
- **Technology:** FastAPI running on Uvicorn with Pydantic V2.
- **Responsibilities:**
  - Ingress request validation and schema enforcement.
  - Role-Based Access Control (RBAC) verification.
  - Quality Control (QC) scoring before triggering GPU inference.
  - Image base64 / binary multipart decoding and storage orchestration.
  - Report compilation and PDF document generation.

### 2.3 Deep Learning Inference Tier
- **Technology:** PyTorch 2.2+, timm 0.9+, OpenCV, Pillow.
- **Responsibilities:**
  - Aspect-ratio-preserving $300 \times 300$ image preprocessing (`ResizeWithPadding`).
  - Thread-safe forward pass through fine-tuned EfficientNet-B3.
  - Softmax probability computation and top-1 ICDR severity classification.
  - Forward/backward hook extraction on `model.conv_head` to generate Grad-CAM heatmaps.
  - Alpha-blending pseudo-colored heatmaps (Jet colormap) with preprocessed fundus images.

### 2.4 Persistence & Cloud Tier
- **Technology:** Supabase (PostgreSQL 15+, GoTrue, S3 Storage).
- **Responsibilities:**
  - 10-table normalized relational schema.
  - Strict Row Level Security (RLS) enforcement on all patient records.
  - Zero public S3 bucket exposure; time-limited signed URL generation.
  - Immutable audit logging for clinical accountability.

---

## 3. End-to-End Screening Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Tech as Field Technician
    participant App as Flutter Client
    participant API as FastAPI Backend
    participant QC as QC Engine
    participant ML as PyTorch Model
    participant GC as Grad-CAM Hook
    participant S3 as Supabase Storage
    participant DB as Supabase Postgres

    Tech->>App: 1. Intake Patient & Capture Fundus Image (OD/OS)
    Tech->>App: 2. Submit Screening Request
    App->>API: 3. POST /api/v1/screenings (Multipart: file + metadata)
    API->>API: 4. Verify Bearer JWT & Technician Role
    API->>QC: 5. Execute Blur (Laplacian) & Illumination Check
    alt QC Check Failed
        QC-->>API: QC Score < Threshold (Blurry/Ungradable)
        API-->>App: 422 Unprocessable Entity (Retake Recommended)
    else QC Check Passed
        QC-->>API: QC Passed (Gradable)
        API->>S3: 6. Upload Raw Fundus Image to 'fundus-images'
        API->>ML: 7. Run Aspect Preprocessing (300x300, Padding)
        API->>ML: 8. Execute EfficientNet-B3 Forward Pass
        ML-->>API: 9. 5-Class Logits & Softmax Probabilities
        API->>GC: 10. Backward Pass on Predicted Class (conv_head)
        GC-->>API: 11. Activation Map Matrix (300x300)
        API->>API: 12. Blend Heatmap Overlay with Fundus Scan
        API->>S3: 13. Upload Blended Heatmap to 'gradcam-heatmaps'
        API->>DB: 14. Persist Prediction & Probability Records
        API->>DB: 15. Write Clinical Audit Log Entry
        API->>S3: 16. Generate Signed URLs for Fundus & Heatmap
        API-->>App: 17. Return PredictionResponse (Grade, Confidence, URLs)
        App->>Tech: 18. Display Diagnostic Card & Grad-CAM Heatmap
    end
```

---

## 4. Availability, Resilience & Scalability

- **Stateless Application Servers:** The FastAPI backend is fully stateless. Worker processes can be scaled horizontally behind a round-robin load balancer.
- **Asynchronous Execution:** Heavy disk I/O and S3 uploads are handled asynchronously to prevent blocking the event loop.
- **GPU / CPU Portability:** The PyTorch loader automatically selects `cuda` if available, falling back gracefully to optimized multi-threaded `cpu` execution.

