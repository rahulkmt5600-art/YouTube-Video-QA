# YouTube-Video-QA

AI-powered YouTube Video Q&A application using Retrieval-Augmented Generation (RAG).

The application allows users to enter a YouTube video URL and ask questions about the video's transcript. Relevant transcript sections are retrieved using FAISS and Hugging Face embeddings, and Google Gemini generates the final answer.

## Features

- YouTube video URL input
- YouTube video preview
- Transcript extraction
- Transcript chunking
- Timestamp metadata
- Hugging Face Sentence Transformer embeddings
- FAISS vector search
- Retrieval-Augmented Generation (RAG)
- Google Gemini for answer generation
- LangChain LCEL pipeline
- FastAPI backend
- HTML, CSS and JavaScript frontend
- Chat history
- Persistent FAISS vector storage

## Tech Stack

### Backend
- Python
- FastAPI
- LangChain
- FAISS
- Google Gemini
- YouTube Transcript API

### AI / ML
- Hugging Face Sentence Transformers
- `all-MiniLM-L6-v2`
- Retrieval-Augmented Generation (RAG)

### Frontend
- HTML
- CSS
- JavaScript

## How It Works

```text
YouTube URL
     ↓
Get Transcript
     ↓
Transcript + Timestamps
     ↓
Split into Chunks
     ↓
Generate Embeddings
     ↓
Store in FAISS
     ↓
Retrieve Relevant Chunks
     ↓
Send Context to Gemini
     ↓
Generate Answer
     ↓
Display Answer
