import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from App.modules.logger import get_logger, log_function_call
from App.modules.visualization import EmotionVisualizer


class AnalysisResultsHandler:
    """Обработчик результатов анализа эмоций для сохранения в JSON и экспорта в PDF"""

    def __init__(self):
        self.logger = get_logger("analysis_results_handler")
        self.visualizer = EmotionVisualizer()

    @log_function_call("analysis_results_handler")
    def save_to_json(self, analysis_data: Dict, output_path: str) -> bool:

        """Сохранение результатов анализа в JSON файл

        Args:
            analysis_data: Данные анализа
            output_path: Путь для сохранения JSON файла

        Returns:
            True если успешно, False в случае ошибки
        """

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Подготовка данных для сохранения
            json_data = self._prepare_json_data(analysis_data)

            # Сохранение в файл
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Результаты анализа сохранены в JSON: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка сохранения в JSON: {str(e)}")
            return False

    def _prepare_json_data(self, analysis_data: Dict) -> Dict:
        """Подготовка данных для JSON (удаление base64 изображений)

        Args:
            analysis_data: Исходные данные анализа

        Returns:
            Очищенные данные для JSON
        """
        
        json_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "analysis": {}
        }

        # Копируем данные, исключая base64 изображения
        if "comments" in analysis_data:
            json_data["analysis"]["comments"] = []
            for comment in analysis_data["comments"]:
                comment_copy = {
                    "comment_index": comment.get("comment_index"),
                    "original_text": comment.get("original_text"),
                    "valid_sentences_count": comment.get("valid_sentences_count"),
                    "skipped_sentences_count": comment.get("skipped_sentences_count"),
                    "comment_summary": comment.get("comment_summary"),
                    "sentence_results": []
                }

                # Копируем результаты предложений без chart
                for sentence in comment.get("sentence_results", []):
                    sentence_copy = {
                        "text": sentence.get("text"),
                        "emotion": sentence.get("emotion"),
                        "confidence": sentence.get("confidence"),
                        "all_probabilities": sentence.get("all_probabilities"),
                        "sentence_index_in_comment": sentence.get("sentence_index_in_comment")
                    }
                    comment_copy["sentence_results"].append(sentence_copy)

                json_data["analysis"]["comments"].append(comment_copy)

        # Копируем общую статистику
        if "overall_summary" in analysis_data:
            json_data["analysis"]["overall_summary"] = analysis_data["overall_summary"]

        if "total_comments" in analysis_data:
            json_data["analysis"]["total_comments"] = analysis_data["total_comments"]

        if "total_analyzed_sentences" in analysis_data:
            json_data["analysis"]["total_analyzed_sentences"] = analysis_data["total_analyzed_sentences"]

        # Добавляем статистику визуализации без изображений
        if "overall_visualization" in analysis_data:
            viz = analysis_data["overall_visualization"]
            json_data["analysis"]["overall_statistics"] = {
                "emotion_counts": viz.get("emotion_counts", {}),
                "total_sentences": viz.get("total_sentences", 0)
            }

        return json_data

    @log_function_call("analysis_results_handler")
    def export_to_html(self, analysis_data: Dict, output_path: str, include_sentence_details: bool = True) -> bool:
        """Экспорт результатов анализа в HTML с встроенными изображениями

        Args:
            analysis_data: Данные анализа
            output_path: Путь для сохранения HTML файла
            include_sentence_details: Включать ли детали по каждому предложению

        Returns:
            True если успешно, False в случае ошибки
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Генерируем HTML контент
            html_content = self._generate_html_report(analysis_data, include_sentence_details)

            # Сохраняем в файл
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.logger.info(f"HTML отчет создан: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка создания HTML: {str(e)}")
            return False

    def _generate_html_report(self, analysis_data: Dict, include_sentence_details: bool) -> str:
        """Генерация HTML контента отчета"""
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        # Пересоздаем визуализации если их нет
        if 'comments' in analysis_data:
            # Иерархический анализ
            all_sentence_results = []
            for comment in analysis_data.get('comments', []):
                for sentence in comment.get('sentence_results', []):
                    all_sentence_results.append(sentence)

            if all_sentence_results:
                overall_visualization = self.visualizer.create_visualizations(all_sentence_results)
            else:
                overall_visualization = {}
        else:
            # Обычный анализ
            overall_visualization = {}

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет анализа эмоций</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; font-size: 32px; }}
        h2 {{ color: #34495e; margin-top: 30px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #3498db; }}
        h3 {{ color: #7f8c8d; margin-top: 20px; margin-bottom: 10px; }}
        .metadata {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 14px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }}
        .stat-label {{ font-size: 12px; color: #7f8c8d; text-transform: uppercase; margin-bottom: 5px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .emotion-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; color: white; margin: 5px; }}
        .emotion-радость {{ background: #2ecc71; }}
        .emotion-грусть {{ background: #3498db; }}
        .emotion-злость {{ background: #eb2222; }}
        .emotion-страх {{ background: #95a5a6; }}
        .emotion-удивление {{ background: #f1c40f; color: #333; }}
        .emotion-любовь {{ background: #cb4184; }}
        .chart-container {{ margin: 20px 0; text-align: center; }}
        .chart-container img {{ max-width: 100%; height: auto; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .comment-block {{ background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #3498db; }}
        .comment-text {{ background: white; padding: 15px; border-radius: 5px; margin: 10px 0; font-style: italic; }}
        .sentence-item {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 3px solid #95a5a6; }}
        .confidence {{ display: inline-block; padding: 3px 10px; background: #e8f5e9; color: #2e7d32; border-radius: 3px; font-size: 12px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; font-weight: bold; }}
        tr:hover {{ background: #f5f5f5; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Отчет анализа эмоций</h1>
        <div class="metadata">
            <strong>Дата создания:</strong> {timestamp}<br>
            <strong>Версия:</strong> 1.0.0
        </div>
"""

        # Общая статистика
        html += self._generate_html_statistics(analysis_data)

        # Визуализации
        if overall_visualization:
            html += self._generate_html_visualizations(overall_visualization)

        # Детали по комментариям
        if include_sentence_details and 'comments' in analysis_data:
            html += self._generate_html_comments(analysis_data['comments'])

        html += """
        <div class="footer">
            <p>Создано системой анализа эмоций EmotionAnalyzer</p>
            <p>Powered by RuBERT-base-cased</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_html_statistics(self, analysis_data: Dict) -> str:
        """Генерация HTML блока статистики"""
        html = "<h2>📈 Общая статистика</h2>\\n<div class='stats-grid'>\\n"

        if "total_comments" in analysis_data:
            html += f"""
            <div class="stat-card">
                <div class="stat-label">Комментариев</div>
                <div class="stat-value">{analysis_data['total_comments']}</div>
            </div>
"""

        if "total_analyzed_sentences" in analysis_data:
            html += f"""
            <div class="stat-card">
                <div class="stat-label">Предложений</div>
                <div class="stat-value">{analysis_data['total_analyzed_sentences']}</div>
            </div>
"""

        if "overall_summary" in analysis_data:
            summary = analysis_data["overall_summary"]
            if "dominant_emotion" in summary:
                html += f"""
            <div class="stat-card">
                <div class="stat-label">Доминирующая эмоция</div>
                <div class="stat-value">
                    <span class="emotion-badge emotion-{summary['dominant_emotion']}">{summary['dominant_emotion']}</span>
                </div>
            </div>
"""
            if "average_confidence" in summary:
                avg_conf = summary["average_confidence"] * 100
                html += f"""
            <div class="stat-card">
                <div class="stat-label">Средняя уверенность</div>
                <div class="stat-value">{avg_conf:.1f}%</div>
            </div>
"""

        html += "</div>\\n"

        # Таблица распределения эмоций
        if "overall_summary" in analysis_data and "emotion_counts" in analysis_data["overall_summary"]:
            html += "<h3>Распределение эмоций</h3>\\n<table>\\n<tr><th>Эмоция</th><th>Количество</th></tr>\\n"
            for emotion, count in analysis_data["overall_summary"]["emotion_counts"].items():
                html += f"<tr><td><span class='emotion-badge emotion-{emotion}'>{emotion}</span></td><td>{count}</td></tr>\\n"
            html += "</table>\\n"

        return html

    def _generate_html_visualizations(self, visualization_data: Dict) -> str:
        """Генерация HTML блока визуализаций"""
        html = "<h2>📊 Визуализации</h2>\\n"

        if "overall_chart" in visualization_data and visualization_data["overall_chart"]:
            html += f"""
        <div class="chart-container">
            <h3>Общее распределение эмоций</h3>
            <img src="{visualization_data['overall_chart']}" alt="Общее распределение эмоций">
        </div>
"""

        if "frequency_chart" in visualization_data and visualization_data["frequency_chart"]:
            html += f"""
        <div class="chart-container">
            <h3>Частота эмоций</h3>
            <img src="{visualization_data['frequency_chart']}" alt="Частота эмоций">
        </div>
"""

        return html

    def _generate_html_comments(self, comments: List[Dict]) -> str:
        """Генерация HTML блока с комментариями"""
        html = "<h2>💬 Детальный анализ комментариев</h2>\\n"

        for comment in comments:
            comment_idx = comment.get("comment_index", 0)
            original_text = comment.get("original_text", "")

            html += f"""
        <div class="comment-block">
            <h3>Комментарий #{comment_idx + 1}</h3>
            <div class="comment-text">{original_text}</div>
"""

            if "comment_summary" in comment and comment["comment_summary"]:
                summary = comment["comment_summary"]
                html += f"""
            <p><strong>Доминирующая эмоция:</strong>
                <span class="emotion-badge emotion-{summary.get('dominant_emotion', 'N/A')}">{summary.get('dominant_emotion', 'N/A')}</span>
            </p>
            <p><strong>Средняя уверенность:</strong> <span class="confidence">{summary.get('average_confidence', 0)*100:.1f}%</span></p>
            <p><strong>Предложений:</strong> {summary.get('total_sentences', 0)}</p>
"""

            # Предложения
            if "sentence_results" in comment and comment["sentence_results"]:
                html += "<h4>Предложения:</h4>\\n"
                for i, sentence in enumerate(comment["sentence_results"]):
                    html += f"""
            <div class="sentence-item">
                <p><strong>Предложение {i+1}:</strong> {sentence.get('text', '')}</p>
                <p><strong>Эмоция:</strong>
                    <span class="emotion-badge emotion-{sentence.get('emotion', '')}">{sentence.get('emotion', '')}</span>
                    <span class="confidence">{sentence.get('confidence', 0)*100:.1f}%</span>
                </p>
            </div>
"""

            html += "</div>\\n"

        return html

    @log_function_call("analysis_results_handler")
    def prepare_for_database(self, analysis_data: Dict) -> Dict:
        """Подготовка данных для сохранения в БД

        Args:
            analysis_data: Данные анализа

        Returns:
            Структурированные данные для БД
        """
        return self._prepare_json_data(analysis_data)
