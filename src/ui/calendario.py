import customtkinter as ctk
import sys
import os
import ctypes
import re
from datetime import datetime
from tkinter import messagebox
from PIL import Image, ImageTk 
from tkcalendar import DateEntry 

# --- CONFIGURAÇÃO DE TEMA ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def aplicar_id_app():
    try:
        myappid = u'leo.barberagente.agendador.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

aplicar_id_app()

CAMINHO_IMG = r'\public\img\icon.png'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
sys.path.append(os.path.join(ROOT_DIR, 'src'))

from database.connection import inicializar_banco

class BarberAgenteApp(ctk.CTk):
    """
    CLASSE PRINCIPAL DA INTERFACE DO CALENDÁRIO.
    Gerencia agendamentos e possui validação de data retroativa e logout.
    """
    def __init__(self, on_logout=None):
        """ 
        Inicializa a janela. 
        :param on_logout: Função callback vinda do main.py para reiniciar o login.
        """
        super().__init__()
        
        self.on_logout = on_logout # Armazena a função de retorno ao login
        self.title("BarberAgente v1.0")
        self.geometry("550x850") 
        self.configurar_icone_taskbar()

        self.conn = inicializar_banco()
        if self.conn:
            self.cursor = self.conn.cursor()
        else:
            messagebox.showerror("Erro", "Falha na conexão com o banco.")
            self.destroy()
            return

        self.setup_ui()
        self.atualizar_relogio()
        self.atualizar_lista_agenda()

    def configurar_icone_taskbar(self):
        if os.path.exists(CAMINHO_IMG):
            try:
                pil_img = Image.open(CAMINHO_IMG)
                self.icon_tk = ImageTk.PhotoImage(pil_img)
                self.wm_iconphoto(True, self.icon_tk)
            except Exception:
                pass

    def setup_ui(self):
        """ Organiza botões, campos de entrada e a área de listagem. """
        
        # --- BOTÃO VOLTAR / LOGOUT ---
        self.btn_logout = ctk.CTkButton(self, text="⬅ TROCAR CONTA", font=("Arial", 11, "bold"),
                                        fg_color="#E74C3C", hover_color="#C0392B", width=120,
                                        command=self.executar_logout)
        self.btn_logout.place(x=410, y=20)

        # Botão de Acesso Administrativo
        self.btn_admin = ctk.CTkButton(self, text="⚙ GERENCIAR ACESSOS", font=("Arial", 11, "bold"),
                                       fg_color="#444", hover_color="#666", width=150,
                                       command=self.abrir_gestao_usuarios)
        self.btn_admin.place(x=20, y=20)

        # Cabeçalho
        self.lbl_nome_app = ctk.CTkLabel(self, text="BARBER AGENTE", font=("Impact", 35), text_color="#3b8ed0")
        self.lbl_nome_app.pack(pady=(70, 0))

        self.lbl_relogio = ctk.CTkLabel(self, text="", font=("Arial", 18, "bold"))
        self.lbl_relogio.pack(pady=5)

        # Frame de Entradas
        self.frame_inputs = ctk.CTkFrame(self, border_width=2, corner_radius=10)
        self.frame_inputs.pack(pady=20, padx=20, fill="x")

        # Widget de Calendário
        ctk.CTkLabel(self.frame_inputs, text="Selecione a Data:", font=("Arial", 13, "bold")).pack(pady=(10, 0))
        self.cal = DateEntry(self.frame_inputs, width=15, background='#3b8ed0', 
                             foreground='white', borderwidth=2, year=2026, 
                             locale='pt_BR', date_pattern='y-mm-dd')
        self.cal.pack(pady=10)

        # Seletores de Horário
        ctk.CTkLabel(self.frame_inputs, text="Horário (Digite ou Selecione):", font=("Arial", 13, "bold")).pack(pady=(5, 0))
        self.time_frame = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        self.time_frame.pack(pady=10)

        self.ent_hora = ctk.CTkComboBox(self.time_frame, width=90, border_width=2,
                                        values=[f"{i:02d}" for i in range(8, 21)])
        self.ent_hora.set("10")
        self.ent_hora.pack(side="left", padx=5)

        ctk.CTkLabel(self.time_frame, text=":", font=("Arial", 18, "bold")).pack(side="left")

        self.ent_minuto = ctk.CTkComboBox(self.time_frame, width=90, border_width=2,
                                          values=["00", "15", "30", "45"])
        self.ent_minuto.set("00")
        self.ent_minuto.pack(side="left", padx=5)

        self.btn_agendar = ctk.CTkButton(self, text="VERIFICAR E AGENDAR", font=("Arial", 14, "bold"),
                                         fg_color="#3b8ed0", hover_color="#2a699d", 
                                         border_width=2, corner_radius=10,
                                         command=self.processar_agendamento)
        self.btn_agendar.pack(pady=20)

        self.scroll_agenda = ctk.CTkScrollableFrame(self, width=450, height=300, border_width=2)
        self.scroll_agenda.pack(pady=10, padx=20, fill="both", expand=True)

    def executar_logout(self):
        """ Fecha o calendário e sinaliza ao main.py para reabrir o login. """
        if messagebox.askyesno("Sair", "Deseja encerrar a sessão e trocar de conta?"):
            self.destroy()
            if self.on_logout:
                self.on_logout()

    def processar_agendamento(self):
        """ Valida se a data é futura e se o horário está livre. """
        data_selecionada = self.cal.get_date()
        hora = int(self.ent_hora.get())
        minuto = int(self.ent_minuto.get())

        # CRIAÇÃO DO OBJETO DATETIME PARA COMPARAÇÃO
        data_hora_agendamento = datetime(data_selecionada.year, data_selecionada.month, data_selecionada.day, hora, minuto)
        agora = datetime.now()

        # VALIDAÇÃO: BLOQUEIO DE PASSADO
        if data_hora_agendamento < agora:
            messagebox.showerror("Erro de Data", "Não é possível realizar agendamentos no passado!")
            return

        data_hora_str = data_hora_agendamento.strftime('%Y-%m-%d %H:%M:%S')

        try:
            self.cursor.execute("SELECT COUNT(*) FROM Agendamentos WHERE DataHora = ?", (data_hora_str,))
            if self.cursor.fetchone()[0] > 0:
                messagebox.showwarning("Ocupado", "Este horário já possui agendamento.")
                return

            self.cursor.execute("INSERT INTO Agendamentos (DataHora, ClienteId, BarbeiroId) VALUES (?, 1, 99)", (data_hora_str,))
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Agendado!")
            self.atualizar_lista_agenda()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def abrir_gestao_usuarios(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Gerenciamento de Barbeiros")
        janela.geometry("400x550")
        janela.grab_set()

        ctk.CTkLabel(janela, text="NOVO USUÁRIO", font=("Impact", 20), text_color="#3b8ed0").pack(pady=10)
        ent_n_user = ctk.CTkEntry(janela, placeholder_text="Nome do Usuário", border_width=2)
        ent_n_user.pack(pady=5, padx=30, fill="x")
        ent_n_pass = ctk.CTkEntry(janela, placeholder_text="Senha", show="*", border_width=2)
        ent_n_pass.pack(pady=5, padx=30, fill="x")

        def salvar():
            u, s = ent_n_user.get(), ent_n_pass.get()
            if not u or not s: return
            if not re.match(r'^[a-zA-Z]', u):
                messagebox.showerror("Erro", "O usuário deve iniciar com uma letra!")
                return
            try:
                self.cursor.execute("INSERT INTO Usuarios (Usuario, Senha) VALUES (?, ?)", (u, s))
                self.conn.commit()
                messagebox.showinfo("Sucesso", "Usuário cadastrado!")
                atualizar_lista_ui()
            except:
                messagebox.showerror("Erro", "Usuário já existe!")

        ctk.CTkButton(janela, text="CADASTRAR", fg_color="#2ECC71", font=("Arial", 12, "bold"), 
                      command=salvar).pack(pady=10, padx=30, fill="x")

        ctk.CTkLabel(janela, text="USUÁRIOS ATIVOS", font=("Impact", 20)).pack(pady=(20, 5))
        lista_frame = ctk.CTkScrollableFrame(janela, height=200, border_width=2)
        lista_frame.pack(pady=10, padx=30, fill="both")

        def deletar(nome):
            if nome == "Mestre":
                messagebox.showwarning("Aviso", "O usuário Mestre não pode ser excluído.")
                return
            if messagebox.askyesno("Confirmar", f"Excluir acesso de {nome}?"):
                self.cursor.execute("DELETE FROM Usuarios WHERE Usuario = ?", (nome,))
                self.conn.commit()
                atualizar_lista_ui()

        def atualizar_lista_ui():
            for w in lista_frame.winfo_children(): w.destroy()
            self.cursor.execute("SELECT Usuario FROM Usuarios")
            for row in self.cursor.fetchall():
                f = ctk.CTkFrame(lista_frame, fg_color="transparent")
                f.pack(pady=2, fill="x")
                ctk.CTkLabel(f, text=row[0]).pack(side="left", padx=5)
                ctk.CTkButton(f, text="X", width=30, fg_color="#E74C3C", 
                              command=lambda n=row[0]: deletar(n)).pack(side="right")
        atualizar_lista_ui()

    def atualizar_relogio(self):
        self.lbl_relogio.configure(text=f"Horário Atual: {datetime.now().strftime('%H:%M:%S')}")
        self.after(1000, self.atualizar_relogio)

    def atualizar_lista_agenda(self):
        for widget in self.scroll_agenda.winfo_children(): widget.destroy()
        try:
            self.cursor.execute("SELECT Id, DataHora FROM Agendamentos ORDER BY DataHora ASC")
            for registro in self.cursor.fetchall():
                txt = f"{registro[1].strftime('%d/%m %H:%M')} - CANCELAR"
                btn = ctk.CTkButton(self.scroll_agenda, text=txt, fg_color="#E74C3C", 
                                     border_width=1, command=lambda i=registro[0]: self.cancelar(i))
                btn.pack(pady=5, fill="x", padx=10)
        except: pass

    def cancelar(self, id_ag):
        if messagebox.askyesno("Confirmar", "Deseja cancelar?"):
            self.cursor.execute("DELETE FROM Agendamentos WHERE Id = ?", (id_ag,))
            self.conn.commit()
            self.atualizar_lista_agenda()

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
    app = BarberAgenteApp()
    app.mainloop()