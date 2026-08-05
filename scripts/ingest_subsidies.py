#!/usr/bin/env python3
"""Extract public-entity transfers from Mirandela's 2025 accounts.

Named natural-person beneficiaries are intentionally excluded from published output.
"""

from __future__ import annotations

import html
import json
import re
import unicodedata
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber
import ijson

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data" / "raw" / "municipality" / "pec-2025.pdf"
PDF_URL = "https://www.cm-mirandela.pt/cmmirandela/uploads/document/file/8237/prestacao_de_contas_2025.pdf"
PARISH_URL = "https://www.cm-mirandela.pt/p/freguesias"
IMPIC_RAW = ROOT / "data" / "raw" / "impic"
FFF_URL = "https://portalautarquico.dgal.gov.pt/ficheiros/?channel=a7187039-4863-4c6c-9ef0-1422b677728d&content_id=7F882D7D-4D09-4A16-B4D7-DD6CA4E5E991&dtestate=2026-01-12111538&field=storage_image&filetype=pdf&lang=pt&schema=f7664ca7-3a1a-4b25-9f46-2056eef44c33&ver=1"
FFF_PDF = ROOT / "data" / "raw" / "dgal" / "fff-2026.pdf"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
PAGES = range(213, 234)
COLS = [(51, 160), (160, 245), (245, 347), (347, 473), (473, 519), (519, 563), (563, 607), (607, 650), (650, 691), (691, 786)]


def words_text(words: list[dict], x0: float, x1: float, top: float, bottom: float) -> str:
    selected = sorted(
        [word for word in words if x0 <= word["x0"] < x1 and top <= word["top"] < bottom],
        key=lambda word: (word["top"], word["x0"]),
    )
    lines: list[list] = []
    for word in selected:
        if not lines or abs(lines[-1][0] - word["top"]) > 2:
            lines.append([word["top"], [word]])
        else:
            lines[-1][1].append(word)
    return " ".join(" ".join(word["text"] for word in sorted(line, key=lambda item: item["x0"])) for _, line in lines)


def amount(value: str) -> float:
    match = re.search(r"\d[\d.]*,\d{2}", value or "")
    return round(float(match.group().replace(".", "").replace(",", ".")), 2) if match else 0.0


def parse_ledger() -> list[dict]:
    records = []
    with pdfplumber.open(PDF) as document:
        for page_number in PAGES:
            page = document.pages[page_number - 1]
            words = page.extract_words(x_tolerance=1, y_tolerance=1)
            anchors = sorted(
                [word for word in words if re.fullmatch(r"\d{9}", word["text"]) and 340 < word["x0"] < 380],
                key=lambda word: word["top"],
            )
            for index, anchor in enumerate(anchors):
                top = anchor["top"] - 1
                bottom = anchors[index + 1]["top"] - 1 if index + 1 < len(anchors) else 555
                cells = [words_text(words, *column, top, bottom) for column in COLS]
                entity = re.match(r"(\d{9})\s+(.*)", cells[3])
                if not entity:
                    continue
                records.append({
                    "year": 2025,
                    "page": page_number,
                    "expense_type": cells[0],
                    "legal_basis": cells[1],
                    "purpose": cells[2],
                    "nif": entity.group(1),
                    "name": entity.group(2),
                    "budgeted": amount(cells[4]),
                    "authorized": amount(cells[5]),
                    "paid": amount(cells[6]),
                    "unpaid": amount(cells[7]),
                    "observations": cells[9],
                    "source_url": f"{PDF_URL}#page={page_number}",
                })
    return records


def category(record: dict) -> str:
    value = record["expense_type"]
    if "Freguesias" in value:
        return "Freguesias"
    if "Instituições sem Fins" in value:
        return "Instituições"
    if "PRIVADAS" in value:
        return "Comércio local"
    if "Empresas Públicas" in value:
        return "Empresas públicas"
    if "Associações de Municípios" in value:
        return "Associações municipais"
    return "Outras entidades"


def aggregate(records: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for record in records:
        current = grouped.setdefault(record["nif"], {
            "nif": record["nif"], "name": record["name"], "paid": 0.0, "authorized": 0.0,
            "unpaid": 0.0, "record_count": 0, "categories": set(), "purposes": [], "pages": set(),
        })
        current["paid"] += record["paid"]
        current["authorized"] += record["authorized"]
        current["unpaid"] += record["unpaid"]
        current["record_count"] += 1
        current["categories"].add(category(record))
        current["pages"].add(record["page"])
        if record["purpose"] and record["purpose"] not in current["purposes"]:
            current["purposes"].append(record["purpose"])
    result = []
    for row in grouped.values():
        result.append({**row, "paid": round(row["paid"], 2), "authorized": round(row["authorized"], 2),
                       "unpaid": round(row["unpaid"], 2), "categories": sorted(row["categories"]),
                       "pages": sorted(row["pages"])})
    return sorted(result, key=lambda row: row["paid"], reverse=True)


def fold(value: str) -> str:
    value = "".join(char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char)).casefold()
    stop = {"junta", "freguesia", "freguesias", "uniao", "das", "dos", "da", "do", "de", "e"}
    return " ".join(word for word in re.findall(r"[a-z]+", value) if word not in stop)


def parish_electors() -> list[dict]:
    request = urllib.request.Request(PARISH_URL, headers={"User-Agent": "OpenMirandela/0.3 (+public-interest data reuse)"})
    with urllib.request.urlopen(request, timeout=90) as response:
        page = response.read().decode("utf-8", "replace")
    rows = re.findall(r"<tr>\s*<td>(.*?)</td>\s*<td>([\d.]+)</td>\s*</tr>", page, re.I | re.S)
    result = [{"name": " ".join(re.sub(r"<[^>]+>", " ", html.unescape(name)).split()), "electors": int(count.replace(".", ""))} for name, count in rows]
    if len(result) != 30:
        raise RuntimeError(f"Expected 30 official parish rows; found {len(result)}")
    return result


def join_parishes(parish_records: list[dict], profiles: list[dict]) -> list[dict]:
    by_nif = aggregate(parish_records)
    for parish in by_nif:
        target = set(fold(parish["name"]).split())
        candidates = [(len(target & set(fold(profile["name"]).split())), profile) for profile in profiles]
        score, match = max(candidates, key=lambda item: item[0])
        parish["display_name"] = match["name"] if score else parish["name"].title()
        parish["electors"] = match["electors"] if score else None
        parish["profile_url"] = PARISH_URL
        parish["current_paid"] = round(sum(row["paid"] for row in parish_records if row["nif"] == parish["nif"] and row["expense_type"].startswith("0405")), 2)
        parish["capital_paid"] = round(sum(row["paid"] for row in parish_records if row["nif"] == parish["nif"] and row["expense_type"].startswith("0805")), 2)
    return sorted(by_nif, key=lambda row: row["paid"], reverse=True)


def clean_contract_text(value) -> str:
    result = str(value or "").strip()
    for _ in range(3):
        decoded = html.unescape(result)
        if decoded == result:
            break
        result = decoded
    return result


def contract_entities(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_contract_text(item) for item in value if clean_contract_text(item)]
    return [clean_contract_text(value)] if clean_contract_text(value) else []


def supplier_parts(value: str) -> dict:
    match = re.match(r"^\s*(\d{9})\s+-\s+(.*)$", value or "")
    if match:
        return {"nif": match.group(1), "name": clean_contract_text(match.group(2))}
    return {"nif": None, "name": re.sub(r"^(?:-\s*)+", "", clean_contract_text(value))}


def parish_contracts(parishes: list[dict]) -> dict:
    """Cross-match official BASE bulk archives using each parish NIF."""
    by_nif = {row["nif"]: row for row in parishes}
    contracts: dict[str, list[dict]] = defaultdict(list)
    archives = sorted(IMPIC_RAW.glob("contratos*.zip"))
    if not archives:
        return {"count": 0, "value": 0.0, "parishes_with_contracts": 0, "coverage": None}
    for archive_path in archives:
        with zipfile.ZipFile(archive_path) as archive:
            names = [name for name in archive.namelist() if name.lower().endswith(".json")]
            if len(names) != 1:
                raise RuntimeError(f"Expected one contract JSON in {archive_path}; found {names}")
            with archive.open(names[0]) as source:
                for record in ijson.items(source, "item", use_float=True):
                    adjudicantes = contract_entities(record.get("adjudicante"))
                    matched = [nif for nif in by_nif if any(nif in entity for entity in adjudicantes)]
                    if not matched:
                        continue
                    price = round(float(record.get("precoContratual") or 0), 2)
                    suppliers = [supplier_parts(value) for value in contract_entities(record.get("adjudicatarios"))]
                    normalized = {
                        "id": str(record.get("idcontrato") or ""),
                        "year": int(record.get("Ano") or 0),
                        "date": str(record.get("dataPublicacao") or record.get("dataCelebracaoContrato") or ""),
                        "object": clean_contract_text(record.get("objectoContrato") or record.get("descContrato")),
                        "procedure": clean_contract_text(record.get("tipoprocedimento")),
                        "price": price,
                        "suppliers": suppliers,
                        "url": f"https://www.base.gov.pt/Base4/pt/detalhe/?type=contratos&id={record.get('idcontrato') or ''}",
                    }
                    for nif in matched:
                        contracts[nif].append(normalized)
    for parish in parishes:
        rows = sorted(contracts[parish["nif"]], key=lambda row: (row["year"], row["date"]), reverse=True)
        suppliers: dict[str, dict] = {}
        for row in rows:
            allocation = row["price"] / len(row["suppliers"]) if row["suppliers"] else 0
            for supplier in row["suppliers"]:
                key = supplier["nif"] or fold(supplier["name"])
                current = suppliers.setdefault(key, {**supplier, "contracts": 0, "value": 0.0})
                current["contracts"] += 1
                current["value"] += allocation
        parish["contracts"] = rows
        parish["contract_count"] = len(rows)
        parish["contract_value"] = round(sum(row["price"] for row in rows), 2)
        parish["supplier_count"] = len(suppliers)
        parish["top_suppliers"] = sorted(
            [{**row, "value": round(row["value"], 2)} for row in suppliers.values()],
            key=lambda row: row["value"], reverse=True,
        )[:5]
    all_rows = [row for rows in contracts.values() for row in rows]
    years = [row["year"] for row in all_rows if row["year"]]
    return {
        "count": len(all_rows),
        "value": round(sum(row["price"] for row in all_rows), 2),
        "parishes_with_contracts": sum(bool(rows) for rows in contracts.values()),
        "coverage": [min(years), max(years)] if years else None,
    }


def state_parish_funding(parishes: list[dict]) -> dict:
    """Add the 2026 FFF and statutory excess from DGAL's official Map 13."""
    if not FFF_PDF.exists():
        FFF_PDF.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(FFF_URL, headers={"User-Agent": "OpenMirandela/0.3 (+public-interest data reuse)"})
        with urllib.request.urlopen(request, timeout=120) as response:
            FFF_PDF.write_bytes(response.read())
    rows = []
    with pdfplumber.open(FFF_PDF) as document:
        for page in document.pages:
            for line in (page.extract_text() or "").splitlines():
                if not line.startswith("MIRANDELA "):
                    continue
                amounts = list(re.finditer(r"\d[\d ]*,\d{2}", line))
                if len(amounts) < 2:
                    continue
                name = line[len("MIRANDELA "):amounts[0].start()].strip()
                values = [float(match.group().replace(" ", "").replace(",", ".")) for match in amounts]
                rows.append({"name": name, "fff": values[0], "excess": values[1]})
    if len(rows) != 30:
        raise RuntimeError(f"Expected 30 Mirandela rows in DGAL Map 13; found {len(rows)}")
    for parish in parishes:
        target = set(fold(parish["display_name"]).split())
        score, match = max(
            ((len(target & set(fold(row["name"]).split())), row) for row in rows),
            key=lambda item: item[0],
        )
        if not score:
            raise RuntimeError(f"Could not join DGAL funding for {parish['display_name']}")
        parish["state_fff_2026"] = match["fff"]
        parish["state_excess_2026"] = match["excess"]
        parish["state_total_2026"] = round(match["fff"] + match["excess"], 2)
    return {
        "year": 2026,
        "fff": round(sum(row["fff"] for row in rows), 2),
        "excess": round(sum(row["excess"] for row in rows), 2),
        "total": round(sum(row["fff"] + row["excess"] for row in rows), 2),
        "source_url": FFF_URL,
    }


def main() -> None:
    all_records = parse_ledger()
    private = [row for row in all_records if row["nif"].startswith(("1", "2", "3"))]
    legal = [row for row in all_records if not row["nif"].startswith(("1", "2", "3"))]
    parish_records = [row for row in legal if category(row) == "Freguesias"]
    # Publish actual support categories. Treasury reimbursements and internal/self
    # movements classified as "other" are not presented as subsidies.
    subsidy_records = [row for row in legal if category(row) in {"Instituições", "Comércio local", "Empresas públicas"}]
    for row in subsidy_records:
        row["category"] = category(row)
    beneficiaries = aggregate(subsidy_records)
    parishes = join_parishes(parish_records, parish_electors())
    parish_contract_summary = parish_contracts(parishes)
    state_funding_summary = state_parish_funding(parishes)
    nonprofit_paid = round(sum(row["paid"] for row in all_records if row["expense_type"].startswith("040701")), 2)
    parish_current = round(sum(row["paid"] for row in parish_records if row["expense_type"].startswith("0405")), 2)
    if nonprofit_paid != 1109371.54 or parish_current != 391200.00 or len(parishes) != 30:
        raise RuntimeError(f"Validation failed: nonprofit={nonprofit_paid}, parish={parish_current}, parishes={len(parishes)}")
    summary = {
        "record_count": len(subsidy_records), "beneficiary_count": len(beneficiaries),
        "paid_total": round(sum(row["paid"] for row in subsidy_records), 2),
        "authorized_total": round(sum(row["authorized"] for row in subsidy_records), 2),
        "category_totals": [{"category": name, "records": count, "paid": round(sum(row["paid"] for row in subsidy_records if row["category"] == name), 2)} for name, count in Counter(row["category"] for row in subsidy_records).most_common()],
        "excluded_natural_person_records": len(private),
        "excluded_natural_person_paid": round(sum(row["paid"] for row in private), 2),
    }
    package = {
        "meta": {"generated_at": datetime.now(timezone.utc).isoformat(), "year": 2025, "source_url": PDF_URL,
                 "source_pages": [213, 233], "privacy": "Natural-person NIFs and names are excluded from public output."},
        "summary": summary, "beneficiaries": beneficiaries, "records": subsidy_records,
        "parishes": {"summary": {"count": len(parishes), "paid_total": round(sum(row["paid"] for row in parish_records), 2),
                                    "current_paid": parish_current, "capital_paid": round(sum(row["paid"] for row in parish_records if row["expense_type"].startswith("0805")), 2)},
                     "contracts_summary": parish_contract_summary, "state_funding_summary": state_funding_summary,
                     "records": parishes, "directory_url": PARISH_URL},
    }
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(package, ensure_ascii=False, separators=(",", ":"))
    (PROCESSED / "subsidies.json").write_text(payload, encoding="utf-8")
    (PROCESSED / "subsidies.js").write_text("window.OPEN_MIRANDELA_SUBSIDIES=" + payload + ";\n", encoding="utf-8")
    report = {"generated_at": package["meta"]["generated_at"], "ledger_records": len(all_records), "public_legal_records": len(legal),
              "subsidy_records": len(subsidy_records), "parish_records": len(parish_records), "nonprofit_current_paid": nonprofit_paid,
              "parish_current_paid": parish_current, "parish_contracts": parish_contract_summary, "state_funding": state_funding_summary,
              "privacy_exclusions": {"records": len(private), "paid": summary["excluded_natural_person_paid"]}}
    (REPORTS / "subsidies-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"summary": summary, "parishes": package["parishes"]["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
