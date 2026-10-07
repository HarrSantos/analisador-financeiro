CREATE DATABASE IF NOT EXISTS analisador_financeiro;

USE analisador_financeiro;


CREATE TABLE usuario (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE importacao (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT UNSIGNED NOT NULL,
    nome_arquivo VARCHAR(255) NOT NULL,
    data_importacao DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


CREATE TABLE registro (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    importacao_id INT UNSIGNED NOT NULL,
    numero_linha INT UNSIGNED NOT NULL,
    dados JSON NOT NULL,

    FOREIGN KEY (importacao_id) REFERENCES importacao(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    UNIQUE (importacao_id, numero_linha)
);


CREATE TABLE analise (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    importacao_id INT UNSIGNED NOT NULL,
    data_analise DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('PENDENTE', 'PROCESSANDO', 'CONCLUIDA', 'ERRO') DEFAULT 'PENDENTE',

    FOREIGN KEY (importacao_id) REFERENCES importacao(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


CREATE TABLE anomalia (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    analise_id INT UNSIGNED NOT NULL,
    registro_id BIGINT UNSIGNED NOT NULL,
    nivel ENUM('BAIXO', 'MEDIO', 'ALTO') NOT NULL,
    descricao TEXT NOT NULL,

    FOREIGN KEY (analise_id) REFERENCES analise(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    FOREIGN KEY (registro_id) REFERENCES registro(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);