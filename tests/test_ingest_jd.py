from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from ingest_jd import (  # noqa: E402
    EXIT_PASTE,
    AllowlistRedirectHandler,
    IngestError,
    adapter_for_url,
    api_url_for,
    html_to_text,
    parse_payload,
    run_ingest,
)


FIXTURES = ROOT / "tests" / "fixtures" / "ingest"


class HtmlToTextTests(unittest.TestCase):
    def test_strips_tags(self) -> None:
        text = html_to_text("<p>Hola <strong>HTML</strong></p><script>x()</script>")
        self.assertIn("Hola", text)
        self.assertIn("HTML", text)
        self.assertNotIn("x()", text)


class AllowlistTests(unittest.TestCase):
    def test_greenhouse_board_url(self) -> None:
        url = "https://boards.greenhouse.io/acme/jobs/99"
        self.assertEqual(adapter_for_url(url), "greenhouse")
        self.assertEqual(
            api_url_for(url),
            "https://boards-api.greenhouse.io/v1/boards/acme/jobs/99",
        )

    def test_lever_and_ashby(self) -> None:
        lever = "https://jobs.lever.co/acme/uuid-1"
        self.assertEqual(adapter_for_url(lever), "lever")
        self.assertEqual(api_url_for(lever), "https://api.lever.co/v0/postings/acme/uuid-1")
        ashby = "https://jobs.ashbyhq.com/acme/job-uuid"
        self.assertEqual(adapter_for_url(ashby), "ashby")
        self.assertIn("posting-api/job-board/acme/job/job-uuid", api_url_for(ashby))

    def test_https_api_reconstruida(self) -> None:
        api = "https://boards-api.greenhouse.io/v1/boards/acme/jobs/99"
        self.assertEqual(api_url_for(api), api)

    def test_http_y_credenciales_rechazados(self) -> None:
        with self.assertRaises(IngestError):
            api_url_for("http://boards.greenhouse.io/acme/jobs/99")
        with self.assertRaises(IngestError):
            api_url_for("https://user:pass@boards.greenhouse.io/acme/jobs/99")
        with self.assertRaises(IngestError):
            api_url_for("https://boards.greenhouse.io:8443/acme/jobs/99")

    def test_segmento_path_invalido(self) -> None:
        with self.assertRaises(IngestError):
            api_url_for("https://boards.greenhouse.io/../jobs/99")
        with self.assertRaises(IngestError):
            api_url_for("https://boards.greenhouse.io/acme!/jobs/99")

    def test_workday_no_allowlist(self) -> None:
        url = "https://acme.wd3.myworkdayjobs.com/en-US/Careers/job/Foo"
        self.assertIsNone(adapter_for_url(url))
        code = run_ingest(url=url, out_dir=Path(tempfile.mkdtemp()))
        self.assertEqual(code, EXIT_PASTE)


class RedirectHandlerTests(unittest.TestCase):
    def test_redirect_fuera_allowlist_falla(self) -> None:
        handler = AllowlistRedirectHandler()
        req = type("Req", (), {})()
        with self.assertRaises(IngestError) as ctx:
            handler.redirect_request(
                req,
                None,
                302,
                "Found",
                {},
                "https://evil.example.com/steal",
            )
        self.assertIn("allowlist", str(ctx.exception).lower())

    def test_redirect_http_falla(self) -> None:
        handler = AllowlistRedirectHandler()
        req = type("Req", (), {})()
        with self.assertRaises(IngestError):
            handler.redirect_request(
                req,
                None,
                302,
                "Found",
                {},
                "http://boards.greenhouse.io/acme/jobs/99",
            )

    def test_redirect_allowlist_delega(self) -> None:
        """Con host allowlist HTTPS, no lanza IngestError y delega al padre."""
        from unittest.mock import MagicMock, patch

        handler = AllowlistRedirectHandler()
        req = MagicMock()
        newurl = "https://boards-api.greenhouse.io/v1/boards/acme/jobs/99"
        with patch.object(
            AllowlistRedirectHandler.__bases__[0],
            "redirect_request",
            return_value="delegated",
        ) as parent:
            result = handler.redirect_request(req, None, 302, "Found", {}, newurl)
        self.assertEqual(result, "delegated")
        parent.assert_called_once()


class ParseFixtureTests(unittest.TestCase):
    def test_greenhouse_fixture(self) -> None:
        payload = json.loads((FIXTURES / "greenhouse_job.json").read_text(encoding="utf-8"))
        job = parse_payload("greenhouse", payload, payload["absolute_url"])
        self.assertEqual(job.title, "Desarrollador web junior")
        self.assertEqual(job.company, "Acme Demo SL")
        self.assertIn("HTML", job.description)
        self.assertNotIn("<p>", job.description)

    def test_lever_and_ashby_fixtures(self) -> None:
        lever = json.loads((FIXTURES / "lever_job.json").read_text(encoding="utf-8"))
        job_l = parse_payload("lever", lever, lever["hostedUrl"])
        self.assertIn("HTML", job_l.description)
        ashby = json.loads((FIXTURES / "ashby_job.json").read_text(encoding="utf-8"))
        job_a = parse_payload("ashby", ashby, ashby["jobUrl"])
        self.assertEqual(job_a.company, "Acme Demo SL")


class WriteOfertaTests(unittest.TestCase):
    def test_from_file_writes_descripcion_y_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            code = run_ingest(
                url="https://boards.greenhouse.io/acmedemo/jobs/4242",
                from_file=FIXTURES / "greenhouse_job.json",
                adapter="greenhouse",
                out_dir=out,
            )
            self.assertEqual(code, 0)
            desc = (out / "descripcion.md").read_text(encoding="utf-8")
            self.assertIn("Desarrollador web junior", desc)
            self.assertIn("HTML", desc)
            meta_text = (out / "meta.yaml").read_text(encoding="utf-8")
            self.assertIn("greenhouse", meta_text)
            self.assertIn("Acme Demo SL", meta_text)


if __name__ == "__main__":
    unittest.main()
