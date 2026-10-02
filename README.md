# Academic RAG Study Assistant

Academic RAG is a Streamlit study assistant that answers questions from academic PDF notes. It retrieves relevant passages from indexed PDFs, asks Google's Gemini API to answer from that evidence, and displays source filenames and page numbers so answers can be checked against the original material.

## How it works

1. Upload one or more text-based PDF files in the Streamlit app.
2. The app validates each PDF, extracts text page by page, and splits it into overlapping passages.
3. Gemini creates an embedding for each passage; Chroma stores the vector, text, source filename, and page number locally.
4. A student's question is embedded and used to retrieve up to three relevant passages.
5. Gemini generates an answer from those passages, and the app displays the answer with source-page evidence.

## Technology

- Python and Streamlit for the application and user interface
- pypdf for PDF validation and text extraction
- Google Gemini API for embeddings and grounded answer generation
- ChromaDB for local persistent vector storage
- python-dotenv for local API-key configuration

## Run locally (Windows PowerShell)

Use Python 3.10 or newer and a Gemini API key.

```powershell
git clone https://github.com/PlaasmaCoder/Academic-RAG.git
Set-Location Academic-RAG
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your own key to `.env`:

```text
GEMINI_API_KEY=your_gemini_api_key
```

Then start the app:

```powershell
streamlit run app.py
```

Keep your actual `.env` file private. The repository ignores `.env`, uploaded PDFs, the local Chroma database, and Python virtual environments. Never commit API keys or private study materials.

## Project structure

```text
Academic-RAG/
├── app.py                  Streamlit interface and workflow
├── requirements.txt        Python dependencies
├── .env.example            API-key placeholder
├── src/
│   ├── pdf_loader.py       PDF validation and page text extraction
│   ├── text_splitter.py    Overlapping passage creation
│   ├── embeddings.py       Gemini embedding requests
│   ├── gemini_client.py    Gemini client and key configuration
│   ├── vector_store.py     Persistent Chroma storage and retrieval
│   ├── rag_chain.py        Evidence-grounded answer generation
│   └── errors.py           User-facing error handling
├── docs/                   Project report
└── data/                   Local uploads and vector database (ignored by Git)
```

## Current limitations

- Text-based PDFs only; OCR for scanned PDFs is not implemented.
- Maximum PDF size is 25 MB and maximum length is 1,000 pages.
- Uploaded files and Chroma data are local; the prototype has no user accounts or per-user data isolation.
- Gemini features require internet access, a valid API key, and available API quota.
- Response latency and retrieval quality have not yet been benchmarked formally.
