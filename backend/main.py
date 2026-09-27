
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag import process_video, ask_question



# FASTAPI APP


app = FastAPI(
    title="YouTube RAG API",
    description="YouTube Video Question Answering API",
    version="1.0.0"
)



# CORS


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class VideoRequest(BaseModel):

    youtube_url: str


class QuestionRequest(BaseModel):

    question: str



# GLOBAL STATE


rag_chain = None

chat_history = []



# HOME


@app.get("/")
def home():

    return {
        "message": "YouTube RAG API is running"
    }



# PROCESS VIDEO


@app.post("/process-video")
def process_youtube_video(
    request: VideoRequest
):

    global rag_chain
    global chat_history

    try:

        # Create/load RAG system
        result = process_video(
            request.youtube_url
        )

        rag_chain = result["rag_chain"]

        # Clear previous conversation
        chat_history = []

        return {

            "success": True,

            "message":
                "Video processed successfully",

            "chunks":
                result["chunk_count"],

            "video_id":
                result["video_id"]

        }

    except Exception as e:

        return {

            "success": False,

            "message":
                str(e)

        }



# ASK QUESTION


@app.post("/ask")
def ask_video_question(
    request: QuestionRequest
):

    global rag_chain
    global chat_history

    if rag_chain is None:

        return {
            "success": False,
            "message": "Please process a YouTube video first."
        }

    try:

        history_text = ""

        for message in chat_history:

            history_text += (
                f"User: {message['question']}\n"
            )

            history_text += (
                f"Assistant: {message['answer']}\n\n"
            )

        answer = ask_question(
            rag_chain,
            request.question,
            history_text
        )

        chat_history.append({
            "question": request.question,
            "answer": answer
        })

        return {
            "success": True,
            "question": request.question,
            "answer": answer
        }

    except RuntimeError as e:

        return {
            "success": False,
            "message": str(e)
        }

    except Exception as e:

        return {
            "success": False,
            "message": "Something went wrong while generating the answer."
        }

# GET CHAT HISTORY


@app.get("/chat-history")
def get_chat_history():

    return {

        "success": True,

        "history":
            chat_history

    }



# CLEAR CHAT


@app.post("/clear-chat")
def clear_chat():

    global chat_history

    chat_history = []

    return {

        "success": True,

        "message":
            "Chat history cleared."

    }