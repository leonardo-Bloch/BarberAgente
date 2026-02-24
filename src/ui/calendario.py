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

CAMINHO_IMG = r'C:\Users\Windows 10\Documents\BarberProject\public\img\icon.ico'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
sys.path.append(os.path.join(ROOT_DIR, 'src'))

from database.connection import inicializar_banco

class BarberAgenteApp(ctk.CTk):
    def __init__(self, on_logout=None):
        super().__init__()
        self.on_logout = on_logout 
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
        caminho_icone = r"C:\Users\Windows 10\Documents\BarberProject\public\img\icon.ico"
        if os.path.exists(caminho_icone):
            try:
                pil_img = Image.open(caminho_icone)
                self.icon_tk = ImageTk.PhotoImage(pil_img)
                self.wm_iconphoto(True, self.icon_tk)
                self.iconbitmap(caminho_icone)
            except Exception as e:
                print(f"Erro ao aplicar ícone: {e}")

    def setup_ui(self):
        self.btn_logout = ctk.CTkButton(self, text="⬅ TROCAR CONTA", font=("Arial", 11, "bold"),
                                        fg_color="#E74C3C", hover_color="#C0392B", width=120,
                                        command=self.executar_logout)
        self.btn_logout.place(x=410, y=20)

        self.btn_admin = ctk.CTkButton(self, text="⚙ GERENCIAR ACESSOS", font=("Arial", 11, "bold"),
                                       fg_color="#444", hover_color="#666", width=150,
                                       command=self.abrir_gestao_usuarios)
        self.btn_admin.place(x=20, y=20)

        self.lbl_nome_app = ctk.CTkLabel(self, text="BARBER AGENTE", font=("Impact", 35), text_color="#3b8ed0")
        self.lbl_nome_app.pack(pady=(70, 0))

        self.lbl_relogio = ctk.CTkLabel(self, text="", font=("Arial", 18, "bold"))
        self.lbl_relogio.pack(pady=5)

        self.frame_inputs = ctk.CTkFrame(self, border_width=2, corner_radius=10)
        self.frame_inputs.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(self.frame_inputs, text="Selecione a Data:", font=("Arial", 13, "bold")).pack(pady=(10, 0))
        self.cal = DateEntry(self.frame_inputs, width=15, background='#3b8ed0', 
                             foreground='white', borderwidth=2, year=2026, 
                             locale='pt_BR', date_pattern='y-mm-dd')
        self.cal.pack(pady=10)

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
        if messagebox.askyesno("Sair", "Deseja encerrar a sessão e trocar de conta?"):
            self.destroy()
            if self.on_logout:
                self.on_logout()

    # --- MÉTODO MODIFICADO PARA PADRÃO ISO ---
    # --- MÉTODO MODIFICADO PARA RESOLVER O ERRO 242 ---
    def processar_agendamento(self):
        """ Valida se a data é futura e salva no banco usando Formato ISO. """
        try:
            data_selecionada = self.cal.get_date()
            hora = int(self.ent_hora.get())
            minuto = int(self.ent_minuto.get())

            # Criação do objeto datetime completo
            data_hora_agendamento = datetime(data_selecionada.year, data_selecionada.month, data_selecionada.day, hora, minuto)
            agora = datetime.now()

            # Permite agendar para hoje se o horário for futuro
            if data_hora_agendamento < agora:
                messagebox.showerror("Erro de Data", "Não é possível realizar agendamentos no passado!")
                return

            # A LINHA ABAIXO É A CHAVE: O formato ISO (YYYY-MM-DDTHH:MM:SS) é infalível no SQL Server
            data_hora_iso = data_hora_agendamento.strftime('%Y-%m-%dT%H:%M:%S') 

            # Verificação de conflito no banco
            # DICA: Use aspas simples na query para garantir que o SQL trate como data
            self.cursor.execute("SELECT COUNT(*) FROM Agendamentos WHERE DataHora = ?", (data_hora_iso,))
            
            if self.cursor.fetchone()[0] > 0:
                messagebox.showwarning("Ocupado", "Este horário já possui agendamento.")
                return

            # Inserção correta
            self.cursor.execute(
                "INSERT INTO Agendamentos (DataHora, ClienteId, BarbeiroId) VALUES (?, 1, 99)", 
                (data_hora_iso,)
            )
            
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Agendado com sucesso!")
            self.atualizar_lista_agenda()

        except Exception as e:
            # Isso ajudará a ver se o erro mudou
            messagebox.showerror("Erro de Banco", f"Erro Técnico: {str(e)}")

    def abrir_gestao_usuarios(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Gerenciamento de Barbeiros")
        janela.geometry("400x550")
        janela.grab_set()
        # ... (restante do código de gestão permanece igual)

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

if __name__ == "__main__":
    app = BarberAgenteApp()
    app.mainloop()