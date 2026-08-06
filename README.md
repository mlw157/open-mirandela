# Open Mirandela

An independent, source-first explorer for public information about the Municipality of Mirandela.

## Run locally

```bash
npm run dev
```

Then open <http://localhost:4173>.

The browser application has no runtime dependencies and is served by a small Node HTTP server. Data refresh scripts use the isolated Python environment in `.venv`.

## What is implemented

- Responsive overview, finance, contracts, subsidies, parishes, and decisions views.
- A complete IMPIC/BASE contract index for Mirandela: 1,474 contracts from 2012–2026, 588 normalized suppliers, €108.4M in published contract value, and 248 linked modification records.
- Search and filters for contract year, category, procedure, object, and supplier, plus annual and supplier rankings.
- Verified 2024 and 2025 annual-account dashboards: revenue, expenditure, economic categories, current transfers, debt, execution, and 2024 balance-sheet indicators.
- The complete 2025 public-entity subsidy ledger: 107 records, 62 beneficiaries, €1.48M paid, purposes, legal bases, and direct page links. Natural-person records are excluded from the browser bundle.
- Profiles for all 30 parishes with official display names, NIF, elector counts, €963,973.84 paid in 2025, current/capital splits, supported works, and source pages.
- Parish procurement cross-matched by NIF against the national IMPIC archives: 248 contracts from 2012–2026, €5.08M in published value, supplier counts, latest awards, procedures, and direct BASE links for 25 parishes with published records.
- 2026 State funding from DGAL's official Map 13: €3.04M across the 30 parishes, separated into Fundo de Financiamento das Freguesias and the statutory excess.
- Direct source links from every contract and finance section.
- Source synchronization script for monitoring official dataset and municipal archive metadata.

The decisions archive and CAOP parish geometry remain source indexes rather than complete record-level databases. They are deliberately labelled as such in the UI.

## Refresh structured data

```bash
npm run sync:contracts
npm run sync:finances
npm run sync:minutes
npm run sync:subsidies
```

The contract job downloads the official yearly IMPIC archives, filters contracting entity NIPC `506881784`, normalizes records, links modifications by contract ID, and emits both JSON and browser bundles in `data/processed/`. Raw official downloads are retained locally under the ignored `data/raw/` directory.

The finance job reads the municipality's official account PDFs, verifies selected values against the source text/rendered page, and writes an audit report to `reports/finances-validation.json`.

The subsidy job parses the 2025 individual ledger, reconciles category totals, removes natural-person records before generating public data, enriches parish transfers with the municipality's official directory, cross-matches parish NIFs against locally downloaded IMPIC archives, and imports DGAL's annual State-funding map. Its audit report is `reports/subsidies-validation.json`.

## Refresh source metadata

```bash
python3 scripts/sync_sources.py
```

This checks official public pages and writes `data/source-health.json`. Contract and finance refreshes are separate because the IMPIC archives and annual accounts are much larger.

## Data principles

1. Every published number must identify its source and reference year.
2. Original documents remain authoritative.
3. Amounts, dates, NIF/NIPC values, and vote results are never rewritten by an LLM.
4. Missing data is shown as missing—not estimated.
5. Personal data unnecessary for public scrutiny is not republished.

## Remaining ingestion milestones

1. Extend annual-account extraction to 2020–2023 and reconcile with DGAL's structured accounts.
2. Extract structured agenda items and voting outcomes from executive minutes.
3. Import CAOP geometry and add the parish-level map.
4. Recover record-level subsidy and parish-transfer history for 2024 and earlier (the 2024 PDF uses a non-extractable embedded font map).
