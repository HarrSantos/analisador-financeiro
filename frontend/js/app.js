/*
 * Base compartilhada das páginas internas:
 * ícones, formatadores, badges e a mesma sidebar/topbar em todas as telas.
 * Só interação local, sem rede.
 */


/* ---------- Seleção de elementos ---------- */

function elemento(seletor, raiz = document) {
  return raiz.querySelector(seletor);
}

function elementos(seletor, raiz = document) {
  return [...raiz.querySelectorAll(seletor)];
}


/* ---------- Ícones ---------- */

const CAMINHOS_ICONES = {
  dashboard: `
    <rect x="3" y="3" width="7" height="9" rx="1"/>
    <rect x="14" y="3" width="7" height="5" rx="1"/>
    <rect x="14" y="12" width="7" height="9" rx="1"/>
    <rect x="3" y="16" width="7" height="5" rx="1"/>`,
  plus: '<path d="M12 5v14M5 12h14"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  out: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  up: '<path d="M12 16V4M7 9l5-5 5 5M4 20h16"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
};

function icone(nome) {
  return `<svg class="i" viewBox="0 0 24 24" aria-hidden="true">${CAMINHOS_ICONES[nome]}</svg>`;
}


/* ---------- Formatadores ---------- */

function escaparHtml(texto) {
  const substituicoes = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
  };

  return String(texto).replace(/[&<>"]/g, (caractere) => substituicoes[caractere]);
}

function formatarNumero(valor, casasDecimais = 0) {
  return Number(valor).toLocaleString('pt-BR', {
    minimumFractionDigits: casasDecimais,
    maximumFractionDigits: casasDecimais,
  });
}

function formatarDataHora(dataIso) {
  return new Date(dataIso).toLocaleString('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  });
}

function formatarTamanhoArquivo(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return formatarNumero(bytes / 1024, 1) + ' KB';
  return formatarNumero(bytes / 1048576, 1) + ' MB';
}


/* ---------- Status e níveis ----------
   Valores reais do backend: analise.status e anomalia.nivel.
   O ML ainda envia "MÉDIO" com acento, por isso normalizarNivel(). */

const STATUS_ANALISE = {
  CONCLUIDA: { texto: 'Concluída', cor: 'green' },
  PROCESSANDO: { texto: 'Processando', cor: 'blue' },
  PENDENTE: { texto: 'Pendente', cor: 'gray' },
  ERRO: { texto: 'Erro', cor: 'red' },
};

const NIVEIS_ANOMALIA = {
  ALTO: { texto: 'Alto', cor: 'red', simbolo: '▲' },
  MEDIO: { texto: 'Médio', cor: 'amber', simbolo: '◆' },
  BAIXO: { texto: 'Baixo', cor: 'blue', simbolo: '●' },
};

function normalizarNivel(nivel) {
  return String(nivel)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase();
}

function badgeStatus(status) {
  const { texto, cor } = STATUS_ANALISE[status];

  return `<span class="badge ${cor}">${texto}</span>`;
}

function badgeNivel(nivel) {
  const { texto, cor, simbolo } = NIVEIS_ANOMALIA[normalizarNivel(nivel)];

  return `<span class="badge lv ${cor}">${simbolo} ${texto}</span>`;
}


/* ---------- Tabela de análises (usada no Dashboard e no Histórico) ---------- */

function linhaTabelaAnalise(analise) {
  const temResultado = analise.status === 'CONCLUIDA';
  const acao = temResultado
    ? `<a class="btn ghost sm" href="detalhes-analise.html?id=${analise.id}">Ver análise</a>`
    : '<span class="mut sm">Sem resultado</span>';

  return `
    <tr>
      <td><span class="fn">${icone('file')}${escaparHtml(analise.nome_arquivo)}</span></td>
      <td class="num">#${analise.id}</td>
      <td>${formatarDataHora(analise.data_analise)}</td>
      <td>${badgeStatus(analise.status)}</td>
      <td>${acao}</td>
    </tr>`;
}


/* ---------- Paginação local ---------- */

function renderizarPaginacao(container, total, paginaAtual, itensPorPagina, aoMudarPagina) {
  const totalPaginas = Math.max(1, Math.ceil(total / itensPorPagina));
  const primeiroItem = total ? (paginaAtual - 1) * itensPorPagina + 1 : 0;
  const ultimoItem = Math.min(paginaAtual * itensPorPagina, total);
  const desabilitarAnterior = paginaAtual <= 1 ? ' disabled' : '';
  const desabilitarProxima = paginaAtual >= totalPaginas ? ' disabled' : '';

  container.innerHTML = `
    <span>${primeiroItem}–${ultimoItem} de ${total}</span>
    <div>
      <button type="button" class="btn ghost sm" data-p="${paginaAtual - 1}"${desabilitarAnterior}>Anterior</button>
      <span>${paginaAtual} de ${totalPaginas}</span>
      <button type="button" class="btn ghost sm" data-p="${paginaAtual + 1}"${desabilitarProxima}>Próxima</button>
    </div>`;

  container.onclick = (evento) => {
    const botao = evento.target.closest('button[data-p]');

    if (botao && !botao.disabled) {
      aoMudarPagina(Number(botao.dataset.p));
    }
  };
}


/* ---------- Layout base: sidebar, topbar e menu mobile ---------- */

const LOGO_SVG = `
  <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">
    <rect width="34" height="34" rx="9" fill="#2457F5"/>
    <path d="M8 23l6-7 5 4 7-9" fill="none" stroke="#fff" stroke-width="2.5"
          stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`;

function montarSidebar(paginaAtual) {
  const itensMenu = [
    { pagina: 'dashboard', nomeIcone: 'dashboard', texto: 'Dashboard' },
    { pagina: 'nova-analise', nomeIcone: 'plus', texto: 'Nova análise' },
    { pagina: 'historico', nomeIcone: 'clock', texto: 'Histórico' },
  ];

  const linksMenu = itensMenu
    .map(({ pagina, nomeIcone, texto }) => {
      const atributoAtivo = pagina === paginaAtual
        ? ' aria-current="page"'
        : '';

      return `
        <a href="${pagina}.html"${atributoAtivo}>
          ${icone(nomeIcone)}${texto}
        </a>`;
    })
    .join('');

  elemento('#side').innerHTML = `
    <a class="brand" href="dashboard.html">
      ${LOGO_SVG}
      <div>
        <b>Analisador</b>
        <span>Financeiro</span>
      </div>
    </a>

    <nav class="nav" aria-label="Principal">
      ${linksMenu}
    </nav>

    <nav class="nav out" aria-label="Conta">
      <a href="login.html" id="btn-sair">
        ${icone('out')}Sair
      </a>
    </nav>
  `;

  /* ---------- Logout ---------- */

  elemento('#btn-sair').addEventListener('click', async (evento) => {
    evento.preventDefault();

    try {
      const resposta = await fetch(
        'http://127.0.0.1:5000/api/auth/logout',
        {
          method: 'POST',
          credentials: 'include'
        }
      );

      if (!resposta.ok) {
        console.error('Não foi possível encerrar a sessão.');
      }

    } catch (erro) {
      console.error('Erro ao fazer logout:', erro);

    } finally {
      window.location.href = 'login.html';
    }
  });
}

async function montarTopbar() {
  let nomeUsuario = 'Usuário';

  try {
    const resposta = await fetch(
      'http://127.0.0.1:5000/api/auth/verificar-sessao',
      {
        method: 'GET',
        credentials: 'include'
      }
    );

    if (resposta.ok) {
      const dados = await resposta.json();

      if (dados.nome) {
        nomeUsuario = dados.nome;
      }
    }

  } catch (erro) {
    console.error(
      'Não foi possível carregar o usuário:',
      erro
    );
  }

  const iniciais = nomeUsuario
    .trim()
    .charAt(0)
    .toUpperCase();

  const migalhas = (document.body.dataset.crumb || '')
    .split(',')
    .map((migalha) => migalha.split('|'));

  const migalhasHtml = migalhas
    .map(([texto, link]) => {
      const item = link
        ? `<a href="${link}">${texto}</a>`
        : `<b aria-current="page">${texto}</b>`;

      return `<span aria-hidden="true">/</span>${item}`;
    })
    .join('');

  elemento('#top').innerHTML = `
    <div class="tl">
      <button type="button" id="menu" class="btn ghost sm"
              aria-label="Abrir menu" aria-expanded="false">
        ${icone('menu')}
      </button>

      <nav class="crumbs" aria-label="Você está em">
        <a href="dashboard.html">Analisador Financeiro</a>
        ${migalhasHtml}
      </nav>
    </div>

    <div class="user">
      <span>${escaparHtml(nomeUsuario)}</span>

      <div class="av" aria-hidden="true">
        ${escaparHtml(iniciais)}
      </div>
    </div>
  `;
}

function configurarMenuMobile() {
  const corpo = document.body;
  const botaoMenu = elemento('#menu');

  corpo.insertAdjacentHTML('beforeend', '<div class="scrim" id="scrim"></div>');
  const fundoEscuro = elemento('#scrim');

  function definirMenuAberto(aberto) {
    corpo.classList.toggle('nav-open', aberto);
    botaoMenu.setAttribute('aria-expanded', aberto);
  }

  botaoMenu.onclick = () => definirMenuAberto(!corpo.classList.contains('nav-open'));
  fundoEscuro.onclick = () => definirMenuAberto(false);

  addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape') {
      definirMenuAberto(false);
    }
  });
}

function montarLayoutBase() {
  const paginaAtual = document.body.dataset.nav;

  if (!paginaAtual) return;

  montarSidebar(paginaAtual);
  montarTopbar();
  configurarMenuMobile();
}


/* ---------- Inicialização ---------- */

montarLayoutBase();

// Preenche os ícones declarados no HTML com data-ic="nome"
elementos('[data-ic]').forEach((marcador) => {
  marcador.insertAdjacentHTML('afterbegin', icone(marcador.dataset.ic));
});
