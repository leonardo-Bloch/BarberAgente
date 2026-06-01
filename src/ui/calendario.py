import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from database.data_manager import DataManager
from datetime import datetime, timedelta
import pywhatkit as kit
import pyautogui
import threading
import time

class BarberAgenteApp(ctk.CTk):
    def __init__(self, usuario_logado, theme_toggle_callback):
        super().__init__()
        self.user = usuario_logado
        self.db_manager = DataManager()
        self.theme_toggle_callback = theme_toggle_callback
        self.title(f"BarberAgente - {self.user['nome']}")
        self.geometry("1250x850")
        
        self.barbeiro_id_sel = None
        self.cliente_id_sel = None
        self.servico_id_sel = None
        self.lista_barbeiros = []
        self.lista_servicos = []
        self.servicos_cache = {} # Cache para id -> {nome, duracao}
        self.enviados_hoje = set() 

        self.setup_ui()
        self.carregar_dados_iniciais()
        
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

        ctk.CTkLabel(self.f_left, text="4. Serviço:", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        self.combo_servico = ctk.CTkComboBox(self.f_left, width=320, command=self.ao_selecionar_servico)
        self.combo_servico.pack(pady=5)

        ctk.CTkLabel(self.f_left, text="5. Pesquisar Cliente:", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        self.ent_busca = ctk.CTkEntry(self.f_left, placeholder_text="Digite o nome...", width=320)
        self.ent_busca.pack(pady=5)
        ctk.CTkButton(self.f_left, text="Validar Cliente", command=self.buscar_cliente, fg_color="#3b8ed0").pack(pady=5)
        self.lbl_status_cli = ctk.CTkLabel(self.f_left, text="Nenhum cliente selecionado", text_color="orange")
        self.lbl_status_cli.pack()

        # --- PAINEL DIREITO ---
        self.f_right = ctk.CTkFrame(self, corner_radius=15)
        self.f_right.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        ctk.CTkLabel(self.f_right, text="AGENDA DO DIA", font=("Impact", 28)).pack(pady=20)
        
        # Estilo da Treeview para cores de status
        style = ttk.Style()
        style.map("Treeview", background=[('selected', '#347083')])
        style.configure("Treeview", rowheight=25)
        self.tree = ttk.Treeview(self.f_right, columns=("ID", "Hora", "Cliente", "Servico", "Status"), show="headings")
        self.tree.tag_configure('Agendado', background='#f0e68c', foreground='black') # Amarelo claro
        self.tree.tag_configure('Confirmado', background='#98fb98', foreground='black') # Verde claro

        # Definição das Colunas
        self.tree.heading("ID", text="ID")
        self.tree.heading("Hora", text="Horário")
        self.tree.heading("Cliente", text="Nome do Cliente") # Título corrigido
        self.tree.heading("Servico", text="Serviço")
        self.tree.heading("Status", text="Status")
        
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
        # Botão para gerenciar serviços, visível apenas para Admin
        if self.user.get('tipo_acesso') == 'Admin':
            ctk.CTkButton(self.f_bottom, text="Gerenciar Serviços", command=self.abrir_gerenciar_servicos).pack(side="left", padx=10)

        ctk.CTkButton(self.f_bottom, text="Novo Cliente", command=self.abrir_cadastro_cliente).pack(side="left", padx=10)
        ctk.CTkButton(self.f_bottom, text="CONFIRMAR NOVO AGENDAMENTO", fg_color="#2fa572", height=45, font=("Arial", 14, "bold"), command=self.salvar_agendamento).pack(side="right", padx=10)
        
        # Interruptor de Tema
        self.theme_switch = ctk.CTkSwitch(self.f_bottom, text="Modo Claro", command=self.toggle_theme_ui)
        self.theme_switch.pack(side="right", padx=20)
        self.theme_switch.deselect() # Começa no modo escuro

    # --- LÓGICA WHATSAPP AUTOMÁTICA ---
    def disparar_whatsapp(self, nome, telefone, hora):
        msg = f"Olá {nome}! Passando para lembrar do seu horário hoje às {hora} na BarberAgente. Por favor, responda com SIM para confirmar ou NÃO para cancelar. Até já!"
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
        """
        Verifica continuamente por agendamentos que estão se aproximando para enviar
        um lembrete de confirmação via WhatsApp.
        A lógica busca por agendamentos que ocorrerão entre 60 e 62 minutos a partir do
        momento da verificação, garantindo uma janela de 2 minutos para capturar o evento.
        """
        while True:
            agora = datetime.now()
            # Define uma janela de tempo mais segura para a verificação (ex: entre 60 e 62 minutos a partir de agora)
            inicio = (agora + timedelta(minutes=60)).replace(second=0, microsecond=0)
            fim = (agora + timedelta(minutes=62)).replace(second=0, microsecond=0)
            
            agendamentos = self.db_manager.get_appointments_for_whatsapp(inicio, fim)
            for nome, telefone, agend_id, hora in agendamentos or []:
                if agend_id not in self.enviados_hoje:
                    self.disparar_whatsapp(nome, telefone, hora)
                    self.enviados_hoje.add(agend_id)
            time.sleep(30)

    def toggle_theme_ui(self):
        """Chamado pelo interruptor para trocar o tema e atualizar o texto."""
        new_theme = self.theme_toggle_callback()
        if new_theme == "light":
            self.theme_switch.configure(text="Modo Escuro")
        else:
            self.theme_switch.configure(text="Modo Claro")

    # --- LÓGICA DE DADOS ---
    def atualizar_grid(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        if not self.barbeiro_id_sel: return
        data_sql = self.cal.selection_get().strftime('%Y-%m-%d')
        
        agendamentos = self.db_manager.get_appointments_for_day(self.barbeiro_id_sel, data_sql)
        if agendamentos:
            for row in agendamentos:
                status = row[4]
                self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3], status), tags=(status,))

    def deletar_agendamento(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um agendamento na lista para deletar.")
            return
        
        valores = self.tree.item(selected_item)['values']
        if not valores: return
        agendamento_id = valores[0]

        if messagebox.askyesno("Confirmar", f"Deseja realmente excluir o agendamento ID {agendamento_id}?"):
            sucesso = self.db_manager.delete_appointment(agendamento_id)
            if sucesso:
                messagebox.showinfo("Sucesso", "Agendamento removido!")
                self.atualizar_grid()
            else:
                messagebox.showerror("Erro", "Não foi possível deletar o agendamento.")

    def salvar_agendamento(self):
        # 1. Validação básica de seleção
        if not self.barbeiro_id_sel or not self.cliente_id_sel or not self.servico_id_sel:
            messagebox.showwarning("Atenção", "É obrigatório selecionar: Barbeiro, Data, Hora, Serviço e Cliente.")
            return
        
        # 2. Captura e conversão da data/hora
        try:
            data_sel = self.cal.selection_get() 
            hora_sel = self.combo_hora.get()
            dt_obj = datetime.strptime(f"{data_sel} {hora_sel}", "%Y-%m-%d %H:%M")

            duracao_servico = self.servicos_cache[self.servico_id_sel]['duracao']
            dt_fim_obj = dt_obj + timedelta(minutes=duracao_servico)
            
            # --- REGRA DE NEGÓCIO 1: Bloquear agendamentos no passado ---
            if dt_obj < datetime.now():
                messagebox.showerror("Erro de Regra", "Não é possível realizar agendamentos em datas ou horários que já passaram.")
                return

            # --- REGRA DE NEGÓCIO 2: Bloquear conflito de horário ---
            conflito = self.db_manager.check_appointment_conflict(self.barbeiro_id_sel, dt_fim_obj, dt_obj)
            if conflito:
                hora_conflito = conflito[1].strftime('%H:%M')
                messagebox.showerror("Conflito de Horário", 
                                   f"Este barbeiro já possui um agendamento que conflita com este horário.\n\nCliente: {conflito[0]} às {hora_conflito}")
                return

            # 3. Inserção se passar em todas as regras
            sucesso = self.db_manager.save_appointment(self.barbeiro_id_sel, self.cliente_id_sel, self.servico_id_sel, dt_obj)
            if sucesso:
                messagebox.showinfo("Sucesso", "Agendamento confirmado com sucesso!")
                self.atualizar_grid()
            else:
                messagebox.showerror("Erro de Banco", "Não foi possível salvar o agendamento.")
                
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Erro ao processar agendamento: {e}")

    def carregar_dados_iniciais(self):
        # Carrega barbeiros
        self.lista_barbeiros = self.db_manager.get_barbers()
        nomes_barbeiros = [b["nome"] for b in self.lista_barbeiros]
        if nomes_barbeiros:
            self.combo_barbeiro.configure(values=nomes_barbeiros)
            self.combo_barbeiro.set(nomes_barbeiros[0])
            self.barbeiro_id_sel = self.lista_barbeiros[0]["id"]
        
        # Carrega serviços e atualiza a grid
        self.carregar_servicos()
        self.atualizar_grid()

    def carregar_servicos(self):
        self.lista_servicos, self.servicos_cache = self.db_manager.get_services()
        nomes_servicos = [s["nome"] for s in self.lista_servicos]
        if nomes_servicos:
            self.combo_servico.configure(values=nomes_servicos)
            self.combo_servico.set(nomes_servicos[0])
            self.servico_id_sel = self.lista_servicos[0]["id"]

    def ao_selecionar_barbeiro(self, nome):
        self.barbeiro_id_sel = next((b["id"] for b in self.lista_barbeiros if b["nome"] == nome), None)
        self.atualizar_grid()

    def ao_selecionar_servico(self, nome):
        self.servico_id_sel = next((s["id"] for s in self.lista_servicos if s["nome"] == nome), None)

    def buscar_cliente(self):
        nome = self.ent_busca.get().strip()
        if not nome: return
        res = self.db_manager.find_client_by_name(nome)
        if res:
            self.cliente_id_sel = res[0]
            self.lbl_status_cli.configure(text=f"Selecionado: {res[1]}", text_color="#2fa572")
        else:
            self.cliente_id_sel = None
            self.lbl_status_cli.configure(text="Cliente não encontrado.", text_color="orange")
            messagebox.showwarning("Busca", "Nenhum cliente encontrado com esse nome.")

    def abrir_gerenciar(self):
        from ui.gerenciar_barbeiros import GerenciarBarbeiroApp
        GerenciarBarbeiroApp(self, self.user, on_close_callback=self.carregar_dados_iniciais)

    def abrir_cadastro_cliente(self):
        from ui.cadastro_clientes import CadastroClienteApp
        CadastroClienteApp(self)

    def abrir_gerenciar_servicos(self):
        from ui.gerenciar_servicos import GerenciarServicosApp
        GerenciarServicosApp(self)