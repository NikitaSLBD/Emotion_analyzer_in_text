import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoConfig, AutoModel
from typing import Dict, List
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

from modules.logger import get_logger, log_function_call

class RuBertEmotionClassifier(nn.Module):
    def __init__(self, num_labels=6, model_name=None):
        super(RuBertEmotionClassifier, self).__init__()
        self.num_labels = num_labels
        self.logger = get_logger("rubert_base_model")
        
        try:
            
            self.config = AutoConfig.from_pretrained(model_name, num_labels=num_labels)
            self.bert = AutoModel.from_pretrained(model_name, config=self.config)
            
            
            # Классификатор поверх BERT
            self.dropout = nn.Dropout(self.config.hidden_dropout_prob)
            self.classifier = nn.Linear(self.config.hidden_size, num_labels)
            
            self.logger.info(f"Инициализирована модель RuBERT-base-cased с {num_labels} классами")
            self.logger.info(f"Hidden size: {self.config.hidden_size}, Layers: {self.config.num_hidden_layers}")
            self.logger.info(f"Vocab size: {self.config.vocab_size}")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации RuBERT-base-cased модели: {str(e)}")
            raise

    def forward(self, input_ids, attention_mask=None, token_type_ids=None):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            return_dict=True
        )
        
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        
        return logits

class RuBertEmotionAnalyzer:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger = get_logger("rubert_base_analyzer")
        
        self.id2label = {
            0: "грусть", 
            1: "радость",
            2: "любовь",
            3: "злость",
            4: "страх",
            5: "удивление"
        }
        
        self.emotion_colors = {
            "грусть": "#3498db", 
            "радость": "#2ecc71",
            "любовь": "#cb4184",
            "злость": "#eb2222",
            "страх": "#95a5a6",
            "удивление": "#f1c40f"
        }

    @log_function_call("rubert_base_model")
    def load_model(self, model_path: str = None):
        """Загрузка модели RuBERT-base-cased и токенизатора из обученных файлов"""
        if model_path is None:
            model_dir = Path(__file__).parent.parent / "model"
        else:
            model_dir = Path(model_path).parent
        
        try:
            self.logger.info(f"Загрузка RuBERT-base-cased модели из директории: {model_dir}")
            
            model_file = model_dir / "rubert_emotion_classifier.pt"
            tokenizer_dir = model_dir / "tokenizer_data"
            
            if not model_file.exists():
                self.logger.error(f"Файл модели не найден: {model_file}")
                return False
            
            tokenizer_files = [
                tokenizer_dir / "special_tokens_map.json",
                tokenizer_dir / "tokenizer_config.json", 
                tokenizer_dir / "vocab.txt"
            ]
            
            existing_files = [f for f in tokenizer_files if f.exists()]
            self.logger.info(f"Найдено файлов токенизатора: {len(existing_files)}")
            
            # Загружаем токенизатор
            if all(f.exists() for f in tokenizer_files):
                self.logger.info("Загрузка токенизатора из локальных файлов")
                self.tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir))
            else:
                self.logger.info("Загрузка токенизатора DeepPavlov/rubert-base-cased")
                self.tokenizer = AutoTokenizer.from_pretrained("DeepPavlov/rubert-base-cased")
            
            # Загружаем словарь состояния модели
            self.logger.info(f"Загрузка весов модели из {model_file}")
            state_dict = torch.load(model_file, map_location=self.device)
            
            # Создаем модель RuBERT-base-cased
            self.model = RuBertEmotionClassifier(num_labels=6, model_name="DeepPavlov/rubert-base-cased")
            
            # Загружаем веса
            self.model.load_state_dict(state_dict, strict=True)
            self.model.to(self.device)
            self.model.eval()
            
            self.logger.info("RuBERT-base-cased модель и токенизатор успешно загружены")
            self.logger.info(f"Размер словаря: {len(self.tokenizer)}")
            self.logger.info(f"Архитектура: {self.model.config.num_hidden_layers} слоев, hidden_size={self.model.config.hidden_size}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки RuBERT-base-cased модели: {str(e)}")
            return False

    def is_loaded(self) -> bool:
        """Проверка загрузки модели"""
        return self.model is not None and self.tokenizer is not None

    @log_function_call("rubert_base_model")
    def predict_emotion(self, text: str) -> Dict:
        """Предсказание эмоции для текста"""
        if not self.is_loaded():
            return {"error": "Модель не загружена"}
        
        try:
            # Токенизация текста
            inputs = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            
            # Предсказание
            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.softmax(outputs, dim=1)
                predicted_class = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][predicted_class].item()
            
            all_probs = {
                self.id2label[i]: float(prob) 
                for i, prob in enumerate(probabilities[0])
            }
            
            result = {
                "emotion": self.id2label[predicted_class],
                "confidence": confidence,
                "all_probabilities": all_probs,
                "text": text
            }
            
            self.logger.debug(f"Предсказана эмоция: {result['emotion']} (уверенность: {confidence:.3f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка предсказания: {str(e)}")
            return {"error": str(e)}

    @log_function_call("rubert_base_model")
    def analyze_sentences(self, sentences: List[str]) -> List[Dict]:
        """Анализ списка предложений"""
        self.logger.info(f"Начинается анализ {len(sentences)} предложений с RuBERT-base-cased")
        results = []
        
        for i, sentence in enumerate(sentences):
            try:
                result = self.predict_emotion(sentence)
                if "error" not in result:
                    results.append(result)
                else:
                    self.logger.warning(f"Ошибка при анализе предложения {i+1}: {sentence}")
            except Exception as e:
                self.logger.error(f"Исключение при анализе предложения {i+1}: {str(e)}")
        
        self.logger.info(f"RuBERT-base-cased анализ завершен: {len(results)} из {len(sentences)} предложений")
        return results

    @log_function_call("visualization")
    def create_emotion_chart(self, probabilities: Dict[str, float], title: str) -> str:
        """Создание круговой диаграммы для эмоций"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            emotions = list(probabilities.keys())
            probs = list(probabilities.values())
            colors = [self.emotion_colors.get(emotion, '#cccccc') for emotion in emotions]
            
            wedges, texts, autotexts = ax.pie(probs, labels=emotions, colors=colors, 
                                             autopct='%1.1f%%', startangle=90)
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            self.logger.debug(f"Создана круговая диаграмма: {title}")
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            self.logger.error(f"Ошибка создания круговой диаграммы: {str(e)}")
            return ""

    @log_function_call("visualization")
    def create_frequency_chart(self, emotion_counts: Dict[str, int]) -> str:
        """Создание диаграммы частоты эмоций"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            emotions = list(emotion_counts.keys())
            counts = list(emotion_counts.values())
            colors = [self.emotion_colors.get(emotion, '#cccccc') for emotion in emotions]
            
            bars = ax.bar(emotions, counts, color=colors)
            ax.set_title('Частота эмоций в тексте', fontsize=14, fontweight='bold')
            ax.set_ylabel('Количество предложений')
            
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{count}', ha='center', va='bottom', fontweight='bold')
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            buffer.seek(0)
            frequency_chart = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            plt.close()
            
            self.logger.debug("Создана диаграмма частоты эмоций")
            return frequency_chart
            
        except Exception as e:
            self.logger.error(f"Ошибка создания диаграммы частоты: {str(e)}")
            return ""

    @log_function_call("visualization")
    def create_visualizations(self, sentence_results: List[Dict]) -> Dict:
        """Создание всех визуализаций для результатов"""
        self.logger.info("Создание визуализаций для результатов анализа")
        
        # Создаем диаграммы для каждого предложения
        for i, result in enumerate(sentence_results):
            result['chart'] = self.create_emotion_chart(
                result['all_probabilities'], 
                f"Предложение {i+1}: {result['text'][:30]}..."
            )
        
        overall_probs = {}
        emotion_counts = {}
        
        for result in sentence_results:
            for emotion, prob in result['all_probabilities'].items():
                if emotion not in overall_probs:
                    overall_probs[emotion] = 0
                overall_probs[emotion] += prob
            
            emotion = result['emotion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Усредняем вероятности
        for emotion in overall_probs:
            overall_probs[emotion] /= len(sentence_results)
        
        # Общая диаграмма
        overall_chart = self.create_emotion_chart(overall_probs, "Общее распределение эмоций")
        
        # Диаграмма частоты эмоций
        frequency_chart = self.create_frequency_chart(emotion_counts)
        
        self.logger.info("Визуализации успешно созданы")
        
        return {
            "overall_chart": overall_chart,
            "frequency_chart": frequency_chart,
            "emotion_counts": emotion_counts,
            "total_sentences": len(sentence_results)
        }
    
    @log_function_call("preparing_for_storage")
    def prepare_analysis_for_storage(self, original_text: str, analysis_results: List[Dict]) -> Dict:
        """Подготавливает результаты анализа для хранения в БД"""
        return {
            "original_text": original_text,
            "sentences_count": len(analysis_results),
            "analysis_results": analysis_results,
            "summary": self._create_analysis_summary(analysis_results)
        }


    @log_function_call("summary_creation")
    def _create_analysis_summary(self, analysis_results: List[Dict]) -> Dict:
        """Создает сводку по анализу"""
        emotion_counts = {}
        total_confidence = 0

        for result in analysis_results:
            emotion = result['emotion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_confidence += result['confidence']

        avg_confidence = total_confidence / len(analysis_results) if analysis_results else 0

        return {
            "emotion_counts": emotion_counts,
            "dominant_emotion": max(emotion_counts, key=emotion_counts.get) if emotion_counts else "неизвестно",
            "average_confidence": avg_confidence,
            "total_sentences": len(analysis_results)
        }

    @log_function_call("hierarchical_analysis")
    def analyze_with_comments(self, comments_data: List[Dict]) -> Dict:
        """
        Иерархический анализ: комментарии -> предложения

        Args:
            comments_data: Список словарей с данными комментариев из preprocessor

        Returns:
            Словарь с иерархической структурой анализа
        """
        self.logger.info(f"Starting hierarchical analysis for {len(comments_data)} comments")

        analyzed_comments = []
        all_sentence_results = []

        for comment_data in comments_data:
            comment_index = comment_data['comment_index']
            valid_sentences = comment_data['valid_sentences']

            if not valid_sentences:
                self.logger.warning(f"Comment {comment_index} has no valid sentences, skipping")
                analyzed_comments.append({
                    "comment_index": comment_index,
                    "original_text": comment_data['original_text'],
                    "sentence_results": [],
                    "comment_summary": None,
                    "comment_chart": None,
                    "skipped_sentences": comment_data.get('skipped_sentences', []),
                    "valid_sentences_count": 0,
                    "skipped_sentences_count": len(comment_data.get('skipped_sentences', []))
                })
                continue

            # Анализируем предложения комментария
            self.logger.info(f"Analyzing comment {comment_index + 1} with {len(valid_sentences)} sentences")
            sentence_results = self.analyze_sentences(valid_sentences)

            # Создаем визуализации для каждого предложения
            for i, result in enumerate(sentence_results):
                result['chart'] = self.create_emotion_chart(
                    result['all_probabilities'],
                    f"Комментарий {comment_index + 1}, Предложение {i + 1}"
                )
                result['sentence_index_in_comment'] = i

            # Создаем сводку по комментарию
            comment_summary = self._create_analysis_summary(sentence_results)

            # Создаем общую диаграмму для комментария
            if sentence_results:
                overall_probs = {}
                for result in sentence_results:
                    for emotion, prob in result['all_probabilities'].items():
                        if emotion not in overall_probs:
                            overall_probs[emotion] = 0
                        overall_probs[emotion] += prob

                # Усредняем вероятности
                for emotion in overall_probs:
                    overall_probs[emotion] /= len(sentence_results)

                comment_chart = self.create_emotion_chart(
                    overall_probs,
                    f"Комментарий {comment_index + 1}: Общее распределение"
                )
            else:
                comment_chart = None

            analyzed_comments.append({
                "comment_index": comment_index,
                "original_text": comment_data['original_text'],
                "sentence_results": sentence_results,
                "comment_summary": comment_summary,
                "comment_chart": comment_chart,
                "skipped_sentences": comment_data.get('skipped_sentences', []),
                "valid_sentences_count": len(sentence_results),
                "skipped_sentences_count": comment_data.get('skipped_sentences_count', 0)
            })

            all_sentence_results.extend(sentence_results)

        # Создаем общую статистику по всем комментариям
        if all_sentence_results:
            overall_visualization = self.create_visualizations(all_sentence_results)
            overall_summary = self._create_analysis_summary(all_sentence_results)
        else:
            overall_visualization = {}
            overall_summary = {}

        result = {
            "comments": analyzed_comments,
            "overall_summary": overall_summary,
            "overall_visualization": overall_visualization,
            "total_comments": len(comments_data),
            "total_analyzed_sentences": len(all_sentence_results)
        }

        self.logger.info(f"Hierarchical analysis completed: {len(analyzed_comments)} comments, "
                        f"{len(all_sentence_results)} sentences analyzed")

        return result