# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-file LangChain/LangGraph agent (`agent.py`) that answers news questions. Gemini is the model, NewsAPI is the data source. There is no test suite, no lint config, no `requirements.txt`, and no git repo — the `.venv` is the source of truth for dependencies.

## Commands

```bash
.venv/bin/python agent.py          # run the agent (prompts twice on stdin)
.venv/bin/pip list                 # inspect installed deps
.venv/bin/pip install <pkg>        # add a dep (also record it if a requirements.txt is ever added)
```

Python 3.13. Key versions: `langchain` 1.3, `langgraph` 1.2, `langchain-google-genai` 4.3, `newsapi-python` 0.2.7.

## Environment

`.env` (loaded via `load_dotenv()`) must provide:

- `GOOGLE_API_KEY` — read implicitly by `ChatGoogleGenerativeAI`, never referenced in code
- `NEWS_API_KEY` — passed to `NewsApiClient`
- `GEMINI_MODEL` — optional, defaults to `gemini-3.1-flash-lite`
- `DATABASE_URL` / `SUPABASE_DB_URL` / `SUPABASE_POOLER_URL` / `SUPABASE_URL` — Postgres connection string for the LangGraph checkpointer. If the direct `db.<project>.supabase.co` host does not resolve locally, use the Supabase Session Pooler URL instead.

## Architecture

`agent.py` is linear top-to-bottom:

1. **Module-level NewsAPI calls** (`top_headlines`, `all_articles`, `sources`) fire at import time and their results are never used. They consume NewsAPI quota on every run — expect 429s on the free tier. Removing or guarding them is safe.
2. **Tools** — `get_news(topic)` and `get_regional_news(region)` are plain functions passed to `create_agent`; LangChain derives their schemas from the type hints, so the annotations are load-bearing. Both `print()` to stdout and return `None`, so the model receives no tool output — this is the main structural bug if answers come back empty or hallucinated. Fix by returning a string/list instead of printing.
3. **Agent** — `create_agent` (LangChain 1.x `langchain.agents`, not the deprecated `initialize_agent`) with a system prompt that encodes the category-offering workflow.
4. **Memory** — `InMemorySaver()` checkpointer with a hardcoded `thread_id: "1"`, so the two hardcoded turns share conversation history and then it's discarded. `PostgresSaver` is imported but unused; swapping it in (with `SUPABASE_URL`) is the apparent next step and requires `PostgresSaver.setup()` on first use.
5. **Entry point** — two hardcoded `input()`/`invoke()` rounds. There is no loop, no `if __name__ == "__main__"` guard, so importing `agent.py` runs everything.

Response extraction is `response['messages'][-1].content[0]['text']` — this assumes Gemini returns content as a list of blocks. It raises `TypeError` when the content is a plain string, which happens with some models/responses; index defensively when touching this.
