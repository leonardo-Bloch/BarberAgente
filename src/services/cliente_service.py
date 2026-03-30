from database.connection import conectar
import pyodbc

class ClienteService:
    def cadastrar_cliente(self, nome, telefone):
        conn = conectar()
        if not conn: return False
        
        try:
            cursor = conn.cursor()
            # Limpa o telefone para deixar apenas números
            telefone_limpo = ''.join(filter(str.isdigit, telefone))
            
            cursor.execute(
                "INSERT INTO Clientes (nome, telefone) VALUES (?, ?)",
                (nome, telefone_limpo)
            )
            conn.commit()
            return True
        except pyodbc.IntegrityError:
            # Telefone já cadastrado
            return "Telefone já cadastrado."
        except Exception as e:
            print(f"Erro ao cadastrar cliente: {e}")
            return False
        finally:
            conn.close()

    def buscar_cliente_por_telefone(self, telefone):
        conn = conectar()
        if not conn: return None
        
        try:
            cursor = conn.cursor()
            telefone_limpo = ''.join(filter(str.isdigit, telefone))
            cursor.execute("SELECT id, nome, telefone FROM Clientes WHERE telefone = ?", (telefone_limpo,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "nome": row[1], "telefone": row[2]}
            return None
        finally:
            conn.close()