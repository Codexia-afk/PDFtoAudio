# Security Policy — PDFtoAudio

## Privacy & Local-First Processing
PDFtoAudio is designed with privacy as a foundational principle.

* **Local Document Storage**: All uploaded documents, extracted text files, transcripts, bookmarks, notes, and study materials are stored locally on your device within the application storage directory.
* **No Secret Telemetry**: Document text and private files are never transmitted to external analytics or third-party servers without explicit user setup.
* **Neural Voice Stream Privacy**: Voice synthesis uses local TTS synthesis pipelines or direct HTTPS streams. No user document content is logged or persisted by external analytics trackers.

## Data Protection & File Handling
* **Path Traversal Prevention**: Filenames and paths are sanitized before processing.
* **File Upload Limits**: Document uploads are constrained to a maximum size limit of 50MB and maximum 500 pages per document.
* **Temporary File Cleanup**: Audio stream buffers and temporary conversion files are automatically purged after generation.

## Secrets Management
* Never commit API keys or secret tokens to source code. Use environment variables as shown in `.env.example`.
