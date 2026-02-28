import customtkinter as ctk
import os
import re
import sys
import ctypes
from tkinter import messagebox
from PIL import Image, ImageTk

# Ajuste de path para garantir a importação do banco de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(os.path.join(ROOT_DIR, 'src'))

from database.connection import inicializar_banco

# Configurações globais de aparência
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LoginApp(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        
        # Função callback que agora espera receber o nome do usuário
        self.on_login_success = on_login_success
        
        self.title("BarberAgente - Acesso Restrito")
        self.geometry("450x600")
        self.resizable(False, False)

        # Inicializa conexão
        self.conn = inicializar_banco()
        if not self.conn:
            messagebox.showerror("Erro de Banco", "Não foi possível conectar ao Banco de Dados.")
            self.destroy()
            return
            
        self.setup_ui()

    def setup_ui(self):
        self.lbl_nome_app = ctk.CTkLabel(self, text="BARBER AGENTE", font=("Impact", 40), text_color="#3b8ed0")
        self.lbl_nome_app.pack(pady=(60, 20))

        self.frame_login = ctk.CTkFrame(self, border_width=2, corner_radius=15)
        self.frame_login.pack(pady=20, padx=40, fill="both", expand=True)

        ctk.CTkLabel(self.frame_login, text="USUÁRIO", font=("Arial", 13, "bold")).pack(pady=(30, 5))
        self.ent_user = ctk.CTkEntry(self.frame_login, placeholder_text="USER NAME", 
                                     height=40, border_width=2, corner_radius=8)
        self.ent_user.pack(pady=5, padx=30, fill="x")

        ctk.CTkLabel(self.frame_login, text="SENHA", font=("Arial", 13, "bold")).pack(pady=(20, 5))
        self.ent_pass = ctk.CTkEntry(self.frame_login, placeholder_text="PASSWORD", 
                                     show="*", height=40, border_width=2, corner_radius=8)
        self.ent_pass.pack(pady=5, padx=30, fill="x")

        self.btn_login = ctk.CTkButton(self, text="ACESSAR SISTEMA", font=("Arial", 15, "bold"),
                                       fg_color="#3b8ed0", hover_color="#2a699d", 
                                       height=50, corner_radius=10, border_width=2,
                                       command=self.executar_login)
        self.btn_login.pack(pady=40, padx=70, fill="x")

    def executar_login(self):
        user_input = self.ent_user.get().strip()
        senha_input = self.ent_pass.get().strip()

        if not user_input or not senha_input:
            messagebox.showwarning("Campo Vazio", "Por favor, preencha usuário e senha.")
            return

        if not re.match(r'^[a-zA-Z]', user_input):
            messagebox.showerror("Usuário Inválido", "O usuário deve começar com uma letra.")
            return

        try:
            cursor = self.conn.cursor()
            # Buscamos o usuário e a senha.
            cursor.execute("SELECT Usuario FROM Usuarios WHERE Usuario = ? AND Senha = ?", (user_input, senha_input))
            resultado = cursor.fetchone()

            if resultado:
                # O 'resultado[0]' contém o nome exato vindo do banco (ex: 'Mestre')
                nome_usuario_validado = resultado[0]
                
                self.destroy() 
                # Notifica o main.py passando o nome de quem logou
                self.on_login_success(nome_usuario_validado) 
            else:
                messagebox.showerror("Erro de Autenticação", "Usuário ou Senha incorretos.")
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro ao validar acesso: {e}")

if __name__ == "__main__":
    # Teste isolado passando uma função que aceita o argumento 'user'
    app = LoginApp(lambda user: print(f"Sucesso! Logado como: {user}"))
    app.mainloop()