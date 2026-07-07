# ⚙️ DriveIQ Backend API

The **DriveIQ Backend API** is a high-performance REST API built with FastAPI. It handles core application authentication, psychometric test evaluations, and MCQ CRUD operations for the DriveIQ Driver Assessment ecosystem.

---

## 🛠️ Tech Stack
* **Framework**: FastAPI (Python 3.10+)
* **Database**: MongoDB (utilizing `motor` for asynchronous MongoDB interactions)
* **Text-To-Speech**: `gTTS` (Google Text-to-Speech) to generate audio files dynamically
* **Validation**: Pydantic v2
* **Web Server**: Uvicorn

---

## 📂 Project Structure Overview
* `main.py`: Entry point of the application. Sets up CORS, mounts static assets, and registers routers.
* `database.py`: Handles MongoDB client connections, initializations, and reference retrievals.
* `models.py`: Pydantic models enforcing payload validation for MCQ creation, updates, and user auth.
* `seed.py`: Seed script to clean, populate, and download local copies of multimedia MCQ assets.
* `routes/`:
  * `auth.py`: User registration and login handlers.
  * `mcqs.py`: Read operations for fetching MCQ categories.
  * `evaluation.py`: Processes driving test submissions and calculates scores, fatigue eligibility, and risk profiles.
  * `admin.py`: CRUD endpoints for administrators, including bulk import/export of questions.
* `static/`:
  * `/audio/`: Cached MP3 files generated dynamically from TTS transcriptions.
  * `/uploads/`: Local cached copies of external images, GIFs, and videos used in MCQs.

---

## ⚙️ Configuration & Environment Setup

Create a `.env` file in the root of the `backend` directory:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/quizDB?retryWrites=true&w=majority
DB_NAME=quizDB
```

---

## 🏃 Run Locally

### Prerequisites
* **Python 3.10** or higher
* **pip** (Python package installer)

### Steps
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install package requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. **Seed the database** (mandatory on first setup to populate initial MCQs and admin user):
   ```bash
   python seed.py
   ```
5. Start the development server using Uvicorn:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
6. Access interactive API documentation (Swagger UI):
   * Open `http://localhost:8000/docs` in your browser.
