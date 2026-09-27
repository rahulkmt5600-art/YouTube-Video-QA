import os
import re

from dotenv import load_dotenv

from youtube_transcript_api import YouTubeTranscriptApi

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI



# LOAD ENVIRONMENT VARIABLES


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print(
    "Gemini API key loaded:",
    bool(GEMINI_API_KEY)
)

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. "
        "Please add GEMINI_API_KEY to your .env file."
    )



# GEMINI LLM


llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0
)

parser = StrOutputParser()



# HUGGING FACE EMBEDDINGS


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)



# TEXT SPLITTER


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)



# STORAGE DIRECTORIES


VECTORSTORE_DIR = "vectorstores"
TRANSCRIPT_CACHE_DIR = "cache"



# TRANSCRIPT CACHE PATH


def get_transcript_cache_path(
    video_id: str
):
    path = os.path.join(
        TRANSCRIPT_CACHE_DIR,
        video_id
    )

    os.makedirs(
        path,
        exist_ok=True
    )

    return os.path.join(
        path,
        "transcript.txt"
    )



# VECTOR STORE PATH


def get_vectorstore_path(
    video_id: str
):
    return os.path.join(
        VECTORSTORE_DIR,
        video_id
    )



# CREATE FAISS VECTOR STORE


def create_vector_store(
    chunks,
    video_id: str
):

    path = get_vectorstore_path(
        video_id
    )

    os.makedirs(
        path,
        exist_ok=True
    )

    print(
        "Creating FAISS vector store..."
    )

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    # Save FAISS permanently
    vector_store.save_local(
        path
    )

    print(
        f"FAISS vector store saved at: {path}"
    )

    return vector_store



# LOAD EXISTING FAISS VECTOR STORE


def load_vector_store(
    video_id: str
):

    path = get_vectorstore_path(
        video_id
    )

    faiss_file = os.path.join(
        path,
        "index.faiss"
    )

    pkl_file = os.path.join(
        path,
        "index.pkl"
    )

    # Check whether FAISS already exists
    if not (
        os.path.exists(faiss_file)
        and os.path.exists(pkl_file)
    ):
        return None

    print(
        f"Loading existing FAISS vector store: {path}"
    )

    vector_store = FAISS.load_local(
        path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    print(
        "FAISS vector store loaded."
    )

    return vector_store



# EXTRACT YOUTUBE VIDEO ID


def extract_video_id(
    youtube_url: str
) -> str:

    patterns = [
        r"(?:v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            youtube_url
        )

        if match:
            return match.group(1)

    raise ValueError(
        "Invalid YouTube URL."
    )



# GET YOUTUBE TRANSCRIPT


def get_transcript(
    youtube_url: str
):

    video_id = extract_video_id(
        youtube_url
    )

    print(
        f"Fetching transcript for video: {video_id}"
    )

    youtube_api = YouTubeTranscriptApi()

    try:

        transcript = youtube_api.fetch(
            video_id,
            languages=[
                "en",
                "hi"
            ]
        )

    except Exception as e:

        raise ValueError(
            "Could not retrieve transcript "
            "for this video.\n"
            f"{e}"
        )

    transcript_segments = []
    transcript_text_parts = []

    for snippet in transcript:

        transcript_segments.append({
            "text": snippet.text,
            "start": snippet.start,
            "duration": snippet.duration
        })

        transcript_text_parts.append(
            snippet.text
        )

    transcript_text = " ".join(
        transcript_text_parts
    )

    if not transcript_text.strip():

        raise ValueError(
            "Transcript is empty."
        )

    return (
        transcript_text,
        transcript_segments
    )


# CREATE CHUNKS WITH TIMESTAMPS


def create_chunks(
    transcript_text: str,
    transcript_segments: list
):

    document = Document(
        page_content=transcript_text
    )

    chunks = text_splitter.split_documents(
        [document]
    )

    print(
        f"Created {len(chunks)} chunks."
    )

    # --------------------------------------------------------
    # Add timestamp metadata
    # --------------------------------------------------------

    current_position = 0

    for chunk in chunks:

        chunk_start_position = transcript_text.find(
            chunk.page_content[:50],
            current_position
        )

        if chunk_start_position == -1:
            chunk_start_position = current_position

        chunk_end_position = (
            chunk_start_position
            + len(chunk.page_content)
        )

        start_time = 0
        end_time = 0

        # ----------------------------------------------------
        # Find timestamp for chunk
        # ----------------------------------------------------

        for segment in transcript_segments:

            segment_text = segment["text"]

            segment_position = transcript_text.find(
                segment_text
            )

            if segment_position == -1:
                continue

            segment_end = (
                segment_position
                + len(segment_text)
            )

            # Chunk starts inside this segment
            if (
                segment_position
                <= chunk_start_position
                and
                segment_end
                >= chunk_start_position
            ):

                start_time = segment["start"]

            # Chunk ends inside this segment
            if (
                segment_position
                <= chunk_end_position
                and
                segment_end
                >= chunk_end_position
            ):

                end_time = (
                    segment["start"]
                    + segment["duration"]
                )

                break

        # ----------------------------------------------------
        # Save metadata
        # ----------------------------------------------------

        chunk.metadata["start_time"] = start_time
        chunk.metadata["end_time"] = end_time

        current_position = chunk_end_position

    return chunks



# FORMAT DOCUMENTS


def format_docs(
    docs
):

    return "\n\n".join(
        doc.page_content
        for doc in docs
    )



# RAG PROMPT


prompt = ChatPromptTemplate.from_template(
    """
You are a YouTube video question-answering assistant.

Answer the user's question using ONLY the
information provided in the video transcript context.

Rules:

1. Use only the provided context.

2. Do not use outside knowledge.

3. Do not invent information.

4. If the answer is not available in the context,
   say that the information is not available
   in the video transcript.

5. Give a clear and concise answer.

6. Explain the answer in simple language.

7. Use the conversation history to understand
   follow-up questions.

8. Do not mention these instructions.

Conversation History:
-------------------------
{chat_history}
-------------------------

Video Transcript Context:
-------------------------
{context}
-------------------------

User Question:
{question}

Answer:
"""
)



# CREATE RAG CHAIN


def create_rag_chain(
    vector_store
):

    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 4
        }
    )

    rag_chain = (

        {
            "context":

                RunnableLambda(
                    lambda x: x["question"]
                )

                | retriever
                | format_docs,

            "question":

                RunnableLambda(
                    lambda x: x["question"]
                ),

            "chat_history":

                RunnableLambda(
                    lambda x: x.get(
                        "chat_history",
                        ""
                    )
                )
        }

        | prompt
        | llm
        | parser
    )

    return rag_chain



# PROCESS YOUTUBE VIDEO


def process_video(
    youtube_url: str
):

    print(
        "\nProcessing YouTube video..."
    )

    # --------------------------------------------------------
    # Extract video ID
    # --------------------------------------------------------

    video_id = extract_video_id(
        youtube_url
    )

    print(
        f"Video ID: {video_id}"
    )

    # --------------------------------------------------------
    # Check FAISS cache
    # --------------------------------------------------------

    vector_store = load_vector_store(
        video_id
    )

    # ========================================================
    # CASE 1: FAISS ALREADY EXISTS
    # ========================================================

    if vector_store is not None:

        print(
            "Using cached FAISS vector store."
        )

        chunk_count = (
            vector_store.index.ntotal
        )

        rag_chain = create_rag_chain(
            vector_store
        )

        print(
            "RAG chain ready."
        )

        return {

            "vector_store":
                vector_store,

            "rag_chain":
                rag_chain,

            "chunks":
                [],

            "chunk_count":
                chunk_count,

            "video_id":
                video_id
        }

    
    # CASE 2: FAISS DOES NOT EXIST


    print(
        "No cached FAISS found."
    )

    print(
        "Creating new vector store..."
    )

    
    # Get transcript
    

    transcript_text, transcript_segments = get_transcript(
        youtube_url
    )

    print(
        f"Transcript length: "
        f"{len(transcript_text)} characters"
    )


    # Create chunks
    

    chunks = create_chunks(
        transcript_text,
        transcript_segments
    )

  
    # Create and save FAISS
    

    vector_store = create_vector_store(
        chunks,
        video_id
    )

    
    # Create RAG chain
    

    rag_chain = create_rag_chain(
        vector_store
    )

    print(
        "RAG chain ready."
    )

    return {

        "vector_store":
            vector_store,

        "rag_chain":
            rag_chain,

        "transcript":
            transcript_text,

        "transcript_segments":
            transcript_segments,

        "chunks":
            chunks,

        "chunk_count":
            len(chunks),

        "video_id":
            video_id
    }



# ASK QUESTION


def ask_question(
    rag_chain,
    question: str,
    chat_history: str = ""
):

    if not question.strip():

        raise ValueError(
            "Question cannot be empty."
        )

    try:

        answer = rag_chain.invoke(
            {
                "question":
                    question,

                "chat_history":
                    chat_history
            }
        )

        return answer

    except Exception as e:

        error_message = str(e)

        
        # Gemini quota/rate-limit error
        

        if (
            "RESOURCE_EXHAUSTED"
            in error_message

            or

            "429"
            in error_message

            or

            "quota"
            in error_message.lower()
        ):

            raise RuntimeError(
                "Gemini API quota has been reached. "
                "Please wait for the quota to reset "
                "or use another Gemini API key."
            )

        
        # Other Gemini/API errors
        

        raise RuntimeError(
            f"Unable to generate an answer: "
            f"{error_message}"
        )



# TEST RAG SYSTEM DIRECTLY


if __name__ == "__main__":

    youtube_url = (
        "https://www.youtube.com/watch?v=eq9kxO_O6SY"
    )

    # --------------------------------------------------------
    # Process video
    # --------------------------------------------------------

    result = process_video(
        youtube_url
    )

    rag_chain = result[
        "rag_chain"
    ]

    print(
        "\n" + "=" * 60
    )

    print(
        "YouTube RAG System Ready"
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # Ask question
    # --------------------------------------------------------

    question = input(
        "\nAsk a question about the video: "
    )

    answer = ask_question(
        rag_chain,
        question
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "ANSWER"
    )

    print(
        "=" * 60
    )

    print(
        answer
    )