from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
import tempfile
import os

from infrastructure.config import settings

from modules.emotion_classifier import RuBertEmotionAnalyzer
from modules.text_preprocessing import TextPreprocessor
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
from modules.social_media import CollectorFactory
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
        form_data = OAuth2PasswordRequestForm(
            username=username,
            password=password
        )
        
        token_data = await login_for_access_token(form_data, db)
        
        # Перенаправляем на главную с установкой cookie
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token", 
            value=token_data['access_token'], 
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

@app.get("/analysis/{analysis_id}")
async def analysis_detail(
    analysis_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Просмотр деталей конкретного анализа"""
    from modules.visualization import EmotionVisualizer

    analysis = db.query(TextAnalysis).filter(
        TextAnalysis.id == analysis_id,
        TextAnalysis.user_id == current_user.id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")

    # Определяем тип анализа по структуре данных
    analysis_data = analysis.analysis_results
    is_hierarchical = 'comments' in analysis_data

    # Создаем визуализатор для пересоздания диаграмм
    visualizer = EmotionVisualizer()

    if is_hierarchical:
        # Пересоздаем визуализации для иерархического анализа
        all_sentence_results = []
        for comment in analysis_data.get('comments', []):
            for sentence in comment.get('sentence_results', []):
                all_sentence_results.append(sentence)

        # Создаем визуализации
        if all_sentence_results:
            overall_visualization = visualizer.create_visualizations(all_sentence_results)
        else:
            overall_visualization = {}

        # Иерархический анализ (с комментариями)
        return templates.TemplateResponse("results_hierarchical.html", {
            "request": request,
            "user": current_user,
            "analysis_id": analysis.id,
            "original_text": analysis.original_text,
            "source_info": analysis_data.get('source'),
            "comments_data": analysis_data.get('comments_statistics'),
            "validation_result": {
                'comments_count': analysis_data.get('comments_count', 0),
                'total_sentences_count': analysis_data.get('total_sentences_count', 0),
                'total_valid_sentences_count': analysis_data.get('total_valid_sentences_count', 0),
                'total_skipped_sentences_count': analysis_data.get('total_skipped_sentences_count', 0),
            },
            "analysis_result": {
                'comments': analysis_data.get('comments', []),
                'overall_summary': analysis_data.get('overall_summary', {}),
                'overall_visualization': overall_visualization,
                'total_comments': analysis_data.get('total_comments', 0),
                'total_analyzed_sentences': analysis_data.get('total_analyzed_sentences', 0)
            },
            **overall_visualization
        })
    else:
        # Пересоздаем визуализации для обычного анализа
        sentence_results = analysis_data.get('sentence_results', [])

        if sentence_results:
            visualization_data = visualizer.create_visualizations(sentence_results)
        else:
            visualization_data = {
                'overall_chart': '',
                'frequency_chart': '',
                'emotion_counts': {},
                'total_sentences': 0
            }

        # Обычный анализ
        return templates.TemplateResponse("results.html", {
            "request": request,
            "user": current_user,
            "analysis_id": analysis.id,
            "original_text": analysis.original_text,
            "processed_text": analysis_data.get('processed_text', analysis.original_text),
            "was_corrected": analysis_data.get('validation', {}).get('has_corrections', False),
            "corrections": analysis_data.get('validation', {}).get('spell_corrections', []),
            "sentence_results": sentence_results,
            "source_info": analysis_data.get('source'),
            "comments_data": analysis_data.get('comments_statistics'),
            "skipped_sentences": analysis_data.get('skipped_sentences', []),
            "valid_sentences_count": analysis_data.get('valid_sentences_count', 0),
            "total_sentences_count": analysis_data.get('total_sentences_count', 0),
            **visualization_data
        })

@app.post("/analyze")
async def analyze_text(
    request: Request,
    text: Optional[str] = Form(None),
    source_type: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    max_comments: Optional[int] = Form(50),
    auto_correct: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Анализ текста из формы или комментариев из социальных сетей"""
    if not emotion_analyzer.is_loaded():
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Модель не загружена",
            "user": current_user
        })

    # Определяем источник текста
    input_text = None
    source_info = None
    comments_data = None

    if source_type and source_url:
        # Обработка комментариев из социальных сетей
        try:
            # Получаем учетные данные из переменных окружения
            credentials = {}
            if source_type == 'youtube':
                api_key = settings.YOUTUBE_API_KEY
                if not api_key:
                    return templates.TemplateResponse("error.html", {
                        "request": request,
                        "error": "YouTube API ключ не настроен. Обратитесь к администратору.",
                        "user": current_user
                    })
                credentials['api_key'] = api_key
            elif source_type == 'telegram':
                api_id = settings.TELEGRAM_API_ID
                api_hash = settings.TELEGRAM_API_HASH
                bot_token = settings.TELEGRAM_BOT_TOKEN

                # Проверяем наличие api_id и api_hash (обязательны даже для ботов)
                if not api_id or not api_hash:
                    return templates.TemplateResponse("error.html", {
                        "request": request,
                        "error": "Telegram API данные не настроены. Укажите TELEGRAM_API_ID и TELEGRAM_API_HASH (обязательны даже для ботов).",
                        "user": current_user
                    })

                credentials['api_id'] = int(api_id)
                credentials['api_hash'] = api_hash

                # Если есть bot_token, используем Bot API
                if bot_token:
                    credentials['bot_token'] = bot_token
                    logger.info("Using Telegram Bot API")
                else:
                    logger.info("Using Telegram User API (anonymous access)")

            # Создаем коллектор
            collector = CollectorFactory.create_collector(source_type, credentials)

            # Собираем комментарии
            logger.info(f"Сбор комментариев из {source_type}: {source_url}")
            comments = collector.collect_comments(
                source_url,
                max_comments=max_comments,
                include_replies=False
            )

            if not comments:
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "error": "Не удалось получить комментарии. Проверьте URL и доступность источника.",
                    "user": current_user
                })

            # Объединяем комментарии в текст
            input_text = collector.format_comments_as_text(comments)

            # Сохраняем информацию об источнике
            source_info = {
                'type': source_type,
                'url': source_url,
                'comments_count': len(comments)
            }

            # Сохраняем статистику комментариев
            comments_data = collector.get_statistics(comments)

            logger.info(f"Собрано {len(comments)} комментариев из {source_type}")

        except ValueError as e:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": f"Ошибка обработки URL: {str(e)}",
                "user": current_user
            })
        except ConnectionError as e:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": f"Ошибка подключения к {source_type}: {str(e)}",
                "user": current_user
            })
        except ImportError as e:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": f"Отсутствует необходимая библиотека: {str(e)}",
                "user": current_user
            })
        except Exception as e:
            logger.error(f"Social media collection error: {str(e)}")
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": f"Не удалось собрать комментарии: {str(e)}",
                "user": current_user
            })

    elif text:
        # Обработка текста из формы
        input_text = text
        source_info = {'type': 'text'}
    else:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Необходимо ввести текст или указать источник комментариев",
            "user": current_user
        })

    # Определяем, есть ли комментарии в тексте
    has_comments = '\n' + '_' * 2 + '\n' in input_text

    if has_comments:
        # Иерархический анализ с комментариями
        logger.info("Detected comment structure, using hierarchical analysis")
        validation_result = text_preprocessor.validate_and_correct_text_with_comments(
            input_text,
            auto_correct=auto_correct,
            use_speller=True,
            skip_invalid=True
        )

        if not validation_result['valid']:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": f"Текст не прошел валидацию: не найдено ни одного валидного предложения",
                "user": current_user
            })

        # Иерархический анализ эмоций
        analysis_result = emotion_analyzer.analyze_with_comments(validation_result['comments'])

        if not analysis_result['total_analyzed_sentences']:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Не удалось проанализировать текст",
                "user": current_user
            })

        # Сохраняем анализ в БД только для авторизованных пользователей
        if current_user:
            analysis_data = {
                "original_text": input_text,
                "analysis_type": "hierarchical",
                "comments_count": validation_result['comments_count'],
                "total_sentences_count": validation_result['total_sentences_count'],
                "total_valid_sentences_count": validation_result['total_valid_sentences_count'],
                "total_skipped_sentences_count": validation_result['total_skipped_sentences_count'],
                "comments": analysis_result['comments'],
                "overall_summary": analysis_result['overall_summary'],
                "validation": {
                    "has_corrections": validation_result.get('has_corrections', False),
                    "original_text": input_text
                },
                "source": source_info
            }

            if comments_data:
                analysis_data['comments_statistics'] = comments_data

            db_analysis = TextAnalysis(
                user_id=current_user.id,
                original_text=input_text,
                analysis_results=analysis_data
            )

            db.add(db_analysis)
            db.commit()
            db.refresh(db_analysis)  # Получаем ID после commit
            logger.info(f"Hierarchical analysis saved to database for user {current_user.username}")
            analysis_id = db_analysis.id
        else:
            logger.info("Hierarchical analysis performed for anonymous user, not saved to database")
            analysis_id = None

        return templates.TemplateResponse("results_hierarchical.html", {
            "request": request,
            "user": current_user,
            "analysis_id": analysis_id,
            "original_text": input_text,
            "source_info": source_info,
            "comments_data": comments_data,
            "validation_result": validation_result,
            "analysis_result": analysis_result,
            **analysis_result['overall_visualization']
        })

    else:
        # Обычный анализ без комментариев
        logger.info("No comment structure detected, using standard analysis")
        validation_result = text_preprocessor.validate_and_correct_text(
            input_text,
            auto_correct=auto_correct,
            use_speller=True,
            skip_invalid=True  # Пропускаем невалидные предложения
        )

    if not validation_result['valid']:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Текст не прошел валидацию: не найдено ни одного валидного предложения",
            "user": current_user,
            "issues": validation_result.get('issues', []),
            "skipped_sentences": validation_result.get('skipped_sentences', [])
        })

    # Используем только валидные предложения для анализа
    valid_sentences = validation_result.get('valid_sentences', [])
    skipped_sentences = validation_result.get('skipped_sentences', [])

    if not valid_sentences:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Не найдено валидных предложений для анализа",
            "user": current_user,
            "skipped_sentences": skipped_sentences
        })

    # Анализируем только валидные предложения
    analysis_results = emotion_analyzer.analyze_sentences(valid_sentences)

    if not analysis_results:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Не удалось проанализировать текст",
            "user": current_user
        })

    # Создаем визуализации
    visualization_data = emotion_analyzer.create_visualizations(analysis_results)

    # Сохраняем анализ в БД только для авторизованных пользователей
    if current_user:
        analysis_data = emotion_analyzer.prepare_analysis_for_storage(
            validation_result['corrected_text'],
            analysis_results
        )

        # Добавляем информацию о валидации и исправлениях
        analysis_data['validation'] = {
            'was_corrected': validation_result['has_corrections'],
            'original_text': input_text,
            'corrections': validation_result.get('spell_corrections', []),
            'issues': validation_result.get('issues', []),
            'valid_sentences_count': validation_result.get('valid_sentences_count', 0),
            'skipped_sentences_count': validation_result.get('skipped_sentences_count', 0),
            'skipped_sentences': skipped_sentences
        }

        # Добавляем информацию об источнике
        analysis_data['source'] = source_info
        if comments_data:
            analysis_data['comments_statistics'] = comments_data

        db_analysis = TextAnalysis(
            user_id=current_user.id,
            original_text=input_text,
            analysis_results=analysis_data
        )

        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)  # Получаем ID после commit
        logger.info(f"Analysis saved to database for user {current_user.username}")
        analysis_id = db_analysis.id
    else:
        logger.info("Analysis performed for anonymous user, not saved to database")
        analysis_id = None

    return templates.TemplateResponse("results.html", {
        "request": request,
        "user": current_user,
        "analysis_id": analysis_id,
        "original_text": input_text,
        "processed_text": validation_result['corrected_text'],
        "was_corrected": validation_result['has_corrections'],
        "corrections": validation_result.get('spell_corrections', []),
        "sentence_results": analysis_results,
        "source_info": source_info,
        "comments_data": comments_data,
        "skipped_sentences": skipped_sentences,
        "valid_sentences_count": len(valid_sentences),
        "total_sentences_count": validation_result.get('sentences_count', 0),
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

# Export routes
@app.get("/export/json/{analysis_id}")
async def export_analysis_json(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Экспорт результатов анализа в JSON"""
    from modules.analysis_results_handler import AnalysisResultsHandler
    from fastapi.responses import FileResponse
    import tempfile
    import os

    # Получаем анализ из БД
    analysis = db.query(TextAnalysis).filter(
        TextAnalysis.id == analysis_id,
        TextAnalysis.user_id == current_user.id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")

    # Создаем обработчик результатов
    results_handler = AnalysisResultsHandler()

    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        temp_path = f.name

    try:
        # Сохраняем в JSON
        success = results_handler.save_to_json(analysis.analysis_results, temp_path)

        if not success:
            raise HTTPException(status_code=500, detail="Ошибка создания JSON файла")

        # Формируем имя файла
        timestamp = analysis.created_at.strftime('%Y%m%d_%H%M%S')
        filename = f"analysis_{analysis_id}_{timestamp}.json"

        return FileResponse(
            temp_path,
            media_type='application/json',
            filename=filename,
            background=None
        )
    except Exception as e:
        # Удаляем временный файл в случае ошибки
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        logger.error(f"Ошибка экспорта JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")

@app.get("/export/html/{analysis_id}")
async def export_analysis_html(
    analysis_id: int,
    include_details: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required)
):
    """Экспорт результатов анализа в HTML"""
    from modules.analysis_results_handler import AnalysisResultsHandler
    from fastapi.responses import FileResponse
    import tempfile
    import os

    # Получаем анализ из БД
    analysis = db.query(TextAnalysis).filter(
        TextAnalysis.id == analysis_id,
        TextAnalysis.user_id == current_user.id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")

    # Создаем обработчик результатов
    results_handler = AnalysisResultsHandler()

    # Создаем временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        temp_path = f.name

    try:
        # Создаем HTML
        success = results_handler.export_to_html(
            analysis.analysis_results,
            temp_path,
            include_sentence_details=include_details
        )

        if not success:
            raise HTTPException(status_code=500, detail="Ошибка создания HTML файла")

        # Формируем имя файла
        timestamp = analysis.created_at.strftime('%Y%m%d_%H%M%S')
        filename = f"analysis_report_{analysis_id}_{timestamp}.html"

        return FileResponse(
            temp_path,
            media_type='text/html',
            filename=filename,
            background=None
        )
    except Exception as e:
        # Удаляем временный файл в случае ошибки
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        logger.error(f"Ошибка экспорта HTML: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")