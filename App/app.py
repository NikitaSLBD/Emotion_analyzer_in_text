from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from modules.emotion_classifier import RuBertEmotionAnalyzer
from modules.text_preprocessor import TextPreprocessor
from modules.logger import get_logger
from modules.database import get_db, init_db
from modules.user import User, TextAnalysis
from modules.auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_current_admin_user
)
from modules.user_control import get_current_user_optional, get_current_user_required
from modules.data import UserCreate, Token, UserResponse
from pathlib import Path

logger = get_logger("web")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Загрузка модели и инициализация БД при запуске приложения"""
    # Инициализация БД
    init_db()
    
    # Загрузка модели
    emotion_analyzer.load_model()
    
    yield

app = FastAPI(
    title="EmotionAnalyzer", 
    version="1.0.0", 
    lifespan=lifespan,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

BASE_DIR = Path(__file__).parent

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=BASE_DIR / "web" / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "web" / "templates")

# Инициализация компонентов
emotion_analyzer = RuBertEmotionAnalyzer()
text_preprocessor = TextPreprocessor()

# API Routes 
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 совместимый endpoint для получения токена"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
async def register_web(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    is_admin: str = Form("false"),  
    db: Session = Depends(get_db)
):
    """Регистрация пользователя (веб-форма)"""
    try:
        # Преобразуем is_admin из строки в boolean
        is_admin_bool = is_admin.lower() == "true"
        
        # Создаем объект UserCreate
        user_data = UserCreate(
            email=email.strip(),
            username=username.strip(),
            password=password,
            is_admin=is_admin_bool
        )
        
        # Проверяем, существует ли пользователь
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Пользователь с таким email или именем уже существует"
            })
        
        # Создаем пользователя
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            is_admin=user_data.is_admin
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Создаем токен для автоматического входа
        access_token = create_access_token(data={"sub": user.username})
        
        # Перенаправляем на главную с установкой cookie
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token", 
            value=access_token, 
            httponly=True,
            max_age=1800  # 30 минут
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка регистрации: {str(e)}"
        })

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return current_user

# Web Routes
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    current_user: User = Depends(get_current_user_optional)
):
    """Главная страница с формой ввода"""
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "user": current_user
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_web(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Аутентификация пользователя (веб-форма)"""
    try:
        # Используем OAuth2 endpoint для аутентификации
        form_data = OAuth2PasswordRequestForm(
            username=username,
            password=password
        )
        
        token_data = await login_for_access_token(form_data, db)
        
        # Перенаправляем на главную с установкой cookie
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token", 
            value=token_data.access_token, 
            httponly=True,
            max_age=1800  # 30 минут
        )
        
        return response
        
    except HTTPException as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Неверное имя пользователя или пароль"
        })

@app.post("/logout")
async def logout():
    """Выход из системы"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response

@app.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Страница истории анализов"""
    analyses = db.query(TextAnalysis).filter(
        TextAnalysis.user_id == current_user.id
    ).order_by(TextAnalysis.created_at.desc()).all()
    
    return templates.TemplateResponse("history.html", {
        "request": request,
        "user": current_user,
        "analyses": analyses,
        "total": len(analyses)
    })

@app.post("/analyze")
async def analyze_text(
    request: Request,
    text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Анализ текста и сохранение результатов"""
    if not emotion_analyzer.is_loaded():
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Модель не загружена",
            "user": current_user
        })
    
    # Разделяем текст на предложения
    sentences = text_preprocessor.split_into_sentences(text)
    
    if not sentences:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Не удалось выделить предложения из текста",
            "user": current_user
        })
    
    # Анализируем каждое предложение
    analysis_results = emotion_analyzer.analyze_sentences(sentences)
    
    if not analysis_results:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Не удалось проанализировать текст",
            "user": current_user
        })
    
    # Создаем визуализации
    visualization_data = emotion_analyzer.create_visualizations(analysis_results)
    
    # Сохраняем анализ в БД
    analysis_data = emotion_analyzer.prepare_analysis_for_storage(text, analysis_results)
    
    db_analysis = TextAnalysis(
        user_id=current_user.id,
        original_text=text,
        analysis_results=analysis_data
    )
    
    db.add(db_analysis)
    db.commit()
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "user": current_user,
        "original_text": text,
        "sentence_results": analysis_results,
        **visualization_data
    })

# Admin routes
@app.get("/admin/analyses")
async def get_all_analyses(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """Получить все анализы (только для администраторов)"""
    analyses = db.query(TextAnalysis).order_by(TextAnalysis.created_at.desc()).all()
    return {"analyses": analyses}

@app.get("/health")
async def health_check():
    """Проверка статуса приложения"""
    return {
        "status": "healthy",
        "model_loaded": emotion_analyzer.is_loaded()
    }