import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from typing import Dict, List
from App.modules.logger import get_logger, log_function_call


class EmotionVisualizer:
    """Класс для создания визуализаций результатов анализа эмоций"""

    def __init__(self):
        self.logger = get_logger("visualization")

        self.emotion_colors = {
            "грусть": "#bbdefb",
            "радость": "#b8e6c9",
            "любовь": "#e1bee7",
            "злость": "#ffb8b8",
            "страх": "#bac3c4",
            "удивление": "#fff59d"
        }

    @log_function_call("visualization")
    def create_emotion_chart(self, probabilities: Dict[str, float], title: str) -> str:
        """Создание круговой диаграммы для эмоций

        Args:
            probabilities: Словарь с вероятностями эмоций
            title: Заголовок диаграммы

        Returns:
            Base64-encoded изображение в формате data URI
        """
        try:
            fig, ax = plt.subplots(figsize=(8, 6))

            emotions = list(probabilities.keys())
            probs = list(probabilities.values())
            colors = [self.emotion_colors.get(emotion, '#cccccc') for emotion in emotions]

            wedges, texts, autotexts = ax.pie(probs, labels=emotions, colors=colors,
                                             autopct='%1.1f%%', startangle=90)

            for autotext in autotexts:
                autotext.set_color('black')
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
        """Создание диаграммы частоты эмоций

        Args:
            emotion_counts: Словарь с количеством каждой эмоции

        Returns:
            Base64-encoded изображение в формате data URI
        """
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
        """Создание всех визуализаций для результатов анализа

        Args:
            sentence_results: Список результатов анализа предложений

        Returns:
            Словарь с визуализациями и статистикой
        """
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