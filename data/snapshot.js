window.OPEN_MIRANDELA_DATA = {
  meta: {
    updated: "2026-08-05",
    municipalityNipc: "506881784",
    municipalityCode: "0407",
    status: "Arquivo público em expansão"
  },
  headline: {
    population: 21296,
    populationYear: 2022,
    areaKm2: 659,
    parishes: 30,
    contractCount: 694,
    supplierCount: 350,
    contractSnapshotDate: "2025-06-17"
  },
  finance2024: {
    nonprofitTransfers: 986668.5,
    parishCurrentTransfers: 555255,
    nonprofitShareLabel: "maior rubrica de transferências correntes",
    parishDirection: "aumento face a 2023"
  },
  financeSeries: [
    { year: 2020, status: "source-ready" },
    { year: 2021, status: "source-ready" },
    { year: 2022, status: "source-ready" },
    { year: 2023, status: "source-ready" },
    { year: 2024, status: "verified" },
    { year: 2025, status: "source-ready" }
  ],
  meeting2024: {
    count: 26,
    dates: [
      "26 de dezembro", "12 de dezembro", "28 de novembro", "14 de novembro",
      "31 de outubro", "17 de outubro", "03 de outubro", "23 de setembro",
      "19 de setembro", "05 de setembro", "22 de agosto", "08 de agosto",
      "31 de julho", "11 de julho", "21 de junho", "13 de junho",
      "31 de maio", "16 de maio", "02 de maio", "18 de abril",
      "21 de março", "07 de março", "22 de fevereiro", "08 de fevereiro",
      "25 de janeiro", "11 de janeiro"
    ]
  },
  sources: [
    {
      id: "pec",
      name: "Prestação de Contas 2025",
      owner: "Município de Mirandela",
      kind: "PDF",
      cadence: "Anual",
      coverage: "2012–2025",
      status: "verified",
      url: "https://www.cm-mirandela.pt/cmmirandela/uploads/document/file/8237/prestacao_de_contas_2025.pdf",
      note: "Fonte dos indicadores financeiros mais recentes; 2024 também está estruturado no explorador."
    },
    {
      id: "subsidies",
      name: "Transferências e Subsídios Concedidos 2025",
      owner: "Município de Mirandela",
      kind: "PDF · registos",
      cadence: "Anual",
      coverage: "2025 · págs. 213–233",
      status: "verified",
      url: "https://www.cm-mirandela.pt/cmmirandela/uploads/document/file/8237/prestacao_de_contas_2025.pdf#page=213",
      note: "107 apoios a 62 entidades coletivas e transferências individualizadas às 30 freguesias; pessoas singulares excluídas do ficheiro público."
    },
    {
      id: "impic",
      name: "Contratos públicos 2012–2026",
      owner: "IMPIC / Portal BASE",
      kind: "JSON · XLSX",
      cadence: "Semanal",
      coverage: "2012–2026",
      status: "verified",
      url: "https://dados.gov.pt/datasets/contratos-publicos-portal-base-impic-contratos-de-2012-a-2026",
      note: "1.474 contratos do Município e 248 contratos das 30 freguesias, filtrados pelos respetivos NIF."
    },
    {
      id: "mods",
      name: "Modificações contratuais",
      owner: "IMPIC / Portal BASE",
      kind: "JSON · XLSX",
      cadence: "Semanal",
      coverage: "2012–2026",
      status: "verified",
      url: "https://dados.gov.pt/datasets/contratos-publicos-portal-base-impic-modificacoes-contratuais-de-2012-a-2026",
      note: "Modificações cruzadas pelo identificador único do contrato."
    },
    {
      id: "minutes",
      name: "Atas do Executivo Camarário",
      owner: "Município de Mirandela",
      kind: "PDF",
      cadence: "Quinzenal",
      coverage: "2005–2026",
      status: "verified",
      url: "https://www.cm-mirandela.pt/municipio/camara-municipal/orgaos-e-funcionamento/reunioes-de-camara/reunioes-e-atas-do-executivo-camarario/atas",
      note: "26 atas listadas para 2024; extração de deliberações ainda por implementar."
    },
    {
      id: "dgal",
      name: "Contas de gerência municipais",
      owner: "DGAL",
      kind: "ODS · tabelas",
      cadence: "Anual",
      coverage: "Série histórica",
      status: "ready",
      url: "https://portalautarquico.dgal.gov.pt/pt-PT/financas-locais/dados-financeiros/contas-de-gerencia/",
      note: "Fonte estruturada para reconciliação de receita e despesa."
    },
    {
      id: "profile",
      name: "Perfil municipal 0407",
      owner: "INE",
      kind: "PDF · API",
      cadence: "Anual",
      coverage: "Indicadores municipais",
      status: "verified",
      url: "https://www.ine.pt/documentos/municipios/0407_2023.pdf",
      note: "Fonte da população residente de 2022 apresentada no MVP."
    },
    {
      id: "transparency",
      name: "Bilhete de identidade municipal",
      owner: "Portal da Transparência",
      kind: "Dados abertos",
      cadence: "Variável",
      coverage: "Perfil atual",
      status: "verified",
      url: "https://transparencia.gov.pt/pt/municipios/bi-municipios/municipios/municipio/0407/",
      note: "Indicadores contextuais e lista de freguesias."
    },
    {
      id: "parishDirectory",
      name: "Diretório oficial das freguesias",
      owner: "Município de Mirandela",
      kind: "Página web",
      cadence: "Variável",
      coverage: "30 freguesias",
      status: "verified",
      url: "https://www.cm-mirandela.pt/p/freguesias",
      note: "Denominações oficiais e número de eleitores inscritos usados nos perfis territoriais."
    },
    {
      id: "parishFunding",
      name: "Mapa 13 — Transferências para as Freguesias 2026",
      owner: "DGAL / Orçamento do Estado",
      kind: "PDF · XLSX",
      cadence: "Anual",
      coverage: "2026 · 30 freguesias",
      status: "verified",
      url: "https://portalautarquico.dgal.gov.pt/pt-PT/financas-locais/transferencias/freguesias/",
      note: "FFF e excedente legal individualizados para cada freguesia de Mirandela."
    },
    {
      id: "caop",
      name: "CAOP 2025",
      owner: "Direção-Geral do Território",
      kind: "GeoPackage",
      cadence: "Anual",
      coverage: "Limites oficiais",
      status: "ready",
      url: "https://www.dgterritorio.gov.pt/atividades/cartografia/cartografia-tematica/caop",
      note: "Geometrias oficiais para o futuro mapa de freguesias."
    }
  ]
};
