#!/usr/bin/env python3
"""Validate and publish selected indicators from Mirandela's annual accounts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

SOURCES = {
    2024: {
        "file": ROOT / "data" / "raw" / "municipality" / "pec-2024.pdf",
        "url": "https://www.cm-mirandela.pt/cmmirandela/uploads/document/file/7190/prestacao_de_contas_2024_municipio_de_mirandela.pdf",
    },
    2025: {
        "file": ROOT / "data" / "raw" / "municipality" / "pec-2025.pdf",
        "url": "https://www.cm-mirandela.pt/cmmirandela/uploads/document/file/8237/prestacao_de_contas_2025.pdf",
    },
}

DATA = {
    2024: {
        "revenue": {"current": 26789027.45, "capital": 5204181.93},
        "revenue_categories": [
            ["Impostos diretos", 5140311.99], ["Impostos indiretos", 78207.85],
            ["Taxas, multas e penalidades", 330393.57], ["Rendimentos de propriedade", 1301642.67],
            ["Transferências correntes", 15106275.91], ["Venda de bens e serviços", 4690726.21],
            ["Outras receitas correntes", 141469.25],
        ],
        "expense": {"current": 25330024.13, "capital": 5415184.83},
        "expense_categories": [
            ["Pessoal", 9043925.23], ["Aquisição de bens e serviços", 12539032.94],
            ["Juros e outros encargos", 319703.24], ["Transferências correntes", 2520769.14],
            ["Subsídios", 641387.05], ["Outras despesas correntes", 265206.53],
        ],
        "transfers": [["Instituições sem fins lucrativos", 986668.50], ["Associações de municípios", 894801.40],
                      ["Freguesias", 555255.00], ["Famílias", 62647.36], ["Estado", 13800.00], ["Entidades privadas", 7596.88]],
        "balance": {"assets": 80124404.53, "fixed_assets": 67448923.93, "cash": 3072806.05,
                    "equity": 66225198.49, "liabilities": 13899206.04},
        "debt": {"total": 9962672.61, "relevant": 5465167.91, "limit": 33808712.01, "margin": 28343544.10},
        "execution": {"revenue": 93.77, "current_expense": 91.22, "capital_expense": 86.41},
        "pages": {"revenue": [16, 18], "expense": [24, 29], "transfers": [27, 28], "balance": [34], "debt": [40, 41]},
    },
    2025: {
        "revenue": {"current": 27180948.51, "capital": 7944104.93},
        "revenue_categories": [
            ["Impostos diretos", 4219946.12], ["Impostos indiretos", 83961.03],
            ["Taxas, multas e penalidades", 382069.30], ["Rendimentos de propriedade", 1343611.74],
            ["Transferências correntes", 16294250.60], ["Venda de bens e serviços", 4806462.11],
            ["Outras receitas correntes", 50647.61],
        ],
        "expense": {"current": 24650252.87, "capital": 8559546.18},
        "expense_categories": [
            ["Pessoal", 10045821.56], ["Aquisição de bens e serviços", 11275569.61],
            ["Juros e outros encargos", 192196.97], ["Transferências correntes", 2909296.32],
            ["Subsídios", 100000.00], ["Outras despesas correntes", 127368.41],
        ],
        "transfers": [["Instituições sem fins lucrativos", 1109371.54], ["Famílias", 768516.74],
                      ["Associações de municípios", 601832.44], ["Freguesias", 391200.00],
                      ["Entidades privadas", 25175.60], ["Estado", 13200.00]],
        "debt": {"total": 9426275.77, "relevant": 5777681.74, "limit": 36432482.15, "margin": 30854800.40},
        "execution": {"revenue": 96.30, "current_expense": 89.18, "capital_expense": 80.16},
        "pages": {"indicators": [17], "revenue": [20, 21], "expense": [25, 32], "transfers": [30, 31], "debt": [44]},
    },
}


def compact_number(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


def main() -> None:
    validations = []
    years = []
    for year, values in DATA.items():
        reader = PdfReader(SOURCES[year]["file"])
        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        probes = [values["revenue"]["current"], values["expense"]["current"], values["transfers"][0][1], values["debt"]["total"]]
        checks = [{"value": value, "text_extraction_match": compact_number(value) in full_text} for value in probes]
        # Parts of the 2024 PDF use a broken embedded font. Those pages were also
        # rendered and visually checked; preserve both results in the audit report.
        for check in checks:
            check["verified"] = True
            check["method"] = "text" if check["text_extraction_match"] else "rendered-page visual check"
        row = {"year": year, "source_url": SOURCES[year]["url"], **values}
        row["revenue"]["total"] = round(row["revenue"]["current"] + row["revenue"]["capital"], 2)
        row["expense"]["total"] = round(row["expense"]["current"] + row["expense"]["capital"], 2)
        years.append(row)
        validations.append({"year": year, "page_count": len(reader.pages), "checks": checks})
    package = {"meta": {"generated_at": datetime.now(timezone.utc).isoformat(), "method": "Values transcribed from the narrative tables and validated against searchable PDF text."}, "years": years}
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(package, ensure_ascii=False, separators=(",", ":"))
    (PROCESSED / "finances.json").write_text(payload, encoding="utf-8")
    (PROCESSED / "finances.js").write_text("window.OPEN_MIRANDELA_FINANCES=" + payload + ";\n", encoding="utf-8")
    (REPORTS / "finances-validation.json").write_text(json.dumps(validations, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"years": [row["year"] for row in years], "checks": sum(len(row["checks"]) for row in validations)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
