#!/usr/bin/env python3
"""
us-sleep-regulatory / reg.py

One CLI for the official US regulatory sources that matter to an app-based
sleep-therapy clinical service:

  openFDA       510(k), De Novo, classification, recalls, MAUDE
  eCFR          21 CFR 820 / 882, 45 CFR 160-164, 16 CFR 318
  Federal Register  rules, proposed rules, guidance notices
  ClinicalTrials.gov v2
  PubMed E-utilities
  Local guidance registry (curated, with last-verified dates)

Design rules:
  * stdlib only, no install step
  * every response carries _meta.source / _meta.url / _meta.retrieved_at
  * cache is transparent and reported (cached: true)
  * no parallel hammering; polite retries and a 24h default TTL
  * HTML on fda.gov / hhs.gov is often blocked from shell clients; this CLI
    never scrapes those pages. Use the agent's web-fetch/browser tool for HTML.

Examples:
  python3 reg.py doctor
  python3 reg.py 510k-search --product-code QVO
  python3 reg.py 510k-get K191716 --fetch-summary
  python3 reg.py classify --product-code QVO
  python3 reg.py predicates --product-code QVO
  python3 reg.py cfr 45 164.308
  python3 reg.py fr-search --term "software as a medical device" --since 2024-01-01
  python3 reg.py trials --condition insomnia --intervention "cognitive behavioral therapy"
  python3 reg.py pubmed --term "digital CBT-I insomnia randomized"
  python3 reg.py guidance --topic ai
  python3 reg.py snapshot --out-dir snapshots
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

VERSION = "1.7.0"
SKILL_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = Path(os.environ.get("US_REG_CACHE", Path.home() / ".cache" / "us-sleep-regulatory"))
DEFAULT_TTL = int(os.environ.get("US_REG_CACHE_TTL", "86400"))
DEFAULT_JOBS = int(os.environ.get("US_REG_JOBS", "6"))
_HOST_LIMITS = {
    "www.ecfr.gov": 2,
    "api.fda.gov": 4,
    "www.federalregister.gov": 3,
    "clinicaltrials.gov": 3,
    "eutils.ncbi.nlm.nih.gov": 2,
    "www.accessdata.fda.gov": 2,
}
_HOST_SEMAPHORES: dict[str, threading.Semaphore] = {}
_HOST_SEM_LOCK = threading.Lock()
OPENFDA_KEY = os.environ.get("OPENFDA_API_KEY", "").strip()
NCBI_EMAIL = os.environ.get("NCBI_EMAIL", "").strip()

OPENFDA = "https://api.fda.gov"
ECFR = "https://www.ecfr.gov"
FR = "https://www.federalregister.gov/api/v1"
CTGOV = "https://clinicaltrials.gov/api/v2"
NCBI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = f"us-sleep-regulatory-skill/{VERSION}"

FR_AGENCIES = {
    "fda": "food-and-drug-administration",
    "hhs": "health-and-human-services-department",
    "ocr": "health-and-human-services-department",
    "ftc": "federal-trade-commission",
    "cms": "centers-for-medicare-medicaid-services",
    "onc": "national-coordinator-for-health-information-technology",
    "nih": "national-institutes-of-health",
}


class RegError(RuntimeError):
    pass


class ApiNotFound(RegError):
    pass


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# HTTP + cache
# ---------------------------------------------------------------------------

def _cache_key(url: str, params: dict | None) -> str:
    payload = url + "?" + urllib.parse.urlencode(params or {}, doseq=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache_path(key: str) -> Path:
    return CACHE_DIR / "http" / f"{key}.json"


def _cache_read(key: str, ttl: int) -> dict | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if ttl is not None and ttl > 0:
        age = time.time() - float(obj.get("fetched_at", 0))
        if age > ttl:
            return None
    return obj


def _cache_write(key: str, url: str, params: dict | None, body: Any) -> None:
    path = _cache_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        {"url": url, "params": params or {}, "fetched_at": time.time(), "body": body},
        ensure_ascii=False,
    )
    # Atomic replace: concurrent refreshes must never leave a half-written JSON
    # file for the next reader to trip over.
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


def _host_semaphore(host: str) -> threading.Semaphore:
    with _HOST_SEM_LOCK:
        semaphore = _HOST_SEMAPHORES.get(host)
        if semaphore is None:
            semaphore = threading.Semaphore(_HOST_LIMITS.get(host, 4))
            _HOST_SEMAPHORES[host] = semaphore
        return semaphore


def _request(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    retries: int = 3,
    timeout: int = 35,
) -> str:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json, text/xml, */*",
            "Accept-Encoding": "gzip",
            **(headers or {}),
        },
    )
    host = urllib.parse.urlparse(url).netloc
    last_error: Exception | None = None
    for attempt in range(retries):
        # Hold the per-host slot only for the request itself. Sleeping while
        # holding it would serialise every other thread of the same host
        # behind one 429.
        try:
            with _host_semaphore(host):
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = resp.read()
                    if resp.headers.get("Content-Encoding", "").lower() == "gzip":
                        data = gzip.decompress(data)
                    return data.decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            if exc.headers.get("Content-Encoding", "").lower() == "gzip":
                try:
                    raw = gzip.decompress(raw)
                except OSError:
                    pass
            text = raw.decode("utf-8", "replace")
            if exc.code == 404 and "NOT_FOUND" in text:
                raise ApiNotFound(f"No matches: {url}") from exc
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                last_error = exc
                if exc.code == 429:
                    retry_after = exc.headers.get("Retry-After")
                    try:
                        delay = max(1.0, float(retry_after))
                    except (TypeError, ValueError):
                        delay = 2.0 * (attempt + 1)
                else:
                    delay = 1.5 ** attempt
                time.sleep(delay)
                continue
            raise RegError(f"HTTP {exc.code} for {url}\n{text[:600]}") from exc
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(1.5 ** attempt)
                continue
            raise RegError(f"Network error for {url}: {exc.reason}") from exc
    raise RegError(f"Request failed for {url}: {last_error}")

def _get_json(
    url: str,
    params: dict | None = None,
    ttl: int = DEFAULT_TTL,
    use_cache: bool = True,
    cache_params: dict | None = None,
    headers: dict | None = None,
) -> tuple[Any, dict]:
    params = dict(params or {})
    key = _cache_key(url, cache_params if cache_params is not None else params)
    if use_cache and ttl > 0:
        cached = _cache_read(key, ttl)
        if cached:
            return cached["body"], {
                "cached": True,
                "cache_fetched_at": dt.datetime.fromtimestamp(
                    cached["fetched_at"], dt.timezone.utc
                ).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            }
    try:
        text = _request(url, params, headers=headers)
    except ApiNotFound:
        return {"results": [], "meta": {"not_found": True}}, {"cached": False, "not_found": True}
    try:
        body = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RegError(f"Expected JSON from {url}, got:\n{text[:400]}") from exc
    _cache_write(key, url, cache_params if cache_params is not None else params, body)
    return body, {"cached": False}


def _download(url: str, path: Path, timeout: int = 90) -> Path:
    """Download a binary file (PDF) without UTF-8 decoding."""
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/pdf", "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        if resp.headers.get("Content-Encoding", "").lower() == "gzip":
            data = gzip.decompress(data)
    if not data.startswith(b"%PDF"):
        raise RegError(f"Expected a PDF from {url}, got {len(data)} bytes starting {data[:20]!r}")
    path.write_bytes(data)
    return path


def _get_text(
    url: str,
    params: dict | None = None,
    ttl: int = DEFAULT_TTL,
    use_cache: bool = True,
    cache_params: dict | None = None,
) -> tuple[str, dict]:
    params = dict(params or {})
    key = _cache_key(url, cache_params if cache_params is not None else params)
    if use_cache and ttl > 0:
        cached = _cache_read(key, ttl)
        if cached and isinstance(cached.get("body"), dict) and "text" in cached["body"]:
            return cached["body"]["text"], {
                "cached": True,
                "cache_fetched_at": dt.datetime.fromtimestamp(
                    cached["fetched_at"], dt.timezone.utc
                ).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            }
    text = _request(url, params)
    _cache_write(key, url, cache_params if cache_params is not None else params, {"text": text})
    return text, {"cached": False}


def _meta(source: str, url: str, query: Any, cache: dict, **extra: Any) -> dict:
    meta = {
        "source": source,
        "url": url,
        "query": query,
        "retrieved_at": utcnow(),
        "cached": bool(cache.get("cached")),
        "disclaimer": "Public-source research aid, not legal advice. Verify against the current official text.",
    }
    if cache.get("cache_fetched_at"):
        meta["cache_fetched_at"] = cache["cache_fetched_at"]
    if cache.get("not_found"):
        meta["not_found"] = True
    meta.update(extra)
    return meta


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(value: Any) -> str:
        text = "" if value is None else str(value)
        return text.replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines += ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def _run_parallel(tasks: dict[str, Callable[[], Any]], jobs: int = DEFAULT_JOBS) -> tuple[dict[str, Any], dict[str, str]]:
    """Run independent I/O tasks concurrently and isolate failures.

    A bounded thread pool is the right primitive here: urllib is blocking, the
    workload is network-bound, and the project stays dependency-free. jobs=1
    gives a deterministic sequential run for debugging.
    """
    jobs = max(1, min(int(jobs or DEFAULT_JOBS), 12))
    results: dict[str, Any] = {}
    errors: dict[str, str] = {}
    if not tasks:
        return results, errors
    with ThreadPoolExecutor(max_workers=jobs, thread_name_prefix="reg-http") as pool:
        future_map = {pool.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(future_map):
            name = future_map[future]
            try:
                results[name] = future.result()
            except Exception as exc:  # noqa: BLE001
                errors[name] = str(exc)[:400]
    return results, errors


# ---------------------------------------------------------------------------
# openFDA
# ---------------------------------------------------------------------------

def _openfda_search_fields(record: dict) -> dict:
    openfda = record.get("openfda") or {}
    return {
        "regulation_number": openfda.get("regulation_number"),
        "device_class": openfda.get("device_class"),
        "medical_specialty": openfda.get("medical_specialty_description"),
        "device_name_classification": openfda.get("device_name"),
    }


def _pdf_year(k_number: str) -> int:
    yy = int(k_number[1:3])
    return 2000 + yy if yy < 90 else 1900 + yy


def _summary_pdf_url(k_number: str) -> str | None:
    if k_number.startswith("DEN"):
        return f"https://www.accessdata.fda.gov/cdrh_docs/reviews/{k_number}.pdf"
    if k_number.startswith("K") and len(k_number) >= 6:
        year = _pdf_year(k_number)
        return f"https://www.accessdata.fda.gov/cdrh_docs/pdf{year % 100:02d}/{k_number}.pdf"
    return None


def _fda_510k_url(k_number: str) -> str:
    return f"https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm?ID={k_number}"


def _normalize_510k(record: dict) -> dict:
    k_number = record.get("k_number", "")
    classification = _openfda_search_fields(record)
    return {
        "k_number": k_number,
        "device_name": record.get("device_name"),
        "applicant": record.get("applicant"),
        "product_code": record.get("product_code"),
        "decision_date": record.get("decision_date"),
        "decision_code": record.get("decision_code"),
        "decision_description": record.get("decision_description"),
        "clearance_type": record.get("clearance_type"),
        "statement_or_summary": record.get("statement_or_summary"),
        "advisory_committee": record.get("advisory_committee_description"),
        "regulation_number": classification.get("regulation_number"),
        "device_class": classification.get("device_class"),
        "is_de_novo": k_number.startswith("DEN"),
        "fda_url": _fda_510k_url(k_number),
        "summary_pdf_url": _summary_pdf_url(k_number),
    }


def fda_510k_search(
    query: str | None = None,
    product_code: str | None = None,
    applicant: str | None = None,
    k_number: str | None = None,
    decision_from: str | None = None,
    decision_to: str | None = None,
    raw_search: str | None = None,
    limit: int = 20,
    use_cache: bool = True,
    ttl: int = DEFAULT_TTL,
) -> dict:
    clauses: list[str] = []
    if raw_search:
        clauses.append(f"({raw_search})")
    if k_number:
        clauses.append(f'k_number:"{k_number}"')
    if product_code:
        clauses.append(f'product_code:"{product_code}"')
    if applicant:
        clauses.append(f'applicant:"{applicant}"')
    if query:
        clauses.append(f'device_name:"{query}"')
    if decision_from or decision_to:
        start = decision_from or "1900-01-01"
        end = decision_to or dt.date.today().isoformat()
        clauses.append(f"decision_date:[{start} TO {end}]")
    search = " AND ".join(clauses) or "_exists_:k_number"
    params: dict[str, Any] = {"search": search, "limit": max(1, min(int(limit), 100))}
    request_params = dict(params)
    if OPENFDA_KEY:
        request_params["api_key"] = OPENFDA_KEY
    body, cache = _get_json(
        f"{OPENFDA}/device/510k.json",
        request_params,
        ttl=ttl,
        use_cache=use_cache,
        cache_params=params,
    )
    results = [_normalize_510k(r) for r in body.get("results", [])]
    results.sort(key=lambda r: r.get("decision_date") or "", reverse=True)
    meta = _meta("openFDA device/510k", f"{OPENFDA}/device/510k.json", {"search": search}, cache)
    meta["openfda_last_updated"] = (body.get("meta") or {}).get("last_updated")
    meta["total"] = (body.get("meta") or {}).get("results", {}).get("total")
    out = {"_meta": meta, "results": results}
    if results:
        out["_md"] = _md_table(
            ["K/De Novo", "Device", "Applicant", "Product code", "Decision", "Class", "Reg"],
            [
                [
                    r["k_number"],
                    r["device_name"],
                    r["applicant"],
                    r["product_code"],
                    r["decision_date"],
                    r["device_class"],
                    r["regulation_number"],
                ]
                for r in results
            ],
        )
    return out


def _extract_pdf_text(path: Path) -> tuple[str | None, str]:
    if shutil.which("pdftotext"):
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout, "pdftotext"
        except (OSError, subprocess.SubprocessError):
            pass
    if shutil.which("mutool"):
        try:
            result = subprocess.run(
                ["mutool", "draw", "-F", "txt", str(path)],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout, "mutool"
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(str(path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        if text.strip():
            return text, "pypdf"
    except Exception:
        pass
    return None, "none"


def fda_510k_get(
    k_number: str,
    fetch_summary: bool = False,
    use_cache: bool = True,
    ttl: int = DEFAULT_TTL,
) -> dict:
    out = fda_510k_search(
        k_number=k_number,
        limit=1,
        use_cache=use_cache,
        ttl=ttl,
    )
    if not out["results"]:
        raise RegError(f"No 510(k)/De Novo record found for {k_number}")
    record = out["results"][0]
    out["results"] = record
    pdf_url = record.get("summary_pdf_url")
    record["summary_text"] = None
    if fetch_summary and pdf_url:
        pdf_path = CACHE_DIR / "pdfs" / f"{k_number}.pdf"
        if not pdf_path.exists():
            _download(pdf_url, pdf_path)
        record["summary_pdf_path"] = str(pdf_path)
        text, method = _extract_pdf_text(pdf_path)
        record["summary_text"] = (text or "")[:30000] if text else None
        record["summary_extraction_method"] = method
        if not text:
            record["summary_note"] = (
                "PDF downloaded but no text extractor is available. Read the PDF with the "
                "agent's file/PDF reader, or install poppler (pdftotext)."
            )
    if record.get("summary_text"):
        out["_md"] = (out.get("_md") or "") + (
            "\n\n### 510(k) summary excerpt\n\n```text\n"
            + record["summary_text"][:6000]
            + "\n```"
        )
    elif record.get("summary_pdf_path"):
        out["_md"] = (out.get("_md") or "") + (
            f"\n\nSummary PDF downloaded to `{record['summary_pdf_path']}`. "
            "Read it with the agent's PDF reader."
        )
    return out


def fda_classification(
    product_code: str | None = None,
    name: str | None = None,
    limit: int = 20,
    use_cache: bool = True,
    ttl: int = DEFAULT_TTL,
) -> dict:
    clauses = []
    if product_code:
        clauses.append(f'product_code:"{product_code}"')
    if name:
        clauses.append(f'device_name:"{name}"')
    search = " AND ".join(clauses) or "_exists_:product_code"
    params: dict[str, Any] = {"search": search, "limit": max(1, min(int(limit), 100))}
    request_params = dict(params)
    if OPENFDA_KEY:
        request_params["api_key"] = OPENFDA_KEY
    body, cache = _get_json(
        f"{OPENFDA}/device/classification.json",
        request_params,
        ttl=ttl,
        use_cache=use_cache,
        cache_params=params,
    )
    results = []
    for r in body.get("results", []):
        reg = r.get("regulation_number")
        results.append(
            {
                "product_code": r.get("product_code"),
                "device_name": r.get("device_name"),
                "device_class": r.get("device_class"),
                "regulation_number": reg,
                "submission_type_id": r.get("submission_type_id"),
                "gmp_exempt_flag": r.get("gmp_exempt_flag"),
                "third_party_flag": r.get("third_party_flag"),
                "summary_malfunction_reporting": r.get("summary_malfunction_reporting"),
                "cfr_url": f"https://www.ecfr.gov/current/title-21/section-{reg}" if reg else None,
                "fda_url": (
                    "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPCD/classification.cfm?ID="
                    + str(r.get("product_code"))
                ),
            }
        )
    meta = _meta("openFDA device/classification", f"{OPENFDA}/device/classification.json", {"search": search}, cache)
    meta["openfda_last_updated"] = (body.get("meta") or {}).get("last_updated")
    meta["total"] = (body.get("meta") or {}).get("results", {}).get("total")
    out = {"_meta": meta, "results": results}
    if results:
        out["_md"] = _md_table(
            ["Product code", "Device", "Class", "21 CFR", "GMP exempt"],
            [[r["product_code"], r["device_name"], r["device_class"], r["regulation_number"], r["gmp_exempt_flag"]] for r in results],
        )
    return out


def fda_predicates(product_code: str, limit: int = 100, use_cache: bool = True, ttl: int = DEFAULT_TTL) -> dict:
    classification = fda_classification(product_code=product_code, limit=10, use_cache=use_cache, ttl=ttl)
    clearances = fda_510k_search(product_code=product_code, limit=limit, use_cache=use_cache, ttl=ttl)
    results = clearances.get("results", [])
    latest = results[0] if results else None
    notes = [
        "openFDA is a convenience copy. Confirm the current decision and summary on accessdata.fda.gov.",
        "A predicate is usable only for the same intended use and similar technological characteristics; a cleared device is not automatically a valid predicate for your claims.",
        "The product-code name, the CFR heading, and the predicate's cleared intended use can differ. Read all three before relying on a code.",
    ]
    cfr: dict[str, Any] = {}
    reg_numbers = {
        r.get("regulation_number")
        for r in classification.get("results", [])
        if r.get("regulation_number")
    }
    for reg in sorted(reg_numbers):
        try:
            doc = ecfr_get("21", section=reg, use_cache=use_cache, ttl=ttl)
            cfr[reg] = {
                "heading": doc.get("heading"),
                "url": doc.get("human_url"),
                "excerpt": (doc.get("text") or "")[:1600],
            }
            heading = (doc.get("heading") or "").lower()
            if "sleep" not in heading and "insomnia" not in heading:
                notes.append(
                    f"21 CFR {reg} is titled '{doc.get('heading')}'. That heading may not match the "
                    "product-code name; read the regulation text and the predicate's cleared intended use."
                )
        except RegError as exc:
            cfr[reg] = {"error": str(exc)}
    if product_code == "QVO":
        notes.append(
            "QVO is Class II, prescription-only, and the regulation describes an adjunct to clinician-supervised "
            "outpatient treatment. A direct-to-consumer, non-prescription model conflicts with that labeling."
        )
    out = {
        "_meta": {
            **clearances["_meta"],
            "source": "openFDA device/510k + device/classification + eCFR",
            "product_code": product_code,
        },
        "product_code": product_code,
        "classification": classification.get("results", []),
        "classification_meta": classification.get("_meta"),
        "cfr": cfr,
        "count": len(results),
        "latest": latest,
        "clearances": results,
        "notes": notes,
    }
    if results:
        out["_md"] = (
            f"**Product code {product_code}** — {len(results)} clearance(s) in openFDA\n\n"
            + _md_table(
                ["K/De Novo", "Device", "Applicant", "Decision", "Type", "Summary"],
                [
                    [
                        r["k_number"],
                        r["device_name"],
                        r["applicant"],
                        r["decision_date"],
                        r["clearance_type"],
                        "PDF" if r.get("summary_pdf_url") else "",
                    ]
                    for r in results
                ],
            )
            + "\n\n"
            + "\n".join(f"- {n}" for n in notes)
        )
    return out


# ---------------------------------------------------------------------------
# eCFR
# ---------------------------------------------------------------------------

def _ecfr_current_date(title: str, use_cache: bool = True) -> str:
    body, _ = _get_json(f"{ECFR}/api/versioner/v1/titles.json", {}, ttl=3600, use_cache=use_cache)
    for item in body.get("titles", []):
        if str(item.get("number")) == str(title):
            return item.get("up_to_date_as_of") or dt.date.today().isoformat()
    return dt.date.today().isoformat()


def _xml_to_text(root: ET.Element) -> str:
    lines: list[str] = []
    for element in root.iter():
        if element.tag in {"HEAD", "P", "FP", "NOTE", "CITA"}:
            text = _clean("".join(element.itertext()))
            if text:
                lines.append(text)
    return "\n".join(lines)


def ecfr_get(
    title: str,
    section: str | None = None,
    part: str | None = None,
    date: str | None = None,
    use_cache: bool = True,
    ttl: int = DEFAULT_TTL,
) -> dict:
    if section and not part:
        part = section.split(".")[0]
    if not part:
        raise RegError("Provide a section (e.g. 164.308) or a part (e.g. 820).")
    as_of = date or _ecfr_current_date(title, use_cache=use_cache)
    params = {"part": part}
    if section:
        params["section"] = section
    api_url = f"{ECFR}/api/versioner/v1/full/{as_of}/title-{title}.xml"
    xml_text, cache = _get_text(api_url, params, ttl=ttl, use_cache=use_cache)
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise RegError(f"Could not parse eCFR XML for {title} CFR {section or part}") from exc
    heading = ""
    for element in root.iter("HEAD"):
        heading = _clean("".join(element.itertext()))
        break
    body = _xml_to_text(root)
    citation = f"{title} CFR {section}" if section else f"{title} CFR Part {part}"
    human_url = (
        f"https://www.ecfr.gov/current/title-{title}/section-{section}"
        if section
        else f"https://www.ecfr.gov/current/title-{title}/part-{part}"
    )
    out = {
        "_meta": _meta(
            "eCFR",
            api_url,
            params,
            cache,
            as_of=as_of,
            note="eCFR is the official codification; the API 'as_of' date is reported.",
        ),
        "citation": citation,
        "heading": heading,
        "text": body,
        "char_count": len(body),
        "human_url": human_url,
    }
    out["_md"] = f"### {citation} — {heading}\n\n```text\n{body[:8000]}\n```"
    return out


def ecfr_search(query: str, title: str | None = None, limit: int = 10, use_cache: bool = True, ttl: int = DEFAULT_TTL) -> dict:
    params: dict[str, Any] = {"query": query, "per_page": max(1, min(int(limit), 50))}
    if title:
        params["hierarchy_title"] = title
    body, cache = _get_json(f"{ECFR}/api/search/v1/results", params, ttl=ttl, use_cache=use_cache)
    results = []
    for r in body.get("results", []):
        h = r.get("hierarchy") or {}
        results.append(
            {
                "title": h.get("title"),
                "part": h.get("part"),
                "section": h.get("section"),
                "citation": f"{h.get('title')} CFR {h.get('section') or h.get('part')}",
                "headings": r.get("headings"),
                "url": f"https://www.ecfr.gov/current/title-{h.get('title')}/section-{h.get('section')}"
                if h.get("section")
                else None,
            }
        )
    return {
        "_meta": _meta("eCFR search", f"{ECFR}/api/search/v1/results", params, cache),
        "results": results,
    }


# ---------------------------------------------------------------------------
# Federal Register
# ---------------------------------------------------------------------------

def fr_search(
    term: str | None = None,
    agency: str = "fda",
    doc_type: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 20,
    use_cache: bool = True,
    ttl: int = 3600,
) -> dict:
    agency_slug = FR_AGENCIES.get(agency.lower(), agency)
    params: dict[str, Any] = {
        "per_page": max(1, min(int(limit), 100)),
        "order": "newest",
        "fields[]": [
            "title",
            "type",
            "publication_date",
            "citation",
            "document_number",
            "html_url",
            "abstract",
            "docket_ids",
            "agencies",
        ],
    }
    if term:
        params["conditions[term]"] = term
    if agency_slug:
        params["conditions[agencies][]"] = agency_slug
    if doc_type:
        mapping = {"rule": "RULE", "proposed": "PRORULE", "notice": "NOTICE", "presidential": "PRESDOCU"}
        params["conditions[type][]"] = mapping.get(doc_type.lower(), doc_type.upper())
    if since:
        params["conditions[publication_date][gte]"] = since
    if until:
        params["conditions[publication_date][lte]"] = until
    body, cache = _get_json(f"{FR}/documents.json", params, ttl=ttl, use_cache=use_cache)
    results = []
    for r in body.get("results", []):
        dockets = r.get("docket_ids") or []
        if dockets and isinstance(dockets[0], dict):
            dockets = [d.get("id") for d in dockets if d.get("id")]
        results.append(
            {
                "document_number": r.get("document_number"),
                "title": r.get("title"),
                "type": r.get("type"),
                "publication_date": r.get("publication_date"),
                "citation": r.get("citation"),
                "docket_ids": dockets,
                "agencies": [a.get("name") for a in (r.get("agencies") or [])],
                "html_url": r.get("html_url"),
                "abstract": r.get("abstract"),
            }
        )
    meta = _meta("Federal Register API", f"{FR}/documents.json", params, cache)
    meta["total"] = body.get("count")
    out = {"_meta": meta, "results": results}
    if results:
        out["_md"] = _md_table(
            ["Date", "Type", "Citation", "Title", "Document"],
            [[r["publication_date"], r["type"], r["citation"], r["title"], r["document_number"]] for r in results],
        )
    return out


def fr_get(document_number: str, use_cache: bool = True, ttl: int = 86400) -> dict:
    body, cache = _get_json(f"{FR}/documents/{document_number}.json", {}, ttl=ttl, use_cache=use_cache)
    return {
        "_meta": _meta("Federal Register API", f"{FR}/documents/{document_number}.json", {}, cache),
        "document": body,
    }


# ---------------------------------------------------------------------------
# ClinicalTrials.gov + PubMed
# ---------------------------------------------------------------------------

def trials_search(
    condition: str | None = None,
    intervention: str | None = None,
    term: str | None = None,
    status: str | None = None,
    limit: int = 20,
    use_cache: bool = True,
    ttl: int = 86400,
) -> dict:
    params: dict[str, Any] = {
        "pageSize": max(1, min(int(limit), 100)),
        "fields": (
            "NCTId,BriefTitle,OverallStatus,Phase,EnrollmentCount,StartDate,"
            "LeadSponsorName,Condition,InterventionName,PrimaryOutcomeMeasure"
        ),
    }
    if condition:
        params["query.cond"] = condition
    if intervention:
        params["query.intr"] = intervention
    if term:
        params["query.term"] = term
    if status:
        params["filter.overallStatus"] = status
    body, cache = _get_json(f"{CTGOV}/studies", params, ttl=ttl, use_cache=use_cache)
    results = []
    for study in body.get("studies", []):
        p = study.get("protocolSection") or {}
        ident = p.get("identificationModule") or {}
        status_mod = p.get("statusModule") or {}
        design = p.get("designModule") or {}
        sponsor = p.get("sponsorCollaboratorsModule") or {}
        conditions_mod = p.get("conditionsModule") or {}
        arms = p.get("armsInterventionsModule") or {}
        outcomes = p.get("outcomesModule") or {}
        nct = ident.get("nctId")
        results.append(
            {
                "nct_id": nct,
                "title": ident.get("briefTitle"),
                "status": status_mod.get("overallStatus"),
                "phase": design.get("phases"),
                "enrollment": (design.get("enrollmentInfo") or {}).get("count"),
                "start_date": (status_mod.get("startDateStruct") or {}).get("date"),
                "sponsor": (sponsor.get("leadSponsor") or {}).get("name"),
                "conditions": conditions_mod.get("conditions"),
                "interventions": [i.get("name") for i in (arms.get("interventions") or [])],
                "primary_outcomes": [o.get("measure") for o in (outcomes.get("primaryOutcomes") or [])],
                "url": f"https://clinicaltrials.gov/study/{nct}" if nct else None,
            }
        )
    meta = _meta("ClinicalTrials.gov API v2", f"{CTGOV}/studies", params, cache)
    out = {"_meta": meta, "results": results}
    if results:
        out["_md"] = _md_table(
            ["NCT", "Title", "Status", "Phase", "N", "Start", "Sponsor"],
            [
                [r["nct_id"], r["title"], r["status"], ",".join(r["phase"] or []), r["enrollment"], r["start_date"], r["sponsor"]]
                for r in results
            ],
        )
    return out


def pubmed_search(term: str, limit: int = 10, sort: str = "relevance", use_cache: bool = True, ttl: int = 86400) -> dict:
    params: dict[str, Any] = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": max(1, min(int(limit), 100)),
        "sort": sort,
        "tool": "us-sleep-regulatory-skill",
    }
    if NCBI_EMAIL:
        params["email"] = NCBI_EMAIL
    search, cache1 = _get_json(f"{NCBI}/esearch.fcgi", params, ttl=ttl, use_cache=use_cache)
    ids = (search.get("esearchresult") or {}).get("idlist") or []
    if not ids:
        return {
            "_meta": _meta("PubMed E-utilities", f"{NCBI}/esearch.fcgi", params, cache1),
            "count": 0,
            "results": [],
        }
    summary_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "json",
        "tool": "us-sleep-regulatory-skill",
    }
    if NCBI_EMAIL:
        summary_params["email"] = NCBI_EMAIL
    summary, cache2 = _get_json(f"{NCBI}/esummary.fcgi", summary_params, ttl=ttl, use_cache=use_cache)
    result_map = summary.get("result") or {}
    results = []
    for pmid in result_map.get("uids", ids):
        item = result_map.get(pmid) or {}
        authors = [a.get("name") for a in (item.get("authors") or [])][:3]
        doi = next((a.get("value") for a in (item.get("articleids") or []) if a.get("idtype") == "doi"), None)
        results.append(
            {
                "pmid": pmid,
                "title": item.get("title"),
                "journal": item.get("fulljournalname") or item.get("source"),
                "pubdate": item.get("pubdate"),
                "authors": authors,
                "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
        )
    meta = _meta("PubMed E-utilities", f"{NCBI}/esearch.fcgi", params, cache1)
    meta["count"] = (search.get("esearchresult") or {}).get("count")
    out = {"_meta": meta, "results": results}
    if results:
        out["_md"] = _md_table(
            ["PMID", "Title", "Journal", "Date"],
            [[r["pmid"], r["title"], r["journal"], r["pubdate"]] for r in results],
        )
    return out


# ---------------------------------------------------------------------------
# Local guidance registry
# ---------------------------------------------------------------------------

def load_guidance() -> list[dict]:
    path = SKILL_DIR / "references" / "guidance-registry.json"
    if not path.exists():
        raise RegError(f"Guidance registry not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("entries", data if isinstance(data, list) else [])


def _registry_verification(entries: list[dict]) -> dict[str, Any]:
    """Describe how the registry was verified.

    A registry where most entries share one `last_verified` date has a bulk
    bump, not per-entry verification. Surfacing that keeps the stale flag from
    claiming more than it can support (SKILL.md rule 6).
    """
    dates = [str(entry.get("last_verified")) for entry in entries if entry.get("last_verified")]
    if not dates:
        return {"mode": "unknown", "entries": len(entries)}
    counts: dict[str, int] = {}
    for value in dates:
        counts[value] = counts.get(value, 0) + 1
    dominant_date, count = max(counts.items(), key=lambda item: item[1])
    share = count / len(entries)
    evidenced = sum(1 for entry in entries if str(entry.get("verified_via") or "").strip())
    evidence_coverage = evidenced / len(entries)
    if share < 0.8 or len(entries) < 6:
        mode = "per-entry"
    elif evidence_coverage >= 0.9:
        # Same-day verification, but every entry records what the page said.
        mode = "bulk-evidenced"
    else:
        mode = "bulk"
    return {
        "mode": mode,
        "dominant_date": dominant_date,
        "share": round(share, 3),
        "evidence_coverage": round(evidence_coverage, 3),
        "entries": len(entries),
    }


def guidance_search(
    query: str | None = None,
    topic: str | None = None,
    status: str | None = None,
    max_age_days: int = 120,
) -> dict:
    registry = load_guidance()
    entries = []
    today = dt.date.today()
    for entry in registry:
        haystack = " ".join(
            str(entry.get(k, ""))
            for k in ("id", "title", "notes", "status", "docket", "topics")
        ).lower()
        if query and query.lower() not in haystack:
            continue
        if topic and topic.lower() not in [t.lower() for t in entry.get("topics", [])]:
            continue
        if status and status.lower() != str(entry.get("status", "")).lower():
            continue
        item = dict(entry)
        try:
            verified = dt.date.fromisoformat(entry.get("last_verified", ""))
            item["age_days"] = (today - verified).days
            item["stale"] = item["age_days"] > max_age_days
        except ValueError:
            item["age_days"] = None
            item["stale"] = True
        entries.append(item)
    verification = _registry_verification(registry)
    note = "Local index only. Re-verify status/date on the FDA page before relying on an entry."
    if verification["mode"] == "bulk":
        note += (
            f" Verification is bulk ({verification['share']:.0%} of entries share "
            f"last_verified={verification['dominant_date']} without per-entry evidence); "
            "the stale flag is not verification."
        )
    elif verification["mode"] == "bulk-evidenced":
        note += (
            f" All entries were checked on {verification['dominant_date']}; "
            "verified_via records the page evidence for each."
        )
    out = {
        "_meta": {
            "source": "Curated guidance registry (local)",
            "url": str(SKILL_DIR / "references" / "guidance-registry.json"),
            "retrieved_at": utcnow(),
            "note": note,
            "stale_threshold_days": max_age_days,
            "verification": verification,
        },
        "count": len(entries),
        "results": entries,
    }
    if entries:
        out["_md"] = _md_table(
            ["ID", "Status", "Issued", "Title", "Verified", "Stale"],
            [[e.get("id"), e.get("status"), e.get("issued"), e.get("title"), e.get("last_verified"), e.get("stale")] for e in entries],
        )
    return out


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------

def build_snapshot(
    product_codes: list[str] | None = None,
    query: str = "insomnia",
    out_dir: str | Path = "snapshots",
    use_cache: bool = True,
    jobs: int = DEFAULT_JOBS,
) -> dict:
    product_codes = product_codes or ["QVO", "QMZ", "LEL"]
    bundle: dict[str, Any] = {
        "_meta": {
            "generated_at": utcnow(),
            "product_codes": product_codes,
            "query": query,
            "tool_version": VERSION,
            "jobs": jobs,
            "note": "OpenFDA data is a convenience copy; eCFR is official; FDA guidance is nonbinding.",
        },
        "classifications": {},
        "predicates": {},
        "cfr": {},
        "guidance": None,
        "federal_register": {},
        "clinical_trials": None,
        "pubmed": None,
    }

    cfr_refs = [
        ("21", "882.5801"),
        ("21", "882.5705"),
        ("21", "882.5050"),
        ("21", "820.1"),
        ("45", "164.308"),
        ("45", "164.402"),
    ]
    tasks: dict[str, Callable[[], Any]] = {}
    for code in product_codes:
        tasks[f"predicates:{code}"] = lambda code=code: fda_predicates(
            product_code=code, use_cache=use_cache
        )
    for title, section in cfr_refs:
        tasks[f"cfr:{title}:{section}"] = lambda title=title, section=section: ecfr_get(
            title, section=section, use_cache=use_cache
        )
    tasks["guidance"] = lambda: guidance_search(topic=None, max_age_days=365)
    tasks["fr:samd"] = lambda: fr_search(
        term='"software as a medical device"',
        agency="fda",
        since="2024-01-01",
        limit=20,
        use_cache=use_cache,
    )
    tasks["fr:ai"] = lambda: fr_search(
        term='"artificial intelligence"',
        agency="fda",
        since="2024-01-01",
        limit=20,
        use_cache=use_cache,
    )
    tasks["trials"] = lambda: trials_search(
        condition=query,
        intervention="cognitive behavioral therapy",
        limit=20,
        use_cache=use_cache,
    )
    tasks["pubmed"] = lambda: pubmed_search(
        term=f"digital cognitive behavioral therapy {query} randomized",
        limit=20,
        use_cache=use_cache,
    )

    results, errors = _run_parallel(tasks, jobs=jobs)

    for code in product_codes:
        key = f"predicates:{code}"
        data = results.get(key)
        if data:
            bundle["predicates"][code] = data
            bundle["classifications"][code] = {
                "_meta": data.get("classification_meta") or data["_meta"],
                "results": data.get("classification", []),
            }
        else:
            error = errors.get(key, "unknown error")
            bundle["predicates"][code] = {"_error": error}
            bundle["classifications"][code] = {"_error": error}

    for title, section in cfr_refs:
        key = f"cfr:{title}:{section}"
        label = f"{title} CFR {section}"
        bundle["cfr"][label] = results.get(key) or {"_error": errors.get(key, "unknown error")}

    bundle["guidance"] = results.get("guidance") or {"_error": errors.get("guidance", "unknown error")}
    bundle["federal_register"]["samd"] = results.get("fr:samd") or {"_error": errors.get("fr:samd", "unknown error")}
    bundle["federal_register"]["ai"] = results.get("fr:ai") or {"_error": errors.get("fr:ai", "unknown error")}
    bundle["clinical_trials"] = results.get("trials") or {"_error": errors.get("trials", "unknown error")}
    bundle["pubmed"] = results.get("pubmed") or {"_error": errors.get("pubmed", "unknown error")}

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    stamp = dt.date.today().isoformat()
    json_path = out_path / f"{stamp}-regulatory-snapshot.json"
    md_path = out_path / f"{stamp}-regulatory-snapshot.md"
    json_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# Regulatory snapshot — {stamp}",
        "",
        f"Generated: {bundle['_meta']['generated_at']}  ",
        f"Product codes: {', '.join(product_codes)}  ",
        f"Query: `{query}`",
        "",
        "> Public-source research aid, not legal advice. openFDA is a convenience copy; eCFR is official. FDA guidance is nonbinding.",
        "",
        "## Device classification",
        "",
    ]
    for code, data in bundle["classifications"].items():
        if data.get("_error"):
            lines.append(f"- **{code}**: ERROR — {data['_error']}")
            continue
        for r in data.get("results", []):
            lines.append(
                f"- **{code}** — {r['device_name']} · Class {r['device_class']} · 21 CFR {r['regulation_number']}"
            )
    lines += ["", "## Predicate landscape", ""]
    for code, data in bundle["predicates"].items():
        if data.get("_error"):
            lines.append(f"- **{code}**: ERROR — {data['_error']}")
            continue
        lines.append(f"### {code} ({data.get('count', 0)} clearances)")
        for r in data.get("clearances", []):
            lines.append(
                f"- `{r['k_number']}` {r['device_name']} — {r['applicant']} ({r['decision_date']})"
            )
        lines.append("")
    lines += ["## Codified rules (eCFR)", ""]
    for key, data in bundle["cfr"].items():
        if data.get("_error"):
            lines.append(f"- **{key}**: ERROR — {data['_error']}")
        else:
            lines.append(f"- **{key}** — {data.get('heading', '')} ([eCFR]({data.get('human_url')}))")
    lines.append("")
    lines.append(
        "> If a CFR heading does not match the classification name, the product-code mapping may be legacy. "
        "Read the regulation text and the predicate's cleared intended use before relying on it."
    )
    lines += ["", "## Guidance registry", ""]
    g = bundle["guidance"] or {}
    for e in (g.get("results") or [])[:40]:
        flag = " ⚠️ stale" if e.get("stale") else ""
        lines.append(f"- **{e.get('status')}** — {e.get('title')} ({e.get('issued')}){flag}")
    lines += ["", "## Recent Federal Register documents", ""]
    for bucket, data in bundle["federal_register"].items():
        lines.append(f"### {bucket}")
        for r in (data.get("results") or [])[:10]:
            lines.append(f"- {r.get('publication_date')} · {r.get('title')} ({r.get('citation')})")
        lines.append("")
    lines += ["## Clinical trials", ""]
    for r in ((bundle["clinical_trials"] or {}).get("results") or [])[:15]:
        lines.append(f"- `{r.get('nct_id')}` {r.get('title')} — {r.get('status')} ({r.get('start_date')})")
    lines += ["", "## PubMed", ""]
    for r in ((bundle["pubmed"] or {}).get("results") or [])[:15]:
        lines.append(f"- PMID {r.get('pmid')} — {r.get('title')} ({r.get('journal')}, {r.get('pubdate')})")
    lines += [
        "",
        "## Machine-readable bundle",
        "",
        f"`{json_path}`",
        "",
        "Every section in the JSON retains its own `_meta.url`, `_meta.retrieved_at`, and `_meta.cached`.",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "_meta": {"generated_at": bundle["_meta"]["generated_at"], "tool_version": VERSION, "jobs": jobs},
        "json": str(json_path),
        "markdown": str(md_path),
        "sections": {k: _section_status(v) for k, v in bundle.items() if k != "_meta"},
    }


def _section_status(value: Any) -> str:
    if isinstance(value, dict):
        if value.get("_error"):
            return "error"
        nested = [item for item in value.values() if isinstance(item, dict)]
        if nested and all(item.get("_error") for item in nested):
            return "error"
    return "ok"


# ---------------------------------------------------------------------------
# Local knowledge base (SQLite + FTS5)
# ---------------------------------------------------------------------------

KB_SCHEMA_VERSION = "1"
KB_DEFAULT_TTL_DAYS = 90

KB_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    citation TEXT,
    url TEXT,
    retrieved_at TEXT NOT NULL,
    as_of TEXT,
    status TEXT,
    tags TEXT,
    text TEXT NOT NULL,
    metadata TEXT,
    sha256 TEXT NOT NULL,
    ttl_days INTEGER
);

CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_retrieved ON documents(retrieved_at);

CREATE TABLE IF NOT EXISTS sources (
    name TEXT PRIMARY KEY,
    last_refresh TEXT,
    last_status TEXT,
    detail TEXT
);
"""

KB_FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title,
    citation,
    text,
    tags,
    content='documents',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, title, citation, text, tags)
    VALUES (new.rowid, new.title, new.citation, new.text, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, citation, text, tags)
    VALUES ('delete', old.rowid, old.title, old.citation, old.text, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, citation, text, tags)
    VALUES ('delete', old.rowid, old.title, old.citation, old.text, old.tags);
    INSERT INTO documents_fts(rowid, title, citation, text, tags)
    VALUES (new.rowid, new.title, new.citation, new.text, new.tags);
END;
"""


def kb_path() -> Path:
    """Return the local knowledge-base path (US_REG_KB overrides it)."""
    return Path(os.environ.get("US_REG_KB", str(CACHE_DIR / "kb.sqlite"))).expanduser()


def _kb_meta_get(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def _kb_meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )


def _kb_fts_enabled(conn: sqlite3.Connection) -> bool:
    return _kb_meta_get(conn, "fts") == "1"


def _kb_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(KB_SCHEMA)
    try:
        conn.executescript(KB_FTS_SCHEMA)
        _kb_meta_set(conn, "fts", "1")
    except sqlite3.OperationalError:
        # SQLite built without FTS5: search falls back to LIKE.
        _kb_meta_set(conn, "fts", "0")
    _kb_meta_set(conn, "schema_version", KB_SCHEMA_VERSION)
    conn.commit()


def _kb_split_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    meta: dict[str, str] = {}
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    meta[key.strip().lower()] = value.strip().strip('"').strip("'")
            body = parts[2].lstrip("\n")
    return meta, body


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _kb_upsert(conn: sqlite3.Connection, doc: dict[str, Any]) -> str:
    text = doc.get("text") or ""
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    existing = conn.execute("SELECT sha256 FROM documents WHERE id = ?", (doc["id"],)).fetchone()
    if existing and existing["sha256"] == sha:
        return "unchanged"
    conn.execute(
        """
        INSERT INTO documents
            (id, source, source_type, title, citation, url, retrieved_at, as_of,
             status, tags, text, metadata, sha256, ttl_days)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            source = excluded.source,
            source_type = excluded.source_type,
            title = excluded.title,
            citation = excluded.citation,
            url = excluded.url,
            retrieved_at = excluded.retrieved_at,
            as_of = excluded.as_of,
            status = excluded.status,
            tags = excluded.tags,
            text = excluded.text,
            metadata = excluded.metadata,
            sha256 = excluded.sha256,
            ttl_days = excluded.ttl_days
        """,
        (
            doc["id"],
            doc.get("source") or "local",
            doc.get("source_type") or "internal",
            doc.get("title") or doc["id"],
            doc.get("citation"),
            doc.get("url"),
            doc.get("retrieved_at") or utcnow(),
            doc.get("as_of"),
            doc.get("status") or "internal",
            doc.get("tags") or "",
            text,
            json.dumps(doc.get("metadata") or {}, ensure_ascii=False),
            sha,
            doc.get("ttl_days"),
        ),
    )
    return "updated" if existing else "inserted"


def _kb_ingest_markdown_file(
    conn: sqlite3.Connection,
    path: Path,
    *,
    source: str,
    source_type: str,
    status: str,
    tags: str,
    ttl_days: int,
    id_prefix: str,
) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    meta, body = _kb_split_frontmatter(raw)
    title = meta.get("title") or _first_heading(body) or path.stem
    doc_id = meta.get("id") or f"{id_prefix}:{path.stem}"
    try:
        mtime = dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).replace(microsecond=0)
        file_time = mtime.isoformat().replace("+00:00", "Z")
    except OSError:
        file_time = utcnow()
    merged_tags = ",".join(t for t in [tags, meta.get("tags", "")] if t)
    ttl = ttl_days
    try:
        if meta.get("ttl_days"):
            ttl = int(meta["ttl_days"])
    except ValueError:
        pass
    return _kb_upsert(
        conn,
        {
            "id": doc_id,
            "source": meta.get("source") or source,
            "source_type": meta.get("source_type") or source_type,
            "title": title,
            "citation": meta.get("citation"),
            "url": meta.get("url"),
            "retrieved_at": meta.get("retrieved_at") or file_time,
            "as_of": meta.get("as_of"),
            "status": meta.get("status") or status,
            "tags": merged_tags,
            "text": body.strip(),
            "metadata": {"path": str(path)},
            "ttl_days": ttl,
        },
    )


def _kb_ingest_local(conn: sqlite3.Connection) -> dict[str, int]:
    counts = {"inserted": 0, "updated": 0, "unchanged": 0}

    def bump(result: str) -> None:
        counts[result] = counts.get(result, 0) + 1

    refs_dir = SKILL_DIR / "references"
    if refs_dir.exists():
        for path in sorted(refs_dir.glob("*.md")):
            bump(
                _kb_ingest_markdown_file(
                    conn,
                    path,
                    source="local-references",
                    source_type="internal",
                    status="internal",
                    tags="internal,playbook",
                    ttl_days=365,
                    id_prefix="internal",
                )
            )

    try:
        for entry in load_guidance():
            topics = entry.get("topics") or []
            if isinstance(topics, str):
                topics = [topics]
            text = "\n".join(
                [
                    entry.get("title", ""),
                    "",
                    f"Status: {entry.get('status', '')}",
                    f"Issued: {entry.get('issued', '')}",
                    f"Docket: {entry.get('docket') or 'n/a'}",
                    f"Topics: {', '.join(topics)}",
                    f"Notes: {entry.get('notes', '')}",
                ]
            )
            bump(
                _kb_upsert(
                    conn,
                    {
                        "id": f"guidance:{entry.get('id')}",
                        "source": "curated-guidance-registry",
                        "source_type": "guidance",
                        "title": entry.get("title") or entry.get("id"),
                        "citation": entry.get("docket"),
                        "url": entry.get("url"),
                        "retrieved_at": entry.get("last_verified") or utcnow(),
                        "as_of": entry.get("issued"),
                        "status": entry.get("status") or "guidance",
                        "tags": ",".join(["guidance"] + topics),
                        "text": text,
                        "metadata": {"registry_id": entry.get("id")},
                        "ttl_days": 30,
                    },
                )
            )
    except RegError:
        pass

    seed_dir = SKILL_DIR / "knowledge" / "seed"
    if seed_dir.exists():
        for path in sorted(seed_dir.glob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            bump(
                _kb_ingest_markdown_file(
                    conn,
                    path,
                    source="local-seed",
                    source_type="internal",
                    status="internal",
                    tags="seed",
                    ttl_days=KB_DEFAULT_TTL_DAYS,
                    id_prefix="seed",
                )
            )

    conn.commit()
    return counts


def _kb_init_conn(conn: sqlite3.Connection) -> dict[str, int]:
    counts = _kb_ingest_local(conn)
    _kb_meta_set(conn, "initialized", "1")
    _kb_meta_set(conn, "last_init", utcnow())
    _kb_meta_set(conn, "schema_version", KB_SCHEMA_VERSION)
    conn.commit()
    return counts


def _kb_connect(auto_init: bool = True) -> sqlite3.Connection:
    path = kb_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    _kb_schema(conn)
    if auto_init and not _kb_meta_get(conn, "initialized"):
        _kb_init_conn(conn)
    return conn


def _kb_age_days(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        value = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt.timezone.utc)
        return max(0, (dt.datetime.now(dt.timezone.utc) - value).days)
    except (ValueError, TypeError):
        return None


def _kb_stats_conn(conn: sqlite3.Connection) -> dict[str, Any]:
    by_type = {
        row["source_type"]: row["n"]
        for row in conn.execute("SELECT source_type, count(*) AS n FROM documents GROUP BY source_type")
    }
    by_status = {
        row["status"]: row["n"]
        for row in conn.execute("SELECT status, count(*) AS n FROM documents GROUP BY status")
    }
    total = conn.execute("SELECT count(*) AS n FROM documents").fetchone()["n"]
    sources = [dict(row) for row in conn.execute("SELECT * FROM sources ORDER BY name")]
    stale_rows = []
    oldest = None
    newest = None
    for row in conn.execute("SELECT id, title, source, retrieved_at, ttl_days FROM documents"):
        age = _kb_age_days(row["retrieved_at"])
        if age is not None:
            if oldest is None or age > oldest[0]:
                oldest = (age, row["id"], row["retrieved_at"])
            if newest is None or age < newest[0]:
                newest = (age, row["id"], row["retrieved_at"])
            ttl = row["ttl_days"] or KB_DEFAULT_TTL_DAYS
            if age > ttl:
                stale_rows.append({"id": row["id"], "title": row["title"], "source": row["source"], "age_days": age, "ttl_days": ttl})
    return {
        "documents": total,
        "by_source_type": by_type,
        "by_status": by_status,
        "sources": sources,
        "stale_count": len(stale_rows),
        "stale": sorted(stale_rows, key=lambda r: r["age_days"], reverse=True)[:20],
        "oldest": {"age_days": oldest[0], "id": oldest[1], "retrieved_at": oldest[2]} if oldest else None,
        "newest": {"age_days": newest[0], "id": newest[1], "retrieved_at": newest[2]} if newest else None,
        "last_init": _kb_meta_get(conn, "last_init"),
        "last_refresh": _kb_meta_get(conn, "last_refresh"),
        "fts": _kb_fts_enabled(conn),
    }


def kb_init(force: bool = False) -> dict:
    conn = _kb_connect(auto_init=False)
    if force:
        conn.execute("DELETE FROM documents")
        conn.execute("DELETE FROM sources")
        conn.commit()
    counts = _kb_init_conn(conn)
    stats = _kb_stats_conn(conn)
    out = {
        "_meta": {
            "source": "local knowledge base",
            "db": str(kb_path()),
            "retrieved_at": utcnow(),
            "note": "Offline init from references/, the guidance registry, and knowledge/seed/.",
        },
        "action": "reinit" if force else "init",
        "counts": counts,
        "documents": stats["documents"],
        "by_source_type": stats["by_source_type"],
        "fts": stats["fts"],
    }
    out["_md"] = (
        f"**Local KB {'reinitialized' if force else 'initialized'}** — {stats['documents']} documents\n\n"
        + _md_table(
            ["Action", "Count"],
            [[k, v] for k, v in counts.items()],
        )
        + "\n\n"
        + _md_table(
            ["Source type", "Documents"],
            [[k or "(none)", v] for k, v in sorted(stats["by_source_type"].items())],
        )
    )
    conn.close()
    return out


FTS_STOPWORDS = frozenset(
    """
    a an and are as at be been but by can could did do does for from had has have
    how if in into is it its may might no not of on or should than that the their
    them then there these they this those to was were what when which who why will
    with would versus vs about
    """.split()
)


def _search_terms(query: str) -> list[str]:
    """Tokenize a search query for FTS5.

    Common English words are dropped: ORing every token made `QVO OR` match
    every document containing "or". If the query is *only* stopwords, keep the
    raw tokens so an intentional search still works.
    """
    raw = re.findall(r"[A-Za-z0-9][A-Za-z0-9_.-]*", query)
    terms: list[str] = []
    seen: set[str] = set()
    for token in raw:
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        if len(token) < 2 or key in FTS_STOPWORDS:
            continue
        terms.append(token)
    return (terms or raw)[:12]


def _like_pattern(query: str) -> str:
    """Escape SQL LIKE wildcards so `%` and `_` are literal characters."""
    escaped = (
        query.lower()
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"


def _kb_search_fts(
    conn: sqlite3.Connection,
    query: str,
    limit: int,
    source_type: str | None,
    status: str | None,
) -> list[dict]:
    if not _kb_fts_enabled(conn):
        return []
    terms = _search_terms(query)
    if not terms:
        return []
    match = " OR ".join(f'"{term}"' for term in terms[:12])
    sql = """
        SELECT d.id, d.source, d.source_type, d.title, d.citation, d.url,
               d.retrieved_at, d.as_of, d.status, d.tags,
               snippet(documents_fts, 2, '[', ']', ' … ', 24) AS snippet,
               bm25(documents_fts) AS rank
        FROM documents_fts
        JOIN documents d ON d.rowid = documents_fts.rowid
        WHERE documents_fts MATCH ?
    """
    params: list[Any] = [match]
    if source_type:
        sql += " AND d.source_type = ?"
        params.append(source_type)
    if status:
        sql += " AND d.status = ?"
        params.append(status)
    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)
    try:
        return [dict(row) for row in conn.execute(sql, params)]
    except sqlite3.OperationalError:
        return []


def _kb_search_like(
    conn: sqlite3.Connection,
    query: str,
    limit: int,
    source_type: str | None,
    status: str | None,
) -> list[dict]:
    like = _like_pattern(query)
    sql = """
        SELECT d.id, d.source, d.source_type, d.title, d.citation, d.url,
               d.retrieved_at, d.as_of, d.status, d.tags,
               substr(d.text, 1, 320) AS snippet,
               0.0 AS rank
        FROM documents d
        WHERE (
            lower(d.title) LIKE ? ESCAPE '\\'
            OR lower(coalesce(d.citation, '')) LIKE ? ESCAPE '\\'
            OR lower(coalesce(d.id, '')) LIKE ? ESCAPE '\\'
            OR lower(d.text) LIKE ? ESCAPE '\\'
        )
    """
    params: list[Any] = [like, like, like, like]
    if source_type:
        sql += " AND d.source_type = ?"
        params.append(source_type)
    if status:
        sql += " AND d.status = ?"
        params.append(status)
    sql += " ORDER BY d.retrieved_at DESC, d.title LIMIT ?"
    params.append(limit)
    return [dict(row) for row in conn.execute(sql, params)]


def kb_search(
    query: str,
    limit: int = 10,
    source_type: str | None = None,
    status: str | None = None,
) -> dict:
    query = (query or "").strip()
    limit = max(1, min(int(limit), 50))
    conn = _kb_connect()
    if not query:
        rows = [
            dict(row)
            for row in conn.execute(
                "SELECT id, source, source_type, title, citation, url, retrieved_at, as_of, status, tags, "
                "substr(text, 1, 320) AS snippet, 0.0 AS rank "
                "FROM documents ORDER BY retrieved_at DESC LIMIT ?",
                (limit,),
            )
        ]
    else:
        rows = _kb_search_fts(conn, query, limit, source_type, status)
        # Add exact id/citation/URL hits and short queries that FTS may miss.
        for row in _kb_search_like(conn, query, limit, source_type, status):
            if all(existing["id"] != row["id"] for existing in rows):
                rows.append(row)
            if len(rows) >= limit:
                break
        rows = rows[:limit]
    out = {
        "_meta": {
            "source": "local knowledge base",
            "db": str(kb_path()),
            "retrieved_at": utcnow(),
            "fts": _kb_fts_enabled(conn),
            "note": "Offline search. Use `kb refresh` to update the local copy.",
        },
        "query": query,
        "count": len(rows),
        "results": rows,
    }
    if rows:
        out["_md"] = _md_table(
            ["ID", "Type", "Status", "Title", "Retrieved"],
            [[r["id"], r["source_type"], r["status"], r["title"], r["retrieved_at"]] for r in rows],
        )
    conn.close()
    return out


def kb_get(key: str, source_type: str | None = None) -> dict:
    key = (key or "").strip()
    conn = _kb_connect()
    rows: list[sqlite3.Row] = []
    if key:
        for clause in ("id = ?", "url = ?", "citation = ?"):
            sql = f"SELECT * FROM documents WHERE {clause}"
            params: list[Any] = [key]
            if source_type:
                sql += " AND source_type = ?"
                params.append(source_type)
            # Stable order: a URL shared by a CFR seed and a guidance stub must
            # not resolve differently between runs.
            sql += " ORDER BY id"
            rows = conn.execute(sql, params).fetchall()
            if rows:
                break
    if not rows and key:
        sql = "SELECT * FROM documents WHERE title LIKE ? ESCAPE '\\'"
        params = [_like_pattern(key)]
        if source_type:
            sql += " AND source_type = ?"
            params.append(source_type)
        sql += " ORDER BY retrieved_at DESC, id LIMIT 20"
        rows = conn.execute(sql, params).fetchall()
    if not rows:
        hint = f" (source_type={source_type})" if source_type else ""
        conn.close()
        raise RegError(f"No local knowledge document matched: {key}{hint}")
    row = rows[0]
    doc = dict(row)
    doc["metadata"] = json.loads(doc["metadata"]) if doc.get("metadata") else {}
    meta = {
        "source": "local knowledge base",
        "db": str(kb_path()),
        "retrieved_at": utcnow(),
        "note": "Offline read. Verify the official URL before relying on it.",
    }
    if len(rows) > 1:
        meta["ambiguous"] = True
        meta["alternatives"] = [
            {"id": other["id"], "source_type": other["source_type"], "title": other["title"]}
            for other in rows[1:10]
        ]
        meta["note"] = (
            "Multiple documents matched this key; showing the first by id. "
            "Use the exact id or --source-type to disambiguate."
        )
    conn.close()
    return {"_meta": meta, "document": doc}


def kb_stats() -> dict:
    conn = _kb_connect()
    stats = _kb_stats_conn(conn)
    path = kb_path()
    out = {
        "_meta": {
            "source": "local knowledge base",
            "db": str(path),
            "retrieved_at": utcnow(),
        },
        "db": str(path),
        "db_bytes": path.stat().st_size if path.exists() else 0,
        **stats,
    }
    out["_md"] = (
        f"**Local KB** — `{path}`\n\n"
        + f"- Documents: **{stats['documents']}**\n"
        + f"- FTS5: **{stats['fts']}**\n"
        + f"- Last init: {stats['last_init'] or 'never'}\n"
        + f"- Last refresh: {stats['last_refresh'] or 'never'}\n"
        + f"- Stale: **{stats['stale_count']}**\n\n"
        + _md_table(
            ["Source type", "Documents"],
            [[k or "(none)", v] for k, v in sorted(stats["by_source_type"].items())],
        )
    )
    conn.close()
    return out


def kb_stale(days: int | None = None) -> dict:
    conn = _kb_connect()
    rows = []
    for row in conn.execute(
        "SELECT id, title, source, source_type, url, retrieved_at, ttl_days FROM documents ORDER BY retrieved_at"
    ):
        age = _kb_age_days(row["retrieved_at"])
        ttl = days if days is not None else (row["ttl_days"] or KB_DEFAULT_TTL_DAYS)
        if age is not None and age > ttl:
            rows.append({**dict(row), "age_days": age, "ttl_days": ttl})
    out = {
        "_meta": {
            "source": "local knowledge base",
            "db": str(kb_path()),
            "retrieved_at": utcnow(),
            "threshold_days": days,
        },
        "count": len(rows),
        "results": rows,
    }
    if rows:
        out["_md"] = _md_table(
            ["ID", "Type", "Age (days)", "TTL", "Title"],
            [[r["id"], r["source_type"], r["age_days"], r["ttl_days"], r["title"]] for r in rows],
        )
    conn.close()
    return out


def kb_note_add(
    text: str,
    title: str | None = None,
    tags: str | None = None,
    sources: list[str] | None = None,
) -> dict:
    text = (text or "").strip()
    if not text:
        raise RegError("Note text is required.")
    now = utcnow()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    note_id = f"note:{now.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')}-{digest}"
    source_lines = [s for s in (sources or []) if s.strip()]
    body = text
    if source_lines:
        body += "\n\nSources:\n" + "\n".join(f"- {s}" for s in source_lines)
    conn = _kb_connect()
    _kb_upsert(
        conn,
        {
            "id": note_id,
            "source": "agent-note",
            "source_type": "note",
            "title": title or text.splitlines()[0][:80],
            "citation": None,
            "url": source_lines[0] if source_lines else None,
            "retrieved_at": now,
            "as_of": now[:10],
            "status": "note",
            "tags": ",".join(t for t in ["note", tags or ""] if t),
            "text": body,
            "metadata": {"sources": source_lines},
            "ttl_days": 365,
        },
    )
    conn.commit()
    conn.close()
    return {
        "_meta": {"source": "local knowledge base", "db": str(kb_path()), "retrieved_at": utcnow()},
        "id": note_id,
        "title": title or text.splitlines()[0][:80],
        "tags": tags or "",
        "sources": source_lines,
    }


def kb_note_list(limit: int = 20) -> dict:
    conn = _kb_connect()
    rows = [
        dict(row)
        for row in conn.execute(
            "SELECT id, title, tags, url, retrieved_at, substr(text, 1, 400) AS text "
            "FROM documents WHERE source_type = 'note' ORDER BY retrieved_at DESC LIMIT ?",
            (max(1, min(int(limit), 100)),),
        )
    ]
    out = {
        "_meta": {"source": "local knowledge base", "db": str(kb_path()), "retrieved_at": utcnow()},
        "count": len(rows),
        "results": rows,
    }
    if rows:
        out["_md"] = _md_table(
            ["ID", "Title", "Tags", "Retrieved"],
            [[r["id"], r["title"], r["tags"], r["retrieved_at"]] for r in rows],
        )
    conn.close()
    return out


def _kb_export_text(conn: sqlite3.Connection, fmt: str) -> str:
    rows = conn.execute("SELECT * FROM documents ORDER BY source_type, retrieved_at DESC, id").fetchall()

    def as_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            **dict(row),
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
        }

    if fmt == "jsonl":
        return "\n".join(json.dumps(as_dict(row), ensure_ascii=False) for row in rows) + "\n"
    if fmt == "json":
        return json.dumps(
            {
                "generated_at": utcnow(),
                "count": len(rows),
                "documents": [as_dict(row) for row in rows],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n"
    lines = [
        "# US Sleep Regulatory — local knowledge export",
        "",
        f"Generated: {utcnow()}  ",
        f"Documents: {len(rows)}",
        "",
        "> Local snapshot. Verify the official URL before relying on a document.",
        "",
    ]
    for row in rows:
        lines += [
            f"## {row['title']}",
            "",
            f"- id: `{row['id']}`",
            f"- source: {row['source']}",
            f"- type: {row['source_type']}",
            f"- status: {row['status']}",
            f"- citation: {row['citation'] or ''}",
            f"- url: {row['url'] or ''}",
            f"- retrieved_at: {row['retrieved_at']}",
            f"- as_of: {row['as_of'] or ''}",
            f"- tags: {row['tags'] or ''}",
            "",
            row["text"],
            "",
        ]
    return "\n".join(lines)


def kb_export(fmt: str = "md", out: str | None = None) -> str:
    if fmt not in {"md", "json", "jsonl"}:
        raise RegError(f"Unsupported export format: {fmt}. Use md, json, or jsonl.")
    conn = _kb_connect()
    text = _kb_export_text(conn, fmt)
    if out:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    conn.close()
    return text


def _kb_ingest_text(
    conn: sqlite3.Connection,
    *,
    text: str,
    title: str,
    source: str,
    source_type: str,
    tags: str,
    url: str | None = None,
    metadata: dict | None = None,
) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
    doc_id = f"ingest:{re.sub(r'[^A-Za-z0-9_.-]+', '-', title)[:60]}-{digest}"
    return _kb_upsert(
        conn,
        {
            "id": doc_id,
            "source": source,
            "source_type": source_type,
            "title": title,
            "citation": None,
            "url": url,
            "retrieved_at": utcnow(),
            "as_of": utcnow()[:10],
            "status": "internal",
            "tags": ",".join(t for t in ["ingest", tags or ""] if t),
            "text": text,
            "metadata": metadata or {},
            "ttl_days": 365,
        },
    )


def kb_ingest(
    path: str,
    source: str | None = None,
    title: str | None = None,
    tags: str | None = None,
) -> dict:
    target = Path(path).expanduser()
    if not target.exists():
        raise RegError(f"Path not found: {target}")
    files = [target] if target.is_file() else sorted(p for p in target.rglob("*") if p.is_file())
    conn = _kb_connect()
    results = []
    for file in files:
        suffix = file.suffix.lower()
        try:
            if suffix == ".pdf":
                text, method = _extract_pdf_text(file)
                if not text:
                    results.append({"path": str(file), "status": "skipped", "detail": "No PDF text extractor; install pypdf or pdftotext."})
                    continue
            elif suffix in {".md", ".txt"}:
                text = file.read_text(encoding="utf-8", errors="replace")
            elif suffix == ".json":
                text = json.dumps(json.loads(file.read_text(encoding="utf-8")), ensure_ascii=False, indent=2)
            elif suffix in {".html", ".htm"}:
                raw = file.read_text(encoding="utf-8", errors="replace")
                text = _clean(re.sub(r"<[^>]+>", " ", raw))
            else:
                results.append({"path": str(file), "status": "skipped", "detail": "Unsupported file type."})
                continue
            doc_title = title if (title and len(files) == 1) else (_first_heading(text) or file.stem)
            status = _kb_ingest_text(
                conn,
                text=text,
                title=doc_title,
                source=source or "local-file",
                source_type="internal",
                tags=tags or "",
                metadata={"path": str(file)},
            )
            results.append({"path": str(file), "status": status, "title": doc_title})
        except Exception as exc:  # noqa: BLE001
            results.append({"path": str(file), "status": "error", "detail": str(exc)[:300]})
    conn.commit()
    out = {
        "_meta": {"source": "local knowledge base", "db": str(kb_path()), "retrieved_at": utcnow()},
        "count": sum(1 for r in results if r["status"] in {"inserted", "updated", "unchanged"}),
        "results": results,
    }
    if results:
        out["_md"] = _md_table(
            ["Path", "Status", "Title/Detail"],
            [[r["path"], r["status"], r.get("title") or r.get("detail", "")] for r in results],
        )
    conn.close()
    return out


def _kb_source_update(conn: sqlite3.Connection, name: str, status: str, detail: str) -> None:
    conn.execute(
        "INSERT INTO sources(name, last_refresh, last_status, detail) VALUES(?, ?, ?, ?) "
        "ON CONFLICT(name) DO UPDATE SET last_refresh = excluded.last_refresh, "
        "last_status = excluded.last_status, detail = excluded.detail",
        (name, utcnow(), status, detail[:1000]),
    )


CFR_REFS = [
    ("21", "882.5801", False),
    ("21", "882.5705", False),
    ("21", "882.5050", False),
    ("21", "820.1", False),
    ("45", "164.308", False),
    ("45", "164.402", False),
    ("16", "318", True),
]

FR_SEED_TAGS = {
    "2024-01709": "qmsr,quality,binding",
    "2024-30983": "hipaa,security,proposed",
    "2024-10855": "ftc,breach,privacy,binding",
    "2024-28361": "ai,pccp,guidance",
    "2024-31543": "ai,draft,guidance",
    "2026-10734": "human-factors,guidance",
}


def _kb_fetch_cfr(title: str, ref: str, is_part: bool, use_cache: bool = True, ttl: int = DEFAULT_TTL) -> dict:
    doc = (
        ecfr_get(title, part=ref, use_cache=use_cache, ttl=ttl)
        if is_part
        else ecfr_get(title, section=ref, use_cache=use_cache, ttl=ttl)
    )
    citation = f"{title} CFR Part {ref}" if is_part else f"{title} CFR {ref}"
    return {
        "id": f"cfr-{title}-{ref}",
        "source": "eCFR",
        "source_type": "cfr",
        "title": f"{citation} — {doc.get('heading', '')}",
        "citation": citation,
        "url": doc.get("human_url"),
        "retrieved_at": doc["_meta"]["retrieved_at"],
        "as_of": doc["_meta"].get("as_of"),
        "status": "binding",
        "tags": "cfr,binding",
        "text": doc.get("text", ""),
        "metadata": {"api_url": doc["_meta"].get("url")},
        "ttl_days": 90,
    }


def _kb_fetch_classification(code: str, use_cache: bool = True, ttl: int = DEFAULT_TTL) -> list[dict]:
    data = fda_classification(product_code=code, use_cache=use_cache, ttl=ttl)
    return [
        {
            "id": f"classification-{code}",
            "source": "openFDA device/classification",
            "source_type": "classification",
            "title": f"{code} — {record.get('device_name')}",
            "citation": record.get("regulation_number"),
            "url": record.get("fda_url"),
            "retrieved_at": data["_meta"]["retrieved_at"],
            "as_of": data["_meta"].get("openfda_last_updated"),
            "status": "data",
            "tags": f"device,classification,{code}",
            "text": json.dumps(record, ensure_ascii=False, indent=2),
            "metadata": {"product_code": code},
            "ttl_days": 30,
        }
        for record in data.get("results", [])
    ]


def _kb_fetch_510k(code: str, use_cache: bool = True, ttl: int = DEFAULT_TTL) -> list[dict]:
    data = fda_510k_search(product_code=code, limit=100, use_cache=use_cache, ttl=ttl)
    docs = []
    for record in data.get("results", []):
        text = "\n".join(
            [
                f"Device: {record.get('device_name')}",
                f"Applicant: {record.get('applicant')}",
                f"Product code: {record.get('product_code')}",
                f"Decision: {record.get('decision_date')} ({record.get('decision_description')})",
                f"Regulation: {record.get('regulation_number')} (Class {record.get('device_class')})",
                f"Summary PDF: {record.get('summary_pdf_url') or 'n/a'}",
            ]
        )
        docs.append(
            {
                "id": f"510k-{record['k_number']}",
                "source": "openFDA device/510k",
                "source_type": "510k",
                "title": f"{record['k_number']} — {record.get('device_name')}",
                "citation": record["k_number"],
                "url": record.get("fda_url"),
                "retrieved_at": data["_meta"]["retrieved_at"],
                "as_of": record.get("decision_date"),
                "status": "data",
                "tags": f"device,510k,{code},predicate",
                "text": text,
                "metadata": record,
                "ttl_days": 30,
            }
        )
    return docs


def _kb_fetch_fr(document_number: str, tags: str, use_cache: bool = True, ttl: int = DEFAULT_TTL) -> dict:
    data = fr_get(document_number, use_cache=use_cache, ttl=ttl)["document"]
    doc_type = data.get("type") or ""
    status = "binding" if doc_type == "Rule" else "proposed" if "Proposed" in doc_type else "notice"
    text = "\n\n".join(x for x in [data.get("title"), data.get("abstract")] if x)
    return {
        "id": f"fr-{document_number}",
        "source": "Federal Register",
        "source_type": "federal-register",
        "title": data.get("title") or document_number,
        "citation": data.get("citation"),
        "url": data.get("html_url"),
        "retrieved_at": utcnow(),
        "as_of": data.get("publication_date"),
        "status": status,
        "tags": f"federal-register,{tags}",
        "text": text,
        "metadata": {
            "document_number": document_number,
            "docket_ids": data.get("docket_ids"),
        },
        "ttl_days": 30,
    }


def _kb_fetch_fr_search(term: str, use_cache: bool = True, ttl: int = DEFAULT_TTL) -> list[dict]:
    data = fr_search(term=term, agency="fda", since="2024-01-01", limit=20, use_cache=use_cache, ttl=ttl)
    docs = []
    for record in data.get("results", []):
        doc_type = record.get("type") or ""
        status = "binding" if doc_type == "Rule" else "proposed" if "Proposed" in doc_type else "notice"
        docs.append(
            {
                "id": f"fr-{record.get('document_number')}",
                "source": "Federal Register",
                "source_type": "federal-register",
                "title": record.get("title") or record.get("document_number"),
                "citation": record.get("citation"),
                "url": record.get("html_url"),
                "retrieved_at": data["_meta"]["retrieved_at"],
                "as_of": record.get("publication_date"),
                "status": status,
                "tags": "federal-register,device,software,ai",
                "text": "\n\n".join(x for x in [record.get("title"), record.get("abstract")] if x),
                "metadata": {"document_number": record.get("document_number")},
                "ttl_days": 30,
            }
        )
    return docs


def _kb_fetch_trials(use_cache: bool = True, ttl: int = DEFAULT_TTL) -> list[dict]:
    trials = trials_search(
        condition="insomnia",
        intervention="cognitive behavioral therapy",
        limit=20,
        use_cache=use_cache,
        ttl=ttl,
    )
    return [
        {
            "id": f"trial-{record.get('nct_id')}",
            "source": "ClinicalTrials.gov",
            "source_type": "trial",
            "title": f"{record.get('nct_id')} — {record.get('title')}",
            "citation": record.get("nct_id"),
            "url": record.get("url"),
            "retrieved_at": trials["_meta"]["retrieved_at"],
            "as_of": record.get("start_date"),
            "status": "data",
            "tags": "trial,insomnia,cbt-i",
            "text": json.dumps(record, ensure_ascii=False, indent=2),
            "metadata": record,
            "ttl_days": 30,
        }
        for record in trials.get("results", [])
    ]


def _kb_fetch_pubmed(use_cache: bool = True, ttl: int = DEFAULT_TTL) -> list[dict]:
    pubmed = pubmed_search("digital CBT-I insomnia randomized", limit=20, use_cache=use_cache, ttl=ttl)
    return [
        {
            "id": f"pubmed-{record.get('pmid')}",
            "source": "PubMed",
            "source_type": "pubmed",
            "title": record.get("title") or record.get("pmid"),
            "citation": record.get("pmid"),
            "url": record.get("url"),
            "retrieved_at": pubmed["_meta"]["retrieved_at"],
            "as_of": record.get("pubdate"),
            "status": "data",
            "tags": "pubmed,insomnia,cbt-i",
            "text": json.dumps(record, ensure_ascii=False, indent=2),
            "metadata": record,
            "ttl_days": 30,
        }
        for record in pubmed.get("results", [])
    ]


def _kb_fetch_summary(k_number: str, use_cache: bool = True, ttl: int = DEFAULT_TTL) -> dict | None:
    data = fda_510k_get(k_number, fetch_summary=True, use_cache=use_cache, ttl=ttl)
    record = data["results"]
    text = record.get("summary_text")
    if not text:
        return None
    return {
        "id": f"510k-summary-{k_number}",
        "source": "FDA 510(k) summary",
        "source_type": "510k-summary",
        "title": f"{k_number} — {record.get('device_name')} (summary)",
        "citation": k_number,
        "url": record.get("summary_pdf_url"),
        "retrieved_at": data["_meta"]["retrieved_at"],
        "as_of": record.get("decision_date"),
        "status": "data",
        "tags": "device,510k,summary,predicate",
        "text": text,
        "metadata": record,
        "ttl_days": 90,
    }


def kb_refresh(
    extended: bool = False,
    summaries: bool = False,
    jobs: int = DEFAULT_JOBS,
    use_cache: bool = True,
    ttl: int = DEFAULT_TTL,
) -> dict:
    """Refresh the core official sources into the local KB.

    Cache reads are on by default so a second refresh inside the TTL is cheap
    and idempotent; pass ``use_cache=False`` (``--no-cache``) to force a live
    fetch of every source.
    """
    conn = _kb_connect()
    tasks: dict[str, Callable[[], Any]] = {}

    for title, ref, is_part in CFR_REFS:
        tasks[f"cfr:{title}:{ref}"] = lambda t=title, r=ref, p=is_part: _kb_fetch_cfr(
            t, r, p, use_cache=use_cache, ttl=ttl
        )
    for code in ("QVO", "QMZ", "LEL"):
        tasks[f"classification:{code}"] = lambda c=code: _kb_fetch_classification(
            c, use_cache=use_cache, ttl=ttl
        )
        tasks[f"510k:{code}"] = lambda c=code: _kb_fetch_510k(c, use_cache=use_cache, ttl=ttl)
    for document_number, tags in FR_SEED_TAGS.items():
        tasks[f"federal-register:{document_number}"] = lambda d=document_number, tg=tags: _kb_fetch_fr(
            d, tg, use_cache=use_cache, ttl=ttl
        )
    if extended:
        tasks["extended:fr-samd"] = lambda: _kb_fetch_fr_search(
            '"software as a medical device"', use_cache=use_cache, ttl=ttl
        )
        tasks["extended:fr-ai"] = lambda: _kb_fetch_fr_search(
            '"artificial intelligence"', use_cache=use_cache, ttl=ttl
        )
        tasks["extended:trials"] = lambda: _kb_fetch_trials(use_cache=use_cache, ttl=ttl)
        tasks["extended:pubmed"] = lambda: _kb_fetch_pubmed(use_cache=use_cache, ttl=ttl)
    if summaries:
        for k_number in ("K191716", "K233577", "DEN200033"):
            tasks[f"summaries:{k_number}"] = lambda k=k_number: _kb_fetch_summary(
                k, use_cache=use_cache, ttl=ttl
            )

    results, errors = _run_parallel(tasks, jobs=jobs)

    group_totals: dict[str, int] = {}
    group_failures: dict[str, int] = {}
    for key in tasks:
        group = key.split(":", 1)[0]
        group_totals[group] = group_totals.get(group, 0) + 1
    for key in errors:
        group = key.split(":", 1)[0]
        group_failures[group] = group_failures.get(group, 0) + 1

    group_counts: dict[str, int] = {}
    for key, value in results.items():
        group = key.split(":", 1)[0]
        docs = value if isinstance(value, list) else ([value] if value else [])
        for doc in docs:
            _kb_upsert(conn, doc)
            group_counts[group] = group_counts.get(group, 0) + 1

    local_counts = _kb_ingest_local(conn)
    group_totals["local"] = 1
    group_failures["local"] = 0
    group_counts["local"] = sum(local_counts.values())

    sources: dict[str, Any] = {}
    for group in sorted(group_totals):
        total = group_totals[group]
        failed = group_failures.get(group, 0)
        status = "ok" if failed == 0 else ("partial" if failed < total else "error")
        entry: dict[str, Any] = {"status": status, "count": group_counts.get(group, 0)}
        if failed:
            messages = [f"{key}: {value}" for key, value in errors.items() if key.split(":", 1)[0] == group]
            entry["error"] = "; ".join(messages)[:500]
        sources[group] = entry
        detail = f"{entry['count']} documents"
        if failed:
            detail += f"; {failed}/{total} tasks failed"
        _kb_source_update(conn, group, status, detail)

    _kb_meta_set(conn, "last_refresh", utcnow())
    conn.commit()
    stats = _kb_stats_conn(conn)
    out = {
        "_meta": {
            "source": "local knowledge base refresh",
            "db": str(kb_path()),
            "retrieved_at": utcnow(),
            "jobs": jobs,
            "cache_reads": use_cache,
            "cache_ttl_seconds": ttl,
            "note": (
                "Parallel refresh completed, reusing cached responses inside the TTL. "
                "Use --no-cache to force live fetches. Subsequent prompts can use offline kb search."
                if use_cache
                else "Parallel refresh completed with live fetches (cache bypassed). "
                "Subsequent prompts can use offline kb search."
            ),
        },
        "sources": sources,
        "documents": stats["documents"],
        "by_source_type": stats["by_source_type"],
        "stale_count": stats["stale_count"],
    }
    out["_md"] = _md_table(
        ["Source", "Status", "Count / Error"],
        [[k, v.get("status"), v.get("count") if v.get("status") == "ok" else v.get("error", "")] for k, v in sources.items()],
    )
    conn.close()
    return out


# ---------------------------------------------------------------------------
# Doctor
# ---------------------------------------------------------------------------


def doctor() -> dict:
    checks = []

    def run(name: str, fn):
        start = time.perf_counter()
        try:
            result = fn()
            elapsed = round((time.perf_counter() - start) * 1000)
            checks.append({"check": name, "status": "ok", "latency_ms": elapsed, "detail": result})
        except Exception as exc:  # noqa: BLE001
            elapsed = round((time.perf_counter() - start) * 1000)
            checks.append({"check": name, "status": "fail", "latency_ms": elapsed, "detail": str(exc)[:300]})

    run("openFDA classification (QVO)", lambda: fda_classification(product_code="QVO", limit=1, use_cache=False)["results"][0]["device_name"])
    run("openFDA 510(k) (K191716)", lambda: fda_510k_search(k_number="K191716", limit=1, use_cache=False)["results"][0]["device_name"])
    run("eCFR 45 CFR 164.308", lambda: ecfr_get("45", section="164.308", use_cache=False)["heading"])
    run("Federal Register search", lambda: fr_get("2024-30983", use_cache=False)["document"]["title"][:80])
    run("ClinicalTrials.gov v2", lambda: trials_search(condition="insomnia", limit=1, use_cache=False)["results"][0]["nct_id"])
    run("PubMed E-utilities", lambda: pubmed_search("digital CBT-I insomnia", limit=1, use_cache=False)["results"][0]["pmid"])
    def _pdf_check() -> str:
        # HEAD is enough to prove the PDF path is reachable; the old version
        # re-downloaded 460 KB on every `doctor` run.
        url = "https://www.accessdata.fda.gov/cdrh_docs/pdf19/K191716.pdf"
        request = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": UA, "Accept": "application/pdf", "Accept-Encoding": "identity"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            content_type = response.headers.get("Content-Type", "")
            if response.status != 200:
                raise RegError(f"HEAD {url} returned {response.status}")
            if "pdf" not in content_type.lower():
                raise RegError(f"Expected a PDF from {url}, got {content_type!r}")
            return f"HEAD 200, {content_type}, {response.headers.get('Content-Length', '?')} bytes"

    run("accessdata 510(k) PDF", _pdf_check)
    ok = sum(1 for c in checks if c["status"] == "ok")
    out = {
        "_meta": {"source": "multi-source health check", "retrieved_at": utcnow()},
        "summary": f"{ok}/{len(checks)} checks passed",
        "checks": checks,
    }
    out["_md"] = _md_table(
        ["Check", "Status", "Latency (ms)", "Detail"],
        [[c["check"], c["status"], c["latency_ms"], c["detail"]] for c in checks],
    )
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_output(data: dict, fmt: str = "json", out: str | None = None) -> None:
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if fmt == "md" and data.get("_md"):
        print(data["_md"])
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


def _common_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--no-cache", action="store_true", help="Bypass cache reads (still writes cache).")
    p.add_argument("--cache-ttl", type=int, default=DEFAULT_TTL, help=f"Cache TTL seconds (default {DEFAULT_TTL}).")
    # None means "use the command's default": JSON for API commands, Markdown
    # for `kb export`. Resolving it per command keeps `--format json` honest
    # instead of silently falling back to another default.
    p.add_argument("--format", choices=["json", "md"], default=None)
    p.add_argument("--out", help="Write full JSON output to this path.")
    p.add_argument("--jobs", type=int, default=DEFAULT_JOBS, help=f"Parallel HTTP workers (default {DEFAULT_JOBS}, max 12).")
    return p


def main(argv: list[str] | None = None) -> int:
    common = _common_parser()
    parser = argparse.ArgumentParser(
        prog="reg.py",
        description="Official-source US regulatory research for an app-based sleep therapy service.",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("510k-search", parents=[common], help="Search 510(k)/De Novo clearances.")
    p.add_argument("--query", help='Device name phrase, e.g. "Somryst".')
    p.add_argument("--product-code")
    p.add_argument("--applicant")
    p.add_argument("--k-number")
    p.add_argument("--decision-from")
    p.add_argument("--decision-to")
    p.add_argument("--raw-search", help="Raw openFDA search expression (advanced).")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("510k-get", parents=[common], help="Get one 510(k)/De Novo record.")
    p.add_argument("k_number")
    p.add_argument("--fetch-summary", action="store_true", help="Download and extract the decision summary PDF.")

    p = sub.add_parser("classify", parents=[common], help="Search the FDA product classification database.")
    p.add_argument("--product-code")
    p.add_argument("--name")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("predicates", parents=[common], help="Classification + all clearances for a product code.")
    p.add_argument("--product-code", required=True)
    p.add_argument("--limit", type=int, default=100)

    p = sub.add_parser("cfr", parents=[common], help="Fetch an eCFR section or part.")
    p.add_argument("title", help="CFR title number, e.g. 21, 45, 16")
    p.add_argument("section", nargs="?", help="Section, e.g. 164.308")
    p.add_argument("--part", help="Part, e.g. 820")
    p.add_argument("--date", help="eCFR as-of date (YYYY-MM-DD); defaults to current.")
    p.add_argument("--full", action="store_true", help="Fetch a whole part instead of one section.")

    p = sub.add_parser("cfr-search", parents=[common], help="Full-text search eCFR.")
    p.add_argument("query")
    p.add_argument("--title")
    p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser("fr-search", parents=[common], help="Search the Federal Register API.")
    p.add_argument("--term")
    p.add_argument("--agency", default="fda", help="fda, hhs, ftc, cms, onc, or a full slug.")
    p.add_argument("--type", dest="doc_type", choices=["rule", "proposed", "notice", "presidential"])
    p.add_argument("--since")
    p.add_argument("--until")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("fr-get", parents=[common], help="Fetch one Federal Register document by number.")
    p.add_argument("document_number")

    p = sub.add_parser("trials", parents=[common], help="Search ClinicalTrials.gov v2.")
    p.add_argument("--condition")
    p.add_argument("--intervention")
    p.add_argument("--term")
    p.add_argument("--status")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("pubmed", parents=[common], help="Search PubMed via E-utilities.")
    p.add_argument("--term", required=True)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--sort", default="relevance")

    p = sub.add_parser("guidance", parents=[common], help="Search the local curated guidance registry.")
    p.add_argument("--query")
    p.add_argument("--topic")
    p.add_argument("--status")
    p.add_argument("--max-age-days", type=int, default=120)

    p = sub.add_parser("snapshot", parents=[common], help="Build a dated JSON+Markdown regulatory snapshot.")
    p.add_argument("--product-code", action="append", dest="product_codes")
    p.add_argument("--query", default="insomnia")
    p.add_argument("--out-dir", default=str(SKILL_DIR / "snapshots"))

    p = sub.add_parser("kb", help="Local knowledge base (offline-first search).")
    kb_sub = p.add_subparsers(dest="kb_command", required=True)

    kp = kb_sub.add_parser("init", parents=[common], help="Initialize the local KB from references, guidance, and seed.")
    kp.add_argument("--force", action="store_true", help="Clear the KB and re-ingest everything.")

    kp = kb_sub.add_parser("refresh", parents=[common], help="Refresh core official sources into the local KB.")
    kp.add_argument("--extended", action="store_true", help="Also refresh Federal Register, ClinicalTrials.gov, and PubMed.")
    kp.add_argument("--summaries", action="store_true", help="Download and extract 510(k) summary PDFs (needs pdftotext, mutool, or pypdf).")

    kp = kb_sub.add_parser("search", parents=[common], help="Search the local KB (no network).")
    kp.add_argument("query", nargs="?", default="")
    kp.add_argument("--limit", type=int, default=10)
    kp.add_argument("--source-type")
    kp.add_argument("--status")

    kp = kb_sub.add_parser("get", parents=[common], help="Read one local KB document by id, URL, or citation.")
    kp.add_argument("key")
    kp.add_argument("--source-type", help="Disambiguate when several sources share a URL (e.g. cfr, guidance).")

    kb_sub.add_parser("stats", parents=[common], help="Show KB size, counts, and freshness.")

    kp = kb_sub.add_parser("stale", parents=[common], help="List stale local documents.")
    kp.add_argument("--days", type=int)

    kp = kb_sub.add_parser("note", help="Add or list local research notes.")
    note_sub = kp.add_subparsers(dest="note_command", required=True)
    np = note_sub.add_parser("add", parents=[common], help="Add a note with citations.")
    np.add_argument("text")
    np.add_argument("--title")
    np.add_argument("--tags")
    np.add_argument("--source", action="append", default=[])
    np = note_sub.add_parser("list", parents=[common], help="List recent notes.")
    np.add_argument("--limit", type=int, default=20)

    kp = kb_sub.add_parser("export", parents=[common], help="Export the KB as Markdown or JSONL.")
    kp.add_argument("--jsonl", action="store_true")

    kp = kb_sub.add_parser("ingest", parents=[common], help="Ingest local PDF/Markdown/Text/JSON/HTML files.")
    kp.add_argument("path")
    kp.add_argument("--source")
    kp.add_argument("--title")
    kp.add_argument("--tags")

    sub.add_parser("doctor", parents=[common], help="Check every upstream source.")
    sub.add_parser("sources", parents=[common], help="Print the source catalog summary.")

    args = parser.parse_args(argv)
    uc = not args.no_cache
    ttl = args.cache_ttl
    fmt = args.format or "json"

    if args.command == "510k-search":
        data = fda_510k_search(
            query=args.query,
            product_code=args.product_code,
            applicant=args.applicant,
            k_number=args.k_number,
            decision_from=args.decision_from,
            decision_to=args.decision_to,
            raw_search=args.raw_search,
            limit=args.limit,
            use_cache=uc,
            ttl=ttl,
        )
    elif args.command == "510k-get":
        data = fda_510k_get(args.k_number, fetch_summary=args.fetch_summary, use_cache=uc, ttl=ttl)
    elif args.command == "classify":
        data = fda_classification(product_code=args.product_code, name=args.name, limit=args.limit, use_cache=uc, ttl=ttl)
    elif args.command == "predicates":
        data = fda_predicates(args.product_code, limit=args.limit, use_cache=uc, ttl=ttl)
    elif args.command == "cfr":
        data = ecfr_get(
            args.title,
            section=None if args.full else args.section,
            part=args.part or (args.section.split(".")[0] if args.section else None),
            date=args.date,
            use_cache=uc,
            ttl=ttl,
        )
    elif args.command == "cfr-search":
        data = ecfr_search(args.query, title=args.title, limit=args.limit, use_cache=uc, ttl=ttl)
    elif args.command == "fr-search":
        data = fr_search(
            term=args.term,
            agency=args.agency,
            doc_type=args.doc_type,
            since=args.since,
            until=args.until,
            limit=args.limit,
            use_cache=uc,
            ttl=ttl,
        )
    elif args.command == "fr-get":
        data = fr_get(args.document_number, use_cache=uc, ttl=ttl)
    elif args.command == "trials":
        data = trials_search(
            condition=args.condition,
            intervention=args.intervention,
            term=args.term,
            status=args.status,
            limit=args.limit,
            use_cache=uc,
            ttl=ttl,
        )
    elif args.command == "pubmed":
        data = pubmed_search(args.term, limit=args.limit, sort=args.sort, use_cache=uc, ttl=ttl)
    elif args.command == "kb":
        if args.kb_command == "init":
            data = kb_init(force=args.force)
        elif args.kb_command == "refresh":
            data = kb_refresh(
                extended=args.extended,
                summaries=args.summaries,
                jobs=args.jobs,
                use_cache=uc,
                ttl=ttl,
            )
        elif args.kb_command == "search":
            data = kb_search(args.query, limit=args.limit, source_type=args.source_type, status=args.status)
        elif args.kb_command == "get":
            data = kb_get(args.key, source_type=args.source_type)
        elif args.kb_command == "stats":
            data = kb_stats()
        elif args.kb_command == "stale":
            data = kb_stale(days=args.days)
        elif args.kb_command == "note":
            if args.note_command == "add":
                data = kb_note_add(args.text, title=args.title, tags=args.tags, sources=args.source)
            else:
                data = kb_note_list(limit=args.limit)
        elif args.kb_command == "export":
            export_fmt = "jsonl" if args.jsonl else (args.format or "md")
            text = kb_export(fmt=export_fmt, out=args.out)
            if args.out:
                print(f"Wrote {args.out}")
            else:
                print(text)
            return 0
        elif args.kb_command == "ingest":
            data = kb_ingest(args.path, source=args.source, title=args.title, tags=args.tags)
        else:
            parser.error("unknown kb command")
    elif args.command == "guidance":
        data = guidance_search(
            query=args.query,
            topic=args.topic,
            status=args.status,
            max_age_days=args.max_age_days,
        )
    elif args.command == "snapshot":
        data = build_snapshot(
            product_codes=args.product_codes,
            query=args.query,
            out_dir=args.out_dir,
            use_cache=uc,
            jobs=args.jobs,
        )
    elif args.command == "doctor":
        data = doctor()
    elif args.command == "sources":
        catalog = SKILL_DIR / "references" / "source-catalog.md"
        print(catalog.read_text(encoding="utf-8") if catalog.exists() else "source catalog missing")
        return 0
    else:
        parser.error(f"unknown command {args.command}")
        return 2

    _print_output(data, fmt=fmt, out=args.out)
    if args.command == "doctor":
        checks = data.get("checks", [])
        return 0 if checks and all(c.get("status") == "ok" for c in checks) else 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RegError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
