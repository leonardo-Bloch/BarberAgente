import customtkinter as ctk
from tkinter import messagebox
from database.connection import conectar

class LoginApp(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        
        # Configurações da Janela
        self.title("BarberAgente - Acesso Restrito")
        self.geometry("450x600")
        self.resizable(False, False)
        
        # Tema Escuro
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.setup_ui()

    def setup_ui(self):
        # Container Centralizado
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both", padx=40)

        # Título Principal
        self.lbl_titulo = ctk.CTkLabel(
            self.main_frame, 
            text="BARBER AGENTE", 
            font=("Roboto", 32, "bold"), 
            text_color="#3b8ed0"
        )
        self.lbl_titulo.pack(pady=(60, 50))

        # --- SEÇÃO USUÁRIO ---
        ctk.CTkLabel(self.main_frame, text="USUÁRIO", font=("Arial", 13, "bold")).pack(anchor="w", padx=25)
        
        self.ent_user = ctk.CTkEntry(
            self.main_frame, placeholder_text="USER NAME", 
            width=320, height=45, border_width=2
        )
        self.ent_user.pack(pady=(5, 20))

        # --- SEÇÃO SENHA ---
        ctk.CTkLabel(self.main_frame, text="SENHA", font=("Arial", 13, "bold")).pack(anchor="w", padx=25)
        
        self.ent_pass = ctk.CTkEntry(
            self.main_frame, placeholder_text="********", 
            show="*", width=320, height=45, border_width=2
        )
        self.ent_pass.pack(pady=(5, 40))

        # --- BOTÃO DE ACESSO ---
        self.btn_login = ctk.CTkButton(
            self.main_frame, text="ACESSAR O SISTEMA", 
            font=("Arial", 16, "bold"), width=320, height=55, 
            corner_radius=8, command=self.executar_login
        )
        self.btn_login.pack()

    def executar_login(self):
        user = self.ent_user.get().strip()
        pwd = self.ent_pass.get().strip()

        if not user or not pwd:
            messagebox.showwarning("Campos Vazios", "Por favor, informe usuário e senha.")
            return

        conn = conectar()
        if conn:
            try:
                # Criamos o cursor explicitamente
                cursor = conn.cursor()
                
                # Query ultra-compatível (evita o erro HYC00 em drivers antigos)
                sql = "SELECT id, nome, tipo_acesso FROM Usuarios WHERE nome = ? AND senha = ?"
                
                # Execução direta com tratamento de parâmetros
                cursor.execute(sql, (user, pwd))
                resultado = cursor.fetchone()
                
                if resultado:
                    dados_usuario = {
                        "id": resultado[0],
                        "nome": resultado[1],
                        "tipo_acesso": resultado[2]
                    }
                    # Limpeza antes de fechar
                    cursor.close()
                    conn.close()
                    
                    self.destroy()
                    self.on_login_success(dados_usuario)
                else:
                    messagebox.showerror("Acesso Negado", "Usuário ou senha incorretos.")
                    cursor.close()
                    conn.close()
            
            except Exception as e:
                # Se o erro for o HYC00, damos uma instrução clara ao usuário
                if "HYC00" in str(e):
                    messagebox.showerror("Erro de Driver", 
                        "Seu driver SQL Server é antigo. Tente atualizar para 'ODBC Driver 17 for SQL Server' "
                        "ou simplifique o nome do usuário.")
                else:
                    messagebox.showerror("Erro no Banco", f"Falha na consulta: {e}")
                
                if conn: conn.close()
        else:
            messagebox.showerror("Conexão", "Não foi possível conectar ao SQL Server. Verifique se o serviço está rodando.")