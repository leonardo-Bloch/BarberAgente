import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from database.connection import conectar
from datetime import datetime, timedelta
import pywhatkit as kit
import pyautogui
import threading
import time

class BarberAgenteApp(ctk.CTk):
    def __init__(self, usuario_logado):
        super().__init__()
        self.user = usuario_logado
        self.title(f"BarberAgente - {self.user['nome']}")
        self.geometry("1250x850")
        
        self.barbeiro_id_sel = None
        self.cliente_id_sel = None
        self.lista_barbeiros = []
        self.enviados_hoje = set() 

        self.setup_ui()
        self.carregar_barbeiros()
        
        # Inicia o monitor de WhatsApp em segundo plano
        threading.Thread(target=self.loop_verificacao_whatsapp, daemon=True).start()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- PAINEL ESQUERDO ---
        self.f_left = ctk.CTkFrame(self, width=400, corner_radius=15)
        self.f_left.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(self.f_left, text="1. Profissional:", font=("Arial", 14, "bold")).pack(pady=(20, 5))
        self.combo_barbeiro = ctk.CTkComboBox(self.f_left, width=320, command=self.ao_selecionar_barbeiro)
        self.combo_barbeiro.pack(pady=5)

        ctk.CTkLabel(self.f_left, text="2. Data:", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        self.cal = Calendar(self.f_left, locale='pt_BR', selectmode='day', font="Arial 10")
        self.cal.pack(pady=5, padx=10)
        self.cal.bind("<<CalendarSelected>>", lambda e: self.atualizar_grid())

        ctk.CTkLabel(self.f_left, text="3. Horário:", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        horarios = [f"{h:02d}:{m:02d}" for h in range(8, 21) for m in [0, 15, 30, 45]]
        self.combo_hora = ctk.CTkComboBox(self.f_left, width=150, values=horarios)
        self.combo_hora.set("08:00")
        self.combo_hora.pack(pady=5)

        ctk.CTkLabel(self.f_left, text="4. Pesquisar Cliente:", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        self.ent_busca = ctk.CTkEntry(self.f_left, placeholder_text="Digite o nome...", width=320)
        self.ent_busca.pack(pady=5)
        ctk.CTkButton(self.f_left, text="Validar Cliente", command=self.buscar_cliente, fg_color="#3b8ed0").pack(pady=5)
        self.lbl_status_cli = ctk.CTkLabel(self.f_left, text="Nenhum cliente selecionado", text_color="orange")
        self.lbl_status_cli.pack()

        # --- PAINEL DIREITO ---
        self.f_right = ctk.CTkFrame(self, corner_radius=15)
        self.f_right.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        ctk.CTkLabel(self.f_right, text="AGENDA DO DIA", font=("Impact", 28)).pack(pady=20)
        
        # Definição das Colunas
        self.tree = ttk.Treeview(self.f_right, columns=("ID", "Data", "Hora", "Cliente", "Servico"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Data", text="Data")
        self.tree.heading("Hora", text="Horário")
        self.tree.heading("Cliente", text="Nome do Cliente") # Título corrigido
        self.tree.heading("Servico", text="Serviço")
        
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Cliente", width=200, anchor="w")
        self.tree.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.btn_cancelar = ctk.CTkButton(self.f_right, text="CANCELAR AGENDAMENTO SELECIONADO", fg_color="#cc3333", hover_color="#990000", command=self.deletar_agendamento)
        self.btn_cancelar.pack(pady=10)

        # --- RODAPÉ (MANUTENÇÃO DE CADASTROS) ---
        self.f_bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.f_bottom.grid(row=1, column=0, columnspan=2, padx=20, pady=20, sticky="ew")
        
        ctk.CTkButton(self.f_bottom, text="LOGOUT", fg_color="#d35b5b", command=self.destroy).pack(side="left", padx=10)
        ctk.CTkButton(self.f_bottom, text="Gerenciar Barbeiros", command=self.abrir_gerenciar).pack(side="left", padx=10)
        ctk.CTkButton(self.f_bottom, text="Novo Cliente", command=self.abrir_cadastro_cliente).pack(side="left", padx=10)
        ctk.CTkButton(self.f_bottom, text="CONFIRMAR NOVO AGENDAMENTO", fg_color="#2fa572", height=45, font=("Arial", 14, "bold"), command=self.salvar_agendamento).pack(side="right", padx=10)

    # --- LÓGICA WHATSAPP AUTOMÁTICA ---
    def disparar_whatsapp(self, nome, telefone, hora):
        msg = f"Olá {nome}! Passando para lembrar do seu horário hoje às {hora} na BarberAgente. Até já!"
        try:
            tel_limpo = ''.join(filter(str.isdigit, str(telefone)))
            if not tel_limpo.startswith('55'): tel_limpo = "55" + tel_limpo
            tel_final = "+" + tel_limpo
            
            kit.sendwhatmsg_instantly(tel_final, msg, wait_time=15, tab_close=True)
            time.sleep(4)
            pyautogui.press('enter') 
            time.sleep(2)
            pyautogui.hotkey('ctrl', 'w') 
        except Exception as e:
            print(f"Erro envio: {e}")

    def loop_verificacao_whatsapp(self):
        while True:
            agora = datetime.now()
            inicio, fim = agora.replace(microsecond=0), (agora + timedelta(minutes=15)).replace(microsecond=0)
            conn = conectar()
            if conn:
                try:
                    cursor = conn.cursor()
                    query = "SELECT c.nome, c.telefone, a.id, CONVERT(VARCHAR(5), a.data_hora, 108) FROM Agendamentos a INNER JOIN Clientes c ON a.cliente_id = c.id WHERE a.data_hora >= ? AND a.data_hora <= ?"
                    cursor.execute(query, (inicio, fim))
                    for nome, telefone, agend_id, hora in cursor.fetchall():
                        if agend_id not in self.enviados_hoje:
                            self.disparar_whatsapp(nome, telefone, hora)
                            self.enviados_hoje.add(agend_id)
                except Exception as e: print(f"Erro monitor: {e}")
                finally: conn.close()
            time.sleep(30)

    # --- LÓGICA DE DADOS ---
    def atualizar_grid(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if not self.barbeiro_id_sel: return
        data_sql = self.cal.selection_get().strftime('%Y-%m-%d')
        conn = conectar()
        if conn:
            cursor = conn.cursor()
            # MUDANÇA AQUI: Alterada a ordem do SELECT para bater com as colunas da Treeview
            query = """
                SELECT a.id, 
                       FORMAT(a.data_hora, 'dd/MM/yyyy'), 
                       CONVERT(VARCHAR(5), a.data_hora, 108), 
                       c.nome, 
                       a.servico
                FROM Agendamentos a 
                INNER JOIN Clientes c ON a.cliente_id = c.id
                WHERE a.barbeiro_id = ? AND CAST(a.data_hora AS DATE) = ? 
                ORDER BY a.data_hora
            """
            cursor.execute(query, (self.barbeiro_id_sel, data_sql))
            for row in cursor.fetchall():
                # Agora o row[3] é o Nome e o row[4] é o Serviço
                self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4]))
            conn.close()

    def deletar_agendamento(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um agendamento na lista para deletar.")
            return
        
        valores = self.tree.item(selected_item)['values']
        if not valores: return
        agendamento_id = valores[0]

        if messagebox.askyesno("Confirmar", f"Deseja realmente excluir o agendamento ID {agendamento_id}?"):
            conn = conectar()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM Agendamentos WHERE id = ?", (agendamento_id,))
                    conn.commit()
                    messagebox.showinfo("Sucesso", "Agendamento removido!")
                    self.atualizar_grid()
                except Exception as e:
                    messagebox.showerror("Erro", f"Não foi possível deletar: {e}")
                finally:
                    conn.close()

    def salvar_agendamento(self):
        # 1. Validação básica de seleção
        if not self.barbeiro_id_sel or not self.cliente_id_sel:
            messagebox.showwarning("Atenção", "Selecione o Barbeiro e valide o Cliente antes de confirmar.")
            return
        
        # 2. Captura e conversão da data/hora
        try:
            data_sel = self.cal.selection_get() 
            hora_sel = self.combo_hora.get()
            dt_obj = datetime.strptime(f"{data_sel} {hora_sel}", "%Y-%m-%d %H:%M")
            
            # --- REGRA DE NEGÓCIO 1: Bloquear agendamentos no passado ---
            if dt_obj < datetime.now():
                messagebox.showerror("Erro de Regra", "Não é possível realizar agendamentos em datas ou horários que já passaram.")
                return

            conn = conectar()
            if conn:
                cursor = conn.cursor()
                
                # --- REGRA DE NEGÓCIO 2: Bloquear conflito de horário para o mesmo barbeiro ---
                query_conflito = """
                    SELECT TOP 1 c.nome 
                    FROM Agendamentos a
                    INNER JOIN Clientes c ON a.cliente_id = c.id
                    WHERE a.barbeiro_id = ? AND a.data_hora = ?
                """
                cursor.execute(query_conflito, (self.barbeiro_id_sel, dt_obj))
                conflito = cursor.fetchone()
                
                if conflito:
                    messagebox.showerror("Conflito de Horário", 
                                       f"Este barbeiro já possui um agendamento neste horário!\n\nCliente: {conflito[0]}")
                    conn.close()
                    return

                # 3. Inserção se passar em todas as regras
                cursor.execute("""
                    INSERT INTO Agendamentos (barbeiro_id, cliente_id, data_hora, servico) 
                    VALUES (?, ?, ?, ?)
                """, (self.barbeiro_id_sel, self.cliente_id_sel, dt_obj, "Corte Normal"))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Sucesso", "Agendamento confirmado com sucesso!")
                self.atualizar_grid()
                
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro ao processar agendamento: {e}")

    def carregar_barbeiros(self):
        conn = conectar()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM Usuarios ORDER BY nome")
            rows = cursor.fetchall()
            self.lista_barbeiros = [{"id": r[0], "nome": r[1]} for r in rows]
            nomes = [b["nome"] for b in self.lista_barbeiros]
            if nomes:
                self.combo_barbeiro.configure(values=nomes); self.combo_barbeiro.set(nomes[0])
                self.barbeiro_id_sel = self.lista_barbeiros[0]["id"]
                self.atualizar_grid()
            conn.close()

    def ao_selecionar_barbeiro(self, nome):
        for b in self.lista_barbeiros:
            if b["nome"] == nome:
                self.barbeiro_id_sel = b["id"]; self.atualizar_grid(); break

    def buscar_cliente(self):
        nome = self.ent_busca.get().strip()
        if not nome: return
        conn = conectar()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM Clientes WHERE nome LIKE ?", (f"%{nome}%",))
            res = cursor.fetchone()
            if res:
                self.cliente_id_sel = res[0]
                self.lbl_status_cli.configure(text=f"Selecionado: {res[1]}", text_color="#2fa572")
            else: messagebox.showwarning("Busca", "Não encontrado.")
            conn.close()

    def abrir_gerenciar(self):
        from ui.gerenciar_barbeiros import GerenciarBarbeiroApp
        GerenciarBarbeiroApp(self, self.user)

    def abrir_cadastro_cliente(self):
        from ui.cadastro_clientes import CadastroClienteApp
        CadastroClienteApp(self)