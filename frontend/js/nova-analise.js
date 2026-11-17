const API_URL = 'http://127.0.0.1:5000';

const painelFluxo = elemento('#fluxo');
const campoArquivo = elemento('#arq');
const areaUpload = elemento('#drop');

let arquivoSelecionado = null;
let analiseCriadaId = null;


/* ---------- Estados da tela ----------
   inicial, selecionado, processando, concluido e erro. */

function mostrarEstado(estado) {
  elementos('[data-s]', painelFluxo).forEach((painel) => {
    painel.hidden = painel.dataset.s !== estado;
  });
}

function mostrarErro(mensagem) {
  elemento('#msg').textContent = mensagem;
  mostrarEstado('erro');
}

function reiniciarFluxo() {
  arquivoSelecionado = null;
  analiseCriadaId = null;
  campoArquivo.value = '';
  mostrarEstado('inicial');
}


/* ---------- Seleção do arquivo ---------- */

function selecionarArquivo(arquivo) {
  if (!arquivo) return;

  arquivoSelecionado = null;

  if (!arquivo.name.toLowerCase().endsWith('.csv')) {
    return mostrarErro('Envie um arquivo com extensão .csv.');
  }

  if (!arquivo.size) {
    return mostrarErro('O arquivo CSV está vazio.');
  }

  arquivoSelecionado = arquivo;

  elemento('#nome').textContent = arquivo.name;
  elemento('#tam').textContent =
    formatarTamanhoArquivo(arquivo.size);

  mostrarEstado('selecionado');
}

areaUpload.onclick = () => campoArquivo.click();

campoArquivo.onchange = () => {
  selecionarArquivo(campoArquivo.files[0]);
};


/* ---------- Arrastar e soltar ---------- */

['dragenter', 'dragover'].forEach((tipo) => {
  areaUpload.addEventListener(tipo, (evento) => {
    evento.preventDefault();
    areaUpload.classList.add('over');
  });
});

['dragleave', 'drop'].forEach((tipo) => {
  areaUpload.addEventListener(tipo, (evento) => {
    evento.preventDefault();
    areaUpload.classList.remove('over');
  });
});

areaUpload.addEventListener('drop', (evento) => {
  selecionarArquivo(
    evento.dataTransfer.files[0]
  );
});


/* ---------- Remover e recomeçar ---------- */

elemento('#rm').onclick = reiniciarFluxo;

elementos('[data-reset]').forEach((botao) => {
  botao.onclick = reiniciarFluxo;
});


/* ---------- API ---------- */

async function importarArquivo() {
  const formulario = new FormData();

  formulario.append('arquivo', arquivoSelecionado);

  const resposta = await fetch(
    `${API_URL}/api/importacao/csv`,
    {
      method: 'POST',
      credentials: 'include',
      body: formulario
    }
  );

  const dados = await resposta.json();

  if (!resposta.ok) {
    throw new Error(
      dados.erro ||
      'Não foi possível importar o arquivo.'
    );
  }

  return dados;
}


async function criarAnalise(importacaoId) {
  const resposta = await fetch(
    `${API_URL}/api/analise/criar/${importacaoId}`,
    {
      method: 'POST',
      credentials: 'include'
    }
  );

  const dados = await resposta.json();

  if (!resposta.ok) {
    throw new Error(
      dados.erro ||
      'Não foi possível criar a análise.'
    );
  }

  return dados;
}


async function processarAnalise(analiseId) {
  const resposta = await fetch(
    `${API_URL}/api/analise/processar/${analiseId}`,
    {
      method: 'POST',
      credentials: 'include'
    }
  );

  const dados = await resposta.json();

  if (!resposta.ok) {
    throw new Error(
      dados.erro ||
      'Não foi possível processar a análise.'
    );
  }

  return dados;
}


/* ---------- Processamento real ---------- */

elemento('#go').onclick = async () => {
  if (!arquivoSelecionado) {
    mostrarErro(
      'Selecione um arquivo antes de continuar.'
    );
    return;
  }

  mostrarEstado('processando');

  const passos = elementos('#passos li');

  passos.forEach((passo) => {
    passo.className = '';
  });

  try {

    /* 1. Importar arquivo */

    passos[0].className = 'on';

    const importacao = await importarArquivo();

    passos[0].className = 'ok';


    /* 2. Criar análise */

    passos[1].className = 'on';

    const analise = await criarAnalise(
      importacao.importacao_id
    );

    analiseCriadaId = analise.analise_id;

    passos[1].className = 'ok';


    /* 3. Processar análise */

    passos[2].className = 'on';

    await processarAnalise(
      analiseCriadaId
    );

    passos[2].className = 'ok';


    /* ---------- Concluído ---------- */

    elemento('#ok-nome').textContent =
      arquivoSelecionado.name;

    elemento('.acts .btn').href =
      `detalhes-analise.html?id=${analiseCriadaId}`;

    mostrarEstado('concluido');

  } catch (erro) {

    console.error(
      'Erro ao processar análise:',
      erro
    );

    mostrarErro(
      erro.message ||
      'Não foi possível processar o arquivo.'
    );
  }
};


mostrarEstado('inicial');