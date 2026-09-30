# EduGenie 🎓

**AI-Powered Educational Assistant** — Learn smarter. Understand faster.
EduGenie is an intelligent learning workspace that helps students, self-learners, and educators master concepts, test knowledge, and build structured learning paths — all powered by Google's Gemini AI.

## ✨ Features

| Feature | Description |
|---------|-------------|
| **📝 Ask (Q&A)** | Get clear, detailed answers to educational questions |
| **💡 Explain** | Receive simple, structured explanations of complex concepts |
| **🧩 Quiz** | Generate interactive multiple-choice quizzes on any topic |
| **📄 Summarize** | Condense long passages into concise summaries with key points |
| **🗺️ Learning Path** | Get structured, staged roadmaps to master any subject |

## 🏗️ Architecture

```
EduGenie/
├── main.py                 # FastAPI application entry point
├── ai_service.py           # Centralized Gemini AI integration
├── qna.py                  # Q&A endpoint module
├── explanation_module.py   # Concept explanation endpoint
├── quiz_module.py          # Quiz generation with validation
├── summary_module.py       # Text summarization endpoint
├── learning_path.py        # Learning path generation
├── templates/
│   └── index.html          # Main application page
├── static/
│   ├── css/
│   │   └── styles.css      # Application styles
│   └── js/
│       └── app.js          # Frontend interactivity
├── tests/
│   └── test_api.py         # Automated test suite
├── requirements.txt        # Python dependencies
├── Procfile                # Production deployment config
├── .env.example            # Environment variable template
└── .gitignore              # Git ignore rules
```

## 🛠️ Tech Stack

- **Backend:** Python 3.11+, FastAPI, Pydantic
- **AI:** Google Gemini 3.8 Flash via `google-generativeai`
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Server:** Gunicorn + Uvicorn Workers / Vercel Serverless
- **Deployment:** Vercel / Render

## 📋 Prerequisites

- Python 3.11 or higher
- A Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shruthi-s-01/EduGenie.git
   cd EduGenie
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Your Google Gemini API key | ✅ Yes |

## 💻 Local Development

```bash
uvicorn main:app --reload --port 8000
```

Then visit [http://localhost:8000](http://localhost:8000)

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main application page |
| `GET` | `/health` | Health check |
| `POST` | `/qa` | Answer an educational question |
| `POST` | `/explain` | Explain a concept |
| `POST` | `/quiz` | Generate a quiz |
| `POST` | `/summarize` | Summarize text |
| `POST` | `/learn/recommendations` | Create a learning path |

### Request/Response Examples

#### Q&A
```json
// POST /qa
{ "question": "What is photosynthesis?" }
// Response
{ "answer": "Photosynthesis is the process by which..." }
```

#### Quiz
```json
// POST /quiz
{ "topic": "Solar System" }
// Response
{
  "questions": [
    {
      "question": "Which planet is closest to the Sun?",
      "options": ["Venus", "Mercury", "Earth", "Mars"],
      "correct_answer": "Mercury"
    }
  ]
}
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 🌐 Deployment

### Vercel (Recommended)

1. Import your GitHub repository to [Vercel](https://vercel.com)
2. Go to **Settings → Environment Variables**
3. Add `GEMINI_API_KEY` with your Gemini API key value
4. Deploy (Vercel automatically detects `vercel.json` and configures the Python serverless runtime)

### Render

1. Connect your GitHub repository to [Render](https://render.com)
2. Create a new **Web Service**
3. Set the following:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
4. Add the `GEMINI_API_KEY` environment variable
5. Deploy

## 🔮 Future Enhancements

- User authentication and progress tracking
- Flashcard generation
- Study session history
- Export quizzes and summaries
- Multi-language support
- Voice input/output
- Collaborative study features

## 📄 License

This project is for educational purposes.

---

Built with ❤️ for learners, by learners.
