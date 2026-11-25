# NETRAVA — Deployment & Infrastructure Guide

**Document Version:** 1.0.0  
**Authority:** Agent 03 (Backend Engineer) & Agent 00 (Coordinator)

---

## 1. Deployment Topology

NETRAVA is deployed as a hybrid mobile/cloud architecture:
- **Mobile Client:** Distributed as native signed APK/AAB (Android) and TestFlight/IPA (iOS).
- **Backend API:** Containerized microservice running on cloud compute (AWS EC2, GCP Compute Engine, or Azure VM) with GPU or CPU execution.
- **Database & Storage:** Managed Supabase Cloud instance with automated daily snapshots.

---

## 2. Docker Containerization

### 2.1 Backend Dockerfile (`backend/Dockerfile`)
```dockerfile
# Multi-stage production Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim as runner

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY app/ ./app
COPY model/ ./model

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 2.2 Docker Compose (`docker-compose.yml`)
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: netrava_backend
    restart: always
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
      - MODEL_CHECKPOINT_PATH=/app/model/best_efficientnet_b3_staged.pth
      - DEVICE=cpu  # or 'cuda' if nvidia runtime configured
    volumes:
      - ./backend/model:/app/model:ro
```

---

## 3. Flutter Release Build Instructions

### Android Release APK & App Bundle
```bash
cd frontend/flutter_app
flutter clean
flutter pub get
# Build universal release APK
flutter build apk --release --split-per-abi --obfuscate --split-debug-info=./symbols
# Build Google Play App Bundle
flutter build appbundle --release --obfuscate --split-debug-info=./symbols
```

---

## 4. Backup & Disaster Recovery

- **Database:** Supabase automated daily backups with 7-day point-in-time recovery (PITR).
- **Storage Buckets:** Object versioning enabled on `fundus-images` to prevent accidental deletion.
- **Model Artifacts:** Checkpoint weights mirrored across secure S3 backup vaults and Google Drive archives.

