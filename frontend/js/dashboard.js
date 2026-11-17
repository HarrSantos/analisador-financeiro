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


/* ---------- Buscar resultado de uma análise ---------- */

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
      dados.erro || 'Não foi possível carregar o resultado.'
    );
  }

  return dados;
}


/* ---------- Inicialização do dashboard ---------- */

async function iniciarDashboard() {
  const sessaoValida = await verificarSessao();

  if (!sessaoValida) {
    return;
  }

  try {
    /* ---------- Buscar análises ---------- */

    const analises = await buscarAnalises();


    /* ---------- Totais ---------- */

    const totalAnalises = analises.length;

    const contagemPorStatus = {};

    analises.forEach((analise) => {
      contagemPorStatus[analise.status] =
        (contagemPorStatus[analise.status] || 0) + 1;
    });

    const analisesConcluidas =
      contagemPorStatus.CONCLUIDA || 0;


    /* ---------- Buscar resultados concluídos ---------- */

    const resultados = [];

    for (const analise of analises) {
      if (analise.status !== 'CONCLUIDA') {
        continue;
      }

      try {
        const resultado = await buscarResultado(analise.id);

        resultados.push(resultado);

      } catch (erro) {
        console.error(
          `Erro ao carregar análise #${analise.id}:`,
          erro
        );
      }
    }


    /* ---------- Total de registros e anomalias ---------- */

    let totalRegistros = 0;
    let totalAnomalias = 0;

    resultados.forEach((resultado) => {
      totalRegistros +=
        resultado.estatisticas?.total_registros || 0;

      totalAnomalias +=
        resultado.estatisticas?.total_anomalias || 0;
    });


    /* ---------- Saudação ---------- */

    elemento('#oi').textContent = 'Olá! 👋';


    /* ---------- Indicadores ---------- */

    const indicadores = [
      {
        titulo: 'Total de análises',
        valor: totalAnalises,
        detalhe: `${analisesConcluidas} concluídas`,
      },
      {
        titulo: 'Registros analisados',
        valor: totalRegistros,
        detalhe: `em ${analisesConcluidas} análises concluídas`,
      },
      {
        titulo: 'Anomalias encontradas',
        valor: totalAnomalias,
        detalhe: 'nas análises concluídas',
      },
    ];

    elemento('#kpis').innerHTML = indicadores
      .map(({ titulo, valor, detalhe }) => `
        <article class="card kpi">
          <small>${titulo}</small>
          <strong>${formatarNumero(valor)}</strong>
          <span class="mut sm">${detalhe}</span>
        </article>
      `)
      .join('');


    /* ---------- Gráfico de status ---------- */

    const statusDisponiveis =
      Object.keys(STATUS_ANALISE);

    let percentualAcumulado = 0;

    const trechosDonut = statusDisponiveis
      .map((status) => {
        const quantidade =
          contagemPorStatus[status] || 0;

        const inicio = percentualAcumulado;

        if (totalAnalises > 0) {
          percentualAcumulado +=
            quantidade / totalAnalises * 100;
        }

        return `
          var(--${STATUS_ANALISE[status].cor})
          ${inicio}%
          ${percentualAcumulado}%
        `;
      });

    const donut = elemento('#donut');

    if (totalAnalises > 0) {
      donut.style.background =
        `conic-gradient(${trechosDonut.join(',')})`;
    } else {
      donut.style.background =
        'var(--cinza-200)';
    }

    donut.dataset.t = totalAnalises;

    const resumoStatus = statusDisponiveis
      .map(
        (status) =>
          `${STATUS_ANALISE[status].texto} ${
            contagemPorStatus[status] || 0
          }`
      )
      .join(', ');

    donut.setAttribute(
      'aria-label',
      'Análises por status: ' + resumoStatus
    );

    elemento('#lg').innerHTML =
      statusDisponiveis
        .map((status) => {
          const { texto, cor } =
            STATUS_ANALISE[status];

          return `
            <li class="${cor}">
              <i></i>
              ${texto}
              <b>${contagemPorStatus[status] || 0}</b>
            </li>
          `;
        })
        .join('');


    /* ---------- Anomalias por nível ---------- */

    const contagemPorNivel = {
      ALTO: 0,
      MEDIO: 0,
      BAIXO: 0,
    };

    resultados.forEach((resultado) => {
      resultado.anomalias.forEach((anomalia) => {
        const nivel =
          normalizarNivel(anomalia.nivel);

        if (contagemPorNivel[nivel] !== undefined) {
          contagemPorNivel[nivel]++;
        }
      });
    });


    const niveisDisponiveis =
      Object.keys(NIVEIS_ANOMALIA);

    const maiorContagem = Math.max(
      ...niveisDisponiveis.map(
        (nivel) => contagemPorNivel[nivel]
      ),
      1
    );


    /* ---------- Referência da última análise ---------- */

    const ultimaAnaliseConcluida =
      analises.find(
        (analise) => analise.status === 'CONCLUIDA'
      );

    if (ultimaAnaliseConcluida) {
      elemento('#ref').textContent =
        `Última análise concluída (#${ultimaAnaliseConcluida.id})`;
    } else {
      elemento('#ref').textContent =
        'Nenhuma análise concluída';
    }


    /* ---------- Barras de anomalias ---------- */

    elemento('#bars').innerHTML =
      niveisDisponiveis
        .map((nivel) => {
          const {
            texto,
            cor,
            simbolo
          } = NIVEIS_ANOMALIA[nivel];

          const quantidade =
            contagemPorNivel[nivel];

          const percentual =
            quantidade / maiorContagem * 100;

          return `
            <div class="bar ${cor}">
              <span>
                ${simbolo} ${texto}
              </span>

              <div>
                <i style="width:${percentual}%"></i>
              </div>

              <b>${quantidade}</b>
            </div>
          `;
        })
        .join('');


    /* ---------- Análises recentes ---------- */

    const analisesRecentes =
      analises.slice(0, 5);

    if (analisesRecentes.length === 0) {
      elemento('#rc').innerHTML = `
        <tr>
          <td colspan="5" class="mut">
            Nenhuma análise encontrada.
          </td>
        </tr>
      `;
    } else {
      elemento('#rc').innerHTML =
        analisesRecentes
          .map((analise) =>
            linhaTabelaAnalise(analise)
          )
          .join('');
    }


  } catch (erro) {

    console.error(
      'Erro ao carregar dashboard:',
      erro
    );

    elemento('#kpis').innerHTML = `
      <article class="card kpi">
        <small>Erro</small>
        <strong>—</strong>
        <span class="mut sm">
          Não foi possível carregar os dados.
        </span>
      </article>
    `;
  }
}


/* ---------- Iniciar ---------- */

iniciarDashboard();