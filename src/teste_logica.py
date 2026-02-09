import pyodbc
from datetime import datetime, timedelta
# Importamos a string de conexão do seu script que funcionou
from database.connection import string_conexao, inicializar_banco 

# --- SUAS FUNÇÕES DE LÓGICA ---
def verificar_disponibilidade(cursor, barbeiro_id, data_hora_desejada):
    intervalo = timedelta(minutes=30)
    inicio_janela = data_hora_desejada - intervalo
    fim_janela = data_hora_desejada + intervalo

    query = """
    SELECT COUNT(*) FROM Agendamentos 
    WHERE BarbeiroId = ? 
    AND DataHora > ? AND DataHora < ?
    """
    cursor.execute(query, (barbeiro_id, inicio_janela, fim_janela))
    return cursor.fetchone()[0] == 0

def validar_regra_passado(data_hora_desejada):
    return data_hora_desejada > datetime.now()

# --- SCRIPT DE TESTE NA MÁQUINA ---
def executar_testes():
    conn = inicializar_banco()
    if not conn:
        print("Erro: Não foi possível conectar ao SQL Server.")
        return

    cursor = conn.cursor()
    
    # Vamos testar com o horário de AMANHÃ às 14:00
    horario_teste = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
    
    print(f"\n[TESTE 1] Validando Data Passada...")
    data_antiga = datetime(2023, 1, 1)
    if not validar_regra_passado(data_antiga):
        print("✅ SUCESSO: O sistema bloqueou uma data de 2023.")

    print(f"\n[TESTE 2] Simulando Agendamento...")
    # Limpamos o banco para o teste ser limpo
    cursor.execute("DELETE FROM Agendamentos WHERE BarbeiroId = 99") 
    cursor.execute("INSERT INTO Agendamentos (DataHora, ClienteId, BarbeiroId) VALUES (?, ?, ?)", 
                   (horario_teste, 1, 99))
    conn.commit()
    print(f"✅ Horário reservado para o Barbeiro 99 às {horario_teste}")

    print(f"\n[TESTE 3] Testando Conflito (Mesmo horário)...")
    if not verificar_disponibilidade(cursor, 99, horario_teste):
        print("✅ SUCESSO: O sistema detectou que o Barbeiro 99 já está ocupado.")
    else:
        print("❌ ERRO: O sistema permitiu agendar por cima!")

    print(f"\n[TESTE 4] Testando Intervalo Mínimo (30 min)...")
    horario_conflito_perto = horario_teste + timedelta(minutes=10)
    if not verificar_disponibilidade(cursor, 99, horario_conflito_perto):
        print(f"✅ SUCESSO: O sistema bloqueou {horario_conflito_perto} (muito próximo dos 30min).")

    conn.close()

if __name__ == "__main__":
    executar_testes()