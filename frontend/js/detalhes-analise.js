const API_URL = 'http://127.0.0.1:5000';


/* ---------- Verificação de sessão ---------- */

async function verificarSessao() {
  try {
    const resposta = await fetch(
      `${API_URL}/api/auth/verificar-sessao`,
      {
        method: 'GET',
        credentials: 'include'
      }
    );

    if (!resposta.ok) {
      location.href = 'login.html';
      return false;
    }

    return true;

  } catch (erro) {
    console.error(erro);
    location.href = 'login.html';
    return false;
  }
}


/* ---------- Identificar análise ---------- */

function obterIdAnalise() {
  const parametros = new URLSearchParams(
    window.location.search
  );

  return parametros.get('id');
}


/* ---------- Buscar resultado ---------- */

async function buscarResultado(analiseId) {
  const resposta = await fetch(
    `${API_URL}/api/analise/resultado/${analiseId}`,
    {
      method: 'GET',
      credentials: 'include'
    }
  );

  const dados = await resposta.json();

  if (!resposta.ok) {
    throw new Error(
      dados.erro || 'Não foi possível carregar a análise.'
    );
  }

  return dados;
}


/* ---------- Dados da análise ---------- */

let analise;
let registrosAnalise = [];
let anomaliasAnalise = [];
let estatisticasAnalise = {};
let colunasAnalise = {};

let nomesColunas = [];


/* ---------- Funções das colunas ---------- */

function colunaEhNumerica(nomeColuna) {
  return colunasAnalise[nomeColuna]?.tipo === 'numerico';
}


/* ---------- Resumo da análise ---------- */

function renderizarResumo() {
  elemento('#arq').textContent =
    analise.nome_arquivo;

  const itensResumo = [
    {
      rotulo: 'ID da análise',
      valor: '#' + analise.id
    },
    {
      rotulo: 'Data',
      valor: formatarDataHora(analise.data_analise)
    },
    {
      rotulo: 'Status',
      valor: badgeStatus(analise.status)
    },
    {
      rotulo: 'Registros',
      valor: formatarNumero(
        estatisticasAnalise.total_registros
      )
    },
    {
      rotulo: 'Anomalias',
      valor: formatarNumero(
        estatisticasAnalise.total_anomalias
      )
    },
    {
      rotulo: 'Colunas',
      valor: nomesColunas.length
    },
  ];

  elemento('#meta').innerHTML = itensResumo
    .map(({ rotulo, valor }) => `
      <div>
        <dt>${rotulo}</dt>
        <dd>${valor}</dd>
      </div>
    `)
    .join('');
}


/* ---------- Estatísticas ---------- */

function cartaoEstatistica(nomeColuna) {
  const {
    media,
    soma,
    quantidade_valores
  } = estatisticasAnalise[nomeColuna];

  return `
    <div class="st">
      <h3>${escaparHtml(nomeColuna)}</h3>

      <strong>
        ${formatarNumero(media, 2)}
      </strong>

      <span class="mut sm">
        média
      </span>

      <dl>
        <div>
          <dt>Soma</dt>
          <dd>
            ${formatarNumero(soma, 2)}
          </dd>
        </div>

        <div>
          <dt>Valores</dt>
          <dd>
            ${formatarNumero(quantidade_valores)}
          </dd>
        </div>
      </dl>
    </div>
  `;
}


function renderizarEstatisticas() {
  const colunasComEstatistica =
    nomesColunas.filter(
      (nomeColuna) =>
        nomeColuna in estatisticasAnalise
    );

  const colunasSemEstatistica =
    nomesColunas.filter(
      (nomeColuna) =>
        !(nomeColuna in estatisticasAnalise)
    );

  elemento('#stats').innerHTML =
    colunasComEstatistica
      .map(cartaoEstatistica)
      .join('');

  if (colunasSemEstatistica.length > 0) {
    elemento('#fora').textContent =
      'Sem estatísticas (não numéricas, identificadores, datas ou categorias): ' +
      colunasSemEstatistica.join(', ') +
      '.';
  } else {
    elemento('#fora').textContent =
      'Todas as colunas possuem estatísticas numéricas.';
  }
}


/* ---------- Anomalias ---------- */

let nivelSelecionado = '';

const filtroNiveis = elemento('#chips');


function descreverDados(dados) {
  return Object.entries(dados)
    .map(
      ([coluna, valor]) =>
        `<span class="kv">
          ${escaparHtml(coluna)}
          <b>${escaparHtml(valor)}</b>
        </span>`
    )
    .join('');
}


function contarAnomaliasDoNivel(nivel) {
  return anomaliasAnalise.filter(
    (anomalia) =>
      normalizarNivel(anomalia.nivel) === nivel
  ).length;
}


function renderizarFiltrosAnomalias() {
  const opcoesFiltroNivel = [
    {
      nivel: '',
      texto: 'Todos',
      total: anomaliasAnalise.length
    },

    ...Object.entries(NIVEIS_ANOMALIA).map(
      ([nivel, { texto }]) => ({
        nivel,
        texto,
        total: contarAnomaliasDoNivel(nivel),
      })
    ),
  ];

  filtroNiveis.innerHTML =
    opcoesFiltroNivel
      .map(
        ({ nivel, texto, total }) => `
          <button
            type="button"
            class="chip"
            data-n="${nivel}"
            aria-pressed="${nivel === ''}"
          >
            ${texto} ${total}
          </button>
        `
      )
      .join('');
}


filtroNiveis.onclick = (evento) => {
  const botao =
    evento.target.closest('[data-n]');

  if (!botao) {
    return;
  }

  nivelSelecionado =
    botao.dataset.n;

  elementos('.chip', filtroNiveis)
    .forEach((chip) => {
      chip.setAttribute(
        'aria-pressed',
        chip === botao
      );
    });

  renderizarAnomalias();
};


function renderizarAnomalias() {
  const anomaliasFiltradas =
    anomaliasAnalise.filter((anomalia) => {
      return (
        !nivelSelecionado ||
        normalizarNivel(anomalia.nivel) ===
          nivelSelecionado
      );
    });

  const linhas =
    anomaliasFiltradas
      .map(
        (anomalia) => `
          <tr>
            <td class="num">
              ${anomalia.numero_linha}
            </td>

            <td>
              ${badgeNivel(anomalia.nivel)}
            </td>

            <td>
              ${descreverDados(anomalia.dados)}
            </td>

            <td>
              ${escaparHtml(anomalia.descricao)}
            </td>
          </tr>
        `
      )
      .join('');

  elemento('#anom').innerHTML =
    linhas ||
    `
      <tr>
        <td colspan="4">
          <div class="empty">
            Nenhuma anomalia neste nível.
          </div>
        </td>
      </tr>
    `;
}


/* ---------- Registros ---------- */

const REGISTROS_POR_PAGINA = 10;

let paginaRegistros = 1;
let textoBusca = '';


/* ---------- Nível da anomalia por linha ---------- */

const nivelPorLinha = Object.fromEntries(
  anomaliasAnalise.map(
    (anomalia) => [
      anomalia.numero_linha,
      normalizarNivel(anomalia.nivel)
    ]
  )
);


/* ---------- Casas decimais ---------- */

const casasDecimaisPorColuna =
  Object.fromEntries(
    nomesColunas.map((nomeColuna) => {
      const temDecimais =
        registrosAnalise.some((registro) => {
          const valor =
            registro[nomeColuna];

          return (
            typeof valor === 'number' &&
            !Number.isInteger(valor)
          );
        });

      return [
        nomeColuna,
        temDecimais ? 2 : 0
      ];
    })
  );


/* ---------- Formatação das células ---------- */

function formatarCelula(nomeColuna, valor) {
  if (valor == null) {
    return '<span class="mut">—</span>';
  }

  if (!colunaEhNumerica(nomeColuna)) {
    return escaparHtml(valor);
  }

  const ehIdentificador =
    colunasAnalise[nomeColuna].papel ===
    'identificador';

  if (ehIdentificador) {
    return escaparHtml(valor);
  }

  return formatarNumero(
    valor,
    casasDecimaisPorColuna[nomeColuna]
  );
}


/* ---------- Cabeçalho dos registros ---------- */

function renderizarCabecalhoRegistros() {
  const colunasHtml =
    nomesColunas
      .map((nomeColuna) => {
        const classe =
          colunaEhNumerica(nomeColuna)
            ? 'num'
            : '';

        const usadaNaDeteccao =
          colunaEhNumerica(nomeColuna) &&
          colunasAnalise[nomeColuna].papel ===
            'nao_identificador';

        const marcador =
          usadaNaDeteccao
            ? ' <i class="dot" title="Usada na detecção de anomalias"></i>'
            : '';

        return `
          <th class="${classe}">
            ${escaparHtml(nomeColuna)}
            ${marcador}
          </th>
        `;
      })
      .join('');

  elemento('#rh').innerHTML =
    '<th class="num">Linha</th>' +
    colunasHtml;
}


/* ---------- Linha de registro ---------- */

function linhaRegistro([numeroLinha, registro]) {
  const nivel =
    nivelPorLinha[numeroLinha];

  const marcadorAnomalia =
    nivel
      ? `
        <span
          title="Anomalia, nível ${NIVEIS_ANOMALIA[nivel].texto}"
        >
          ${NIVEIS_ANOMALIA[nivel].simbolo}
        </span>
      `
      : '';

  const celulas =
    nomesColunas
      .map((nomeColuna) => {
        const classe =
          colunaEhNumerica(nomeColuna)
            ? 'num'
            : '';

        return `
          <td class="${classe}">
            ${formatarCelula(
              nomeColuna,
              registro[nomeColuna]
            )}
          </td>
        `;
      })
      .join('');

  return `
    <tr class="${nivel ? 'an' : ''}">
      <td class="num">
        ${marcadorAnomalia}
        ${numeroLinha}
      </td>
      ${celulas}
    </tr>
  `;
}


/* ---------- Renderização dos registros ---------- */

function renderizarRegistros() {
  const termo =
    textoBusca.toLowerCase();

  const linhasFiltradas =
    registrosAnalise
      .map(
        (registro, indice) =>
          [indice + 1, registro]
      )
      .filter(([, registro]) => {
        return (
          !termo ||
          Object.values(registro)
            .some((valor) =>
              String(valor)
                .toLowerCase()
                .includes(termo)
            )
        );
      });

  const inicio =
    (paginaRegistros - 1) *
    REGISTROS_POR_PAGINA;

  const linhasDaPagina =
    linhasFiltradas.slice(
      inicio,
      inicio + REGISTROS_POR_PAGINA
    );

  elemento('#rb').innerHTML =
    linhasDaPagina
      .map(linhaRegistro)
      .join('') ||
    `
      <tr>
        <td colspan="${nomesColunas.length + 1}">
          <div class="empty">
            Nenhum registro encontrado.
          </div>
        </td>
      </tr>
    `;

  renderizarPaginacao(
    elemento('#rp'),
    linhasFiltradas.length,
    paginaRegistros,
    REGISTROS_POR_PAGINA,
    (novaPagina) => {
      paginaRegistros = novaPagina;
      renderizarRegistros();
    }
  );
}


elemento('#qr').oninput = (evento) => {
  textoBusca =
    evento.target.value;

  paginaRegistros = 1;

  renderizarRegistros();
};


/* ---------- Inicialização ---------- */

async function iniciarDetalhes() {
  const sessaoValida =
    await verificarSessao();

  if (!sessaoValida) {
    return;
  }

  const analiseId =
    obterIdAnalise();

  if (!analiseId) {
    alert('Análise não informada.');
    location.href = 'historico.html';
    return;
  }

  try {
    const resultado =
      await buscarResultado(analiseId);

    analise = resultado.analise;
    registrosAnalise =
      resultado.registros || [];
    anomaliasAnalise =
      resultado.anomalias || [];
    estatisticasAnalise =
      resultado.estatisticas || {};
    colunasAnalise =
      resultado.colunas || {};

    nomesColunas =
      Object.keys(colunasAnalise);

    renderizarResumo();
    renderizarEstatisticas();
    renderizarFiltrosAnomalias();
    renderizarCabecalhoRegistros();
    renderizarAnomalias();
    renderizarRegistros();

  } catch (erro) {
    console.error(
      'Erro ao carregar detalhes da análise:',
      erro
    );

    alert(
      erro.message ||
      'Não foi possível carregar a análise.'
    );

    location.href = 'historico.html';
  }
}


iniciarDetalhes();