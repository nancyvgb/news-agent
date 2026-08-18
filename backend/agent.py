import os
import requests

from dotenv import load_dotenv
from newsapi import NewsApiClient

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool


# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------

load_dotenv()

DB_URI = os.getenv("SUPABASE_URL")

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
if not NEWS_API_KEY:
    raise RuntimeError(
        "NEWS_API_KEY is not set — add it to .env"
    )

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set — add it to .env"
    )

if not DB_URI:
    raise RuntimeError(
        "SUPABASE_URL is not set — add it to .env"
    )


# ---------------------------------------------------------
# APIs
# ---------------------------------------------------------

newsapi = NewsApiClient(
    api_key=NEWS_API_KEY
)


# ---------------------------------------------------------
# Tools
# ---------------------------------------------------------

@tool
def get_news(category: str, country: str):
    """
    Get top news headlines for a category and country.

    category examples:
    technology, business, politics, sports,
    science, entertainment, health

    country must be a 2-letter country code,
    for example "co" for Colombia.
    """

    try:
        print(
            f"[TOOL] get_news(category={category}, country={country})"
        )

        articles = newsapi.get_top_headlines(
            category=category,
            country=country,
        )

        # Return a simple JSON-serializable structure.
        return {
            "status": "success",
            "category": category,
            "country": country,
            "articles": articles.get("articles", []),
        }

    except Exception as e:
        # IMPORTANT:
        # Don't allow the tool to crash the graph.
        # Return the error as the tool result instead.
        print(f"[TOOL ERROR] get_news: {e}")

        return {
            "status": "error",
            "message": str(e),
            "category": category,
            "country": country,
        }


@tool
def get_location():
    """
    Get the user's current country based on their IP address.
    Returns a two-letter country code.
    """

    try:
        print("[TOOL] get_location()")

        response = requests.get(
            "https://ipinfo.io/json",
            headers={
                "user-agent": "Mozilla/5.0"
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        country = data.get("country")

        if not country:
            raise RuntimeError(
                "Could not determine country from IP information."
            )

        return country.lower()

    except Exception as e:
        print(f"[TOOL ERROR] get_location: {e}")

        return {
            "status": "error",
            "message": str(e),
        }


# ---------------------------------------------------------
# Model
# ---------------------------------------------------------

llm = ChatGoogleGenerativeAI(
    model=os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite",
    ),
    api_key=GOOGLE_API_KEY,
)


# ---------------------------------------------------------
# System prompt
# ---------------------------------------------------------

system_prompt = """
You are a helpful news assistant.

YOUR WORKFLOW:

1. If the user asks for news WITHOUT specifying a category:
   - Offer relevant categories such as:
     technology, business, politics, sports,
     science, entertainment, and health.
   - Ask which category interests them.
   - You may provide general news if appropriate.

2. If the user specifies a category, topic, or company:
   - First call get_location if the user did not specify a country.
   - Then call get_news with:
       category=<appropriate category>
       country=<two-letter country code>

3. If the user specifies a country or region:
   - Use the appropriate two-letter country code.
   - Call get_news.

4. When using get_news:
   - Use valid NewsAPI categories:
     technology
     business
     politics
     sports
     science
     entertainment
     health

5. Colombia's country code is "co".

6. If a tool returns an error:
   - Do not call the same tool repeatedly.
   - Explain the problem to the user clearly.
"""


# ---------------------------------------------------------
# PostgreSQL connection pool
# ---------------------------------------------------------

pool = ConnectionPool(
    DB_URI,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0,
    },
    open=True,
)


# ---------------------------------------------------------
# LangGraph checkpointer
# ---------------------------------------------------------

checkpointer = PostgresSaver(pool)

checkpointer.setup()


# ---------------------------------------------------------
# Agent
# ---------------------------------------------------------

agent = create_react_agent(
    model=llm,
    tools=[
        get_news,
        get_location,
    ],
    prompt=system_prompt,
    checkpointer=checkpointer,
)


# ---------------------------------------------------------
# Local CLI testing
# ---------------------------------------------------------

if __name__ == "__main__":

    thread_id = "local-test"

    while True:

        user_query = input("\nEnter your query: ")

        if user_query.lower() in [
            "bye",
            "quit",
            "exit",
        ]:
            break

        try:

            response = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": user_query,
                        }
                    ]
                },
                {
                    "configurable": {
                        "thread_id": thread_id
                    }
                },
            )

            print("\n--- RESPONSE ---")

            for message in response["messages"]:

                if message.type == "human":
                    print(
                        f"\nUSER: {message.content}"
                    )

                elif message.type == "ai":
                    print(
                        f"\nAI: {message.content}"
                    )

                elif message.type == "tool":
                    print(
                        f"\nTOOL: {message.content}"
                    )

        except Exception as e:

            print("\n--- ERROR ---")
            print(type(e).__name__)
            print(str(e))