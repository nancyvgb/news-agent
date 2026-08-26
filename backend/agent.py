import os
import requests

from dotenv import load_dotenv

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

print(
    "DEBUG CURRENTS_API_KEY exists:",
    bool(os.environ.get("CURRENTS_API_KEY")),
    flush=True
)

CURRENTS_API_KEY = os.getenv("CURRENTS_API_KEY")

if not CURRENTS_API_KEY:
    raise RuntimeError(
        "CURRENTS_API_KEY environment variable is not set"
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
# Currents API
# ---------------------------------------------------------

CURRENTS_LATEST_URL = (
    "https://api.currentsapi.services/v1/latest-news"
)

CURRENTS_SEARCH_URL = (
    "https://api.currentsapi.services/v1/search"
)

CURRENTS_HEADERS = {
    "Authorization": f"Bearer {CURRENTS_API_KEY}"
}


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def normalize_country(country: str) -> str:
    """
    Normalize a country code for Currents.

    co -> CO
    us -> US
    """
    return country.strip().upper()


def normalize_category(category: str) -> str:
    """
    Normalize category values used by the agent.
    """

    category = category.strip().lower()

    aliases = {
        "news": "general",
        "top": "general",
    }

    return aliases.get(category, category)


# ---------------------------------------------------------
# Tools
# ---------------------------------------------------------

@tool
def get_news(
    category: str,
    country: str,
):
    """
    Get recent news for a category and country.

    Examples of categories:
    technology, business, politics, sports,
    science, entertainment, health.

    country must be a 2-letter country code,
    for example "co" for Colombia or "us"
    for the United States.
    """

    try:
        normalized_country = normalize_country(
            country
        )

        normalized_category = normalize_category(
            category
        )

        print(
            "[TOOL] get_news("
            f"category={normalized_category}, "
            f"country={normalized_country}"
            ")"
        )

        params = {
            "language": "en",
            "country": normalized_country,
            "page_size": 10,
        }

        if normalized_category != "general":
            params["category"] = normalized_category

        response = requests.get(
            CURRENTS_LATEST_URL,
            params=params,
            headers=CURRENTS_HEADERS,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            raise RuntimeError(
                data.get("message")
                or f"Currents API returned: {data}"
            )

        articles = data.get(
            "news",
            []
        )

        return {
            "status": "success",
            "category": normalized_category,
            "country": normalized_country,
            "articles": articles,
        }

    except requests.HTTPError as e:

        status_code = (
            e.response.status_code
            if e.response is not None
            else None
        )

        response_body = None

        if e.response is not None:
            try:
                response_body = (
                    e.response.json()
                )
            except Exception:
                response_body = (
                    e.response.text
                )

        print(
            "[TOOL ERROR] get_news:",
            status_code,
            response_body,
        )

        return {
            "status": "error",
            "message": (
                f"Currents API request failed "
                f"with HTTP {status_code}"
            ),
            "details": response_body,
            "category": category,
            "country": country,
        }

    except Exception as e:

        print(
            f"[TOOL ERROR] get_news: {e}"
        )

        return {
            "status": "error",
            "message": str(e),
            "category": category,
            "country": country,
        }


@tool
def search_news(
    query: str,
    country: str,
):
    """
    Search current news by keyword, topic, company,
    organization, person, or event.

    Examples:
    OpenAI
    Tesla
    artificial intelligence
    Colombia elections

    country must be a 2-letter country code.
    """

    try:

        normalized_country = normalize_country(
            country
        )

        query = query.strip()

        print(
            "[TOOL] search_news("
            f"query={query}, "
            f"country={normalized_country}"
            ")"
        )

        params = {
            "keywords": query,
            "language": "en",
            "country": normalized_country,
            "page_size": 10,
        }

        response = requests.get(
            CURRENTS_SEARCH_URL,
            params=params,
            headers=CURRENTS_HEADERS,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            raise RuntimeError(
                data.get("message")
                or f"Currents API returned: {data}"
            )

        articles = data.get(
            "news",
            []
        )

        return {
            "status": "success",
            "query": query,
            "country": normalized_country,
            "articles": articles,
        }

    except requests.HTTPError as e:

        status_code = (
            e.response.status_code
            if e.response is not None
            else None
        )

        response_body = None

        if e.response is not None:
            try:
                response_body = (
                    e.response.json()
                )
            except Exception:
                response_body = (
                    e.response.text
                )

        print(
            "[TOOL ERROR] search_news:",
            status_code,
            response_body,
        )

        return {
            "status": "error",
            "message": (
                f"Currents API request failed "
                f"with HTTP {status_code}"
            ),
            "details": response_body,
            "query": query,
            "country": country,
        }

    except Exception as e:

        print(
            f"[TOOL ERROR] search_news: {e}"
        )

        return {
            "status": "error",
            "message": str(e),
            "query": query,
            "country": country,
        }


@tool
def get_location():
    """
    Get the user's current country based on
    their IP address.

    Returns a two-letter country code.
    """

    try:

        print(
            "[TOOL] get_location()"
        )

        response = requests.get(
            "https://ipinfo.io/json",
            headers={
                "user-agent": "Mozilla/5.0"
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        country = data.get(
            "country"
        )

        if not country:
            raise RuntimeError(
                "Could not determine country "
                "from IP information."
            )

        return country.lower()

    except Exception as e:

        print(
            f"[TOOL ERROR] get_location: {e}"
        )

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

You have access to current news through
the Currents News API.

YOUR WORKFLOW:

1. If the user asks for general news WITHOUT
   specifying a category or topic:

   - If the user specified a country, use it.
   - Otherwise call get_location.
   - Use get_news with an appropriate category.
   - If the user simply asks for "news",
     "latest news", or "top news", use:
       category="top"

2. If the user specifies a news category:

   Examples:
   technology
   business
   politics
   sports
   science
   entertainment
   health

   - If the user did not specify a country,
     call get_location first.
   - Then call get_news.

3. If the user asks about a specific:
   - company
   - person
   - organization
   - event
   - product
   - subject
   - keyword
   - topic

   use search_news instead of get_news.

   Examples:
   "news about OpenAI"
   "what happened with Tesla?"
   "AI news"
   "latest news about Apple"

4. If the user provides a country or region:

   - Convert it to a two-letter country code.
   - Examples:
       Colombia -> co
       United States -> us
       Mexico -> mx
       Spain -> es

5. Colombia's country code is "co".

6. When presenting articles:

   - Prefer recent and relevant articles.
   - Mention the article title.
   - Briefly summarize the description.
   - Mention the publication/source when available.
   - Include the article URL when useful.
   - Do not invent details that are not present
     in the tool response.

7. If the tool returns no articles:

   - Explain that no matching recent articles
     were found.
   - Suggest trying a broader topic or category.

8. If a tool returns an error:

   - Do not repeatedly call the same tool
     with identical arguments.
   - Explain the problem clearly.
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

checkpointer = PostgresSaver(
    pool
)

checkpointer.setup()


# ---------------------------------------------------------
# Agent
# ---------------------------------------------------------

agent = create_react_agent(
    model=llm,
    tools=[
        get_news,
        search_news,
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

        user_query = input(
            "\nEnter your query: "
        )

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

            print(
                "\n--- RESPONSE ---"
            )

            for message in response[
                "messages"
            ]:

                if message.type == "human":

                    print(
                        f"\nUSER: "
                        f"{message.content}"
                    )

                elif message.type == "ai":

                    print(
                        f"\nAI: "
                        f"{message.content}"
                    )

                elif message.type == "tool":

                    print(
                        f"\nTOOL: "
                        f"{message.content}"
                    )

        except Exception as e:

            print(
                "\n--- ERROR ---"
            )

            print(
                type(e).__name__
            )

            print(
                str(e)
            )