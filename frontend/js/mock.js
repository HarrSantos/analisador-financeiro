/*
 * Dados fictícios locais: nada é buscado nem enviado.
 * Os formatos espelham a API:
 *   ANALISES  -> /api/analise/listar
 *   RESULTADO -> /api/analise/resultado/15
 */

const USUARIO = { nome: 'Ana Souza' };


/* ---------- Utilitários do mock ---------- */

// O Python imprime floats como 9840.0; o texto das anomalias imita isso
function formatarFloatComoPython(numero) {
  return Number.isInteger(numero) ? numero.toFixed(1) : String(numero);
}

// Gerador pseudoaleatório com semente fixa: o mock é sempre o mesmo
function criarGeradorAleatorio(semente) {
  let estado = semente;

  return () => {
    estado = estado * 16807 % 2147483647;
    return estado / 2147483647;
  };
}

const proximoAleatorio = criarGeradorAleatorio(2026);

const CATEGORIAS = ['Fornecedores', 'Marketing', 'Infraestrutura', 'Folha', 'Viagens', 'Impostos'];


/* ---------- Resultado da análise #15 ---------- */

// Linhas que serão anomalias, com seus valores e nível
const ANOMALIAS_DEFINIDAS = {
  7: { valor: 9840, quantidade: 1, nivel: 'ALTO' },
  34: { valor: 7215.9, quantidade: 2, nivel: 'ALTO' },
  77: { valor: 6980.5, quantidade: 1, nivel: 'ALTO' },
  28: { valor: 4120, quantidade: 3, nivel: 'MEDIO' },
  58: { valor: 3890.75, quantidade: 2, nivel: 'MEDIO' },
  85: { valor: 15.9, quantidade: 48, nivel: 'MEDIO' },
  104: { valor: 3560, quantidade: 1, nivel: 'MEDIO' },
  19: { valor: 2480, quantidade: 2, nivel: 'BAIXO' },
  47: { valor: 2310.4, quantidade: 1, nivel: 'BAIXO' },
  63: { valor: 8.5, quantidade: 31, nivel: 'BAIXO' },
  96: { valor: 2195, quantidade: 3, nivel: 'BAIXO' },
  113: { valor: 2050.9, quantidade: 2, nivel: 'BAIXO' },
};

function gerarRegistros(totalRegistros) {
  return Array.from({ length: totalRegistros }, (_, indice) => {
    const numeroLinha = indice + 1;
    const anomalia = ANOMALIAS_DEFINIDAS[numeroLinha];

    // A ordem das chamadas a proximoAleatorio() define os valores gerados
    const dia = String(1 + Math.floor(proximoAleatorio() * 31)).padStart(2, '0');
    const categoria = CATEGORIAS[Math.floor(proximoAleatorio() * 6)];
    const valor = anomalia
      ? anomalia.valor
      : Math.round((40 + proximoAleatorio() * 860) * 100) / 100;
    const quantidade = anomalia
      ? anomalia.quantidade
      : 1 + Math.floor(proximoAleatorio() * 9);

    return {
      id_transacao: 1000 + numeroLinha,
      data: `2026-10-${dia}`,
      categoria,
      valor,
      quantidade,
    };
  });
}

const registros = gerarRegistros(120);

const anomalias = Object.keys(ANOMALIAS_DEFINIDAS)
  .map(Number)
  .sort((a, b) => a - b)
  .map((numeroLinha, indice) => {
    const { valor, quantidade, nivel } = ANOMALIAS_DEFINIDAS[numeroLinha];
    const valorTexto = formatarFloatComoPython(valor);
    const quantidadeTexto = formatarFloatComoPython(quantidade);

    return {
      id: indice + 1,
      importacao_id: 15,
      nivel,
      descricao: `Combinação atípica detectada: valor: ${valorTexto}, quantidade: ${quantidadeTexto}.`,
      numero_linha: numeroLinha,
      dados: registros[numeroLinha - 1],
    };
  });

const colunas = {
  id_transacao: { tipo: 'numerico', papel: 'identificador' },
  data: { tipo: 'texto', papel: 'temporal' },
  categoria: { tipo: 'texto', papel: 'categorico' },
  valor: { tipo: 'numerico', papel: 'nao_identificador' },
  quantidade: { tipo: 'numerico', papel: 'nao_identificador' },
};

// Mesma regra do backend: só colunas numéricas que não são identificador,
// data ou categoria, e apenas soma, quantidade_valores e media
const PAPEIS_SEM_ESTATISTICA = ['identificador', 'temporal', 'categorico'];

const estatisticas = {
  total_registros: registros.length,
  total_anomalias: anomalias.length,
};

for (const nomeColuna in colunas) {
  const coluna = colunas[nomeColuna];
  const ehNumerica = coluna.tipo === 'numerico';

  if (ehNumerica && !PAPEIS_SEM_ESTATISTICA.includes(coluna.papel)) {
    const soma = registros.reduce((total, registro) => total + registro[nomeColuna], 0);

    estatisticas[nomeColuna] = {
      soma,
      quantidade_valores: registros.length,
      media: soma / registros.length,
    };
  }
}

const RESULTADO = {
  analise: {
    id: 15,
    importacao_id: 15,
    nome_arquivo: 'despesas_outubro.csv',
    data_analise: '2026-11-11T18:54:00',
    status: 'CONCLUIDA',
  },
  registros,
  anomalias,
  estatisticas,
  colunas,
};


/* ---------- Lista de análises (Dashboard e Histórico) ---------- */

// [id, nome_arquivo, data_analise, status]
const LINHAS_ANALISES = [
  [15, 'despesas_outubro.csv', '2026-11-11T18:54:00', 'CONCLUIDA'],
  [14, 'vendas_q3_2026.csv', '2026-11-09T14:20:00', 'CONCLUIDA'],
  [13, 'fluxo_caixa_novembro.csv', '2026-11-08T09:05:00', 'PROCESSANDO'],
  [12, 'extrato_cartao_out.csv', '2026-11-05T21:40:00', 'CONCLUIDA'],
  [11, 'folha_pagamento_set.csv', '2026-11-03T16:12:00', 'ERRO'],
  [10, 'contas_a_pagar.csv', '2026-10-30T11:33:00', 'CONCLUIDA'],
  [9, 'receitas_setembro.csv', '2026-10-27T08:48:00', 'CONCLUIDA'],
  [8, 'transacoes_pix_out.csv', '2026-10-24T19:26:00', 'PENDENTE'],
  [7, 'compras_fornecedores.csv', '2026-10-21T15:02:00', 'CONCLUIDA'],
  [6, 'despesas_setembro.csv', '2026-10-18T10:15:00', 'CONCLUIDA'],
  [5, 'vendas_q2_2026.csv', '2026-10-14T13:37:00', 'CONCLUIDA'],
  [4, 'extrato_cartao_set.csv', '2026-10-11T20:09:00', 'ERRO'],
  [3, 'fluxo_caixa_outubro.csv', '2026-10-08T17:51:00', 'CONCLUIDA'],
  [2, 'receitas_agosto.csv', '2026-10-06T09:28:00', 'CONCLUIDA'],
  [1, 'teste_ml_01.csv', '2026-10-05T22:14:00', 'CONCLUIDA'],
];

const ANALISES = LINHAS_ANALISES.map(([id, nome_arquivo, data_analise, status]) => ({
  id,
  nome_arquivo,
  data_analise,
  status,
}));

// [registros, anomalias] de cada análise concluída.
// Na API esses números vêm de /resultado, não de /listar.
const TOTAIS_POR_ANALISE = {
  1: [15, 2],
  2: [88, 9],
  3: [96, 10],
  5: [210, 21],
  6: [134, 13],
  7: [75, 8],
  9: [142, 14],
  10: [63, 6],
  12: [180, 18],
  14: [320, 32],
  15: [registros.length, anomalias.length],
};
