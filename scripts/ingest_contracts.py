#!/usr/bin/env python3
"""Download and normalize IMPIC/BASE contract data for Município de Mirandela."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

import ijson

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "impic"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
CONTRACT_DATASET = "https://dados.gov.pt/api/1/datasets/contratos-publicos-portal-base-impic-contratos-de-2012-a-2026/"
MOD_DATASET = "https://dados.gov.pt/api/1/datasets/contratos-publicos-portal-base-impic-modificacoes-contratuais-de-2012-a-2026/"
MUNICIPALITY_NIPC = "506881784"
MUNICIPALITY_NAME = "municipio de mirandela"
YEARS = range(2012, 2027)
USER_AGENT = "OpenMirandela/0.2 (+public-interest data reuse)"


def request_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def download(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as output:
        while block := response.read(1024 * 1024):
            output.write(block)
    temporary.replace(target)


def fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold()


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(item) for item in value if clean_text(item)]
    return [clean_text(value)] if clean_text(value) else []


def clean_text(value: Any) -> str:
    """Decode the occasionally double-escaped HTML found in BASE exports."""
    result = str(value or "").strip()
    for _ in range(3):
        decoded = html.unescape(result)
        if decoded == result:
            break
        result = decoded
    return result


def is_mirandela(record: dict[str, Any]) -> bool:
    for entity in listify(record.get("adjudicante")):
        normalized = fold(entity)
        if MUNICIPALITY_NIPC in entity or MUNICIPALITY_NAME in normalized:
            return True
    return False


def entity_parts(value: str) -> dict[str, str | None]:
    match = re.match(r"^\s*(\d{9})\s+-\s+(.*)$", value or "")
    if not match:
        return {"nif": None, "name": clean_text(value)}
    name = clean_text(re.sub(r"^\d+\s+-\s+", "", match.group(2)))
    return {"nif": match.group(1), "name": name}


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def first(values: Any) -> str | None:
    items = listify(values)
    return items[0] if items else None


def contract_category(types: list[str]) -> str:
    text = fold(" ".join(types))
    if "empreitada" in text or "obra publica" in text:
        return "Empreitadas"
    if "bens moveis" in text or "aquisicao de bens" in text or "locacao de bens" in text:
        return "Bens"
    if "servicos" in text:
        return "Serviços"
    return "Outros"


def normalize_contract(record: dict[str, Any]) -> dict[str, Any]:
    contract_id = str(record.get("idcontrato") or "")
    types = listify(record.get("tipoContrato"))
    suppliers = [entity_parts(value) for value in listify(record.get("adjudicatarios"))]
    effective = number(record.get("PrecoTotalEfetivo"))
    if effective == 0:
        effective = None
    price = number(record.get("precoContratual")) or 0.0
    procedure = clean_text(record.get("tipoprocedimento"))
    return {
        "id": contract_id,
        "year": int(record.get("Ano") or 0),
        "object": clean_text(record.get("objectoContrato") or record.get("descContrato")),
        "description": clean_text(record.get("descContrato")),
        "category": contract_category(types),
        "types": types,
        "procedure": procedure,
        "is_direct_award": "ajuste direto" in fold(procedure),
        "publication_date": str(record.get("dataPublicacao") or ""),
        "contract_date": str(record.get("dataCelebracaoContrato") or ""),
        "award_date": str(record.get("dataDecisaoAdjudicacao") or ""),
        "contract_price": round(price, 2),
        "base_price": number(record.get("precoBaseProcedimento")),
        "effective_price": effective,
        "execution_days": record.get("prazoExecucao"),
        "suppliers": suppliers,
        "cpv": listify(record.get("cpv")),
        "locations": listify(record.get("localExecucao")),
        "material_criteria": str(record.get("CritMateriais") or ""),
        "centralized": str(record.get("ProcedimentoCentralizado") or ""),
        "base_url": f"https://www.base.gov.pt/Base4/pt/detalhe/?type=contratos&id={contract_id}",
        "modifications": [],
    }


def resources_by_year(metadata: dict[str, Any], kind: str) -> dict[int, dict[str, Any]]:
    selected: dict[int, dict[str, Any]] = {}
    for resource in metadata.get("resources", []):
        title = resource.get("title", "")
        match = re.search(r"(20\d{2})", title)
        if not match:
            continue
        year = int(match.group(1))
        format_name = str(resource.get("format") or "").lower()
        if kind == "contracts" and format_name == "zip":
            selected[year] = resource
        if kind == "modifications" and format_name == "json":
            selected[year] = resource
    return selected


def iter_zip_records(path: Path) -> Iterable[dict[str, Any]]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".json")]
        if len(names) != 1:
            raise RuntimeError(f"Expected one JSON file in {path}, found {names}")
        with archive.open(names[0]) as stream:
            yield from ijson.items(stream, "item", use_float=True)


def ingest_contract_archives(resources: dict[int, dict[str, Any]], years: list[int]) -> tuple[list[dict[str, Any]], dict[int, int]]:
    records: list[dict[str, Any]] = []
    scanned: dict[int, int] = {}
    for year in years:
        resource = resources.get(year)
        if not resource:
            print(f"No contract resource for {year}", file=sys.stderr)
            continue
        target = RAW / f"contratos{year}.zip"
        print(f"[{year}] downloading/checking {resource['title']}...", flush=True)
        download(resource["url"], target)
        count = 0
        matches = 0
        for raw_record in iter_zip_records(target):
            count += 1
            if is_mirandela(raw_record):
                records.append(normalize_contract(raw_record))
                matches += 1
        scanned[year] = count
        print(f"[{year}] scanned {count:,}; selected {matches}", flush=True)
    return records, scanned


def ingest_modifications(resources: dict[int, dict[str, Any]], years: list[int], contracts: list[dict[str, Any]]) -> int:
    by_id = {record["id"]: record for record in contracts}
    matched = 0
    for year in years:
        resource = resources.get(year)
        if not resource:
            continue
        target = RAW / f"modcontrats{year}.json"
        download(resource["url"], target)
        with target.open("rb") as source:
            for raw_record in ijson.items(source, "item", use_float=True):
                contract_id = str(raw_record.get("idcontrato") or raw_record.get("IdContrato") or "")
                if contract_id not in by_id:
                    continue
                modification = {
                    "id": str(raw_record.get("idmodificacao") or raw_record.get("idModificacao") or ""),
                    "date": str(raw_record.get("modifContratoData") or raw_record.get("modifDataPublicacao") or ""),
                    "reason": clean_text(raw_record.get("modifContratoFundamento")),
                    "act_type": clean_text(raw_record.get("modifContratoTipoAto")),
                    "price_change": number(raw_record.get("modifContratoPrecoAlterado") or raw_record.get("precoAlterado")),
                    "deadline_change": raw_record.get("modifPrazoExecucao"),
                }
                by_id[contract_id]["modifications"].append(modification)
                matched += 1
    return matched


def supplier_key(supplier: dict[str, Any]) -> str:
    return supplier.get("nif") or fold(supplier.get("name") or "")


def summarize(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    by_year: dict[int, dict[str, Any]] = defaultdict(lambda: {"count": 0, "value": 0.0})
    by_category: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "value": 0.0})
    suppliers: dict[str, dict[str, Any]] = {}
    procedures: Counter[str] = Counter()
    modified_contracts = 0
    for contract in contracts:
        price = contract["contract_price"]
        year = contract["year"]
        by_year[year]["count"] += 1
        by_year[year]["value"] += price
        by_category[contract["category"]]["count"] += 1
        by_category[contract["category"]]["value"] += price
        procedures[contract["procedure"] or "Não indicado"] += 1
        if contract["modifications"]:
            modified_contracts += 1
        allocation = price / max(len(contract["suppliers"]), 1)
        for supplier in contract["suppliers"]:
            key = supplier_key(supplier)
            if not key:
                continue
            current = suppliers.setdefault(key, {"nif": supplier.get("nif"), "name": supplier.get("name"), "contracts": set(), "value": 0.0})
            current["contracts"].add(contract["id"])
            current["value"] += allocation
    supplier_rows = [
        {"nif": row["nif"], "name": row["name"], "contract_count": len(row["contracts"]), "allocated_value": round(row["value"], 2)}
        for row in suppliers.values()
    ]
    supplier_rows.sort(key=lambda row: row["allocated_value"], reverse=True)
    total_value = round(sum(item["contract_price"] for item in contracts), 2)
    return {
        "contract_count": len(contracts),
        "total_value": total_value,
        "supplier_count": len(supplier_rows),
        "modified_contract_count": modified_contracts,
        "years": [dict(year=year, count=row["count"], value=round(row["value"], 2)) for year, row in sorted(by_year.items())],
        "categories": [dict(category=category, count=row["count"], value=round(row["value"], 2)) for category, row in sorted(by_category.items(), key=lambda item: item[1]["value"], reverse=True)],
        "procedures": [{"procedure": name, "count": count} for name, count in procedures.most_common()],
        "top_suppliers": supplier_rows[:50],
    }


def json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Cannot serialize {type(value)}")


def write_outputs(contracts: list[dict[str, Any]], summary: dict[str, Any], metadata: dict[str, Any], scanned: dict[int, int], matched_modifications: int) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    contracts.sort(key=lambda row: (row["year"], row["publication_date"], row["id"]), reverse=True)
    package = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "municipality_nipc": MUNICIPALITY_NIPC,
            "source": CONTRACT_DATASET,
            "source_last_update": metadata.get("last_update"),
            "method": "Filter contracting entities by NIPC/name; supplier values split equally for multi-supplier contracts.",
        },
        "summary": summary,
        "contracts": contracts,
    }
    (PROCESSED / "contracts.json").write_text(json.dumps(package, ensure_ascii=False, separators=(",", ":"), default=json_default), encoding="utf-8")
    (PROCESSED / "contracts.js").write_text(
        "window.OPEN_MIRANDELA_CONTRACTS=" + json.dumps(package, ensure_ascii=False, separators=(",", ":"), default=json_default) + ";\n",
        encoding="utf-8",
    )
    report = {
        "generated_at": package["meta"]["generated_at"],
        "years_scanned": scanned,
        "selected_contracts": len(contracts),
        "matched_modifications": matched_modifications,
        "sum_contract_price": summary["total_value"],
        "contracts_without_supplier": sum(1 for row in contracts if not row["suppliers"]),
        "contracts_without_price": sum(1 for row in contracts if not row["contract_price"]),
        "contracts_without_date": sum(1 for row in contracts if not row["contract_date"]),
    }
    (REPORTS / "contracts-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", nargs="*", type=int, default=list(YEARS))
    parser.add_argument("--skip-modifications", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    years = sorted(set(args.years))
    invalid = [year for year in years if year not in YEARS]
    if invalid:
        raise SystemExit(f"Unsupported years: {invalid}")
    contract_metadata = request_json(CONTRACT_DATASET)
    resources = resources_by_year(contract_metadata, "contracts")
    contracts, scanned = ingest_contract_archives(resources, years)
    matched_modifications = 0
    if not args.skip_modifications:
        mod_metadata = request_json(MOD_DATASET)
        mod_resources = resources_by_year(mod_metadata, "modifications")
        matched_modifications = ingest_modifications(mod_resources, years, contracts)
    summary = summarize(contracts)
    write_outputs(contracts, summary, contract_metadata, scanned, matched_modifications)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
