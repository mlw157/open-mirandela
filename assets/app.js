(function () {
  "use strict";

  const data = window.OPEN_MIRANDELA_DATA;
  const contractData = window.OPEN_MIRANDELA_CONTRACTS;
  const financeData = window.OPEN_MIRANDELA_FINANCES;
  const minutesData = window.OPEN_MIRANDELA_MINUTES;
  const subsidyData = window.OPEN_MIRANDELA_SUBSIDIES;
  if (contractData) {
    data.headline.contractCount = contractData.summary.contract_count;
    data.headline.supplierCount = contractData.summary.supplier_count;
    data.headline.contractSnapshotDate = "arquivo IMPIC 2012–2026";
  }
  const app = document.querySelector("#app");
  const money = new Intl.NumberFormat("pt-PT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
  const integer = new Intl.NumberFormat("pt-PT");

  const navItems = [
    ["overview", "Visão geral"],
    ["finances", "Finanças"],
    ["contracts", "Contratos"],
    ["subsidies", "Subsídios"],
    ["parishes", "Freguesias"],
    ["decisions", "Deliberações"]
  ];

  let activeView = "overview";
  let financeYear = 2025;
  const contractFilters = { year: "all", category: "all", procedure: "all", search: "" };
  const subsidyFilters = { category: "all", search: "" };
  let parishSearch = "";

  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  }

  function percent(value, maximum) { return maximum ? Math.max(2, value / maximum * 100) : 0; }

  function sourceLink(id, label = "Abrir fonte") {
    const source = data.sources.find((item) => item.id === id);
    return `<a class="source-link" href="${source.url}" target="_blank" rel="noreferrer">${label}<span aria-hidden="true">↗</span></a>`;
  }

  function statusPill(status) {
    const labels = { verified: "Verificado", ready: "Pronto a importar", "source-ready": "Fonte disponível" };
    return `<span class="status status--${status}"><i></i>${labels[status] || status}</span>`;
  }

  function metricCard({ eyebrow, value, suffix = "", detail, source, tone = "green" }) {
    return `<article class="metric-card metric-card--${tone}" data-search="${eyebrow} ${value} ${detail}">
      <div class="metric-top"><span>${eyebrow}</span><span class="metric-mark" aria-hidden="true"></span></div>
      <p class="metric-value">${value}<small>${suffix}</small></p>
      <p class="metric-detail">${detail}</p>
      ${sourceLink(source, "Fonte")}
    </article>`;
  }

  function masthead() {
    return `<header class="masthead">
      <a class="brand" href="#overview" data-view="overview" aria-label="Ver Mirandela, início">
        <strong>Ver Mirandela</strong>
      </a>
      <nav class="main-nav" aria-label="Navegação principal">
        ${navItems.map(([id, label]) => `<a href="#${id}" data-view="${id}" class="${activeView === id ? "is-active" : ""}">${label}</a>`).join("")}
      </nav>
    </header>`;
  }

  function overview() {
    const latestFinance = financeData.years.at(-1);
    const nonprofit = latestFinance.transfers.find(([label]) => label === "Instituições sem fins lucrativos")[1];
    const parishes = latestFinance.transfers.find(([label]) => label === "Freguesias")[1];
    return `<section class="view view--overview">
      <div class="hero-grid">
        <div class="hero-copy">
          <div class="kicker"><span></span>Dados públicos de Mirandela</div>
          <h1>Mirandela,<br><em>em números.</em></h1>
          <p class="hero-lede">Contas, contratos, apoios, freguesias e decisões municipais num só lugar.</p>
          <div class="hero-actions">
            <button class="button button--primary" data-view="finances">Ver as finanças <span>→</span></button>
          </div>
        </div>
      </div>

      <div class="section-heading">
        <div><span class="section-number">01</span><h2>Um retrato em números</h2></div>
        <p>Dados oficiais, com o ano indicado.</p>
      </div>
      <div class="metrics-grid">
        ${metricCard({ eyebrow: "Apoios a instituições", value: money.format(nonprofit), detail: `Instituições sem fins lucrativos · ${latestFinance.year}`, source: "pec", tone: "gold" })}
        ${metricCard({ eyebrow: "Juntas de freguesia", value: money.format(parishes), detail: `Transferências correntes · ${latestFinance.year}`, source: "pec", tone: "rust" })}
        ${metricCard({ eyebrow: "Contratos registados", value: integer.format(data.headline.contractCount), detail: `Snapshot oficial · ${data.headline.contractSnapshotDate}`, source: "transparency", tone: "green" })}
        ${metricCard({ eyebrow: "Fornecedores", value: integer.format(data.headline.supplierCount), detail: "Entidades no snapshot de contratação", source: "transparency", tone: "ink" })}
      </div>

      <div class="split-section">
        <article class="feature-panel feature-panel--dark">
          <div class="panel-label">Em foco · ${latestFinance.year}</div>
          <h2>Para onde foram as transferências correntes?</h2>
          <div class="comparison-bars">
            <div><span>Instituições sem fins lucrativos</span><b style="--size: 100%"></b><strong>${money.format(nonprofit)}</strong></div>
            <div><span>Juntas de freguesia</span><b style="--size: ${nonprofit ? parishes / nonprofit * 100 : 0}%"></b><strong>${money.format(parishes)}</strong></div>
          </div>
          <p>Consulte cada entidade apoiada, a finalidade e o valor pago.</p>
          <button class="text-button text-button--light" data-view="subsidies">Ver os beneficiários <span>→</span></button>
        </article>
        <article class="feature-panel feature-panel--paper">
          <div class="panel-label">Reuniões municipais</div>
          <p class="big-number">${data.meeting2024.count}</p>
          <h2>atas do executivo em 2024</h2>
          <p>Abra diretamente cada ata publicada pelo Município.</p>
          <button class="text-button" data-view="decisions">Explorar o arquivo <span>→</span></button>
        </article>
      </div>
    </section>`;
  }

  function finances() {
    const row = financeData.years.find((item) => item.year === financeYear) || financeData.years.at(-1);
    const revenueMax = Math.max(...row.revenue_categories.map((item) => item[1]));
    const expenseMax = Math.max(...row.expense_categories.map((item) => item[1]));
    return `<section class="view inner-view">
      <div class="page-intro"><div><span class="section-number">02</span><p>Finanças</p></div><h1>Receitas e<br>despesas.</h1><p>Contas oficiais do Município, com ligação às páginas de origem.</p></div>
      <div class="data-toolbar"><div class="segmented" aria-label="Ano">${financeData.years.map((item) => `<button class="${item.year === row.year ? "is-active" : ""}" data-finance-year="${item.year}">${item.year}</button>`).join("")}</div><a class="source-link" href="${row.source_url}" target="_blank" rel="noreferrer">Prestação de contas ${row.year} ↗</a></div>
      <div class="finance-kpis">
        <div><span>Receita cobrada</span><strong>${money.format(row.revenue.total)}</strong><small>${row.execution.revenue}% de execução · págs. ${row.pages.revenue.join(" e ")}</small></div>
        <div><span>Despesa paga</span><strong>${money.format(row.expense.total)}</strong><small>Corrente + capital · págs. ${row.pages.expense.join(" e ")}</small></div>
        <div><span>Dívida total</span><strong>${money.format(row.debt.total)}</strong><small>Margem disponível ${money.format(row.debt.margin)}</small></div>
      </div>
      <div class="finance-breakdown">
        <article class="breakdown-card"><div class="card-heading"><div><span>Receita corrente</span><h2>${money.format(row.revenue.current)}</h2></div>${statusPill("verified")}</div><div class="rank-bars">${row.revenue_categories.map(([label, value]) => `<div><span>${esc(label)}</span><i><b style="width:${percent(value, revenueMax)}%"></b></i><strong>${money.format(value)}</strong></div>`).join("")}</div></article>
        <article class="breakdown-card"><div class="card-heading"><div><span>Despesa corrente</span><h2>${money.format(row.expense.current)}</h2></div>${statusPill("verified")}</div><div class="rank-bars">${row.expense_categories.map(([label, value]) => `<div><span>${esc(label)}</span><i><b style="width:${percent(value, expenseMax)}%"></b></i><strong>${money.format(value)}</strong></div>`).join("")}</div></article>
      </div>
      <div class="finance-layout">
        <article class="ledger-card"><div class="card-heading"><div><span>Transferências correntes</span><h2>Destinatários · ${row.year}</h2></div>${statusPill("verified")}</div>${row.transfers.map(([label, value], index) => `<div class="ledger-row"><span class="ledger-index">${String(index + 1).padStart(2, "0")}</span><div><strong>${esc(label)}</strong></div><b>${money.format(value)}</b></div>`).join("")}<footer><a class="source-link" href="${row.source_url}#page=${row.pages.transfers[0]}" target="_blank" rel="noreferrer">Ver páginas ${row.pages.transfers.join("–")} ↗</a></footer></article>
        <aside class="debt-card"><span class="panel-label">Endividamento · ${row.year}</span><h2>${money.format(row.debt.relevant)}</h2><p>Dívida relevante para o limite legal</p><dl><div><dt>Limite legal</dt><dd>${money.format(row.debt.limit)}</dd></div><div><dt>Dívida total</dt><dd>${money.format(row.debt.total)}</dd></div><div><dt>Margem absoluta</dt><dd>${money.format(row.debt.margin)}</dd></div></dl>${row.balance ? `<div class="balance-note"><b>${money.format(row.balance.assets)}</b><span>Ativo total</span><b>${money.format(row.balance.liabilities)}</b><span>Passivo total</span></div>` : ""}<a class="source-link" href="${row.source_url}#page=${row.pages.debt[0]}" target="_blank" rel="noreferrer">Quadro da dívida ↗</a></aside>
      </div>
      <div class="method-note"><span>Método</span><p>Valores das tabelas narrativas</p><i>→</i><p>Validação no texto/PDF renderizado</p><i>→</i><p>Página oficial ligada</p></div>
    </section>`;
  }

  function contracts() {
    const summary = contractData.summary;
    const years = [...summary.years].reverse();
    const matches = contractData.contracts.filter((row) => {
      const haystack = `${row.object} ${row.procedure} ${row.suppliers.map((supplier) => supplier.name).join(" ")}`.toLowerCase();
      return (contractFilters.year === "all" || String(row.year) === contractFilters.year)
        && (contractFilters.category === "all" || row.category === contractFilters.category)
        && (contractFilters.procedure === "all" || row.procedure === contractFilters.procedure)
        && (!contractFilters.search || haystack.includes(contractFilters.search.toLowerCase()));
    });
    const visible = matches.slice(0, 60);
    const maxYear = Math.max(...summary.years.map((item) => item.value));
    const maxSupplier = summary.top_suppliers[0].allocated_value;
    return `<section class="view inner-view">
      <div class="page-intro"><div><span class="section-number">03</span><p>Contratos</p></div><h1>Contratos do<br>Município.</h1><p>Objeto, fornecedor, procedimento e valor, com ligação ao Portal BASE.</p></div>
      <div class="snapshot-banner"><div><span>Contratos 2012–2026</span><strong>${integer.format(summary.contract_count)}</strong><small>${summary.modified_contract_count} com modificações</small></div><div><span>Valor contratual</span><strong>${money.format(summary.total_value)}</strong><small>soma publicada, sem IVA</small></div><div><span>Fornecedores</span><strong>${integer.format(summary.supplier_count)}</strong><small>normalizados por NIF</small></div></div>
      <div class="contract-analytics">
        <article class="year-chart"><div class="card-heading"><div><span>Evolução anual</span><h2>Valor contratual</h2></div>${statusPill("verified")}</div><div class="vertical-bars">${years.map((item) => `<button title="${item.year}: ${money.format(item.value)} · ${item.count} contratos" data-contract-year="${item.year}" class="${contractFilters.year === String(item.year) ? "is-active" : ""}"><i style="height:${percent(item.value, maxYear)}%"></i><span>${String(item.year).slice(2)}</span></button>`).join("")}</div></article>
        <article class="supplier-card"><div class="card-heading"><div><span>Fornecedores</span><h2>Maiores valores atribuídos</h2></div></div><div class="rank-bars rank-bars--compact">${summary.top_suppliers.slice(0, 8).map((supplier) => `<div><span>${esc(supplier.name)}</span><i><b style="width:${percent(supplier.allocated_value, maxSupplier)}%"></b></i><strong>${money.format(supplier.allocated_value)}</strong></div>`).join("")}</div><p>Em consórcios, o valor é repartido igualmente pelos NIF participantes para evitar dupla contagem.</p></article>
      </div>
      <div class="contract-toolbar"><label><span>Pesquisar</span><input type="search" value="${esc(contractFilters.search)}" placeholder="Objeto, fornecedor, procedimento…" data-contract-search /></label><label><span>Ano</span><select data-contract-filter="year"><option value="all">Todos</option>${years.map((item) => `<option ${contractFilters.year === String(item.year) ? "selected" : ""}>${item.year}</option>`).join("")}</select></label><label><span>Categoria</span><select data-contract-filter="category"><option value="all">Todas</option>${summary.categories.map((item) => `<option ${contractFilters.category === item.category ? "selected" : ""}>${item.category}</option>`).join("")}</select></label><label><span>Procedimento</span><select data-contract-filter="procedure"><option value="all">Todos</option>${summary.procedures.map((item) => `<option ${contractFilters.procedure === item.procedure ? "selected" : ""}>${esc(item.procedure)}</option>`).join("")}</select></label><b>${integer.format(matches.length)} resultados</b></div>
      <div class="contract-table"><div class="contract-row contract-row--head"><span>Data / categoria</span><span>Objeto e fornecedor</span><span>Procedimento</span><span>Valor</span><span></span></div>${visible.map((row) => `<a class="contract-row" href="${row.base_url}" target="_blank" rel="noreferrer"><span><b>${esc(row.publication_date || row.contract_date || row.year)}</b><small>${esc(row.category)}${row.modifications.length ? ` · ${row.modifications.length} mod.` : ""}</small></span><span><strong>${esc(row.object || "Sem descrição")}</strong><small>${esc(row.suppliers.map((supplier) => supplier.name).join(" · ") || "Fornecedor não indicado")}</small></span><span>${esc(row.procedure || "Não indicado")}</span><span><b>${money.format(row.contract_price)}</b><small>BASE #${esc(row.id)}</small></span><span>↗</span></a>`).join("")}</div>
      ${matches.length > visible.length ? `<p class="results-note">A mostrar os primeiros ${visible.length} de ${integer.format(matches.length)} resultados. Use os filtros para restringir a lista.</p>` : ""}
    </section>`;
  }

  function subsidies() {
    const summary = subsidyData.summary;
    const categories = summary.category_totals;
    const matches = subsidyData.records.filter((row) => {
      const haystack = `${row.name} ${row.purpose} ${row.legal_basis} ${row.nif} ${row.observations}`.toLowerCase();
      return (subsidyFilters.category === "all" || row.category === subsidyFilters.category)
        && (!subsidyFilters.search || haystack.includes(subsidyFilters.search.toLowerCase()));
    });
    const visible = matches.slice(0, 80);
    const top = subsidyData.beneficiaries.slice(0, 10);
    const maxBeneficiary = top[0]?.paid || 1;
    return `<section class="view inner-view">
      <div class="page-intro"><div><span class="section-number">04</span><p>Subsídios</p></div><h1>Apoios municipais<br>em 2025.</h1><p>Entidades apoiadas, finalidade e valor pago.</p></div>
      <div class="snapshot-banner support-snapshot"><div><span>Valor pago</span><strong>${money.format(summary.paid_total)}</strong><small>${money.format(summary.authorized_total)} autorizado</small></div><div><span>Beneficiários</span><strong>${integer.format(summary.beneficiary_count)}</strong><small>entidades coletivas distintas</small></div><div><span>Registos públicos</span><strong>${integer.format(summary.record_count)}</strong><small>apoios individualizados em 2025</small></div></div>
      <div class="support-layout">
        <article class="breakdown-card"><div class="card-heading"><div><span>Maiores beneficiários</span><h2>Valor efetivamente pago</h2></div>${statusPill("verified")}</div><div class="rank-bars rank-bars--compact">${top.map((row) => `<div><span title="${esc(row.name)}">${esc(row.name)}</span><i><b style="width:${percent(row.paid, maxBeneficiary)}%"></b></i><strong>${money.format(row.paid)}</strong></div>`).join("")}</div></article>
        <article class="breakdown-card category-card"><div class="card-heading"><div><span>Natureza do apoio</span><h2>${summary.record_count} registos</h2></div></div>${categories.map((row) => `<div class="category-row"><div><strong>${esc(row.category)}</strong><small>${integer.format(row.records)} registos</small></div><b>${money.format(row.paid)}</b></div>`).join("")}<div class="privacy-note"><span>Privacidade</span><p>${integer.format(summary.excluded_natural_person_records)} linhas relativas a pessoas singulares foram excluídas do ficheiro público. Os respetivos nomes e NIF nunca são enviados para o navegador.</p></div></article>
      </div>
      <div class="support-toolbar"><label><span>Pesquisar</span><input type="search" value="${esc(subsidyFilters.search)}" placeholder="Beneficiário, finalidade, NIF…" data-subsidy-search /></label><label><span>Categoria</span><select data-subsidy-category><option value="all">Todas</option>${categories.map((row) => `<option value="${esc(row.category)}" ${subsidyFilters.category === row.category ? "selected" : ""}>${esc(row.category)}</option>`).join("")}</select></label><b>${integer.format(matches.length)} resultados</b></div>
      <div class="support-table"><div class="support-row support-row--head"><span>Beneficiário</span><span>Finalidade / fundamento</span><span>Pago</span><span></span></div>${visible.map((row) => `<a class="support-row" href="${row.source_url}" target="_blank" rel="noreferrer"><span><strong>${esc(row.name)}</strong><small>${esc(row.category)} · NIF ${esc(row.nif)}</small></span><span><b>${esc(row.purpose || "Finalidade não indicada")}</b><small>${esc(row.legal_basis)}${row.observations ? ` · ${esc(row.observations)}` : ""}</small></span><span><strong>${money.format(row.paid)}</strong><small>${money.format(row.authorized)} autorizado${row.unpaid ? ` · ${money.format(row.unpaid)} por pagar` : ""}</small></span><span>↗</span></a>`).join("")}</div>
      ${matches.length > visible.length ? `<p class="results-note">A mostrar os primeiros ${visible.length} de ${integer.format(matches.length)} registos. Use a pesquisa para restringir a lista.</p>` : ""}
    </section>`;
  }

  function parishes() {
    const parishData = subsidyData.parishes;
    const contractSummary = parishData.contracts_summary;
    const stateFunding = parishData.state_funding_summary;
    const matches = parishData.records.filter((row) => `${row.display_name} ${row.nif} ${row.purposes.join(" ")} ${row.contracts.map((contract) => `${contract.object} ${contract.procedure} ${contract.suppliers.map((supplier) => supplier.name).join(" ")}`).join(" ")}`.toLowerCase().includes(parishSearch.toLowerCase()));
    return `<section class="view inner-view">
      <div class="page-intro"><div><span class="section-number">05</span><p>Freguesias</p></div><h1>As 30<br>freguesias.</h1><p>Transferências, financiamento do Estado e contratos de cada Junta.</p></div>
      <div class="snapshot-banner parish-snapshot"><div><span>Total pago</span><strong>${money.format(parishData.summary.paid_total)}</strong><small>corrente + capital em 2025</small></div><div><span>Transferências correntes</span><strong>${money.format(parishData.summary.current_paid)}</strong><small>funcionamento e protocolos</small></div><div><span>Transferências de capital</span><strong>${money.format(parishData.summary.capital_paid)}</strong><small>obras e investimento local</small></div></div>
      <aside class="state-funding-overview"><div><span>Financiamento do Estado · ${stateFunding.year}</span><strong>${money.format(stateFunding.total)}</strong><small>atribuição legal às 30 freguesias</small></div><div><span>FFF</span><b>${money.format(stateFunding.fff)}</b><small>Fundo de Financiamento das Freguesias</small></div><div><span>Excedente</span><b>${money.format(stateFunding.excess)}</b><small>artigo 38.º, n.º 8</small></div><a href="${stateFunding.source_url}" target="_blank" rel="noreferrer">Mapa 13 · DGAL ↗</a></aside>
      <aside class="parish-contract-overview"><div><span class="panel-label">Contratação das juntas · ${contractSummary.coverage.join("–")}</span><h2>${integer.format(contractSummary.count)} contratos publicados</h2><p>Compras, serviços e obras adjudicados pelas próprias freguesias — não confundir com contratos do Município executados no seu território.</p></div><dl><div><dt>Valor contratual</dt><dd>${money.format(contractSummary.value)}</dd></div><div><dt>Com registos</dt><dd>${contractSummary.parishes_with_contracts} / ${parishData.summary.count}</dd></div></dl><a href="https://www.base.gov.pt/Base4/pt/pesquisa" target="_blank" rel="noreferrer">Pesquisar no BASE ↗</a></aside>
      <div class="parish-toolbar"><label><span>Pesquisar freguesia, intervenção ou fornecedor</span><input type="search" value="${esc(parishSearch)}" placeholder="Ex.: cemitério, pavimentação, fornecedor…" data-parish-search /></label><div><b>${matches.length}</b> de ${parishData.summary.count} freguesias · <a href="${parishData.directory_url}" target="_blank" rel="noreferrer">diretório oficial ↗</a></div></div>
      <div class="parish-grid">${matches.map((row, index) => `<article class="parish-card"><header><span>${String(index + 1).padStart(2, "0")}</span><div><h2>${esc(row.display_name)}</h2><p>NIF ${esc(row.nif)} · ${integer.format(row.electors)} eleitores inscritos</p></div></header><div class="parish-money"><div><span>Recebido do Município</span><strong>${money.format(row.paid)}</strong></div><div><span>Corrente</span><b>${money.format(row.current_paid)}</b></div><div><span>Capital</span><b>${money.format(row.capital_paid)}</b></div></div><div class="parish-state-money"><span>Estado · ${stateFunding.year}</span><strong>${money.format(row.state_total_2026)}</strong><small>FFF ${money.format(row.state_fff_2026)} · excedente ${money.format(row.state_excess_2026)}</small></div><div class="parish-purposes"><span>Finalidades das transferências municipais</span><ul>${row.purposes.slice(0, 3).map((purpose) => `<li>${esc(purpose)}</li>`).join("")}</ul>${row.purposes.length > 3 ? `<small>+ ${row.purposes.length - 3} outras finalidades no documento</small>` : ""}</div><details class="parish-contracts"><summary><span>Contratos da Junta</span><b>${row.contract_count ? `${integer.format(row.contract_count)} · ${money.format(row.contract_value)}` : "Sem registos no BASE"}</b><i>⌄</i></summary>${row.contract_count ? `<div class="contract-mini-stats"><div><span>Contratos</span><b>${integer.format(row.contract_count)}</b></div><div><span>Fornecedores</span><b>${integer.format(row.supplier_count)}</b></div><div><span>Valor publicado</span><b>${money.format(row.contract_value)}</b></div></div><div class="parish-contract-list">${row.contracts.slice(0, 5).map((contract) => `<a href="${contract.url}" target="_blank" rel="noreferrer"><span><b>${esc(contract.object || "Sem descrição")}</b><small>${esc(contract.suppliers.map((supplier) => supplier.name).join(" · ") || "Fornecedor não indicado")} · ${esc(contract.procedure || "Procedimento não indicado")}</small></span><strong>${money.format(contract.price)}<small>${contract.year}</small></strong><i>↗</i></a>`).join("")}</div>${row.contracts.length > 5 ? `<p>Últimos 5 de ${row.contracts.length} contratos.</p>` : ""}` : `<p>Não encontrámos contratos publicados com o NIF desta freguesia nos arquivos IMPIC de ${contractSummary.coverage.join("–")}. Isto não prova ausência de despesa ou contratação.</p>`}</details><footer><span>${row.record_count} transferências · págs. ${row.pages.join(", ")}</span><a href="${subsidyData.meta.source_url}#page=${row.pages[0]}" target="_blank" rel="noreferrer">Ver contas ↗</a></footer></article>`).join("") || `<p class="no-results">Nenhuma freguesia corresponde à pesquisa.</p>`}</div>
      <div class="method-note"><span>Nota</span><p>Transferências e contratos são fluxos diferentes; não devem ser somados.</p><i>→</i><p>“Eleitores” não significa população residente.</p>${sourceLink("caop", "Fonte cartográfica")}</div>
    </section>`;
  }

  function decisions() {
    const records = minutesData.records;
    return `<section class="view inner-view">
      <div class="page-intro"><div><span class="section-number">06</span><p>Deliberações</p></div><h1>Reuniões<br>municipais.</h1><p>Atas de 2024 com ligação direta ao documento publicado.</p></div>
      <div class="archive-layout"><aside><span class="panel-label">Arquivo</span><strong>${minutesData.records.length}</strong><p>atas publicadas em 2024</p>${sourceLink("minutes", "Arquivo completo")}</aside><div class="document-list">${records.map((record, index) => `<a href="${record.url}" target="_blank" rel="noreferrer" data-search="${esc(record.title)} 2024"><span>${String(index + 1).padStart(2, "0")}</span><div><strong>${esc(record.title)}</strong><small>Reunião do Executivo Camarário · PDF oficial</small></div><b>PDF ↗</b></a>`).join("") || `<p class="no-results">Nenhuma ata corresponde à pesquisa.</p>`}</div></div>
    </section>`;
  }

  function footer() {
    return `<footer class="site-footer"><div><strong>Ver Mirandela</strong></div><div><span>Atualizado</span><b>${new Date(data.meta.updated).toLocaleDateString("pt-PT")}</b></div></footer>`;
  }

  function render() {
    const views = { overview, finances, contracts, subsidies, parishes, decisions };
    app.innerHTML = `<div class="shell">${masthead()}<main id="main">${views[activeView]()}</main>${footer()}</div>`;
    bindEvents();
    document.title = `${navItems.find(([id]) => id === activeView)[1]} — Ver Mirandela`;
  }

  function setView(view) {
    if (!navItems.some(([id]) => id === view)) return;
    activeView = view;
    window.history.replaceState(null, "", `#${view}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
    render();
  }

  function bindEvents() {
    document.querySelectorAll("[data-view]").forEach((element) => element.addEventListener("click", (event) => {
      event.preventDefault();
      setView(element.dataset.view);
    }));
    document.querySelectorAll("[data-finance-year]").forEach((button) => button.addEventListener("click", () => { financeYear = Number(button.dataset.financeYear); render(); }));
    document.querySelectorAll("[data-contract-year]").forEach((button) => button.addEventListener("click", () => { contractFilters.year = contractFilters.year === button.dataset.contractYear ? "all" : button.dataset.contractYear; render(); }));
    document.querySelectorAll("[data-contract-filter]").forEach((select) => select.addEventListener("change", () => { contractFilters[select.dataset.contractFilter] = select.value; render(); }));
    document.querySelector("[data-contract-search]")?.addEventListener("input", (event) => { contractFilters.search = event.target.value; render(); const input = document.querySelector("[data-contract-search]"); input?.focus(); input?.setSelectionRange(input.value.length, input.value.length); });
    document.querySelector("[data-subsidy-category]")?.addEventListener("change", (event) => { subsidyFilters.category = event.target.value; render(); });
    document.querySelector("[data-subsidy-search]")?.addEventListener("input", (event) => { subsidyFilters.search = event.target.value; render(); const input = document.querySelector("[data-subsidy-search]"); input?.focus(); input?.setSelectionRange(input.value.length, input.value.length); });
    document.querySelector("[data-parish-search]")?.addEventListener("input", (event) => { parishSearch = event.target.value; render(); const input = document.querySelector("[data-parish-search]"); input?.focus(); input?.setSelectionRange(input.value.length, input.value.length); });
  }

  const initial = window.location.hash.slice(1);
  if (navItems.some(([id]) => id === initial)) activeView = initial;
  render();
})();
