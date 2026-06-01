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

def inicializar_banco(for_testing=False):
    """Cria as tabelas e garante a integridade dos dados."""
    conn = conectar()
    if not conn: 
        print("Falha crítica: Não foi possível conectar ao banco.")
        return
    
    try:
        cursor = conn.cursor()
        
        if for_testing:
            # Garante um ambiente de teste limpo, recriando as tabelas na ordem correta.
            cursor.execute("IF OBJECT_ID('Agendamentos', 'U') IS NOT NULL DROP TABLE Agendamentos")
            cursor.execute("IF OBJECT_ID('Servicos', 'U') IS NOT NULL DROP TABLE Servicos")
            cursor.execute("IF OBJECT_ID('Clientes', 'U') IS NOT NULL DROP TABLE Clientes")
            cursor.execute("IF OBJECT_ID('Usuarios', 'U') IS NOT NULL DROP TABLE Usuarios")

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

        # 3. Tabela de Serviços
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Servicos' AND xtype='U')
            CREATE TABLE Servicos (
                id INT PRIMARY KEY IDENTITY,
                nome NVARCHAR(100) UNIQUE NOT NULL,
                preco DECIMAL(10, 2) NOT NULL,
                duracao_minutos INT NOT NULL DEFAULT 30
            )
        """)

        # 4. Tabela de Agendamentos (com ON DELETE CASCADE)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Agendamentos' AND xtype='U')
            CREATE TABLE Agendamentos (
                id INT PRIMARY KEY IDENTITY,
                barbeiro_id INT,
                cliente_id INT,
                servico_id INT,
                data_hora DATETIME,
                status NVARCHAR(20) DEFAULT 'Agendado',
                FOREIGN KEY (barbeiro_id) REFERENCES Usuarios(id) ON DELETE CASCADE,
                FOREIGN KEY (cliente_id) REFERENCES Clientes(id) ON DELETE CASCADE,
                FOREIGN KEY (servico_id) REFERENCES Servicos(id)
            )
        """)

        # 5. Inserção do Admin Padrão
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Usuarios WHERE nome = 'Mestre Admin')
            BEGIN
                INSERT INTO Usuarios (nome, senha, tipo_acesso) 
                VALUES ('Mestre Admin', '123', 'Admin')
            END
        """)
        
        # 6. Inserção de Serviços Padrão
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Servicos)
            BEGIN
                INSERT INTO Servicos (nome, preco, duracao_minutos) VALUES 
                ('Corte Normal', 35.00, 30),
                ('Corte + Barba', 55.00, 60),
                ('Barba Terapia', 30.00, 45)
            END
        """)

        # 7. Inserção de Cliente Padrão para Testes
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Clientes)
            BEGIN
                INSERT INTO Clientes (nome, telefone) 
                VALUES ('Cliente Padrão', '(00) 00000-0000')
            END
        """)

        print("Estrutura de tabelas verificada com sucesso!")

    except Exception as e:
        print(f"Erro ao inicializar tabelas: {e}")
    finally:
        conn.close()