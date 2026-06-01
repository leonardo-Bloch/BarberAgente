from .connection import conectar
from datetime import datetime

class DataManager:
    """
    Classe responsável por todas as interações com o banco de dados.
    Centraliza a lógica de queries para ser reutilizada pela aplicação.
    """

    def _execute_query(self, query, params=None, fetch=None):
        """
        Método auxiliar para executar queries de forma segura, gerenciando
        a conexão e o cursor.
        - query: A string SQL a ser executada.
        - params: Uma tupla de parâmetros para a query.
        - fetch: 'one' para fetchone(), 'all' para fetchall(). None para DML.
        """
        conn = conectar()
        if not conn:
            print("Erro crítico: Não foi possível conectar ao banco de dados.")
            return None if fetch else False
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params if params is not None else ())
            
            if fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'all':
                return cursor.fetchall()
            else: # INSERT, UPDATE, DELETE
                conn.commit() # Garante que a transação seja salva
                return True # Sucesso na execução
        except Exception as e:
            print(f"Erro ao executar a query: {e}")
            return None if fetch else False
        finally:
            if conn:
                conn.close()

    # --- Métodos para Agendamentos ---

    def get_appointments_for_day(self, barbeiro_id, data_sql):
        query = """
            SELECT a.id, CONVERT(VARCHAR(5), a.data_hora, 108), c.nome, s.nome, a.status
            FROM Agendamentos a 
            INNER JOIN Clientes c ON a.cliente_id = c.id
            INNER JOIN Servicos s ON a.servico_id = s.id
            WHERE a.barbeiro_id = ? AND CAST(a.data_hora AS DATE) = ? 
            ORDER BY a.data_hora
        """
        return self._execute_query(query, (barbeiro_id, data_sql), fetch='all')

    def check_appointment_conflict(self, barbeiro_id, dt_fim, dt_inicio):
        query = """
            SELECT TOP 1 c.nome, a.data_hora
            FROM Agendamentos a
            INNER JOIN Clientes c ON a.cliente_id = c.id
            INNER JOIN Servicos s ON a.servico_id = s.id
            WHERE a.barbeiro_id = ? AND a.data_hora < ? AND DATEADD(minute, s.duracao_minutos, a.data_hora) > ?
        """
        return self._execute_query(query, (barbeiro_id, dt_fim, dt_inicio), fetch='one')

    def save_appointment(self, barbeiro_id, cliente_id, servico_id, dt_obj):
        query = "INSERT INTO Agendamentos (barbeiro_id, cliente_id, servico_id, data_hora, status) VALUES (?, ?, ?, ?, ?)"
        return self._execute_query(query, (barbeiro_id, cliente_id, servico_id, dt_obj, 'Agendado'))

    def delete_appointment(self, appointment_id):
        query = "DELETE FROM Agendamentos WHERE id = ?"
        return self._execute_query(query, (appointment_id,))

    def get_appointments_for_whatsapp(self, inicio, fim):
        query = """
            SELECT c.nome, c.telefone, a.id, CONVERT(VARCHAR(5), a.data_hora, 108) 
            FROM Agendamentos a 
            INNER JOIN Clientes c ON a.cliente_id = c.id 
            WHERE a.data_hora >= ? AND a.data_hora < ? AND a.status = 'Agendado'
        """
        return self._execute_query(query, (inicio, fim), fetch='all')

    # --- Métodos para outras entidades ---

    def authenticate_user(self, username, password):
        query = "SELECT id, nome, tipo_acesso FROM Usuarios WHERE nome = ? AND senha = ?"
        user_data = self._execute_query(query, (username, password), fetch='one')
        if user_data:
            return {"id": user_data[0], "nome": user_data[1], "tipo_acesso": user_data[2]}
        return None

    def get_barbers(self):
        query = "SELECT id, nome FROM Usuarios ORDER BY nome"
        rows = self._execute_query(query, fetch='all')
        return [{"id": r[0], "nome": r[1]} for r in rows] if rows else []

    def get_all_barbers_details(self):
        query = "SELECT id, nome, tipo_acesso FROM Usuarios ORDER BY nome"
        return self._execute_query(query, fetch='all')

    def get_services(self):
        query = "SELECT id, nome, duracao_minutos FROM Servicos ORDER BY nome"
        rows = self._execute_query(query, fetch='all')
        if not rows:
            return [], {}
        lista_servicos = [{"id": r[0], "nome": r[1]} for r in rows]
        servicos_cache = {r[0]: {"nome": r[1], "duracao": r[2]} for r in rows}
        return lista_servicos, servicos_cache

    def find_client_by_name(self, nome):
        query = "SELECT id, nome FROM Clientes WHERE nome LIKE ?"
        return self._execute_query(query, (f"%{nome}%",), fetch='one')

    def save_barber(self, nome, senha):
        query = "INSERT INTO Usuarios (nome, senha, tipo_acesso) VALUES (?, ?, 'Barbeiro')"
        return self._execute_query(query, (nome, senha))

    def delete_barber(self, user_id):
        query = "DELETE FROM Usuarios WHERE id = ?"
        return self._execute_query(query, (user_id,))

    def check_client_phone_exists(self, telefone):
        query = "SELECT id FROM Clientes WHERE telefone = ?"
        return self._execute_query(query, (telefone,), fetch='one') is not None

    def save_client(self, nome, telefone):
        query = "INSERT INTO Clientes (nome, telefone) VALUES (?, ?)"
        return self._execute_query(query, (nome, telefone))

    def get_recent_clients(self):
        query = "SELECT nome, telefone, CONVERT(VARCHAR(16), data_cadastro, 120) FROM Clientes ORDER BY id DESC"
        return self._execute_query(query, fetch='all')

    def save_service(self, nome, preco, duracao):
        query = "INSERT INTO Servicos (nome, preco, duracao_minutos) VALUES (?, ?, ?)"
        return self._execute_query(query, (nome, preco, duracao))

    def check_service_in_use(self, service_id):
        query = "SELECT COUNT(*) FROM Agendamentos WHERE servico_id = ?"
        result = self._execute_query(query, (service_id,), fetch='one')
        return result[0] > 0 if result else False

    def delete_service(self, service_id):
        query = "DELETE FROM Servicos WHERE id = ?"
        return self._execute_query(query, (service_id,))

    def get_all_services_details(self):
        query = "SELECT id, nome, FORMAT(preco, 'N2'), duracao_minutos FROM Servicos ORDER BY nome"
        return self._execute_query(query, fetch='all')