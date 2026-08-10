document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const dropzone = document.getElementById('dropzone');
    const pdfFileInput = document.getElementById('pdfFileInput');
    const uploadSection = document.getElementById('uploadSection');
    const studioWorkspace = document.getElementById('studioWorkspace');
    const reuploadBtn = document.getElementById('reuploadBtn');

    // Document Info Elements
    const pdfFilename = document.getElementById('pdfFilename');
    const metaPages = document.getElementById('metaPages');
    const metaWords = document.getElementById('metaWords');
    const metaTime = document.getElementById('metaTime');
    const chapterSelect = document.getElementById('chapterSelect');
    const readerContent = document.getElementById('readerContent');

    // Control Elements
    const modeTabs = document.querySelectorAll('.mode-tab');
    const modePanels = {
        audiobook: document.getElementById('modeOptionsAudiobook'),
        podcast: document.getElementById('modeOptionsPodcast'),
        subtitles: document.getElementById('modeOptionsSubtitles')
    };
    const voiceSelect = document.getElementById('voiceSelect');
    const speedSelect = document.getElementById('speedSelect');
    const scopeSelect = document.getElementById('scopeSelect');
    const generateAudioBtn = document.getElementById('generateAudioBtn');
    const audioPlayer = document.getElementById('audioPlayer');
    const downloadAudioBtn = document.getElementById('downloadAudioBtn');
    const exportVttBtn = document.getElementById('exportVttBtn');
    const exportSrtBtn = document.getElementById('exportSrtBtn');

    // Visualizer Canvas
    const canvas = document.getElementById('visualizerCanvas');
    const canvasCtx = canvas.getContext('2d');

    // State Variables
    let currentPdfData = null;
    let activeMode = 'audiobook';
    let audioBlobUrl = null;
    let animationFrameId = null;

    // Load available AI Voices from API
    fetchVoices();

    async function fetchVoices() {
        try {
            const res = await fetch('/api/voices');
            const data = await res.json();
            if (data.voices && data.voices.length > 0) {
                voiceSelect.innerHTML = '';
                data.voices.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = voice.id;
                    option.textContent = `${voice.name} (${voice.gender})`;
                    if (voice.id === 'en-US-GuyNeural') option.selected = true;
                    voiceSelect.appendChild(option);
                });
            }
        } catch (err) {
            console.error('Failed to load voices:', err);
        }
    }

    // Drag & Drop Setup
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    pdfFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    reuploadBtn.addEventListener('click', () => {
        studioWorkspace.classList.add('hidden');
        uploadSection.classList.remove('hidden');
        pdfFileInput.value = '';
    });

    // Upload PDF to API
    async function handleFileUpload(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Please select a valid PDF file.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            dropzone.innerHTML = `
                <div class="dropzone-icon">⏳</div>
                <h2>Parsing PDF & Extracting Text...</h2>
                <p>Analyzing chapters and structure</p>
            `;

            const res = await fetch('/api/upload-pdf', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Upload failed');
            }

            currentPdfData = await res.json();
            renderDocumentWorkspace(currentPdfData);

        } catch (err) {
            alert(`Error processing PDF: ${err.message}`);
            location.reload();
        }
    }

    // Render Document Reader Workspace
    function renderDocumentWorkspace(data) {
        pdfFilename.textContent = data.filename;
        metaPages.textContent = data.metadata.total_pages;
        metaWords.textContent = data.metadata.total_words.toLocaleString();
        metaTime.textContent = `${data.metadata.estimated_minutes} min`;

        // Render Chapter Options
        chapterSelect.innerHTML = '';
        if (data.chapters && data.chapters.length > 0) {
            data.chapters.forEach(ch => {
                const opt = document.createElement('option');
                opt.value = ch.id;
                opt.textContent = ch.title;
                chapterSelect.appendChild(opt);
            });
        }

        chapterSelect.addEventListener('change', () => {
            renderReaderText();
        });

        renderReaderText();

        uploadSection.classList.add('hidden');
        studioWorkspace.classList.remove('hidden');
    }

    // Render Reader Text with Sentence Sync Spans
    function renderReaderText() {
        if (!currentPdfData) return;
        const selectedChId = parseInt(chapterSelect.value) || 1;
        const currentCh = currentPdfData.chapters.find(c => c.id === selectedChId) || currentPdfData.chapters[0];

        if (!currentCh || !currentCh.text) {
            readerContent.innerHTML = '<p>No text found in this chapter.</p>';
            return;
        }

        const rawSentences = currentCh.text.split(/(?<=[.!?])\s+/);
        readerContent.innerHTML = '';

        rawSentences.forEach((sentenceStr, idx) => {
            if (!sentenceStr.trim()) return;
            const span = document.createElement('span');
            span.className = 'sentence-item';
            span.dataset.sentenceIndex = idx;
            span.textContent = sentenceStr + ' ';
            readerContent.appendChild(span);
        });
    }

    // Mode Tabs Switching
    modeTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            modeTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeMode = tab.dataset.mode;

            Object.keys(modePanels).forEach(m => {
                if (m === activeMode) {
                    modePanels[m].classList.remove('hidden');
                } else {
                    modePanels[m].classList.add('hidden');
                }
            });
        });
    });

    // Generate Audio Action
    generateAudioBtn.addEventListener('click', async () => {
        if (!currentPdfData) {
            alert('Please upload a PDF document first.');
            return;
        }

        // Determine text to synthesize based on scope selection
        let textToRead = "";
        if (scopeSelect.value === 'full') {
            textToRead = currentPdfData.full_text;
        } else {
            const selectedChId = parseInt(chapterSelect.value) || 1;
            const ch = currentPdfData.chapters.find(c => c.id === selectedChId);
            textToRead = ch ? ch.text : currentPdfData.full_text;
        }

        if (!textToRead.trim()) {
            alert('No text available in current selection to convert.');
            return;
        }

        generateAudioBtn.disabled = true;
        generateAudioBtn.innerHTML = `⚡ Synthesizing AI Audio...`;

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

            const res = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                throw new Error('Audio generation failed on server.');
            }

            const audioBlob = await res.blob();
            if (audioBlobUrl) URL.revokeObjectURL(audioBlobUrl);
            audioBlobUrl = URL.createObjectURL(audioBlob);

            audioPlayer.src = audioBlobUrl;
            downloadAudioBtn.href = audioBlobUrl;
            downloadAudioBtn.classList.remove('hidden');

            audioPlayer.play();
            startVisualizer();

        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            generateAudioBtn.disabled = false;
            generateAudioBtn.innerHTML = `<span class="btn-icon">⚡</span> Generate AI Audio`;
        }
    });

    // Subtitle Exports
    exportVttBtn.addEventListener('click', () => downloadSubtitles('vtt'));
    exportSrtBtn.addEventListener('click', () => downloadSubtitles('srt'));

    async function downloadSubtitles(type) {
        if (!currentPdfData) return;
        const formData = new FormData();
        formData.append('text', currentPdfData.full_text);
        formData.append('format_type', type);

        const res = await fetch('/api/export-subtitles', {
            method: 'POST',
            body: formData
        });

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `captions.${type}`;
        a.click();
    }

    // Sentence Karaoke Sync during playback
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
            } else {
                span.classList.remove('active');
            }
        });
    });

    // Audio Visualizer Wave Canvas Animation
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
                    if (x === 0) canvasCtx.moveTo(x, y);
                    else canvasCtx.lineTo(x, y);
                }
                canvasCtx.stroke();
            }
            animationFrameId = requestAnimationFrame(draw);
        }
        draw();
    }
});
