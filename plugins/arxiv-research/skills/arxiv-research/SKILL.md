---
name: arxiv-research
description: Search and retrieve arXiv papers for research, literature lookup, paper summaries, and arXiv ID lookups.
---

# arXiv Research

Use this plugin when the user asks to search arXiv, look up an arXiv paper ID, find recent papers, compare papers, or gather paper metadata from arXiv.

Prefer the MCP tools exposed by this plugin:

- `search_papers` for keyword, author, title, abstract, category, or recent-paper searches.
- `get_papers` when the user provides one or more arXiv IDs.

Search query tips:

- Plain text is searched across arXiv with `all:`.
- Use arXiv query syntax when precision matters, such as `ti:"retrieval augmented generation"`, `au:"Yoshua Bengio"`, or `cat:cs.CL AND all:alignment`.
- Use `sort_by="submittedDate"` and `sort_order="descending"` when the user asks for recent papers.

Always include arXiv links when reporting paper results, and distinguish arXiv metadata from your own inference or summary.
