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
        
        # Função callback que será executada no main.py após sucesso
        self.on_login_success = on_login_success
        
        self.title("BarberAgente - Acesso Restrito")
        self.geometry("450x600")
        self.resizable(False, False)

        # Inicializa conexão e garante estrutura de tabelas/usuário mestre
        self.conn = inicializar_banco()
        if not self.conn:
            messagebox.showerror("Erro de Banco", "Não foi possível conectar ao SQL Server.")
            self.destroy()
            return
            
        self.setup_ui()

    def setup_ui(self):
        # Título com a identidade visual do projeto
        self.lbl_nome_app = ctk.CTkLabel(self, text="BARBER AGENTE", font=("Impact", 40), text_color="#3b8ed0")
        self.lbl_nome_app.pack(pady=(60, 20))

        # Container principal (estilo border-radius 10-15 conforme solicitado)
        self.frame_login = ctk.CTkFrame(self, border_width=2, corner_radius=15)
        self.frame_login.pack(pady=20, padx=40, fill="both", expand=True)

        # Campo Usuário
        ctk.CTkLabel(self.frame_login, text="USUÁRIO", font=("Arial", 13, "bold")).pack(pady=(30, 5))
        self.ent_user = ctk.CTkEntry(self.frame_login, placeholder_text="USER NAME", 
                                     height=40, border_width=2, corner_radius=8)
        self.ent_user.pack(pady=5, padx=30, fill="x")

        # Campo Senha
        ctk.CTkLabel(self.frame_login, text="SENHA", font=("Arial", 13, "bold")).pack(pady=(20, 5))
        self.ent_pass = ctk.CTkEntry(self.frame_login, placeholder_text="PASSWORD", 
                                     show="*", height=40, border_width=2, corner_radius=8)
        self.ent_pass.pack(pady=5, padx=30, fill="x")

        # Botão de Ação
        self.btn_login = ctk.CTkButton(self, text="ACESSAR SISTEMA", font=("Arial", 15, "bold"),
                                       fg_color="#3b8ed0", hover_color="#2a699d", 
                                       height=50, corner_radius=10, border_width=2,
                                       command=self.executar_login)
        self.btn_login.pack(pady=40, padx=70, fill="x")

    def executar_login(self):
        user = self.ent_user.get()
        senha = self.ent_pass.get()

        # Validações de Regras de Negócio
        if not user or not senha:
            messagebox.showwarning("Campo Vazio", "Por favor, preencha usuário e senha.")
            return

        # Regra: Iniciar obrigatoriamente com letra
        if not re.match(r'^[a-zA-Z]', user):
            messagebox.showerror("Usuário Inválido", "O usuário deve começar obrigatoriamente com uma letra.")
            return

        try:
            cursor = self.conn.cursor()
            # A query abaixo respeita o Case Sensitive devido ao COLLATE Latin1_General_CS_AS
            cursor.execute("SELECT * FROM Usuarios WHERE Usuario = ? AND Senha = ?", (user, senha))
            resultado = cursor.fetchone()

            if resultado:
                # Fecha esta janela e notifica o script main.py para abrir o calendário
                self.destroy() 
                self.on_login_success() 
            else:
                messagebox.showerror("Erro de Autenticação", "Usuário ou Senha incorretos.")
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro ao validar acesso: {e}")

def configurar_icone_taskbar(self):
        """
        Documentação Técnica:
        ---------------------
        Objetivo: Define a identidade visual do app na janela e na Barra de Tarefas.
        
        1. AppUserModelID: Comando do ctypes que registra um ID único para o processo. 
           Sem isso, o Windows agrupa seu programa no ícone padrão do Python.
        2. wm_iconphoto: Define a imagem que aparece no canto superior esquerdo da janela.
        3. Tratamento de Erro: Caso a imagem não exista, o sistema ignora para não travar o app.
        """
        # IMPORTANTE: Note o 'r' antes das aspas para evitar o erro de 'unicodeescape'
        caminho_icone = r"C:\Users\Windows 10\Documents\BarberProject\public\img\icon.ico"
        
        if os.path.exists(caminho_icone):
            try:
                # Carrega a imagem para o ícone da janela
                pil_img = Image.open(caminho_icone)
                self.icon_tk = ImageTk.PhotoImage(pil_img)
                self.wm_iconphoto(True, self.icon_tk)
                
                # Para garantir o ícone na Barra de Tarefas do Windows:
                self.iconbitmap(caminho_icone)
            except Exception as e:
                print(f"Erro ao aplicar ícone: {e}")

if __name__ == "__main__":
    # Teste isolado (Coringa: Mestre / Barber@2026)
    app = LoginApp(lambda: print("Login com sucesso! Abrindo calendário..."))
    app.mainloop()