#!/usr/bin/env python3
"""Small stdio MCP server for arXiv paper lookup."""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any


SERVER_NAME = "arxiv-research"
SERVER_VERSION = "0.1.0"
API_URL = os.environ.get("ARXIV_API_URL", "https://export.arxiv.org/api/query")
USER_AGENT = os.environ.get(
    "ARXIV_USER_AGENT",
    f"{SERVER_NAME}/{SERVER_VERSION} (Codex MCP plugin)",
)
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("ARXIV_TIMEOUT_SECONDS", "20"))
MIN_DELAY_SECONDS = float(os.environ.get("ARXIV_MIN_DELAY_SECONDS", "3"))
MAX_RESULTS_CAP = 25

ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
OPENSEARCH_NS = "http://a9.com/-/spec/opensearch/1.1/"
NS = {
    "atom": ATOM_NS,
    "arxiv": ARXIV_NS,
    "opensearch": OPENSEARCH_NS,
}

_last_request_at = 0.0
_cache: dict[tuple[tuple[str, str], ...], dict[str, Any]] = {}


TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_papers",
        "description": (
            "Search arXiv through the official API. Accepts plain terms or arXiv "
            "search_query syntax such as ti:\"attention\", au:\"LeCun\", or cat:cs.CL."
        ),
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Plain terms or an arXiv search_query expression.",
                    "minLength": 1,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of papers to return.",
                    "minimum": 1,
                    "maximum": MAX_RESULTS_CAP,
                    "default": 5,
                },
                "start": {
                    "type": "integer",
                    "description": "Zero-based result offset for paging.",
                    "minimum": 0,
                    "default": 0,
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["relevance", "lastUpdatedDate", "submittedDate"],
                    "default": "relevance",
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["ascending", "descending"],
                    "default": "descending",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_papers",
        "description": "Retrieve metadata, abstract, and links for one or more arXiv IDs.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "ids": {
                    "type": "array",
                    "description": "arXiv IDs, with or without the arXiv: prefix.",
                    "minItems": 1,
                    "maxItems": 20,
                    "items": {
                        "type": "string",
                        "minLength": 1,
                    },
                }
            },
            "required": ["ids"],
        },
    },
]


@dataclass(frozen=True)
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    summary: str
    published: str
    updated: str
    primary_category: str
    categories: list[str]
    abstract_url: str
    pdf_url: str
    doi: str
    journal_ref: str
    comment: str


def main() -> None:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            response = handle_message(message)
        except Exception as exc:  # MCP clients expect errors to stay on stdout.
            response = jsonrpc_error(None, -32603, str(exc))
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()


def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        protocol_version = params.get("protocolVersion", "2024-11-05")
        return jsonrpc_result(
            request_id,
            {
                "protocolVersion": protocol_version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return jsonrpc_result(request_id, {})
    if method == "tools/list":
        return jsonrpc_result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        return jsonrpc_result(request_id, call_tool(params))

    return jsonrpc_error(request_id, -32601, f"Unsupported method: {method}")


def call_tool(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments") or {}

    try:
        if name == "search_papers":
            text = search_papers(arguments)
        elif name == "get_papers":
            text = get_papers(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        return {"content": [{"type": "text", "text": text}], "isError": False}
    except Exception as exc:
        return {"content": [{"type": "text", "text": f"arXiv lookup failed: {exc}"}], "isError": True}


def search_papers(arguments: dict[str, Any]) -> str:
    query = require_string(arguments, "query")
    max_results = clamp_int(arguments.get("max_results", 5), 1, MAX_RESULTS_CAP)
    start = clamp_int(arguments.get("start", 0), 0, 30000)
    sort_by = enum_value(
        arguments.get("sort_by", "relevance"),
        {"relevance", "lastUpdatedDate", "submittedDate"},
        "sort_by",
    )
    sort_order = enum_value(
        arguments.get("sort_order", "descending"),
        {"ascending", "descending"},
        "sort_order",
    )

    search_query = normalize_search_query(query)
    feed = fetch_arxiv(
        {
            "search_query": search_query,
            "start": str(start),
            "max_results": str(max_results),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
    )
    total = feed.get("total_results")
    papers = feed["papers"]
    header = f"arXiv search: `{search_query}`"
    if total is not None:
        header += f"\nTotal results reported by arXiv: {total}"
    if not papers:
        return f"{header}\n\nNo papers found."
    return header + "\n\n" + format_papers(papers)


def get_papers(arguments: dict[str, Any]) -> str:
    ids = arguments.get("ids")
    if not isinstance(ids, list) or not ids:
        raise ValueError("ids must be a non-empty array")
    normalized_ids = [normalize_arxiv_id(value) for value in ids]
    feed = fetch_arxiv({"id_list": ",".join(normalized_ids), "max_results": str(len(normalized_ids))})
    papers = feed["papers"]
    if not papers:
        return "No papers found for: " + ", ".join(normalized_ids)
    return "arXiv papers: " + ", ".join(normalized_ids) + "\n\n" + format_papers(papers)


def fetch_arxiv(params: dict[str, str]) -> dict[str, Any]:
    cache_key = tuple(sorted(params.items()))
    if cache_key in _cache:
        return _cache[cache_key]

    wait_for_rate_limit()
    url = API_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {exc.code} from arXiv API. {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach arXiv API at {API_URL}: {exc.reason}") from exc

    result = parse_feed(payload)
    _cache[cache_key] = result
    return result


def wait_for_rate_limit() -> None:
    global _last_request_at
    if MIN_DELAY_SECONDS <= 0:
        return
    now = time.monotonic()
    elapsed = now - _last_request_at
    if _last_request_at and elapsed < MIN_DELAY_SECONDS:
        time.sleep(MIN_DELAY_SECONDS - elapsed)
    _last_request_at = time.monotonic()


def parse_feed(payload: bytes) -> dict[str, Any]:
    root = ET.fromstring(payload)
    total_results_text = find_text(root, "opensearch:totalResults")
    total_results = int(total_results_text) if total_results_text and total_results_text.isdigit() else None
    papers = [parse_entry(entry) for entry in root.findall("atom:entry", NS)]
    errors = [paper.summary for paper in papers if paper.title.lower() == "error"]
    if errors:
        raise RuntimeError("; ".join(errors))
    return {"total_results": total_results, "papers": papers}


def parse_entry(entry: ET.Element) -> Paper:
    entry_id = https_url(find_text(entry, "atom:id"))
    links = entry.findall("atom:link", NS)
    abstract_url = entry_id
    pdf_url = ""
    for link in links:
        href = https_url(link.attrib.get("href", ""))
        if link.attrib.get("rel") == "alternate" and href:
            abstract_url = href
        if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
            pdf_url = href

    categories = [category.attrib.get("term", "") for category in entry.findall("atom:category", NS)]
    categories = [category for category in categories if category]
    primary = entry.find("arxiv:primary_category", NS)
    primary_category = primary.attrib.get("term", "") if primary is not None else ""

    return Paper(
        arxiv_id=arxiv_id_from_url(entry_id or abstract_url),
        title=clean_text(find_text(entry, "atom:title")),
        authors=[clean_text(name.text or "") for name in entry.findall("atom:author/atom:name", NS)],
        summary=clean_text(find_text(entry, "atom:summary")),
        published=find_text(entry, "atom:published"),
        updated=find_text(entry, "atom:updated"),
        primary_category=primary_category,
        categories=categories,
        abstract_url=abstract_url,
        pdf_url=pdf_url,
        doi=clean_text(find_text(entry, "arxiv:doi")),
        journal_ref=clean_text(find_text(entry, "arxiv:journal_ref")),
        comment=clean_text(find_text(entry, "arxiv:comment")),
    )


def format_papers(papers: list[Paper]) -> str:
    blocks = []
    for index, paper in enumerate(papers, start=1):
        authors = ", ".join(paper.authors) if paper.authors else "Unknown authors"
        categories = ", ".join(paper.categories)
        links = [f"[abstract]({paper.abstract_url})" if paper.abstract_url else ""]
        if paper.pdf_url:
            links.append(f"[pdf]({paper.pdf_url})")
        lines = [
            f"{index}. **{paper.title}**",
            f"   arXiv ID: `{paper.arxiv_id}`",
            f"   Authors: {authors}",
            f"   Published: {paper.published or 'unknown'}",
            f"   Updated: {paper.updated or 'unknown'}",
        ]
        if paper.primary_category:
            lines.append(f"   Primary category: {paper.primary_category}")
        if categories:
            lines.append(f"   Categories: {categories}")
        if paper.doi:
            lines.append(f"   DOI: {paper.doi}")
        if paper.journal_ref:
            lines.append(f"   Journal reference: {paper.journal_ref}")
        if paper.comment:
            lines.append(f"   Comment: {paper.comment}")
        lines.append(f"   Links: {' | '.join(link for link in links if link)}")
        lines.append(f"   Abstract: {paper.summary}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def normalize_search_query(query: str) -> str:
    query = clean_text(query)
    if not query:
        raise ValueError("query is required")
    if looks_like_arxiv_query(query):
        return query
    return f"all:{query}"


def looks_like_arxiv_query(query: str) -> bool:
    field_pattern = r"(^|[\s(])(all|ti|au|abs|co|jr|cat|rn|id):"
    has_field = re.search(field_pattern, query, flags=re.IGNORECASE) is not None
    has_operator = re.search(r"\b(AND|OR|ANDNOT)\b", query) is not None
    return has_field or has_operator


def normalize_arxiv_id(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("each arXiv ID must be a string")
    cleaned = value.strip()
    cleaned = re.sub(r"^arxiv:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("https://arxiv.org/abs/", "").replace("http://arxiv.org/abs/", "")
    cleaned = cleaned.replace("https://arxiv.org/pdf/", "").replace("http://arxiv.org/pdf/", "")
    cleaned = cleaned.removesuffix(".pdf")
    if not cleaned:
        raise ValueError("arXiv ID cannot be blank")
    return cleaned


def arxiv_id_from_url(url: str) -> str:
    if "/abs/" not in url:
        return url.rsplit("/", 1)[-1]
    return url.split("/abs/", 1)[1]


def find_text(element: ET.Element, path: str) -> str:
    found = element.find(path, NS)
    return "" if found is None or found.text is None else found.text.strip()


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def https_url(url: str) -> str:
    if url.startswith("http://"):
        return "https://" + url[len("http://") :]
    return url


def require_string(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def clamp_int(value: Any, minimum: int, maximum: int) -> int:
    if not isinstance(value, int):
        raise ValueError(f"expected integer, got {type(value).__name__}")
    return max(minimum, min(maximum, value))


def enum_value(value: Any, allowed: set[str], name: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")
    return value


def jsonrpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def jsonrpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


if __name__ == "__main__":
    main()
