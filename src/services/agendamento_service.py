from datetime import datetime, timedelta

def verificar_disponibilidade(cursor, barbeiro_id, data_hora_desejada):
    """
    Critério: Bloqueio de Conflitos e Intervalo Mínimo
    """
    # Define o intervalo (ex: 30 minutos)
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
    """
    Critério: Regra de Passado
    """
    return data_hora_desejada > datetime.now()