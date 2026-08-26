# main.py

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent import agent, checkpointer


# ---------------------------------------------------------
# FastAPI
# ---------------------------------------------------------

app = FastAPI(
    title="News Agent API",
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

# Example .env:
#
# FRONTEND_ORIGINS=http://localhost:4200
#
# Multiple:
#
# FRONTEND_ORIGINS=http://localhost:4200,https://myapp.com

frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:4200",
)

allowed_origins = [
    origin.strip()
    for origin in frontend_origins.split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Defaults
# ---------------------------------------------------------

DEFAULT_THREAD_ID = "1"


# ---------------------------------------------------------
# Request models
# ---------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
    )

    thread_id: str = DEFAULT_THREAD_ID


class ClearRequest(BaseModel):
    thread_id: str = DEFAULT_THREAD_ID


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def extract_ai_content(content) -> str:
    """
    Normalize content returned by Gemini/LangChain.

    Gemini may return:
      - a plain string
      - a list of content blocks
      - dictionaries containing text
    """

    if isinstance(content, str):
        return content


    if isinstance(content, list):

        parts = []

        for block in content:

            if isinstance(block, str):

                parts.append(block)

            elif isinstance(block, dict):

                text = block.get("text")

                if text:
                    parts.append(str(text))

            else:

                parts.append(str(block))


        return " ".join(parts).strip()


    if content is None:
        return ""


    return str(content)


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "news-agent",
    }


# ---------------------------------------------------------
# Chat
# ---------------------------------------------------------

@app.post("/chat")
def chat(req: ChatRequest):

    message = req.message.strip()

    if not message:

        return JSONResponse(
            status_code=400,
            content={
                "thread_id": req.thread_id,
                "error": "InvalidMessage",
                "message": "Message cannot be empty.",
            },
        )


    config = {
        "configurable": {
            "thread_id": req.thread_id
        }
    }


    try:

        print(
            f"\n[CHAT] thread_id={req.thread_id}"
        )

        print(
            f"[CHAT] message={message}"
        )


        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": message,
                    }
                ]
            },
            config,
        )


        messages = []


        for msg in response.get(
            "messages",
            []
        ):

            if msg.type == "human":

                messages.append(
                    {
                        "type": "human",
                        "content": (
                            extract_ai_content(
                                msg.content
                            )
                        ),
                    }
                )


            elif msg.type == "ai":

                content = extract_ai_content(
                    msg.content
                )


                if content:

                    messages.append(
                        {
                            "type": "ai",
                            "content": content,
                        }
                    )


        return {
            "thread_id": req.thread_id,
            "messages": messages,
        }


    except Exception as e:

        print(
            "\n--- AGENT ERROR ---"
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )


        return JSONResponse(
            status_code=500,
            content={
                "thread_id": req.thread_id,
                "error": type(e).__name__,
                "message": str(e),
            },
        )


# ---------------------------------------------------------
# Clear conversation
# ---------------------------------------------------------

@app.post("/clear")
def clear(req: ClearRequest):

    try:

        print(
            f"[CLEAR] thread_id={req.thread_id}"
        )


        checkpointer.delete_thread(
            req.thread_id
        )


        return {
            "status": "cleared",
            "thread_id": req.thread_id,
        }


    except Exception as e:

        print(
            "\n--- CLEAR ERROR ---"
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )


        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "thread_id": req.thread_id,
                "message": str(e),
            },
        )