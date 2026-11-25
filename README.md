
# 🩺 NETRAVA
### Explainable AI-Based Diabetic Retinopathy Screening System

> An AI-powered retinal image screening prototype designed to assist in the detection and grading of Diabetic Retinopathy using Deep Learning and Explainable AI.

<p align="center">
  <b>Deep Learning • Computer Vision • Explainable AI • Mobile Healthcare</b>
</p>

---

## 📌 About the Project

**NETRAVA** is an Explainable AI-based Diabetic Retinopathy Screening System designed to analyze retinal fundus images and predict the severity level of Diabetic Retinopathy.

The system uses Deep Learning techniques to classify retinal images into different severity grades and integrates Explainable AI techniques to help visualize the regions of an image that influenced the model's prediction.

The project aims to explore how AI-based screening technology can support accessible retinal healthcare, particularly in settings where access to specialized eye-care services may be limited.

---

## 🎯 Problem Statement

Diabetic Retinopathy (DR) is a diabetes-related eye disease that can lead to vision impairment and blindness if not detected and managed appropriately.

Traditional screening requires retinal examination by trained healthcare professionals and specialized equipment. Limited access to screening facilities can make early detection challenging in underserved and rural communities.

NETRAVA explores the use of Deep Learning and Computer Vision to develop an AI-assisted screening prototype that can analyze retinal fundus images and provide severity predictions along with visual explanations.

---

## 💡 Objectives

- Develop a Deep Learning-based system for Diabetic Retinopathy classification.
- Analyze retinal fundus images using Computer Vision techniques.
- Classify images into five DR severity grades.
- Implement Explainable AI using Grad-CAM.
- Develop a mobile application interface using Flutter.
- Build a backend API for model inference and application communication.
- Explore an accessible and scalable AI-assisted screening workflow.

---

## 🔬 Diabetic Retinopathy Classification

The system follows the five-level classification scheme:

| Grade | Classification | Description |
|---|---|---|
| 0 | No DR | No visible diabetic retinopathy |
| 1 | Mild DR | Mild non-proliferative changes |
| 2 | Moderate DR | Moderate non-proliferative changes |
| 3 | Severe DR | Severe non-proliferative changes |
| 4 | Proliferative DR | Advanced proliferative changes |

---

## 🧠 AI / Deep Learning Approach

NETRAVA uses a Deep Learning-based image classification approach for retinal image analysis.

### Model

- **Architecture:** EfficientNet-B3
- **Learning Approach:** Transfer Learning
- **Task:** Multi-class image classification
- **Classes:** 5 DR severity levels
- **Dataset:** APTOS 2019 Blindness Detection Dataset

The pretrained model is adapted to the Diabetic Retinopathy classification task through fine-tuning on retinal fundus images.

### Image Processing Pipeline

```text
Retinal Fundus Image
        │
        ▼
Image Preprocessing
        │
        ▼
Image Resizing & Normalization
        │
        ▼
EfficientNet-B3
        │
        ▼
Feature Extraction
        │
        ▼
Classification Layer
        │
        ▼
DR Severity Prediction (Grade 0–4)
        │
        ▼
Grad-CAM Visualization
```

---

## 🔍 Explainable AI

NETRAVA integrates **Grad-CAM (Gradient-weighted Class Activation Mapping)** to provide visual explanations for model predictions.

Grad-CAM generates a heatmap highlighting image regions that contribute to the model's prediction.

This helps users visualize the areas of the retinal image that influenced the predicted classification.

### Explainability Workflow

1. Input retinal fundus image.
2. Image is processed by the trained Deep Learning model.
3. The model predicts a DR severity class.
4. Grad-CAM generates an activation heatmap.
5. The heatmap is overlaid on the original retinal image.
6. The visual explanation is presented alongside the prediction.

> Explainability visualizations are intended to support model interpretation and do not independently establish a clinical diagnosis.

---

## 📊 Dataset

### APTOS 2019 Blindness Detection

NETRAVA uses the **APTOS 2019 Blindness Detection Dataset** for model development and experimentation.

The dataset contains retinal fundus images labeled according to Diabetic Retinopathy severity.

**Dataset Classes:**

- 0 — No DR
- 1 — Mild
- 2 — Moderate
- 3 — Severe
- 4 — Proliferative DR

### Dataset Preparation

The dataset preparation pipeline includes:

- Image inspection
- Duplicate image analysis
- Data cleaning
- Label verification
- Image preprocessing
- Training and validation splitting
- Data augmentation
- Image normalization

### Preprocessing

- Image resizing
- Normalization
- Data augmentation during training
- Horizontal flipping
- Rotation
- Color augmentation

---

## 🏗️ System Architecture

NETRAVA follows a modular architecture consisting of the mobile frontend, backend services, AI inference component, and database services.

```text
┌──────────────────────────────┐
│       Flutter Mobile App    │
│                              │
│ Image Upload / User Interface│
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       FastAPI Backend        │
│                              │
│ API Routes / Request Handling│
│ Image Processing             │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│      AI Inference Engine     │
│                              │
│      EfficientNet-B3         │
│                              │
│ DR Classification             │
│ Grad-CAM Explainability       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       Result Processing      │
│                              │
│ Prediction / Confidence      │
│ Visualization                │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│     Flutter Results Screen   │
└──────────────────────────────┘

        Database Services
             │
             ▼
          Supabase
```

---

## 🛠️ Technology Stack

### Artificial Intelligence & Machine Learning

- Python
- PyTorch
- EfficientNet-B3
- Transfer Learning
- Computer Vision
- OpenCV
- Grad-CAM
- NumPy
- Pandas
- Matplotlib

### Backend

- FastAPI
- Python
- REST API
- Uvicorn

### Frontend

- Flutter
- Dart

### Database & Services

- Supabase
- PostgreSQL

### Development Tools

- Git
- GitHub
- Jupyter Notebook
- Google Colab
- VS Code

---

## 📱 Application Workflow

```text
User
 │
 ▼
Upload Retinal Image
 │
 ▼
Image Validation
 │
 ▼
Backend Processing
 │
 ▼
AI Model Inference
 │
 ├── DR Severity Classification
 │
 └── Grad-CAM Generation
 │
 ▼
Prediction Results
 │
 ▼
Visual Explanation
 │
 ▼
Results Displayed in Mobile App
```

---

## 📂 Project Structure

```text
NETRAVA/
│
├── ai_model/
│   ├── Model Training
│   ├── Evaluation
│   ├── Inference
│   └── Explainability
│
├── backend/
│   ├── API
│   ├── Services
│   └── Tests
│
├── design_reference/
│   └── UI Design References
│
├── docs/
│   └── Project Documentation
│
├── frontend/
│   └── flutter_app/
│       └── Mobile Application
│
├── scripts/
│   └── Utility Scripts
│
├── shared/
│   └── Shared Components
│
├── supabase/
│   └── Database Configuration
│
├── .env.example
├── .gitignore
├── AGENT.md
├── IMPLEMENTATION_PLAN.md
├── netrava.bat
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/gurindersinghs637-rgb/Netrava-.git
```

Navigate to the project directory:

```bash
cd Netrava-
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

> The backend entry-point and dependency installation commands may need to be adjusted according to the backend configuration.

### 3. Flutter Application Setup

Navigate to the Flutter application:

```bash
cd frontend/flutter_app
```

Install dependencies:

```bash
flutter pub get
```

Run the application:

```bash
flutter run
```

### 4. Environment Configuration

Create your environment configuration using the provided example file:

```text
.env.example
```

Configure the required environment variables according to your local development environment.

**Never commit API keys, passwords, credentials, or private environment files to GitHub.**

---

## 📈 Model Evaluation

The model is evaluated using classification performance metrics such as:

- Accuracy
- Precision
- Recall
- F1-Score
- Confusion Matrix
- Cohen's Kappa

These metrics help evaluate classification performance across the five severity classes, particularly considering class imbalance within the dataset.

---

## 🌍 Applications

NETRAVA explores potential applications of AI-assisted retinal screening in:

- Rural healthcare environments
- Telemedicine workflows
- Preliminary retinal screening
- Healthcare accessibility research
- AI-assisted medical image analysis
- Explainable medical AI research

---

## 🚧 Limitations

- The system is currently a research and development prototype.
- Model performance depends on the dataset and image quality.
- Dataset bias may affect predictions.
- Predictions require appropriate clinical interpretation.
- The system is not a substitute for professional medical examination.
- Further validation using diverse clinical datasets is necessary before real-world clinical use.

---

## 🔮 Future Scope

Future development may include:

- Improved model accuracy and generalization
- Testing additional Deep Learning architectures
- Better image quality assessment
- Advanced explainability techniques
- Real-time screening workflows
- Cloud deployment
- Integration with healthcare workflows
- Multilingual mobile application support
- Clinical validation
- Improved accessibility for rural healthcare settings

---

## 👨‍💻 Project Information

**Project Name:** NETRAVA

**Project Type:** Capstone Project

**Domain:** Artificial Intelligence / Deep Learning / Healthcare

**Primary Application:** Diabetic Retinopathy Screening

**AI Approach:** Transfer Learning & Explainable AI

**Dataset:** APTOS 2019 Blindness Detection

**Model:** EfficientNet-B3

---

## ⚠️ Medical Disclaimer

NETRAVA is an academic and research prototype developed for educational and experimental purposes.

The system's predictions are **not medical diagnoses** and must not be used as a substitute for examination, diagnosis, or treatment by qualified healthcare professionals.

Any retinal image analysis or screening decision should be reviewed by an appropriately qualified medical professional.

---

## ⭐ Acknowledgements

- APTOS 2019 Blindness Detection Dataset
- Open-source Deep Learning community
- PyTorch
- Flutter
- FastAPI
- Supabase

---

<p align="center">
  <b>NETRAVA — Exploring Explainable AI for Accessible Retinal Healthcare</b>
</p>
