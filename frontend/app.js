document.addEventListener('DOMContentLoaded', () => {
    // Navigation Views
    const navBtns = document.querySelectorAll('.nav-btn');
    const viewPanels = {
        viewLibrary: document.getElementById('viewLibrary'),
        viewStudio: document.getElementById('viewStudio'),
        viewChat: document.getElementById('viewChat'),
        viewStudy: document.getElementById('viewStudy')
    };

    // Library Elements
    const dropzone = document.getElementById('dropzone');
    const pdfFileInput = document.getElementById('pdfFileInput');
    const libraryGrid = document.getElementById('libraryGrid');
    const librarySearchInput = document.getElementById('librarySearchInput');

    // Studio Elements
    const pdfFilename = document.getElementById('pdfFilename');
    const metaPages = document.getElementById('metaPages');
    const metaWords = document.getElementById('metaWords');
    const metaTime = document.getElementById('metaTime');
    const resumePlaybackBtn = document.getElementById('resumePlaybackBtn');
    const chapterSelect = document.getElementById('chapterSelect');
    const readerContent = document.getElementById('readerContent');
    const qualityReportBanner = document.getElementById('qualityReportBanner');
    const reuploadBtn = document.getElementById('reuploadBtn');

    // Audio & Mode Elements
    const modeTabs = document.querySelectorAll('.mode-tab');
    const voiceSelect = document.getElementById('voiceSelect');
    const speedSelect = document.getElementById('speedSelect');
    const scopeSelect = document.getElementById('scopeSelect');
    const generateAudioBtn = document.getElementById('generateAudioBtn');
    const audioPlayer = document.getElementById('audioPlayer');
    const downloadAudioBtn = document.getElementById('downloadAudioBtn');

    // Subtitle & Export Controls
    const exportVttBtn = document.getElementById('exportVttBtn');
    const exportSrtBtn = document.getElementById('exportSrtBtn');
    const exportRssBtn = document.getElementById('exportRssBtn');

    // Chat Elements
    const chatLog = document.getElementById('chatLog');
    const chatQueryInput = document.getElementById('chatQueryInput');
    const sendChatBtn = document.getElementById('sendChatBtn');

    // Study Suite Elements
    const studyTabs = document.querySelectorAll('.study-tab');
    const studyPanels = {
        summary: document.getElementById('studyPanelSummary'),
        flashcards: document.getElementById('studyPanelFlashcards'),
        quiz: document.getElementById('studyPanelQuiz')
    };
    const summaryModeSelect = document.getElementById('summaryModeSelect');
    const generateSummaryBtn = document.getElementById('generateSummaryBtn');
    const summaryResultsBox = document.getElementById('summaryResultsBox');
    const generateFlashcardsBtn = document.getElementById('generateFlashcardsBtn');
    const exportAnkiCsvBtn = document.getElementById('exportAnkiCsvBtn');
    const flashcardsGrid = document.getElementById('flashcardsGrid');
    const generateQuizBtn = document.getElementById('generateQuizBtn');
    const quizBox = document.getElementById('quizBox');

    // Accessibility Drawer Elements
    const accessibilityToggleBtn = document.getElementById('accessibilityToggleBtn');
    const accessibilityDrawer = document.getElementById('accessibilityDrawer');
    const closeDrawerBtn = document.getElementById('closeDrawerBtn');
    const highContrastToggle = document.getElementById('highContrastToggle');
    const dyslexiaFontToggle = document.getElementById('dyslexiaFontToggle');
    const textSizeSelect = document.getElementById('textSizeSelect');
    const reducedMotionToggle = document.getElementById('reducedMotionToggle');

    // Visualizer Canvas
    const canvas = document.getElementById('visualizerCanvas');
    const canvasCtx = canvas.getContext('2d');

    // Global State
    let currentDocId = null;
    let currentPdfData = null;
    let libraryDocuments = [];
    let activeMode = 'audiobook';
    let audioBlobUrl = null;
    let animationFrameId = null;

    // Load Initial Data
    fetchVoices();
    loadLibrary();
    loadAccessibilitySettings();

    // --- Navigation View Switching ---
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const target = btn.dataset.target;
            Object.keys(viewPanels).forEach(v => {
                if (v === target) {
                    viewPanels[v].classList.remove('hidden');
                } else {
                    viewPanels[v].classList.add('hidden');
                }
            });
        });
    });

    function switchView(viewId) {
        const btn = document.querySelector(`.nav-btn[data-target="${viewId}"]`);
        if (btn) btn.click();
    }

    // --- Voices List API ---
    async function fetchVoices() {
        try {
            const res = await fetch('/api/voices');
            const data = await res.json();
            if (data.voices) {
                voiceSelect.innerHTML = '';
                data.voices.forEach(v => {
                    const opt = document.createElement('option');
                    opt.value = v.id;
                    opt.textContent = `${v.name} (${v.gender})`;
                    if (v.id === 'en-US-GuyNeural') opt.selected = true;
                    voiceSelect.appendChild(opt);
                });
            }
        } catch (err) {
            console.error('Failed to load voices:', err);
        }
    }

    // --- Document Library API ---
    async function loadLibrary() {
        try {
            const res = await fetch('/api/documents');
            const data = await res.json();
            libraryDocuments = data.documents || [];
            renderLibraryGrid(libraryDocuments);
        } catch (err) {
            console.error('Failed to load library:', err);
        }
    }

    function renderLibraryGrid(docs) {
        if (!docs || docs.length === 0) {
            libraryGrid.innerHTML = '<p class="empty-msg">No documents in library yet. Upload a file above to get started!</p>';
            return;
        }

        libraryGrid.innerHTML = '';
        docs.forEach(doc => {
            const card = document.createElement('div');
            card.className = 'doc-card';
            const ocrBadge = doc.quality_report && doc.quality_report.ocr_required
                ? '<span class="quality-banner" style="display:inline-block; padding: 2px 6px; font-size:0.75rem;">⚠️ Scanned PDF</span>'
                : '';

            card.innerHTML = `
                <div class="doc-title">${doc.title} ${ocrBadge}</div>
                <div class="doc-stats">
                    <span>📄 ${doc.total_pages} Pages</span>
                    <span>📝 ${doc.total_words.toLocaleString()} Words</span>
                    <span>⏱️ ${doc.estimated_minutes} min</span>
                </div>
                <div class="doc-card-actions">
                    <button class="btn-primary btn-sm open-doc-btn" data-id="${doc.id}">📖 Open Studio</button>
                    <button class="btn-secondary btn-sm delete-doc-btn" data-id="${doc.id}">🗑️ Delete</button>
                </div>
            `;

            card.querySelector('.open-doc-btn').addEventListener('click', () => openDocument(doc.id));
            card.querySelector('.delete-doc-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteDocument(doc.id);
            });

            libraryGrid.appendChild(card);
        });
    }

    librarySearchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = libraryDocuments.filter(d => d.title.toLowerCase().includes(query) || d.filename.toLowerCase().includes(query));
        renderLibraryGrid(filtered);
    });

    async function deleteDocument(docId) {
        if (!confirm('Are you sure you want to delete this document from Library?')) return;
        try {
            await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
            loadLibrary();
        } catch (err) {
            alert('Failed to delete document');
        }
    }

    // --- File Upload & Drag-and-Drop ---
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files[0]);
    });

    pdfFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFileUpload(e.target.files[0]);
    });

    reuploadBtn.addEventListener('click', () => switchView('viewLibrary'));

    async function handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            dropzone.innerHTML = '<h2>Parsing Document & Extracting Chapters...</h2>';
            const res = await fetch('/api/upload', { method: 'POST', body: formData });
            if (!res.ok) throw new Error('Upload failed');
            const data = await res.json();
            currentDocId = data.metadata.id;
            currentPdfData = data.content;
            currentPdfData.metadata = data.metadata;

            await loadLibrary();
            renderReaderStudio(data.metadata, data.content);
            switchView('viewStudio');
        } catch (err) {
            alert(`Upload error: ${err.message}`);
            location.reload();
        }
    }

    async function openDocument(docId) {
        try {
            const res = await fetch(`/api/documents/${docId}`);
            if (!res.ok) throw new Error('Failed to load document');
            const data = await res.json();
            currentDocId = docId;
            currentPdfData = data.content;
            currentPdfData.metadata = data.metadata;

            renderReaderStudio(data.metadata, data.content);
            switchView('viewStudio');
        } catch (err) {
            alert(err.message);
        }
    }

    // --- Reader Studio Renderer ---
    function renderReaderStudio(meta, content) {
        pdfFilename.textContent = meta.filename;
        metaPages.textContent = meta.total_pages;
        metaWords.textContent = meta.total_words.toLocaleString();
        metaTime.textContent = `${meta.estimated_minutes} min`;

        // Parser Quality Report Banner
        if (meta.quality_report && meta.quality_report.warnings.length > 0) {
            qualityReportBanner.classList.remove('hidden');
            qualityReportBanner.innerHTML = `⚠️ <strong>Parser Report:</strong> ${meta.quality_report.warnings.join(' ')}`;
        } else {
            qualityReportBanner.classList.add('hidden');
        }

        // Chapters Dropdown
        chapterSelect.innerHTML = '';
        if (content.chapters && content.chapters.length > 0) {
            content.chapters.forEach(ch => {
                const opt = document.createElement('option');
                opt.value = ch.id;
                opt.textContent = `${ch.title} (Page ${ch.start_page})`;
                chapterSelect.appendChild(opt);
            });
        }

        chapterSelect.addEventListener('change', renderReaderText);
        renderReaderText();

        // Resume Playback Listener
        resumePlaybackBtn.onclick = () => {
            if (meta.last_played_sentence_index > 0) {
                const sentenceSpan = readerContent.querySelector(`[data-sentence-index="${meta.last_played_sentence_index}"]`);
                if (sentenceSpan) sentenceSpan.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        };
    }

    // Render Text with Page Pills & Karaoke Spans
    function renderReaderText() {
        if (!currentPdfData) return;
        const selectedChId = parseInt(chapterSelect.value) || 1;
        const currentCh = currentPdfData.chapters.find(c => c.id === selectedChId) || currentPdfData.chapters[0];

        if (!currentCh || !currentCh.text) {
            readerContent.innerHTML = '<p>No text found in chapter.</p>';
            return;
        }

        const chapterSentences = currentPdfData.sentences.filter(s => s.page_number >= currentCh.start_page && s.page_number <= currentCh.end_page);
        readerContent.innerHTML = '';

        let currentDisplayedPage = 0;
        chapterSentences.forEach((s) => {
            if (s.page_number !== currentDisplayedPage) {
                currentDisplayedPage = s.page_number;
                const pageBadge = document.createElement('span');
                pageBadge.className = 'page-pill';
                pageBadge.textContent = `Page ${currentDisplayedPage}`;
                readerContent.appendChild(pageBadge);
            }

            const span = document.createElement('span');
            span.className = 'sentence-item';
            span.dataset.sentenceIndex = s.id;
            span.dataset.pageNumber = s.page_number;
            span.textContent = s.text + ' ';
            span.onclick = () => playFromSentence(s);
            readerContent.appendChild(span);
        });
    }

    function playFromSentence(sentence) {
        audioPlayer.currentTime = sentence.estimated_seconds * (sentence.id - 1);
        audioPlayer.play();
    }

    // --- Mode Tabs ---
    modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            modeTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeMode = tab.dataset.mode;

            document.getElementById('modeOptionsAudiobook').classList.toggle('hidden', activeMode !== 'audiobook');
            document.getElementById('modeOptionsPodcast').classList.toggle('hidden', activeMode !== 'podcast');
            document.getElementById('modeOptionsSubtitles').classList.toggle('hidden', activeMode !== 'subtitles');
        });
    });

    // Generate Audio Action
    generateAudioBtn.addEventListener('click', async () => {
        if (!currentPdfData) {
            alert('Please select a document first.');
            return;
        }

        let textToRead = "";
        if (scopeSelect.value === 'full') {
            textToRead = currentPdfData.full_text;
        } else {
            const selectedChId = parseInt(chapterSelect.value) || 1;
            const ch = currentPdfData.chapters.find(c => c.id === selectedChId);
            textToRead = ch ? ch.text : currentPdfData.full_text;
        }

        generateAudioBtn.disabled = true;
        generateAudioBtn.innerHTML = '⚡ Synthesizing Audio...';

        try {
            const formData = new FormData();
            formData.append('text', textToRead);

            let endpoint = '/api/tts';
            if (activeMode === 'podcast') {
                endpoint = '/api/podcast';
            } else {
                formData.append('voice', voiceSelect.value);
                formData.append('rate', speedSelect.value);
            }

            const res = await fetch(endpoint, { method: 'POST', body: formData });
            if (!res.ok) throw new Error('TTS generation failed');

            const blob = await res.blob();
            if (audioBlobUrl) URL.revokeObjectURL(audioBlobUrl);
            audioBlobUrl = URL.createObjectURL(blob);

            audioPlayer.src = audioBlobUrl;
            downloadAudioBtn.href = audioBlobUrl;
            downloadAudioBtn.classList.remove('hidden');
            audioPlayer.play();
            startVisualizer();

        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            generateAudioBtn.disabled = false;
            generateAudioBtn.innerHTML = '⚡ Generate AI Audio';
        }
    });

    // Subtitle & RSS Exports
    exportVttBtn.onclick = () => exportSubtitles('vtt');
    exportSrtBtn.onclick = () => exportSubtitles('srt');
    exportRssBtn.onclick = () => {
        if (currentDocId) window.open(`/api/documents/${currentDocId}/rss`, '_blank');
    };

    async function exportSubtitles(type) {
        if (!currentPdfData) return;
        const formData = new FormData();
        formData.append('text', currentPdfData.full_text);
        formData.append('format_type', type);

        const res = await fetch('/api/export-subtitles', { method: 'POST', body: formData });
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `captions.${type}`;
        a.click();
    }

    // --- Document Chat (Trust Mode) ---
    sendChatBtn.addEventListener('click', handleSendChat);
    chatQueryInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSendChat(); });

    async function handleSendChat() {
        const query = chatQueryInput.value.trim();
        if (!query || !currentDocId) return;

        appendChatMessage('user', query);
        chatQueryInput.value = '';

        try {
            const formData = new FormData();
            formData.append('query', query);
            const res = await fetch(`/api/documents/${currentDocId}/chat`, { method: 'POST', body: formData });
            const data = await res.json();
            appendChatMessage('assistant', data.text, data.page_references, data.found_in_doc);
        } catch (err) {
            appendChatMessage('assistant', 'Error fetching answer.', [], false);
        }
    }

    function appendChatMessage(sender, text, pageRefs = [], foundInDoc = True) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg ${sender}`;

        let pageTags = pageRefs.map(p => `<span class="page-ref-tag">Page ${p}</span>`).join(' ');
        let unverifiedBadge = !foundInDoc ? '<span style="color:#ef4444; font-size:0.75rem;"> [Not found in document]</span>' : '';

        msgDiv.innerHTML = `
            <div class="msg-bubble">
                ${text} ${pageTags} ${unverifiedBadge}
            </div>
        `;

        chatLog.appendChild(msgDiv);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    // --- Study Suite ---
    studyTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            studyTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const target = tab.dataset.tab;

            Object.keys(studyPanels).forEach(p => {
                studyPanels[p].classList.toggle('hidden', p !== target);
            });
        });
    });

    generateSummaryBtn.addEventListener('click', async () => {
        if (!currentDocId) return alert('Select a document first.');
        summaryResultsBox.innerHTML = '<p>Generating Educational Summary with citations...</p>';

        try {
            const formData = new FormData();
            formData.append('mode', summaryModeSelect.value);
            const res = await fetch(`/api/documents/${currentDocId}/summary`, { method: 'POST', body: formData });
            const summary = await res.json();

            let takeawaysHtml = summary.key_takeaways.map(t => `
                <li>${t.point} <span class="page-ref-tag">Page ${t.page_reference}</span></li>
            `).join('');

            let glossaryHtml = summary.glossary.map(g => `
                <p><strong>${g.term}:</strong> ${g.definition} <span class="page-ref-tag">Page ${g.page_reference}</span></p>
            `).join('');

            summaryResultsBox.innerHTML = `
                <h3>${summary.title}</h3>
                <p><strong>Summary:</strong> ${summary.executive_summary}</p>
                <h4 style="margin-top:16px;">Key Takeaways:</h4>
                <ul>${takeawaysHtml}</ul>
                <h4 style="margin-top:16px;">Glossary Terms:</h4>
                ${glossaryHtml}
            `;

        } catch (err) {
            summaryResultsBox.innerHTML = '<p>Failed to generate summary.</p>';
        }
    });

    generateFlashcardsBtn.addEventListener('click', async () => {
        if (!currentDocId) return;
        flashcardsGrid.innerHTML = '<p>Generating Revision Flashcards...</p>';

        try {
            const res = await fetch(`/api/documents/${currentDocId}/study`, { method: 'POST' });
            const data = await res.json();
            renderFlashcards(data.flashcards);
        } catch (err) {
            flashcardsGrid.innerHTML = '<p>Failed to load flashcards.</p>';
        }
    });

    function renderFlashcards(cards) {
        flashcardsGrid.innerHTML = '';
        cards.forEach(card => {
            const fc = document.createElement('div');
            fc.className = 'flashcard-item';
            let flipped = false;

            fc.innerHTML = `
                <div class="fc-front"><strong>Q:</strong> ${card.front} <br><small>Page ${card.page_reference}</small></div>
                <div class="fc-back hidden"><strong>A:</strong> ${card.back}</div>
            `;

            fc.onclick = () => {
                flipped = !flipped;
                fc.querySelector('.fc-front').classList.toggle('hidden', flipped);
                fc.querySelector('.fc-back').classList.toggle('hidden', !flipped);
            };

            flashcardsGrid.appendChild(fc);
        });
    }

    exportAnkiCsvBtn.onclick = () => {
        if (currentDocId) window.open(`/api/documents/${currentDocId}/anki-csv`, '_blank');
    };

    generateQuizBtn.addEventListener('click', async () => {
        if (!currentDocId) return;
        quizBox.innerHTML = '<p>Generating Quiz Questions...</p>';

        try {
            const res = await fetch(`/api/documents/${currentDocId}/study`, { method: 'POST' });
            const data = await res.json();
            renderQuiz(data.quizzes);
        } catch (err) {
            quizBox.innerHTML = '<p>Failed to load quiz.</p>';
        }
    });

    function renderQuiz(quizzes) {
        quizBox.innerHTML = '';
        quizzes.forEach((q, qIdx) => {
            const item = document.createElement('div');
            item.className = 'quiz-q-item';

            let optionsHtml = q.options.map((opt, oIdx) => `
                <button class="quiz-opt-btn" data-q="${qIdx}" data-o="${oIdx}">${opt}</button>
            `).join('');

            item.innerHTML = `
                <p><strong>Question ${qIdx + 1}:</strong> ${q.question}</p>
                <div class="quiz-options">${optionsHtml}</div>
                <div class="quiz-exp hidden" style="margin-top:10px; font-size:0.85rem; color:#34d399;">${q.explanation}</div>
            `;

            item.querySelectorAll('.quiz-opt-btn').forEach(btn => {
                btn.onclick = () => {
                    const selectedO = parseInt(btn.dataset.o);
                    item.querySelectorAll('.quiz-opt-btn').forEach(b => b.disabled = true);
                    if (selectedO === q.correct_option_index) {
                        btn.classList.add('correct');
                    } else {
                        btn.classList.add('wrong');
                        item.querySelectorAll('.quiz-opt-btn')[q.correct_option_index].classList.add('correct');
                    }
                    item.querySelector('.quiz-exp').classList.remove('hidden');
                };
            });

            quizBox.appendChild(item);
        });
    }

    // --- Audio Player & Karaoke Sync ---
    audioPlayer.addEventListener('timeupdate', () => {
        if (!audioPlayer.duration) return;
        const progress = audioPlayer.currentTime / audioPlayer.duration;
        const sentenceSpans = readerContent.querySelectorAll('.sentence-item');
        if (sentenceSpans.length === 0) return;

        const targetIdx = Math.floor(progress * sentenceSpans.length);
        sentenceSpans.forEach((span, idx) => {
            if (idx === targetIdx) {
                span.classList.add('active');
                span.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

                // Save playback position periodically
                if (currentDocId && idx % 3 === 0) {
                    const formData = new FormData();
                    formData.append('sentence_index', idx);
                    formData.append('seconds', audioPlayer.currentTime);
                    fetch(`/api/documents/${currentDocId}/playback`, { method: 'POST', body: formData });
                }
            } else {
                span.classList.remove('active');
            }
        });
    });

    // Audio Visualizer Animation
    function startVisualizer() {
        if (animationFrameId) cancelAnimationFrame(animationFrameId);
        function draw() {
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
            canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
            if (!audioPlayer.paused) {
                const time = Date.now() * 0.005;
                canvasCtx.beginPath();
                canvasCtx.lineWidth = 3;
                canvasCtx.strokeStyle = '#6366f1';
                for (let x = 0; x < canvas.width; x += 5) {
                    const y = canvas.height / 2 + Math.sin(x * 0.02 + time) * 15 * Math.random();
                    if (x === 0) canvasCtx.moveTo(x, y); else canvasCtx.lineTo(x, y);
                }
                canvasCtx.stroke();
            }
            animationFrameId = requestAnimationFrame(draw);
        }
        draw();
    }

    // --- Accessibility Settings State ---
    accessibilityToggleBtn.onclick = () => accessibilityDrawer.classList.remove('hidden');
    closeDrawerBtn.onclick = () => accessibilityDrawer.classList.add('hidden');

    highContrastToggle.onclick = () => {
        document.body.classList.toggle('high-contrast');
        localStorage.setItem('highContrast', document.body.classList.contains('high-contrast'));
    };

    dyslexiaFontToggle.onclick = () => {
        document.body.classList.toggle('dyslexia-font');
        localStorage.setItem('dyslexiaFont', document.body.classList.contains('dyslexia-font'));
    };

    textSizeSelect.onchange = () => {
        document.body.classList.remove('text-large', 'text-xlarge');
        if (textSizeSelect.value === 'large') document.body.classList.add('text-large');
        if (textSizeSelect.value === 'xlarge') document.body.classList.add('text-xlarge');
        localStorage.setItem('textSize', textSizeSelect.value);
    };

    function loadAccessibilitySettings() {
        if (localStorage.getItem('highContrast') === 'true') document.body.classList.add('high-contrast');
        if (localStorage.getItem('dyslexiaFont') === 'true') document.body.classList.add('dyslexia-font');
        const size = localStorage.getItem('textSize');
        if (size) {
            textSizeSelect.value = size;
            textSizeSelect.dispatchEvent(new Event('change'));
        }
    }

    // Keyboard Shortcuts Listener
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.code === 'Space' || e.key === 'k' || e.key === 'K') {
            e.preventDefault();
            audioPlayer.paused ? audioPlayer.play() : audioPlayer.pause();
        } else if (e.key === 'm' || e.key === 'M') {
            audioPlayer.muted = !audioPlayer.muted;
        } else if (e.key === '?') {
            accessibilityDrawer.classList.toggle('hidden');
        }
    });
});
