#!/usr/bin/env python3
"""
Optional MCP (stdio) wrapper around reg.py.

No third-party dependencies. Any MCP client that speaks newline-delimited
JSON-RPC over stdio can use these tools:

  fda_510k_search, fda_510k_get, fda_classification, fda_predicates,
  ecfr_get, fr_search, trials_search, pubmed_search, guidance_search,
  regulatory_snapshot

OpenCode config (project opencode.jsonc):

  {
    "mcp": {
      "servers": {
        "us-sleep-reg": {
          "type": "local",
          "command": ["python3", ".opencode/skills/us-sleep-regulatory/scripts/mcp_server.py"],
          "cwd": "."
        }
      }
    }
  }

Then: opencode mcp list
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reg  # noqa: E402


def _schema(properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "fda_510k_search",
        "description": "Search FDA 510(k) and De Novo clearances in openFDA. Use product_code for a landscape scan, k_number for one record, or device_name/applicant for a text search.",
        "inputSchema": _schema(
            {
                "query": {"type": "string", "description": "Device name phrase, e.g. 'Somryst'."},
                "product_code": {"type": "string", "description": "FDA product code, e.g. QVO."},
                "applicant": {"type": "string"},
                "k_number": {"type": "string", "description": "e.g. K191716 or DEN200033."},
                "decision_from": {"type": "string", "description": "YYYY-MM-DD."},
                "decision_to": {"type": "string", "description": "YYYY-MM-DD."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
            }
        ),
    },
    {
        "name": "fda_510k_get",
        "description": "Fetch one 510(k)/De Novo record. Set fetch_summary=true to download the decision summary PDF and extract text when a local PDF extractor exists.",
        "inputSchema": _schema(
            {
                "k_number": {"type": "string"},
                "fetch_summary": {"type": "boolean", "default": False},
            },
            ["k_number"],
        ),
    },
    {
        "name": "fda_classification",
        "description": "Look up FDA product classification (class, 21 CFR regulation number, GMP/third-party flags) by product code or device name.",
        "inputSchema": _schema(
            {
                "product_code": {"type": "string"},
                "name": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
            }
        ),
    },
    {
        "name": "fda_predicates",
        "description": "Get the classification, the CFR text, and every 510(k)/De Novo clearance for a product code. Use this before naming a predicate.",
        "inputSchema": _schema(
            {
                "product_code": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 100},
            },
            ["product_code"],
        ),
    },
    {
        "name": "ecfr_get",
        "description": "Fetch the current text of a CFR section (e.g. title 45, section 164.308) or a whole part. Returns citation, heading, text, as-of date, and source URL.",
        "inputSchema": _schema(
            {
                "title": {"type": "string", "description": "CFR title number, e.g. '21', '45', '16'."},
                "section": {"type": "string", "description": "e.g. 164.308."},
                "part": {"type": "string", "description": "e.g. 820."},
                "date": {"type": "string", "description": "YYYY-MM-DD; defaults to the current eCFR date."},
            },
            ["title"],
        ),
    },
    {
        "name": "fr_search",
        "description": "Search the Federal Register for FDA/HHS/FTC rules, proposed rules, and guidance notices. Use exact phrases in quotes for precision.",
        "inputSchema": _schema(
            {
                "term": {"type": "string"},
                "agency": {"type": "string", "default": "fda"},
                "doc_type": {"type": "string", "enum": ["rule", "proposed", "notice", "presidential"]},
                "since": {"type": "string", "description": "YYYY-MM-DD."},
                "until": {"type": "string", "description": "YYYY-MM-DD."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
            }
        ),
    },
    {
        "name": "trials_search",
        "description": "Search ClinicalTrials.gov v2 for interventional or observational studies by condition, intervention, or free text.",
        "inputSchema": _schema(
            {
                "condition": {"type": "string"},
                "intervention": {"type": "string"},
                "term": {"type": "string"},
                "status": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
            }
        ),
    },
    {
        "name": "pubmed_search",
        "description": "Search PubMed and return PMID, title, journal, date, first authors, DOI, and URL.",
        "inputSchema": _schema(
            {
                "term": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 10},
                "sort": {"type": "string", "default": "relevance"},
            },
            ["term"],
        ),
    },
    {
        "name": "guidance_search",
        "description": "Search the local curated FDA/HIPAA guidance registry, including status, issue date, docket, URL, and last-verified age. Always re-verify on the official page before relying.",
        "inputSchema": _schema(
            {
                "query": {"type": "string"},
                "topic": {"type": "string", "description": "e.g. device, software, ai, cyber, hipaa, sleep."},
                "status": {"type": "string"},
                "max_age_days": {"type": "integer", "default": 120},
            }
        ),
    },
    {
        "name": "kb_search",
        "description": "Search the local SQLite knowledge base offline. Use this before live FDA/eCFR tools; it contains the bundled references, guidance registry, CFR sections, classifications, 510(k) records, Federal Register notices, and agent notes.",
        "inputSchema": _schema(
            {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                "source_type": {"type": "string", "description": "e.g. cfr, guidance, 510k, classification, federal-register, note."},
                "status": {"type": "string"},
            }
        ),
    },
    {
        "name": "kb_get",
        "description": "Read one local knowledge-base document by id, URL, or citation. Offline.",
        "inputSchema": _schema({"key": {"type": "string"}}, ["key"]),
    },
    {
        "name": "kb_stats",
        "description": "Show local KB document counts, source types, FTS status, last init/refresh, and staleness. Run this first to decide whether a refresh is needed.",
        "inputSchema": _schema({}),
    },
    {
        "name": "kb_note_add",
        "description": "Save a research note with citations into the local KB. Use this after a session to accumulate durable knowledge.",
        "inputSchema": _schema(
            {
                "text": {"type": "string"},
                "title": {"type": "string"},
                "tags": {"type": "string", "description": "Comma-separated."},
                "sources": {"type": "array", "items": {"type": "string"}},
            },
            ["text"],
        ),
    },
    {
        "name": "kb_refresh",
        "description": "Refresh the local KB from official sources. This is the only KB tool that uses the network. Core refresh is fast; set extended=true for Federal Register/ClinicalTrials/PubMed.",
        "inputSchema": _schema(
            {
                "extended": {"type": "boolean", "default": False},
                "summaries": {"type": "boolean", "default": False},
            }
        ),
    },
    {
        "name": "kb_init",
        "description": "Initialize or reinitialize the local KB from the bundled references, guidance registry, and knowledge/seed. Offline. Set force=true to clear first.",
        "inputSchema": _schema({"force": {"type": "boolean", "default": False}}),
    },
    {
        "name": "regulatory_snapshot",
        "description": "Build a dated JSON + Markdown snapshot covering classifications, predicate landscape, key CFR sections, guidance registry, Federal Register, ClinicalTrials.gov, and PubMed. Writes files to the skill's snapshots/ directory by default.",
        "inputSchema": _schema(
            {
                "product_codes": {"type": "array", "items": {"type": "string"}, "default": ["QVO", "QMZ", "LEL"]},
                "query": {"type": "string", "default": "insomnia"},
                "out_dir": {"type": "string"},
            }
        ),
    },
]


def _dispatch(name: str, args: dict[str, Any]) -> dict:
    def pick(*keys: str) -> dict:
        return {k: args[k] for k in keys if k in args and args[k] is not None}

    if name == "fda_510k_search":
        return reg.fda_510k_search(
            **pick("query", "product_code", "applicant", "k_number", "decision_from", "decision_to", "limit")
        )
    if name == "fda_510k_get":
        return reg.fda_510k_get(**pick("k_number", "fetch_summary"))
    if name == "fda_classification":
        return reg.fda_classification(**pick("product_code", "name", "limit"))
    if name == "fda_predicates":
        return reg.fda_predicates(**pick("product_code", "limit"))
    if name == "ecfr_get":
        return reg.ecfr_get(**pick("title", "section", "part", "date"))
    if name == "fr_search":
        return reg.fr_search(**pick("term", "agency", "doc_type", "since", "until", "limit"))
    if name == "trials_search":
        return reg.trials_search(**pick("condition", "intervention", "term", "status", "limit"))
    if name == "pubmed_search":
        return reg.pubmed_search(**pick("term", "limit", "sort"))
    if name == "guidance_search":
        return reg.guidance_search(**pick("query", "topic", "status", "max_age_days"))
    if name == "regulatory_snapshot":
        product_codes = args.get("product_codes")
        return reg.build_snapshot(
            product_codes=product_codes if isinstance(product_codes, list) else None,
            query=args.get("query", "insomnia"),
            out_dir=args.get("out_dir") or str(reg.SKILL_DIR / "snapshots"),
        )
    if name == "kb_search":
        return reg.kb_search(**pick("query", "limit", "source_type", "status"))
    if name == "kb_get":
        return reg.kb_get(**pick("key"))
    if name == "kb_stats":
        return reg.kb_stats()
    if name == "kb_note_add":
        sources = args.get("sources")
        return reg.kb_note_add(
            args.get("text", ""),
            title=args.get("title"),
            tags=args.get("tags"),
            sources=sources if isinstance(sources, list) else None,
        )
    if name == "kb_refresh":
        return reg.kb_refresh(extended=bool(args.get("extended")), summaries=bool(args.get("summaries")))
    if name == "kb_init":
        return reg.kb_init(force=bool(args.get("force")))
    raise ValueError(f"Unknown tool: {name}")


def send(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params") or {}

        if method == "initialize":
            send(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "us-sleep-regulatory", "version": reg.VERSION},
                        "instructions": (
                            "Official-source US regulatory research for an app-based sleep therapy service. "
                            "Search the local knowledge base (kb_search/kb_get) first; call live tools only when "
                            "the KB lacks the answer or is stale. Always re-verify guidance status and cite "
                            "retrieved_at. This is not legal advice."
                        ),
                    },
                }
            )
        elif method in ("notifications/initialized", "notifications/cancelled"):
            continue
        elif method == "ping":
            send({"jsonrpc": "2.0", "id": msg_id, "result": {}})
        elif method == "tools/list":
            send({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            try:
                result = _dispatch(name, args)
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                            "isError": False,
                        },
                    }
                )
            except Exception as exc:  # noqa: BLE001
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [{"type": "text", "text": f"ERROR: {exc}"}],
                            "isError": True,
                        },
                    }
                )
        else:
            if msg_id is not None:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32601, "message": f"Method not found: {method}"},
                    }
                )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
