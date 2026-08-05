#!/usr/bin/env python3
"""Check official source availability and write a timestamped health snapshot."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "source-health.json"
SOURCES = {
    "mirandela_accounts": "https://www.cm-mirandela.pt/pages/239",
    "mirandela_minutes": "https://www.cm-mirandela.pt/municipio/camara-municipal/orgaos-e-funcionamento/reunioes-de-camara/reunioes-e-atas-do-executivo-camarario/atas",
    "impic_contracts": "https://dados.gov.pt/api/1/datasets/contratos-publicos-portal-base-impic-contratos-de-2012-a-2026/",
    "dgal_accounts": "https://portalautarquico.dgal.gov.pt/pt-PT/financas-locais/dados-financeiros/contas-de-gerencia/",
    "dgt_caop": "https://www.dgterritorio.gov.pt/atividades/cartografia/cartografia-tematica/caop",
}


def check(name: str, url: str) -> dict:
    request = Request(url, headers={"User-Agent": "OpenMirandela/0.1 (+public-interest data monitor)"})
    try:
        with urlopen(request, timeout=20) as response:
            sample = response.read(1024)
            return {
                "name": name,
                "url": url,
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "content_type": response.headers.get("content-type"),
                "sample_bytes": len(sample),
            }
    except HTTPError as error:
        return {"name": name, "url": url, "ok": False, "status": error.code, "error": str(error)}
    except (URLError, TimeoutError) as error:
        return {"name": name, "url": url, "ok": False, "status": None, "error": str(error)}


def main() -> None:
    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "sources": [check(name, url) for name, url in SOURCES.items()],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    healthy = sum(1 for item in payload["sources"] if item["ok"])
    print(f"Checked {len(SOURCES)} sources: {healthy} available. Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
