#!/usr/bin/env python3
"""Build a source-linked index of Mirandela executive minutes."""

from __future__ import annotations

import html
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "processed"
ARCHIVE = "https://www.cm-mirandela.pt/municipio/camara-municipal/orgaos-e-funcionamento/reunioes-de-camara/reunioes-e-atas-do-executivo-camarario/atas?folders_list_282_folder_id=1482"
BASE = "https://www.cm-mirandela.pt"


def main() -> None:
    request = urllib.request.Request(ARCHIVE, headers={"User-Agent": "OpenMirandela/0.2 (+public-interest data reuse)"})
    with urllib.request.urlopen(request, timeout=90) as response:
        page = response.read().decode("utf-8", "replace")
    pattern = re.compile(r'href="(?P<url>/cmmirandela/uploads/document/file/[^\"]+\.pdf)"[^>]*>\s*<span>(?P<title>Ata .*?)</span>', re.I | re.S)
    records = []
    for match in pattern.finditer(page):
        title = re.sub(r"\s+", " ", html.unescape(match.group("title"))).strip()
        records.append({"year": 2024, "title": title, "url": BASE + html.unescape(match.group("url"))})
    if len(records) != 26:
        raise RuntimeError(f"Expected 26 minute PDFs for 2024; found {len(records)}")
    package = {"meta": {"generated_at": datetime.now(timezone.utc).isoformat(), "archive_url": ARCHIVE}, "records": records}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(package, ensure_ascii=False, separators=(",", ":"))
    (OUTPUT / "minutes.json").write_text(payload, encoding="utf-8")
    (OUTPUT / "minutes.js").write_text("window.OPEN_MIRANDELA_MINUTES=" + payload + ";\n", encoding="utf-8")
    print(json.dumps({"records": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
