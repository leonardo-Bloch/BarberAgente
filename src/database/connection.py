import pyodbc

# Configurações para LEOPC-05\SQLEXPRESS
SERVER = r'LEOPC-05\SQLEXPRESS'
DATABASE = 'BarberAgenteDB'
USERNAME = 'sa'
PASSWORD = '123'

# String de conexão
# DICA: Se instalar o ODBC Driver 17, troque {SQL Server} por {ODBC Driver 17 for SQL Server}
STRING_CONEXAO = (
    f"Driver={{SQL Server}};"
    f"Server={SERVER};"
    f"Database={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    "Connect Timeout=5;"
)

def conectar():
    try:
        # autocommit=True evita que transações fiquem presas em "limbo"
        conn = pyodbc.connect(STRING_CONEXAO, autocommit=True)
        
        # --- AJUSTE PARA O ERRO HYC00 ---
        # Essas linhas forçam o driver a tratar strings de forma correta, 
        # eliminando o erro de "Recurso não implementado" em muitos casos.
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
        conn.setencoding(encoding='utf-8')
        
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao SQL Server: {e}")
        return None

def inicializar_banco():
    """Cria as tabelas e garante a integridade dos dados."""
    conn = conectar()
    if not conn: 
        print("Falha crítica: Não foi possível conectar ao banco.")
        return
    
    try:
        cursor = conn.cursor()
        
        # 1. Tabela de Usuarios (Barbeiros)
        # Removida a coluna redundante 'Usuario' se existia, focando em 'nome'
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Usuarios' AND xtype='U')
            CREATE TABLE Usuarios (
                id INT PRIMARY KEY IDENTITY,
                nome NVARCHAR(100) COLLATE Latin1_General_CI_AI UNIQUE NOT NULL,
                senha NVARCHAR(100) NOT NULL,
                tipo_acesso NVARCHAR(20) DEFAULT 'Barbeiro'
            )
        """)

        # 2. Tabela de Clientes
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Clientes' AND xtype='U')
            CREATE TABLE Clientes (
                id INT PRIMARY KEY IDENTITY,
                nome NVARCHAR(100) NOT NULL,
                telefone NVARCHAR(20),
                data_cadastro DATETIME DEFAULT GETDATE()
            )
        """)

        # 3. Tabela de Agendamentos (com ON DELETE CASCADE)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Agendamentos' AND xtype='U')
            CREATE TABLE Agendamentos (
                id INT PRIMARY KEY IDENTITY,
                barbeiro_id INT,
                cliente_id INT,
                data_hora DATETIME,
                servico NVARCHAR(100) DEFAULT 'Corte Especial',
                FOREIGN KEY (barbeiro_id) REFERENCES Usuarios(id) ON DELETE CASCADE,
                FOREIGN KEY (cliente_id) REFERENCES Clientes(id) ON DELETE CASCADE
            )
        """)

        # 4. Inserção do Admin Padrão
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Usuarios WHERE nome = 'Mestre Admin')
            BEGIN
                INSERT INTO Usuarios (nome, senha, tipo_acesso) 
                VALUES ('Mestre Admin', '123', 'Admin')
            END
        """)
        
        print("Estrutura de tabelas verificada com sucesso!")

    except Exception as e:
        print(f"Erro ao inicializar tabelas: {e}")
    finally:
        conn.close()