
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from modules.emotion_classifier import RuBertEmotionAnalyzer
from modules.text_preprocessor import TextPreprocessor
from modules.logger import get_logger
from pathlib import Path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Загрузка модели при запуске приложения"""
    emotion_analyzer.load_model()
    yield

logger = get_logger("web")

app = FastAPI(title="EmotionAnalyzer", version="1.0.0", lifespan=lifespan)

BASE_DIR = Path(__file__).parent

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=BASE_DIR / "web" / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "web" / "templates")

# Инициализация компонентов
emotion_analyzer = RuBertEmotionAnalyzer()
text_preprocessor = TextPreprocessor()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница с формой ввода"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze_text(request: Request, text: str = Form(...)):
    """Анализ текста и возврат результатов"""
    if not emotion_analyzer.is_loaded():
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Модель не загружена"
        })
    
    # Разделяем текст на предложения
    sentences = text_preprocessor.split_into_sentences(text)
    
    if not sentences:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Не удалось выделить предложения из текста"
        })
    
    # Анализируем каждое предложение
    analysis_results = emotion_analyzer.analyze_sentences(sentences)
    
    if not analysis_results:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Не удалось проанализировать текст"
        })
    
    # Создаем визуализации
    visualization_data = emotion_analyzer.create_visualizations(analysis_results)
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "original_text": text,
        "sentence_results": analysis_results,
        **visualization_data
    })

@app.get("/health")
async def health_check():
    """Проверка статуса приложения"""
    return {
        "status": "healthy",
        "model_loaded": emotion_analyzer.is_loaded()
    }