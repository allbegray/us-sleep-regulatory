#!/usr/bin/env python3
"""Offline tests for the reg.py CLI, local KB, and registry validator.

No network access: every test either calls a pure helper, exercises the local
SQLite KB seeded from the repo, or monkeypatches the HTTP layer.

Run:
  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

# reg.py reads these at import time, so point them at a throwaway directory
# before importing it.
TMP_ROOT = Path(tempfile.mkdtemp(prefix="us-reg-tests-"))
os.environ["US_REG_CACHE"] = str(TMP_ROOT / "cache")
os.environ["US_REG_KB"] = str(TMP_ROOT / "kb.sqlite")

import mcp_server  # noqa: E402
import reg  # noqa: E402
import validate_registry  # noqa: E402


def tearDownModule() -> None:
    shutil.rmtree(TMP_ROOT, ignore_errors=True)


class TestPureHelpers(unittest.TestCase):
    def test_pdf_year_and_urls(self) -> None:
        self.assertEqual(reg._pdf_year("K191716"), 2019)
        self.assertEqual(reg._pdf_year("K233577"), 2023)
        self.assertEqual(reg._pdf_year("K000001"), 2000)
        self.assertEqual(
            reg._summary_pdf_url("K191716"),
            "https://www.accessdata.fda.gov/cdrh_docs/pdf19/K191716.pdf",
        )
        self.assertEqual(
            reg._summary_pdf_url("DEN200033"),
            "https://www.accessdata.fda.gov/cdrh_docs/reviews/DEN200033.pdf",
        )
        self.assertIsNone(reg._summary_pdf_url("PMA001"))

    def test_normalize_510k_marks_de_novo(self) -> None:
        record = reg._normalize_510k(
            {
                "k_number": "DEN200033",
                "device_name": "NightWare",
                "product_code": "QVO",
                "decision_date": "2020-11-06",
                "openfda": {"regulation_number": "882.5801", "device_class": "2"},
            }
        )
        self.assertTrue(record["is_de_novo"])
        self.assertEqual(record["regulation_number"], "882.5801")
        self.assertIn("DEN200033", record["summary_pdf_url"])

    def test_md_table_escapes_pipes_and_newlines(self) -> None:
        table = reg._md_table(["A", "B"], [["x|y", "line\nbreak"]])
        self.assertIn("x\\|y", table)
        self.assertIn("line break", table)

    def test_parallel_isolates_failures(self) -> None:
        def boom() -> None:
            raise ValueError("nope")

        results, errors = reg._run_parallel({"ok": lambda: 1, "boom": boom}, jobs=2)
        self.assertEqual(results, {"ok": 1})
        self.assertIn("boom", errors)
        self.assertIn("nope", errors["boom"])

    def test_search_terms_drop_stopwords(self) -> None:
        # This query used to OR in "OR" and match every document.
        self.assertEqual(reg._search_terms('QVO" OR "*'), ["QVO"])
        self.assertEqual(reg._search_terms("predicate for the device"), ["predicate", "device"])
        # A query made only of stopwords still searches for them.
        self.assertEqual(reg._search_terms("the of and"), ["the", "of", "and"])

    def test_like_pattern_escapes_wildcards(self) -> None:
        self.assertEqual(reg._like_pattern("50%_x"), "%50\\%\\_x%")
        self.assertEqual(reg._like_pattern("a\\b"), "%a\\\\b%")

    def test_registry_verification_flags_bulk_dates(self) -> None:
        entries = [{"last_verified": "2026-01-01"} for _ in range(8)]
        self.assertEqual(reg._registry_verification(entries)["mode"], "bulk")

        evidenced = [{"last_verified": "2026-01-01", "verified_via": "page opened"} for _ in range(8)]
        self.assertEqual(reg._registry_verification(evidenced)["mode"], "bulk-evidenced")

        spread = [{"last_verified": f"2026-01-0{day}"} for day in range(1, 8)]
        self.assertEqual(reg._registry_verification(spread)["mode"], "per-entry")


class TestCache(unittest.TestCase):
    def test_cache_key_is_stable(self) -> None:
        first = reg._cache_key("https://example.test/x", {"a": "1"})
        second = reg._cache_key("https://example.test/x", {"a": "1"})
        other = reg._cache_key("https://example.test/x", {"a": "2"})
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_cache_read_honours_ttl_and_bad_json(self) -> None:
        key = reg._cache_key("https://example.test/ttl", None)
        path = reg._cache_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"fetched_at": time.time() - 7200, "body": {"ok": True}}),
            encoding="utf-8",
        )
        self.assertIsNone(reg._cache_read(key, 60))
        self.assertEqual(reg._cache_read(key, 86400)["body"], {"ok": True})

        path.write_text("{not json", encoding="utf-8")
        self.assertIsNone(reg._cache_read(key, 60))


class TestRefreshCacheWiring(unittest.TestCase):
    """`kb refresh --no-cache` must actually change the fetch mode."""

    def _cfr_doc(self) -> dict:
        return {
            "_meta": {"retrieved_at": "2026-01-01T00:00:00Z", "as_of": "2026-01-01", "url": "https://ecfr.test"},
            "heading": "Heading",
            "human_url": "https://www.ecfr.gov/current/title-21/section-820.1",
            "text": "body",
        }

    def test_fetch_cfr_forwards_cache_flags(self) -> None:
        with mock.patch.object(reg, "ecfr_get", return_value=self._cfr_doc()) as called:
            reg._kb_fetch_cfr("21", "820.1", False, use_cache=False, ttl=123)
            called.assert_called_once_with("21", section="820.1", use_cache=False, ttl=123)

    def test_fetch_cfr_defaults_to_cache(self) -> None:
        with mock.patch.object(reg, "ecfr_get", return_value=self._cfr_doc()) as called:
            reg._kb_fetch_cfr("21", "820.1", False)
            called.assert_called_once_with("21", section="820.1", use_cache=True, ttl=reg.DEFAULT_TTL)


class TestKnowledgeBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        reg.kb_init(force=True)

    def test_fts_search_finds_qvo(self) -> None:
        # "QVO" works through both FTS5 and the LIKE fallback, so this test is
        # valid on a Python build without FTS5.
        result = reg.kb_search("QVO")
        self.assertGreater(result["count"], 0)
        self.assertTrue(any("QVO" in row["id"].upper() or "QVO" in (row["title"] or "").upper()
                            for row in result["results"]))

    def test_get_by_exact_id(self) -> None:
        result = reg.kb_get("cfr-21-882.5801")
        self.assertEqual(result["document"]["id"], "cfr-21-882.5801")
        self.assertNotIn("ambiguous", result["_meta"])

    def test_get_by_shared_url_is_disambiguated(self) -> None:
        url = "https://www.ecfr.gov/current/title-21/section-882.5801"
        result = reg.kb_get(url)
        # Deterministic: the full CFR text wins over the guidance stub, and the
        # alternative is disclosed instead of silently dropped.
        self.assertEqual(result["document"]["id"], "cfr-21-882.5801")
        self.assertTrue(result["_meta"].get("ambiguous"))
        self.assertIn("guidance:21-cfr-882-5801", [alt["id"] for alt in result["_meta"]["alternatives"]])

    def test_get_with_source_type_disambiguates(self) -> None:
        url = "https://www.ecfr.gov/current/title-21/section-882.5801"
        result = reg.kb_get(url, source_type="guidance")
        self.assertEqual(result["document"]["id"], "guidance:21-cfr-882-5801")
        self.assertNotIn("ambiguous", result["_meta"])

    def test_get_unknown_key_raises(self) -> None:
        with self.assertRaises(reg.RegError):
            reg.kb_get("no-such-document-anywhere")

    def test_export_formats(self) -> None:
        as_json = reg.kb_export(fmt="json")
        payload = json.loads(as_json)
        self.assertGreaterEqual(payload["count"], 50)
        self.assertEqual(payload["count"], len(payload["documents"]))

        as_jsonl = reg.kb_export(fmt="jsonl")
        lines = [line for line in as_jsonl.splitlines() if line.strip()]
        self.assertGreaterEqual(len(lines), 50)
        json.loads(lines[0])

        as_md = reg.kb_export(fmt="md")
        self.assertTrue(as_md.startswith("# US Sleep Regulatory"))

    def test_export_rejects_unknown_format(self) -> None:
        with self.assertRaises(reg.RegError):
            reg.kb_export(fmt="xml")

    def test_export_writes_json_to_out(self) -> None:
        out = TMP_ROOT / "nested" / "export.json"
        reg.kb_export(fmt="json", out=str(out))
        payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertGreaterEqual(payload["count"], 50)


class TestCliContract(unittest.TestCase):
    """The flags the README documents must do what the README says."""

    @classmethod
    def setUpClass(cls) -> None:
        reg.kb_init(force=True)

    def _run(self, argv: list[str]) -> str:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = reg.main(argv)
        self.assertEqual(code, 0)
        return buffer.getvalue()

    def test_export_defaults_to_markdown(self) -> None:
        self.assertTrue(self._run(["kb", "export"]).startswith("# US Sleep Regulatory"))

    def test_export_format_json_emits_json(self) -> None:
        payload = json.loads(self._run(["kb", "export", "--format", "json"]))
        self.assertIn("documents", payload)

    def test_export_format_md_emits_markdown(self) -> None:
        self.assertTrue(self._run(["kb", "export", "--format", "md"]).startswith("# US Sleep Regulatory"))

    def test_export_jsonl_flag_emits_ndjson(self) -> None:
        text = self._run(["kb", "export", "--jsonl"])
        self.assertNotIn("documents", text.splitlines()[0])
        json.loads(text.splitlines()[0])

    def test_get_source_type_flag(self) -> None:
        url = "https://www.ecfr.gov/current/title-21/section-882.5801"
        payload = json.loads(self._run(["kb", "get", url, "--source-type", "guidance"]))
        self.assertEqual(payload["document"]["source_type"], "guidance")


class TestGuidanceRegistry(unittest.TestCase):
    def test_repo_registry_has_no_structural_errors(self) -> None:
        data = validate_registry.load_registry(ROOT / "references" / "guidance-registry.json")
        errors, warnings = validate_registry.validate(data)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_guidance_search_reports_verification_mode(self) -> None:
        result = reg.guidance_search(topic="device")
        self.assertIn("verification", result["_meta"])
        self.assertIn(result["_meta"]["verification"]["mode"], {"bulk", "bulk-evidenced", "per-entry"})
        self.assertGreater(result["count"], 0)

    def test_validator_accepts_bulk_dates_with_evidence(self) -> None:
        entries = [
            {
                "id": f"entry-{index}",
                "title": "x",
                "status": "Final",
                "issued": "2024-01",
                "topics": ["device"],
                "url": f"https://example.test/{index}",
                "last_verified": "2026-01-01",
                "verified_via": "page opened 2026-01-01",
            }
            for index in range(6)
        ]
        _errors, warnings = validate_registry.validate(
            {"schema_version": "1", "last_updated": "2026-01-01", "entries": entries}
        )
        self.assertFalse(any("bulk verification" in warning for warning in warnings))

    def test_validator_catches_duplicate_ids_and_bad_status(self) -> None:
        entries = [
            {
                "id": "dup",
                "title": "x",
                "status": "Final",
                "issued": "2024-01",
                "topics": ["device"],
                "url": "https://example.test/x",
                "last_verified": "2026-01-01",
            }
            for _ in range(6)
        ]
        entries[1]["status"] = "Definitely a real status"
        errors, warnings = validate_registry.validate(
            {"schema_version": "1", "last_updated": "2026-01-01", "entries": entries}
        )
        self.assertTrue(any("duplicate id" in error for error in errors))
        self.assertTrue(any("unknown status" in error for error in errors))
        self.assertTrue(any("bulk verification" in warning for warning in warnings))


class TestMcpSurface(unittest.TestCase):
    def test_tool_count_and_dispatch(self) -> None:
        names = [tool["name"] for tool in mcp_server.TOOLS]
        self.assertEqual(len(names), 16)
        self.assertEqual(len(set(names)), len(names))

        result = mcp_server._dispatch("kb_stats", {})
        self.assertGreaterEqual(result["documents"], 50)

    def test_kb_get_schema_accepts_source_type(self) -> None:
        tool = next(tool for tool in mcp_server.TOOLS if tool["name"] == "kb_get")
        self.assertIn("source_type", tool["inputSchema"]["properties"])


class TestDocsMatchCode(unittest.TestCase):
    """Documentation drift is a silent failure mode in a skill repo."""

    def test_english_readme_lists_every_mcp_tool(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        block = text.split("Tools:", 1)[1].lstrip().split("\n\n", 1)[0]
        named = set(re.findall(r"`([a-z0-9_]+)`", block))
        actual = {tool["name"] for tool in mcp_server.TOOLS}
        self.assertEqual(named, actual)

    def test_korean_readme_lists_every_mcp_tool(self) -> None:
        text = (ROOT / "README.ko.md").read_text(encoding="utf-8")
        block = text.split("제공 도구:", 1)[1].lstrip().split("\n\n", 1)[0]
        named = set(re.findall(r"`([a-z0-9_]+)`", block))
        actual = {tool["name"] for tool in mcp_server.TOOLS}
        self.assertEqual(named, actual)

    def test_version_files_agree(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        shell = re.search(r'DEFAULT_VERSION="([^"]+)"', (ROOT / "install.sh").read_text(encoding="utf-8"))
        powershell = re.search(r'\$DefaultVersion = "([^"]+)"', (ROOT / "install.ps1").read_text(encoding="utf-8"))
        self.assertIsNotNone(shell)
        self.assertIsNotNone(powershell)
        self.assertEqual(version, shell.group(1))
        self.assertEqual(version, powershell.group(1))
        self.assertEqual(version, reg.VERSION)


class TestRetrievalEval(unittest.TestCase):
    """The retrieval suite is a quality gate, not a code unit — run it here so
    Windows CI (which skips the shell smoke test) still sees it."""

    def test_retrieval_suite_passes(self) -> None:
        import eval_retrieval

        reg.kb_init(force=False)
        cases = eval_retrieval.load_suite(ROOT / "tests" / "evals" / "retrieval.json")
        results = eval_retrieval.evaluate(cases)
        failures = [result for result in results if not result["pass"]]
        self.assertEqual(failures, [], f"retrieval misses: {failures}")


if __name__ == "__main__":
    unittest.main()
