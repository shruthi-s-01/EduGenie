document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initCounters();
    initSmoothScroll();
});

function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs and hide all panels
            document.querySelectorAll('.tab-btn').forEach(t => {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            });
            document.querySelectorAll('.panel').forEach(p => {
                p.classList.remove('active');
                p.classList.add('hidden');
            });

            // Add active class to clicked tab and show corresponding panel
            tab.classList.add('active');
            tab.setAttribute('aria-selected', 'true');
            const tool = tab.getAttribute('data-tool');
            const panel = document.getElementById(`panel-${tool}`);
            if (panel) {
                panel.classList.remove('hidden');
                panel.classList.add('active');
            }
        });
    });
}

function initCounters() {
    const inputs = ['qa-input', 'explain-input', 'quiz-input', 'summarize-input', 'learn-input'];
    
    inputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            const counter = document.getElementById(`${id.split('-')[0]}-counter`);
            const max = parseInt(input.getAttribute('maxlength') || '1000', 10);
            
            input.addEventListener('input', () => {
                const len = input.value.length;
                if (counter) {
                    counter.textContent = len;
                    if (len >= max * 0.9) {
                        counter.parentElement.classList.add('warning');
                    } else {
                        counter.parentElement.classList.remove('warning');
                    }
                }
            });

            // Enter key support for single line inputs
            if (input.tagName.toLowerCase() === 'input') {
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        const tool = id.split('-')[0];
                        document.getElementById(`${tool}-submit`).click();
                    }
                });
            }
        }
    });
}

function initSmoothScroll() {
    const startBtn = document.getElementById('start-learning-btn');
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            document.getElementById('workspace').scrollIntoView({ behavior: 'smooth' });
        });
    }
}

// UI Utility Functions
function showLoading(tool) {
    const submitBtn = document.getElementById(`${tool}-submit`);
    if(submitBtn) submitBtn.disabled = true;
    
    const loading = document.getElementById(`${tool}-loading`);
    if(loading) loading.classList.remove('hidden');
}

function hideLoading(tool) {
    const submitBtn = document.getElementById(`${tool}-submit`);
    if(submitBtn) submitBtn.disabled = false;
    
    const loading = document.getElementById(`${tool}-loading`);
    if(loading) loading.classList.add('hidden');
}

function showResult(tool, contentHtml) {
    const result = document.getElementById(`${tool}-result`);
    if(result) {
        result.innerHTML = `<div class="markdown-content">${contentHtml}</div>`;
        result.classList.remove('hidden');
    }
}

function hideResult(tool) {
    const result = document.getElementById(`${tool}-result`);
    if(result) {
        result.classList.add('hidden');
        result.innerHTML = '';
    }
}

function showError(tool, message) {
    const error = document.getElementById(`${tool}-error`);
    if(error) {
        error.textContent = message;
        error.classList.remove('hidden');
    }
}

function hideError(tool) {
    const error = document.getElementById(`${tool}-error`);
    if(error) {
        error.classList.add('hidden');
        error.textContent = '';
    }
}

function formatMarkdown(text) {
    if (!text) return '';
    let html = text
        // Escape HTML
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        // Headers
        .replace(/^### (.*$)/gim, '<h4>$1</h4>')
        .replace(/^## (.*$)/gim, '<h3>$1</h3>')
        .replace(/^# (.*$)/gim, '<h2>$1</h2>')
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Unordered lists (simple approach)
        .replace(/^\s*-\s(.*$)/gim, '<ul><li>$1</li></ul>')
        // Numbered lists
        .replace(/^\s*\d+\.\s(.*$)/gim, '<ol><li>$1</li></ol>')
        // Paragraphs
        .replace(/\n\n+/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    // Cleanup nested lists formatting artifacts
    html = html.replace(/<\/ul>\s*<ul>/g, '').replace(/<\/ol>\s*<ol>/g, '');
    
    return `<p>${html}</p>`;
}

// API Integration Functions

async function askQuestion() {
    const input = document.getElementById('qa-input');
    const question = input.value.trim();
    if (!question) { showError('qa', 'Please enter a question.'); return; }
    
    showLoading('qa');
    hideError('qa');
    hideResult('qa');
    
    try {
        const response = await fetch('/qa', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Server error (${response.status})`);
        }
        
        const data = await response.json();
        showResult('qa', formatMarkdown(data.answer));
    } catch (error) {
        showError('qa', error.message || 'Failed to get answer. Please try again.');
    } finally {
        hideLoading('qa');
    }
}

async function explainConcept() {
    const input = document.getElementById('explain-input');
    const concept = input.value.trim();
    if (!concept) { showError('explain', 'Please enter a concept.'); return; }
    
    showLoading('explain');
    hideError('explain');
    hideResult('explain');
    
    try {
        const response = await fetch('/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ concept })
        });
        
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Server error (${response.status})`);
        }
        
        const data = await response.json();
        showResult('explain', formatMarkdown(data.explanation));
    } catch (error) {
        showError('explain', error.message || 'Failed to explain concept. Please try again.');
    } finally {
        hideLoading('explain');
    }
}

let currentQuizQuestions = [];

async function generateQuiz() {
    const input = document.getElementById('quiz-input');
    const topic = input.value.trim();
    if (!topic) { showError('quiz', 'Please enter a topic.'); return; }
    
    showLoading('quiz');
    hideError('quiz');
    hideResult('quiz');
    
    try {
        const response = await fetch('/quiz', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic })
        });
        
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Server error (${response.status})`);
        }
        
        const data = await response.json();
        currentQuizQuestions = data.questions || [];
        renderQuiz(currentQuizQuestions);
    } catch (error) {
        showError('quiz', error.message || 'Failed to generate quiz. Please try again.');
    } finally {
        hideLoading('quiz');
    }
}

function renderQuiz(questions) {
    if (!questions || questions.length === 0) {
        showError('quiz', 'No questions received.');
        return;
    }
    
    let html = '<div class="quiz-container">';
    questions.forEach((q, index) => {
        html += `
            <div class="quiz-question-card" id="qcard-${index}">
                <div class="quiz-question-text">${index + 1}. ${escapeHtml(q.question)}</div>
                <div class="quiz-options">
        `;
        
        q.options.forEach((opt, optIndex) => {
            html += `
                <label class="quiz-option" id="label-q${index}-o${optIndex}">
                    <input type="radio" name="q${index}" value="${escapeHtml(opt)}">
                    <span>${escapeHtml(opt)}</span>
                </label>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    });
    
    html += `
        <button class="btn-primary" id="check-quiz-btn" onclick="checkAnswers()">Check Answers</button>
        <div id="quiz-score" class="quiz-score hidden"></div>
    </div>`;
    
    const result = document.getElementById('quiz-result');
    result.innerHTML = html;
    result.classList.remove('hidden');
}

function checkAnswers() {
    let score = 0;
    
    currentQuizQuestions.forEach((q, index) => {
        const selected = document.querySelector(`input[name="q${index}"]:checked`);
        const options = document.querySelectorAll(`input[name="q${index}"]`);
        
        options.forEach((opt, optIndex) => {
            const label = document.getElementById(`label-q${index}-o${optIndex}`);
            opt.disabled = true; // Disable all inputs
            
            if (opt.value === q.correct_answer) {
                label.classList.add('correct');
            } else if (selected && selected === opt && opt.value !== q.correct_answer) {
                label.classList.add('incorrect');
            }
        });
        
        if (selected && selected.value === q.correct_answer) {
            score++;
        }
    });
    
    const checkBtn = document.getElementById('check-quiz-btn');
    if (checkBtn) checkBtn.disabled = true;
    
    const scoreDiv = document.getElementById('quiz-score');
    if (scoreDiv) {
        scoreDiv.textContent = `You got ${score} out of ${currentQuizQuestions.length} correct!`;
        scoreDiv.classList.remove('hidden');
    }
}

async function summarizeText() {
    const input = document.getElementById('summarize-input');
    const text = input.value.trim();
    if (!text || text.length < 10) { showError('summarize', 'Please enter text (min 10 characters).'); return; }
    
    showLoading('summarize');
    hideError('summarize');
    hideResult('summarize');
    
    try {
        const response = await fetch('/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Server error (${response.status})`);
        }
        
        const data = await response.json();
        renderSummary(data);
    } catch (error) {
        showError('summarize', error.message || 'Failed to summarize text. Please try again.');
    } finally {
        hideLoading('summarize');
    }
}

function renderSummary(data) {
    let html = `<div class="markdown-content">`;
    html += `<h3>Summary</h3>`;
    html += `<p>${escapeHtml(data.summary)}</p>`;
    
    if (data.key_points && data.key_points.length > 0) {
        html += `<h3>Key Points</h3><ul>`;
        data.key_points.forEach(point => {
            html += `<li>${escapeHtml(point)}</li>`;
        });
        html += `</ul>`;
    }
    html += `</div>`;
    
    const result = document.getElementById('summarize-result');
    result.innerHTML = html;
    result.classList.remove('hidden');
}

async function generateLearningPath() {
    const input = document.getElementById('learn-input');
    const topic = input.value.trim();
    if (!topic) { showError('learn', 'Please enter a subject.'); return; }
    
    showLoading('learn');
    hideError('learn');
    hideResult('learn');
    
    try {
        const response = await fetch('/learn/recommendations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic })
        });
        
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Server error (${response.status})`);
        }
        
        const data = await response.json();
        renderLearningPath(data.stages || []);
    } catch (error) {
        showError('learn', error.message || 'Failed to create learning path. Please try again.');
    } finally {
        hideLoading('learn');
    }
}

function renderLearningPath(stages) {
    if (!stages || stages.length === 0) {
        showError('learn', 'No learning path stages received.');
        return;
    }
    
    let html = '<div class="learning-timeline">';
    
    stages.forEach(stage => {
        const stageLevel = (stage.stage || 'beginner').toLowerCase();
        const badgeClass = `badge-${stageLevel}`;
        
        html += `
            <div class="stage-card" data-stage="${escapeHtml(stageLevel)}">
                <div class="stage-badge ${escapeHtml(badgeClass)}">${escapeHtml(stage.stage || 'Stage')}</div>
                <h3>${escapeHtml(stage.title || '')}</h3>
                <p>${escapeHtml(stage.description || '')}</p>
        `;
        
        if (stage.topics && stage.topics.length > 0) {
            html += `<h4>Topics to Cover</h4><ul>`;
            stage.topics.forEach(t => html += `<li>${escapeHtml(t)}</li>`);
            html += `</ul>`;
        }
        
        if (stage.resources && stage.resources.length > 0) {
            html += `<h4>Resources</h4><ul>`;
            stage.resources.forEach(r => html += `<li>${escapeHtml(r)}</li>`);
            html += `</ul>`;
        }
        
        if (stage.duration) {
            html += `<span class="duration">⏱ ${escapeHtml(stage.duration)}</span>`;
        }
        
        html += `</div>`;
    });
    
    html += '</div>';
    
    const result = document.getElementById('learn-result');
    result.innerHTML = html;
    result.classList.remove('hidden');
}

function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return '';
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
