from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import agent, pool


# ---------------------------------------------------------
# FastAPI
# ---------------------------------------------------------

app = FastAPI(
    title="News Agent API"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    message: str
    thread_id: str = DEFAULT_THREAD_ID


class ClearRequest(BaseModel):
    thread_id: str = DEFAULT_THREAD_ID


# ---------------------------------------------------------
# Chat
# ---------------------------------------------------------

@app.post("/chat")
def chat(req: ChatRequest):

    config = {
        "configurable": {
            "thread_id": req.thread_id
        }
    }

    try:

        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": req.message,
                    }
                ]
            },
            config,
        )

        messages = []

        for msg in response["messages"]:

            if msg.type == "human":

                messages.append(
                    {
                        "type": "human",
                        "content": msg.content,
                    }
                )

            elif msg.type == "ai" and msg.content:

                content = msg.content

                # Gemini sometimes returns a list
                # of content blocks.
                if isinstance(content, list):

                    content = " ".join(
                        block.get("text", "")
                        if isinstance(block, dict)
                        else str(block)
                        for block in content
                    )

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

        print("\n--- AGENT ERROR ---")
        print(type(e).__name__)
        print(str(e))

        return {
            "thread_id": req.thread_id,
            "error": type(e).__name__,
            "message": str(e),
        }


# ---------------------------------------------------------
# Clear conversation
# ---------------------------------------------------------

@app.post("/clear")
def clear(req: ClearRequest):

    try:

        with pool.connection() as conn:

            conn.execute(
                "DELETE FROM checkpoint_writes "
                "WHERE thread_id = %s",
                (req.thread_id,),
            )

            conn.execute(
                "DELETE FROM checkpoints "
                "WHERE thread_id = %s",
                (req.thread_id,),
            )

            conn.commit()

        return {
            "status": "cleared",
            "thread_id": req.thread_id,
        }

    except Exception as e:

        return {
            "status": "error",
            "thread_id": req.thread_id,
            "message": str(e),
        }