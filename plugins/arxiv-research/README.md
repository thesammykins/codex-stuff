# arXiv Research

Codex plugin for arXiv paper lookup.

## Tools

- `search_papers`: searches arXiv through the official API and returns titles, authors, dates, categories, abstracts, and links.
- `get_papers`: fetches one or more arXiv IDs and returns metadata plus abstract and PDF links.

The server uses Python standard library modules only. No API key is required.

## Notes

arXiv asks automated clients to avoid rapid repeated requests. This server keeps a small in-memory cache and waits between fresh API calls by default. Set `ARXIV_MIN_DELAY_SECONDS=0` only for local testing.
