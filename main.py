import sys
import os
import customtkinter as ctk

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Garante que a pasta 'src' seja a raiz para os imports
caminho_projeto = os.path.dirname(os.path.abspath(__file__))
caminho_src = os.path.join(caminho_projeto, 'src')

if caminho_src not in sys.path:
    sys.path.insert(0, caminho_src)

# Imports após o ajuste de path
from database.connection import inicializar_banco
from ui.login import LoginApp
from ui.calendario import BarberAgenteApp

class SistemaBarber:
    """Classe Orquestradora para gerenciar as transições de tela."""
    def __init__(self):
        # 1. Inicializa o Banco de Dados
        print("Conectando ao SQL Server e verificando tabelas...")
        inicializar_banco()
        
        # Configuração Global de Tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Inicia o fluxo de login
        self.usuario_logado = None
        self.mostrar_login()

    def mostrar_login(self):
        """Abre a tela de login e aguarda o sucesso."""
        print("Iniciando tela de acesso...")
        self.app_login = LoginApp(on_login_success=self.finalizar_login)
        self.app_login.mainloop()

    def finalizar_login(self, dados_usuario):
        """Recebe os dados do login e agenda a abertura da tela principal."""
        self.usuario_logado = dados_usuario
        print(f"Sessão iniciada para: {self.usuario_logado['nome']}")
        
        # O LoginApp já se destrói sozinho. Agora abrimos a principal
        # Usamos o 'after' para garantir que o loop do login encerrou totalmente
        self.mostrar_calendario()

    def mostrar_calendario(self):
        """Abre a tela principal do sistema."""
        self.app_principal = BarberAgenteApp(self.usuario_logado)
        
        # Caso precise de uma função de Logout no futuro:
        # self.app_principal.btn_logout.configure(command=self.realizar_logout)
        
        self.app_principal.mainloop()

    def iniciar():
        try:
            SistemaBarber()
        except Exception as e:
            print(f"Erro crítico no sistema: {e}")

    if __name__ == "__main__":
        iniciar()