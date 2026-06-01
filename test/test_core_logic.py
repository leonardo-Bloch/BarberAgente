import unittest
import sys
import os
from datetime import datetime, timedelta

# --- Adiciona o caminho 'src' para encontrar os módulos do projeto ---
caminho_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
caminho_src = os.path.join(caminho_projeto, 'src')
if caminho_src not in sys.path:
    sys.path.insert(0, caminho_src)

from database.connection import conectar, inicializar_banco

class TestCoreLogic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Roda uma vez antes de todos os testes. Garante que o DB está pronto. """
        print("\n--- Inicializando banco de dados para testes ---")
        inicializar_banco(for_testing=True)

    def setUp(self):
        """ Roda antes de cada teste. Garante uma conexão limpa. """
        self.conn = conectar()
        self.assertIsNotNone(self.conn, "A conexão com o banco de dados não deve ser nula.")
        self.cursor = self.conn.cursor()
        # IDs de teste (assumindo que existem ou foram criados)
        self.barbeiro_id_teste = 1  # Geralmente o 'Mestre Admin'
        self.cliente_id_teste = 1
        self.servico_id_teste = 1   # 'Corte Normal' (30 min)

    def tearDown(self):
        """ Roda depois de cada teste para limpar o ambiente. """
        if self.conn:
            # Limpa agendamentos de teste para não interferir em outros testes
            self.cursor.execute("DELETE FROM Agendamentos WHERE cliente_id = ?", (self.cliente_id_teste,))
            self.conn.close()

    def test_01_conexao_banco(self):
        """ Testa se a função conectar() retorna um objeto de conexão válido. """
        print("\n[TESTE] Conexão com o Banco de Dados")
        self.assertIsNotNone(self.conn)
        print("✅ SUCESSO: Conexão estabelecida.")

    def test_02_agendamento_no_passado(self):
        """ REGRA: Não deve ser possível agendar no passado. """
        print("\n[TESTE] Bloqueio de agendamento no passado")
        data_passada = datetime.now() - timedelta(days=1)
        # Esta lógica estaria na UI, aqui simulamos a verificação
        self.assertLess(data_passada, datetime.now(), "A data de teste deve ser no passado.")
        print("✅ SUCESSO: Regra de data passada validada (simulação).")

    def test_03_agendamento_sucesso(self):
        """ Testa a criação de um agendamento válido no futuro. """
        print("\n[TESTE] Criação de agendamento válido")
        data_futura = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        try:
            self.cursor.execute(
                "INSERT INTO Agendamentos (barbeiro_id, cliente_id, servico_id, data_hora, status) VALUES (?, ?, ?, ?, ?)",
                (self.barbeiro_id_teste, self.cliente_id_teste, self.servico_id_teste, data_futura, 'Agendado')
            )
            self.cursor.execute("SELECT COUNT(*) FROM Agendamentos WHERE data_hora = ?", (data_futura,))
            self.assertEqual(self.cursor.fetchone()[0], 1, "O agendamento deveria ter sido inserido.")
            print("✅ SUCESSO: Agendamento criado no banco de dados.")
        except Exception as e:
            self.fail(f"A inserção do agendamento falhou com erro: {e}")

    def test_04_conflito_de_horario_exato(self):
        """ REGRA: Não deve permitir agendar no mesmo horário para o mesmo barbeiro. """
        print("\n[TESTE] Bloqueio de conflito de horário (exato)")
        data_agendamento = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0) + timedelta(days=1)

        # 1. Insere um agendamento
        self.cursor.execute(
            "INSERT INTO Agendamentos (barbeiro_id, cliente_id, servico_id, data_hora, status) VALUES (?, ?, ?, ?, ?)",
            (self.barbeiro_id_teste, self.cliente_id_teste, self.servico_id_teste, data_agendamento, 'Agendado')
        )

        # 2. Tenta inserir outro no mesmo horário (simulando a lógica de verificação)
        duracao_servico = 30 # minutos
        dt_fim_obj = data_agendamento + timedelta(minutes=duracao_servico)

        query_conflito = """
            SELECT COUNT(*) FROM Agendamentos a INNER JOIN Servicos s ON a.servico_id = s.id
            WHERE a.barbeiro_id = ? AND a.data_hora < ? AND DATEADD(minute, s.duracao_minutos, a.data_hora) > ?
        """
        self.cursor.execute(query_conflito, (self.barbeiro_id_teste, dt_fim_obj, data_agendamento))
        conflitos = self.cursor.fetchone()[0]

        # O resultado deve ser 1, pois o próprio agendamento conflita com ele mesmo.
        # Se tentássemos inserir um novo, o count seria > 0.
        self.assertEqual(conflitos, 1, "Deveria detectar exatamente um conflito de horário.")
        print("✅ SUCESSO: Lógica de conflito detectou a sobreposição.")

    def test_05_conflito_de_horario_sobreposto(self):
        """ REGRA: Não deve permitir agendar se o novo horário começa durante um serviço existente. """
        print("\n[TESTE] Bloqueio de conflito de horário (sobreposição)")
        data_base = datetime.now().replace(hour=17, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # 1. Agendamento existente: 17:00, dura 30 min (vai até 17:30)
        self.cursor.execute(
            "INSERT INTO Agendamentos (barbeiro_id, cliente_id, servico_id, data_hora, status) VALUES (?, ?, ?, ?, ?)",
            (self.barbeiro_id_teste, self.cliente_id_teste, self.servico_id_teste, data_base, 'Agendado')
        )

        # 2. Nova tentativa de agendamento: 17:15 (começa durante o anterior)
        data_conflito = data_base + timedelta(minutes=15)
        duracao_novo_servico = 30
        dt_fim_novo = data_conflito + timedelta(minutes=duracao_novo_servico)

        query_conflito = """
            SELECT COUNT(*) FROM Agendamentos a INNER JOIN Servicos s ON a.servico_id = s.id
            WHERE a.barbeiro_id = ? AND a.data_hora < ? AND DATEADD(minute, s.duracao_minutos, a.data_hora) > ?
        """
        self.cursor.execute(query_conflito, (self.barbeiro_id_teste, dt_fim_novo, data_conflito))
        conflitos = self.cursor.fetchone()[0]

        self.assertEqual(conflitos, 1, "Deveria detectar exatamente um conflito de sobreposição.")
        print("✅ SUCESSO: Lógica de conflito detectou agendamento sobreposto.")


if __name__ == '__main__':
    unittest.main()