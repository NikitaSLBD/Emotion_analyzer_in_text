document.addEventListener('DOMContentLoaded', function() {
    const analysisForm = document.getElementById('analysisForm');
    
    if (analysisForm) {
        analysisForm.addEventListener('submit', function() {
            const loadingElement = document.getElementById('loading');
            const analyzeBtn = document.getElementById('analyzeBtn');
            
            if (loadingElement && analyzeBtn) {
                loadingElement.style.display = 'block';
                analyzeBtn.disabled = true;
                analyzeBtn.textContent = 'Анализ...';
            }
        });
    }
    
    // Плавная прокрутка для якорных ссылок
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Автоматическое увеличение текстового поля при вводе
    const textarea = document.getElementById('text');
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Инициализация высоты
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    }
});