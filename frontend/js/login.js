/*
 * Alterna Login/Cadastro na mesma página.
 * Login e cadastro conectados à API real.
 */

const API_URL = 'http://127.0.0.1:5000';

const elemento = (seletor) => document.querySelector(seletor);

const formularioLogin = elemento('#f-login');
const formularioCadastro = elemento('#f-cad');


/* ---------- Alternar entre Login/Cadastro ---------- */

function mostrarModo(modo) {
  formularioLogin.hidden = modo !== 'login';
  formularioCadastro.hidden = modo !== 'cadastro';

  const primeiroCampo = modo === 'login'
    ? elemento('#le')
    : elemento('#cn');

  primeiroCampo.focus();

  const titulo = modo === 'login'
    ? 'Entrar'
    : 'Criar conta';

  document.title = titulo + ' | Analisador Financeiro';
}

document.addEventListener('click', (evento) => {
  const botaoModo = evento.target.closest('[data-modo]');

  if (botaoModo) {
    mostrarModo(botaoModo.dataset.modo);
  }
});


/* ---------- Mensagem de erro ---------- */

function mostrarErroCadastro(mensagem, campo = null) {
  const mensagemAnterior =
    formularioCadastro.querySelector('.msg-erro');

  if (mensagemAnterior) {
    mensagemAnterior.remove();
  }

  const mensagemErro = document.createElement('p');

  mensagemErro.className = 'msg msg-erro';
  mensagemErro.setAttribute('role', 'alert');
  mensagemErro.textContent = mensagem;

  if (campo) {
    campo.insertAdjacentElement(
      'afterend',
      mensagemErro
    );

    campo.focus();
  } else {
    formularioCadastro.prepend(mensagemErro);
  }
}


/* ---------- Login ---------- */

formularioLogin.addEventListener('submit', async (evento) => {
  evento.preventDefault();

  const email = elemento('#le').value.trim();
  const senha = elemento('#ls').value;

  const botao = formularioLogin.querySelector('.btn');
  const textoOriginal = botao.textContent;

  botao.disabled = true;
  botao.textContent = 'Aguarde…';

  try {
    const resposta = await fetch(
      `${API_URL}/api/auth/login`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          email: email,
          senha: senha
        })
      }
    );

    const dados = await resposta.json();

    if (!resposta.ok) {
      alert(
        dados.erro ||
        'Não foi possível entrar.'
      );

      return;
    }

    location.href = 'dashboard.html';

  } catch (erro) {
    console.error(
      'Erro ao realizar login:',
      erro
    );

    alert(
      'Não foi possível conectar ao servidor.'
    );

  } finally {
    botao.disabled = false;
    botao.textContent = textoOriginal;
  }
});


/* ---------- Cadastro ---------- */

formularioCadastro.addEventListener(
  'submit',
  async (evento) => {
    evento.preventDefault();

    const nome = elemento('#cn').value.trim();
    const email = elemento('#ce').value.trim();
    const senha = elemento('#cs');
    const confirmarSenha = elemento('#ccs');

    const mensagemSucesso = elemento('#ok');

    /* Remove mensagem de erro anterior */

    const mensagemErroAnterior =
      formularioCadastro.querySelector('.msg-erro');

    if (mensagemErroAnterior) {
      mensagemErroAnterior.remove();
    }


    /* Verifica se as senhas são iguais */

    if (senha.value !== confirmarSenha.value) {
      mostrarErroCadastro(
        'As senhas não coincidem.',
        confirmarSenha
      );

      return;
    }


    /* Botão */

    const botao =
      formularioCadastro.querySelector('.btn');

    const textoOriginal =
      botao.textContent;

    botao.disabled = true;
    botao.textContent = 'Aguarde…';


    try {
      const resposta = await fetch(
        `${API_URL}/api/auth/cadastro`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({
            nome: nome,
            email: email,
            senha: senha.value
          })
        }
      );

      const dados = await resposta.json();

      if (!resposta.ok) {
        mostrarErroCadastro(
          dados.erro ||
          'Não foi possível criar a conta.'
        );

        return;
      }


      /* Cadastro concluído */

      mensagemSucesso.hidden = false;

      formularioCadastro.reset();

      setTimeout(() => {
        mensagemSucesso.hidden = true;
        mostrarModo('login');
      }, 1400);

    } catch (erro) {
      console.error(
        'Erro ao realizar cadastro:',
        erro
      );

      mostrarErroCadastro(
        'Não foi possível conectar ao servidor.'
      );

    } finally {
      botao.disabled = false;
      botao.textContent = textoOriginal;
    }
  }
);


/* ---------- Ilustração de análise de dados ---------- */

let sementeIlustracao = 7;

function proximoAleatorio() {
  sementeIlustracao =
    sementeIlustracao * 16807 % 2147483647;

  return sementeIlustracao / 2147483647;
}

let marcacoesSvg = `
  <!-- Grade -->
  <g opacity=".12" stroke="#9DB7F5" stroke-width="1">
    <path d="M30 35H290"/>
    <path d="M30 70H290"/>
    <path d="M30 105H290"/>
    <path d="M30 140H290"/>

    <path d="M80 20V150"/>
    <path d="M130 20V150"/>
    <path d="M180 20V150"/>
    <path d="M230 20V150"/>
    <path d="M280 20V150"/>
  </g>

  <!-- Eixos -->
  <path
    d="M30 150V20M30 150H290"
    fill="none"
    stroke="#6E8BC8"
    stroke-width="1.5"
    opacity=".5"
  />

  <!-- Tendência -->
  <path
    d="M45 133 C90 120, 130 105, 170 88 S235 58, 278 42"
    fill="none"
    stroke="#6F95F4"
    stroke-width="2"
    stroke-linecap="round"
    opacity=".65"
  />
`;


/* Pontos normais */

for (let i = 0; i < 42; i++) {
  const x = 48 + proximoAleatorio() * 205;
  const tendencia = 134 - (x - 48) * 0.43;
  const variacao = (proximoAleatorio() - 0.5) * 28;
  const y = tendencia + variacao;

  marcacoesSvg += `
    <circle
      cx="${x.toFixed(1)}"
      cy="${y.toFixed(1)}"
      r="3"
      fill="#88A8F5"
      opacity=".8"
    />
  `;
}


/* Pontos que fogem do padrão */

const pontosAnormais = [
  [265, 32],
  [276, 116],
  [64, 43]
];

pontosAnormais.forEach(([x, y]) => {
  marcacoesSvg += `
    <circle
      cx="${x}"
      cy="${y}"
      r="10"
      fill="none"
      stroke="#FFB547"
      stroke-width="1.5"
      opacity=".8"
    />

    <circle
      cx="${x}"
      cy="${y}"
      r="4.5"
      fill="#FFB547"
    />
  `;
});


elemento('#viz').innerHTML = marcacoesSvg;