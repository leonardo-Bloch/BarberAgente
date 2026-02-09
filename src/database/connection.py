import pyodbc

# Configurações de Acesso
SERVER = r'LEOPC-05\SQLEXPRESS'
DATABASE = 'BarberAgenteDB'
USERNAME = 'sa'
PASSWORD = '123'

# Montagem da String de Conexão
string_conexao = (
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server={SERVER};"
    f"Database={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
)

def inicializar_banco():
    print(f"\n--- Iniciando Verificação do Banco de Dados ---")
    
    try:
        # 1. Tentativa de conexão com o Master
        print(f"[*] Tentando conectar ao servidor {SERVER}...", end=" ", flush=True)
        conn_master = pyodbc.connect(
            string_conexao.replace(DATABASE, 'master'), 
            autocommit=True
        )
        print("CONECTADO!")

        # 2. Verificação/Criação do Banco de Dados
        print(f"[*] Verificando se o banco '{DATABASE}' existe...", end=" ", flush=True)
        cursor_master = conn_master.cursor()
        cursor_master.execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{DATABASE}') CREATE DATABASE {DATABASE}")
        conn_master.close()
        print("OK (Criado ou já existente).")

        # 3. Conexão com o banco específico
        print(f"[*] Acessando o banco '{DATABASE}'...", end=" ", flush=True)
        conn = pyodbc.connect(string_conexao)
        cursor = conn.cursor()
        print("SUCESSO!")

        # 4. Verificação/Criação da Tabela
        print(f"[*] Verificando estrutura da tabela 'Agendamentos'...", end=" ", flush=True)
        sql_create_table = """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Agendamentos')
        BEGIN
            CREATE TABLE Agendamentos (
                Id INT PRIMARY KEY IDENTITY(1,1),
                DataHora DATETIME NOT NULL,
                ClienteId INT NOT NULL,
                BarbeiroId INT NOT NULL,
                Status NVARCHAR(20) DEFAULT 'Pendente',
                DataCriacao DATETIME DEFAULT GETDATE()
            );
        END
        """
        cursor.execute(sql_create_table)
        conn.commit()
        print("TABELA PRONTA!")

        print("\n" + "="*40)
        print("✅ CONEXÃO E INICIALIZAÇÃO BEM-SUCEDIDAS!")
        print("="*40)
        
        return conn

    except pyodbc.Error as e:
        print("\n" + "!"*40)
        print("❌ ERRO DE CONEXÃO COM O SQL SERVER")
        print(f"Detalhes: {e}")
        print("!"*40)
        return None
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        return None

# Gatilho de execução manual
if __name__ == "__main__":
    conexao = inicializar_banco()
    
    if conexao:
        # Mantém a conexão aberta se quiser testar algo mais, 
        # ou apenas fecha para finalizar o teste.
        conexao.close()
        print("\n[Status] Script finalizado com êxito.")
    else:
        print("\n[Status] O script falhou. Verifique as mensagens de erro acima.")