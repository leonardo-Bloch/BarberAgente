import customtkinter as ctk
import sys
import os
import ctypes
from datetime import datetime
from tkinter import messagebox
from PIL import Image, ImageTk 

# =========================================================================
# 1. TRATAMENTO DE PROCESSO (TASKBAR)
# =========================================================================
def aplicar_id_app():
    try:
        # Força o Windows a reconhecer este script como um App único para mostrar o ícone
        myappid = u'leo.barberagente.agendador.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

aplicar_id_app()

# =========================================================================
# 2. CAMINHOS E BANCO DE DADOS
# =========================================================================
# Caminho fixo do ícone conforme solicitado
CAMINHO_IMG = r'C:\Users\Windows 10\Documents\BarberProject\public\img\BarbarAgente.jpg'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
sys.path.append(os.path.join(ROOT_DIR, 'src'))

from database.connection import inicializar_banco

class BarberAgenteApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("BarberAgente v1.0")
        self.geometry("500x750")

        # Configura o ícone da barra de tarefas
        self.configurar_icone_taskbar()

        # Conecta ao SQL Server
        self.conn = inicializar_banco()
        if self.conn:
            self.cursor = self.conn.cursor()
        else:
            messagebox.showerror("Erro", "Falha na conexão com o banco de dados.")
            self.destroy()
            return

        self.setup_ui()
        self.atualizar_relogio()
        self.atualizar_lista_agenda()

    def configurar_icone_taskbar(self):
        """Usa Pillow para carregar o JPG e aplicar como ícone do sistema"""
        if os.path.exists(CAMINHO_IMG):
            try:
                pil_img = Image.open(CAMINHO_IMG)
                self.icon_tk = ImageTk.PhotoImage(pil_img)
                self.wm_iconphoto(True, self.icon_tk)
            except Exception as e:
                print(f"Erro ao processar ícone: {e}")

    # =========================================================================
    # 3. INTERFACE E SELETORES (DATE TIME PICKER)
    # =========================================================================
    def setup_ui(self):
        self.lbl_nome_app = ctk.CTkLabel(self, text="BARBER AGENTE", font=("Impact", 35), text_color="#3b8ed0")
        self.lbl_nome_app.pack(pady=(20, 0))

        self.lbl_relogio = ctk.CTkLabel(self, text="", font=("Arial", 18, "bold"))
        self.lbl_relogio.pack(pady=5)

        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(pady=20, padx=20, fill="x")

        # Entrada de Data
        ctk.CTkLabel(self.frame_inputs, text="Data (AAAA-MM-DD):").grid(row=0, column=0, padx=10, pady=10)
        self.ent_data = ctk.CTkEntry(self.frame_inputs)
        self.ent_data.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_data.grid(row=0, column=1, padx=10, pady=10)

        # Seletor de Hora e Minuto
        ctk.CTkLabel(self.frame_inputs, text="Hora (HH:MM):").grid(row=1, column=0, padx=10, pady=10)
        self.time_frame = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        self.time_frame.grid(row=1, column=1, padx=10, pady=10)
        
        self.ent_hora = ctk.CTkEntry(self.time_frame, width=50)
        self.ent_hora.insert(0, "10")
        self.ent_hora.pack(side="left", padx=2)
        ctk.CTkLabel(self.time_frame, text=":").pack(side="left")
        self.ent_minuto = ctk.CTkEntry(self.time_frame, width=50)
        self.ent_minuto.insert(0, "00")
        self.ent_minuto.pack(side="left", padx=2)

        self.btn_agendar = ctk.CTkButton(self, text="VERIFICAR E AGENDAR", fg_color="#2ECC71", 
                                         hover_color="#27AE60", command=self.processar_agendamento)
        self.btn_agendar.pack(pady=10)

        self.scroll_agenda = ctk.CTkScrollableFrame(self, width=400, height=280)
        self.scroll_agenda.pack(pady=10, padx=20, fill="both", expand=True)

    # =========================================================================
    # 4. LÓGICA DE VALIDAÇÃO (IMPOSSIBILITAR DUPLICIDADE)
    # =========================================================================
    def processar_agendamento(self):
        """Verifica se o horário está vago e exibe mensagem de erro se estiver ocupado"""
        data = self.ent_data.get()
        hora = self.ent_hora.get()
        minuto = self.ent_minuto.get()
        data_hora_str = f"{data} {hora}:{minuto}:00"

        try:
            # --- PASSO DE VALIDAÇÃO ---
            # Verifica no SQL Server se já existe um registro com este exato momento
            self.cursor.execute("SELECT COUNT(*) FROM Agendamentos WHERE DataHora = ?", (data_hora_str,))
            resultado = self.cursor.fetchone()[0]

            if resultado > 0:
                # Lanço a mensagem indicando o motivo do impedimento
                messagebox.showwarning(
                    "Agendamento Negado", 
                    f"Impossível agendar: O horário {data_hora_str} já está ocupado por outro cliente."
                )
                return # Interrompe a função aqui

            # --- PASSO DE INSERÇÃO ---
            self.cursor.execute(
                "INSERT INTO Agendamentos (DataHora, ClienteId, BarbeiroId) VALUES (?, 1, 99)", 
                (data_hora_str,)
            )
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Horário agendado com sucesso!")
            self.atualizar_lista_agenda()
            
        except Exception as e:
            messagebox.showerror("Erro de Banco", f"Falha na operação: {e}")

    def atualizar_relogio(self):
        agora = datetime.now().strftime("%H:%M:%S")
        self.lbl_relogio.configure(text=f"Horário Atual: {agora}")
        self.after(1000, self.atualizar_relogio)

    def atualizar_lista_agenda(self):
        """Atualiza a lista visual buscando do banco"""
        for widget in self.scroll_agenda.winfo_children(): widget.destroy()
        try:
            self.cursor.execute("SELECT Id, DataHora FROM Agendamentos ORDER BY DataHora ASC")
            for registro in self.cursor.fetchall():
                txt = f"{registro[1].strftime('%d/%m %H:%M')} - CANCELAR"
                btn = ctk.CTkButton(self.scroll_agenda, text=txt, fg_color="#E74C3C", 
                                     command=lambda i=registro[0]: self.cancelar(i))
                btn.pack(pady=2, fill="x")
        except: pass

    def cancelar(self, id_ag):
        if messagebox.askyesno("Confirmar", "Deseja cancelar este horário?"):
            self.cursor.execute("DELETE FROM Agendamentos WHERE Id = ?", (id_ag,))
            self.conn.commit()
            self.atualizar_lista_agenda()

if __name__ == "__main__":
    app = BarberAgenteApp()
    app.mainloop()