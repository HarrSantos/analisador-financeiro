from backend.database import conectar_banco


def criar_analise(usuario_id: int, importacao_id: int) -> int:
    conexao = None
    cursor = None
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        consulta = """
            SELECT importacao.id
            FROM importacao
            WHERE importacao.id = %s
                AND importacao.usuario_id = %s
        """
        
        cursor.execute(consulta, (importacao_id, usuario_id))
        resultado = cursor.fetchone()
        
        if not resultado:
            raise ValueError("Importação não encontrada.")
        
        consulta = """
            INSERT INTO analise (importacao_id)
            VALUES (%s)
        """
        cursor.execute(consulta, (importacao_id,))
        analise_id = cursor.lastrowid
        conexao.commit()
        return analise_id
        
    except ValueError:
        raise
    
    except Exception as erro:
        if conexao is not None:
            conexao.rollback()
        raise RuntimeError("Não foi possível criar a análise.") from erro
    
    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()
            
def listar_analises(usuario_id: int) -> list[dict]:
    conexao = None
    cursor = None
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        consulta = """
            SELECT
                analise.id,
                importacao.nome_arquivo,
                analise.data_analise,
                analise.status
            FROM analise
            INNER JOIN importacao
                ON analise.importacao_id = importacao.id
            WHERE importacao.usuario_id = %s
            ORDER BY analise.data_analise DESC
        """
        
        cursor.execute(consulta, (usuario_id,))
        resultados = cursor.fetchall()
        
        return [
            {
                "id": resultado[0],
                "nome_arquivo": resultado[1],
                "data_analise": resultado[2].isoformat(),
                "status": resultado[3]
            }
            for resultado in resultados
        ]
        
    except Exception as erro:
        raise RuntimeError("Não foi possível listar as análises.") from erro
    
    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()
            
def buscar_analise(usuario_id: int, analise_id: int) -> dict:
    conexao = None
    cursor = None
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        consulta = """
            SELECT
                analise.id,
                importacao.nome_arquivo,
                analise.data_analise,
                analise.status
            FROM analise
            INNER JOIN importacao
                ON analise.importacao_id = importacao.id
            WHERE analise.id = %s
                AND importacao.usuario_id = %s
        """
        
        cursor.execute(consulta, (analise_id, usuario_id))
        resultado = cursor.fetchone()
        
        if not resultado:
            raise ValueError("Análise não encontrada.")
        
        return {
            "id": resultado[0],
            "nome_arquivo": resultado[1],
            "data_analise": resultado[2].isoformat(),
            "status": resultado[3]
        }
        
    except ValueError:
        raise
    
    except Exception as erro:
        raise RuntimeError("Não foi possível buscar a análise.") from erro
    
    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()