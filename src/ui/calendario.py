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

# Ajuste de Caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
if os.path.join(ROOT_DIR, 'src') not in sys.path:
    sys.path.append(os.path.join(ROOT_DIR, 'src'))

from database.connection import inicializar_banco

class JanelaGerenciarUsuarios(ctk.CTkToplevel):
    """Janela de gestão: Apenas o 'Mestre' pode cadastrar e deletar"""
    def __init__(self, master, conn, usuario_logado):
        super().__init__(master)
        self.conn = conn
        self.usuario_logado = usuario_logado.lower() # Normaliza para checagem
        self.title("Equipe BarberAgente")
        self.geometry("450x650")
        self.attributes("-topmost", True)
        self.grab_set() 
        self.setup_ui()
        self.atualizar_lista_barbeiros()

    def setup_ui(self):
        # --- SEÇÃO DE CADASTRO (Bloqueada se não for Admin) ---
        ctk.CTkLabel(self, text="NOVO BARBEIRO", font=("Impact", 25), text_color="#3b8ed0").pack(pady=(20, 10))
        
        self.frame_add = ctk.CTkFrame(self, border_width=2, corner_radius=15)
        self.frame_add.pack(pady=10, padx=30, fill="x")

        self.ent_novo_user = ctk.CTkEntry(self.frame_add, placeholder_text="Nome de Usuário", width=250)
        self.ent_novo_user.pack(pady=(15, 5))

        self.ent_nova_pass = ctk.CTkEntry(self.frame_add, placeholder_text="Senha", show="*", width=250)
        self.ent_nova_pass.pack(pady=5)

        self.btn_salvar = ctk.CTkButton(self.frame_add, text="CADASTRAR", 
                                        fg_color="#28a745", hover_color="#218838", font=("Arial", 12, "bold"),
                                        command=self.salvar_usuario)
        self.btn_salvar.pack(pady=15)

        # Restrição visual: Desabilita cadastro para quem não é Mestre
        if self.usuario_logado != "mestre":
            self.ent_novo_user.configure(state="disabled", placeholder_text="Apenas Admin pode cadastrar")
            self.ent_nova_pass.configure(state="disabled")
            self.btn_salvar.configure(state="disabled", fg_color="gray")

        # --- SEÇÃO DE LISTAGEM ---
        ctk.CTkLabel(self, text="BARBEIROS ATIVOS", font=("Impact", 20)).pack(pady=(20, 5))
        
        self.scroll_lista = ctk.CTkScrollableFrame(self, width=380, height=250, border_width=2)
        self.scroll_lista.pack(pady=10, padx=30, fill="both", expand=True)

    def salvar_usuario(self):
        if self.usuario_logado != "mestre":
            messagebox.showerror("Acesso Negado", "Você não tem permissão para cadastrar.")
            return
            
        user = self.ent_novo_user.get().strip()
        senha = self.ent_nova_pass.get().strip()
        
        if not user or not senha:
            messagebox.showwarning("Aviso", "Preencha todos os campos!")
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO Usuarios (Usuario, Senha) VALUES (?, ?)", (user, senha))
            self.conn.commit()
            self.ent_novo_user.delete(0, 'end')
            self.ent_nova_pass.delete(0, 'end')
            self.atualizar_lista_barbeiros()
            messagebox.showinfo("Sucesso", "Barbeiro adicionado!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha: {e}")

    def atualizar_lista_barbeiros(self):
        for widget in self.scroll_lista.winfo_children():
            widget.destroy()

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT Usuario FROM Usuarios ORDER BY Usuario ASC")
            usuarios = cursor.fetchall()

            for (nome,) in usuarios:
                linha = ctk.CTkFrame(self.scroll_lista, fg_color="transparent")
                linha.pack(fill="x", pady=2)

                ctk.CTkLabel(linha, text=f"👤 {nome}", font=("Arial", 12)).pack(side="left", padx=10)
                
                # SÓ MOSTRA O BOTÃO DE REMOVER SE O LOGADO FOR 'MESTRE'
                # E NÃO PERMITE QUE O MESTRE DELETE A SI MESMO
                if self.usuario_logado == "mestre" and nome.lower() != "mestre":
                    btn_del = ctk.CTkButton(linha, text="REMOVER", width=70, height=24,
                                            fg_color="#C0392B", hover_color="#962D22",
                                            command=lambda n=nome: self.deletar_usuario(n))
                    btn_del.pack(side="right", padx=10)
                elif nome.lower() == "mestre":
                    ctk.CTkLabel(linha, text="[ADMIN]", text_color="gray").pack(side="right", padx=10)
        except Exception as e:
            print(f"Erro ao listar: {e}")

    def deletar_usuario(self, nome_user):
        if self.usuario_logado != "mestre":
            messagebox.showerror("Erro", "Ação não permitida.")
            return

        if messagebox.askyesno("Confirmar", f"Remover o acesso de '{nome_user}'?"):
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM Usuarios WHERE Usuario = ?", (nome_user,))
                self.conn.commit()
                self.atualizar_lista_barbeiros()
                messagebox.showinfo("Sucesso", "Usuário removido.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro: {e}")

class BarberAgenteApp(ctk.CTk):
    def __init__(self, usuario_atual="Barbeiro", on_logout=None): # Recebe quem logou
        super().__init__()
        self.on_logout = on_logout 
        self.usuario_atual = usuario_atual
        self.title(f"BarberAgente v1.0 - Logado como: {self.usuario_atual}")
        self.geometry("550x850") 
        
        self.conn = inicializar_banco()
        if not self.conn:
            messagebox.showerror("Erro", "Falha na conexão com o banco.")
            self.destroy()
            return
        self.cursor = self.conn.cursor()

        self.configurar_icone_taskbar()
        self.setup_ui()
        self.atualizar_relogio()
        self.atualizar_lista_agenda()

    def configurar_icone_taskbar(self):
        caminho_icone = os.path.join(ROOT_DIR, "public", "img", "icon.ico")
        if os.path.exists(caminho_icone):
            try:
                self.iconbitmap(caminho_icone)
            except: pass

    def setup_ui(self):
        # Botão Gestão
        self.btn_admin = ctk.CTkButton(self, text="⚙ GESTÃO BARBEIROS", font=("Arial", 11, "bold"),
                                       fg_color="#444", hover_color="#666", width=100,
                                       command=self.abrir_gestao_usuarios)
        self.btn_admin.place(x=20, y=20)

        self.btn_logout = ctk.CTkButton(self, text="⬅ SAIR", font=("Arial", 11, "bold"),
                                        fg_color="#E74C3C", hover_color="#C0392B", width=100,
                                        command=self.executar_logout)
        self.btn_logout.place(x=430, y=20)

        self.lbl_nome_app = ctk.CTkLabel(self, text="BARBER AGENTE", font=("Impact", 35), text_color="#3b8ed0")
        self.lbl_nome_app.pack(pady=(70, 0))

        # Mostra o nome do usuário na tela principal para saber quem está operando
        self.lbl_user_info = ctk.CTkLabel(self, text=f"Operador: {self.usuario_atual}", text_color="gray")
        self.lbl_user_info.pack()

        self.lbl_relogio = ctk.CTkLabel(self, text="", font=("Arial", 18, "bold"))
        self.lbl_relogio.pack(pady=5)

        self.frame_inputs = ctk.CTkFrame(self, border_width=2, corner_radius=10)
        self.frame_inputs.pack(pady=20, padx=20, fill="x")

        ctk.CTkLabel(self.frame_inputs, text="Selecione a Data:", font=("Arial", 13, "bold")).pack(pady=(10, 0))
        self.cal = DateEntry(self.frame_inputs, width=15, background='#3b8ed0', 
                             foreground='white', borderwidth=2, year=2026, 
                             locale='pt_BR', date_pattern='y-mm-dd')
        self.cal.pack(pady=10)

        self.time_frame = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        self.time_frame.pack(pady=10)
        self.ent_hora = ctk.CTkComboBox(self.time_frame, width=90, values=[f"{i:02d}" for i in range(8, 21)])
        self.ent_hora.set("10")
        self.ent_hora.pack(side="left", padx=5)
        ctk.CTkLabel(self.time_frame, text=":", font=("Arial", 18, "bold")).pack(side="left")
        self.ent_minuto = ctk.CTkComboBox(self.time_frame, width=90, values=["00", "15", "30", "45"])
        self.ent_minuto.set("00")
        self.ent_minuto.pack(side="left", padx=5)

        self.btn_agendar = ctk.CTkButton(self, text="VERIFICAR E AGENDAR", font=("Arial", 14, "bold"),
                                         fg_color="#3b8ed0", height=45, command=self.processar_agendamento)
        self.btn_agendar.pack(pady=20)

        self.scroll_agenda = ctk.CTkScrollableFrame(self, width=450, height=300, border_width=2)
        self.scroll_agenda.pack(pady=10, padx=20, fill="both", expand=True)

    def abrir_gestao_usuarios(self):
        # Passa o nome do usuário logado para a janela filha
        JanelaGerenciarUsuarios(self, self.conn, self.usuario_atual)

    def executar_logout(self):
        if messagebox.askyesno("Sair", "Deseja encerrar a sessão?"):
            self.destroy()
            if self.on_logout: self.on_logout()

    # ... (restante dos métodos processar_agendamento, atualizar_relogio, atualizar_lista_agenda, cancelar)
    def processar_agendamento(self):
        try:
            data_selecionada = self.cal.get_date()
            data_hora_agendamento = datetime(data_selecionada.year, data_selecionada.month, data_selecionada.day, 
                                             int(self.ent_hora.get()), int(self.ent_minuto.get()))
            if data_hora_agendamento < datetime.now():
                messagebox.showerror("Erro", "Não agende no passado!")
                return

            data_hora_iso = data_hora_agendamento.strftime('%Y-%m-%dT%H:%M:%S')
            self.cursor.execute("INSERT INTO Agendamentos (DataHora, ClienteId, BarbeiroId) VALUES (?, 1, 99)", (data_hora_iso,))
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Agendado!")
            self.atualizar_lista_agenda()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def atualizar_relogio(self):
        self.lbl_relogio.configure(text=f"Horário Atual: {datetime.now().strftime('%H:%M:%S')}")
        self.after(1000, self.atualizar_relogio)

    def atualizar_lista_agenda(self):
        for widget in self.scroll_agenda.winfo_children(): widget.destroy()
        try:
            self.cursor.execute("SELECT Id, DataHora FROM Agendamentos ORDER BY DataHora ASC")
            for registro in self.cursor.fetchall():
                btn = ctk.CTkButton(self.scroll_agenda, text=f"{registro[1].strftime('%d/%m %H:%M')} - CANCELAR",
                                    fg_color="#E74C3C", command=lambda i=registro[0]: self.cancelar(i))
                btn.pack(pady=5, fill="x", padx=10)
        except: pass

    def cancelar(self, id_ag):
        if messagebox.askyesno("Confirmar", "Deseja cancelar?"):
            self.cursor.execute("DELETE FROM Agendamentos WHERE Id = ?", (id_ag,))
            self.conn.commit()
            self.atualizar_lista_agenda()

if __name__ == "__main__":
    # Para teste direto, simulamos o admin logado
    app = BarberAgenteApp(usuario_atual="Mestre")
    app.mainloop()