const API_URL = 'http://127.0.0.1:5000';

const ITENS_POR_PAGINA = 8;

const corpoTabela = elemento('#tb');
const campoBusca = elemento('#q');
const filtroStatus = elemento('#fs');
const paginacao = elemento('#pager');

let paginaAtual = 1;
let analises = [];


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


/* ---------- Buscar análises ---------- */

async function buscarAnalises() {
  const resposta = await fetch(
    `${API_URL}/api/analise/listar`,
    {
      method: 'GET',
      credentials: 'include'
    }
  );

  const dados = await resposta.json();

  if (!resposta.ok) {
    throw new Error(
      dados.erro || 'Não foi possível carregar as análises.'
    );
  }

  return dados;
}


/* ---------- Filtro ---------- */

function filtrarAnalises() {
  const termo = campoBusca.value
    .trim()
    .toLowerCase()
    .replace('#', '');

  return analises.filter((analise) => {
    const statusConfere =
      !filtroStatus.value ||
      analise.status === filtroStatus.value;

    const nomeArquivo =
      String(analise.nome_arquivo || '').toLowerCase();

    const buscaConfere =
      !termo ||
      nomeArquivo.includes(termo) ||
      String(analise.id).includes(termo);

    return statusConfere && buscaConfere;
  });
}


/* ---------- Renderização ---------- */

function renderizarTabela() {
  const analisesFiltradas = filtrarAnalises();

  const temResultados =
    analisesFiltradas.length > 0;

  const inicio =
    (paginaAtual - 1) * ITENS_POR_PAGINA;

  elemento('#tabela').hidden = !temResultados;
  paginacao.hidden = !temResultados;
  elemento('#vazio').hidden = temResultados;

  corpoTabela.innerHTML = analisesFiltradas
    .slice(
      inicio,
      inicio + ITENS_POR_PAGINA
    )
    .map((analise) =>
      linhaTabelaAnalise(analise)
    )
    .join('');

  if (!temResultados) {
    return;
  }

  renderizarPaginacao(
    paginacao,
    analisesFiltradas.length,
    paginaAtual,
    ITENS_POR_PAGINA,
    (novaPagina) => {
      paginaAtual = novaPagina;
      renderizarTabela();
    }
  );
}


/* ---------- Eventos ---------- */

function aoAlterarFiltro() {
  paginaAtual = 1;
  renderizarTabela();
}

campoBusca.oninput = aoAlterarFiltro;
filtroStatus.onchange = aoAlterarFiltro;

elemento('#limpar').onclick = () => {
  campoBusca.value = '';
  filtroStatus.value = '';
  paginaAtual = 1;

  renderizarTabela();
};


/* ---------- Esqueleto de carregamento ---------- */

const linhaEsqueleto =
  '<tr>' +
  '<td><div class="sk"></div></td>'.repeat(5) +
  '</tr>';

corpoTabela.innerHTML =
  Array(5)
    .fill(linhaEsqueleto)
    .join('');


/* ---------- Inicialização ---------- */

async function iniciarHistorico() {
  const sessaoValida = await verificarSessao();

  if (!sessaoValida) {
    return;
  }

  try {
    analises = await buscarAnalises();

    paginaAtual = 1;

    renderizarTabela();

  } catch (erro) {
    console.error(
      'Erro ao carregar histórico:',
      erro
    );

    elemento('#tabela').hidden = true;
    paginacao.hidden = true;
    elemento('#vazio').hidden = false;
  }
}

iniciarHistorico();