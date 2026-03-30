import customtkinter as ctk
from tkinter import ttk, messagebox
from database.connection import conectar

class CadastroClienteApp(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent # Referência para a tela de calendário
        self.title("BarberAgente - Cadastrar Cliente")
        self.geometry("600x700")
        self.resizable(False, False)
        
        # Faz a janela ficar na frente e impede interação com a de baixo
        self.grab_set()
        
        self.setup_ui()
        self.atualizar_grid_clientes()

    def setup_ui(self):
        ctk.CTkLabel(self, text="NOVO CLIENTE", font=("Roboto", 24, "bold"), text_color="#3b8ed0").pack(pady=20)

        # --- CAMPOS DE ENTRADA ---
        self.f_inputs = ctk.CTkFrame(self, fg_color="transparent")
        self.f_inputs.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.f_inputs, text="Nome do Cliente:", font=("Arial", 12, "bold")).pack(anchor="w", padx=25)
        self.ent_nome = ctk.CTkEntry(self.f_inputs, placeholder_text="Digite o nome completo...", width=500, height=40)
        self.ent_nome.pack(pady=(5, 15))

        ctk.CTkLabel(self.f_inputs, text="Telefone:", font=("Arial", 12, "bold")).pack(anchor="w", padx=25)
        self.ent_tel = ctk.CTkEntry(self.f_inputs, placeholder_text="(00) 00000-0000", width=500, height=40)
        self.ent_tel.pack(pady=(5, 15))

        self.btn_confirmar = ctk.CTkButton(
            self, 
            text="CONFIRMAR CADASTRO", 
            fg_color="#2fa572", 
            hover_color="#106a43",
            font=("Arial", 14, "bold"),
            height=50,
            command=self.salvar_cliente
        )
        self.btn_confirmar.pack(pady=20)

        # --- GRID DE CLIENTES ---
        ctk.CTkLabel(self, text="Clientes Cadastrados Recentemente:", font=("Arial", 12, "italic")).pack(pady=(10, 0))
        
        self.f_grid = ctk.CTkFrame(self)
        self.f_grid.pack(expand=True, fill="both", padx=20, pady=20)

        # Estilização da tabela
        self.tree = ttk.Treeview(self.f_grid, columns=("Nome", "Telefone", "Data"), show="headings")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Telefone", text="Telefone")
        self.tree.heading("Data", text="Data Cadastro")
        
        self.tree.column("Nome", width=200)
        self.tree.column("Telefone", width=120, anchor="center")
        self.tree.column("Data", width=150, anchor="center")
        self.tree.pack(expand=True, fill="both")

    def salvar_cliente(self):
        nome = self.ent_nome.get().strip()
        tel = self.ent_tel.get().strip()

        if not nome or not tel:
            messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios!")
            return

        conn = conectar()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Verificação de segurança: evita cadastrar o mesmo telefone duas vezes
                cursor.execute("SELECT id FROM Clientes WHERE telefone = ?", (tel,))
                if cursor.fetchone():
                    messagebox.showerror("Erro", "Este número de telefone já está cadastrado!")
                    return

                cursor.execute(
                    "INSERT INTO Clientes (nome, telefone) VALUES (?, ?)",
                    (nome, tel)
                )
                conn.commit()
                
                messagebox.showinfo("Sucesso", f"Cliente {nome} cadastrado com sucesso!")
                
                # Limpa os campos
                self.ent_nome.delete(0, 'end')
                self.ent_tel.delete(0, 'end')
                
                # Atualiza a lista da janela atual
                self.atualizar_grid_clientes()
                
                # Opcional: Se quiser que o nome já apareça na busca da tela principal
                if hasattr(self.parent, 'ent_busca'):
                    self.parent.ent_busca.delete(0, 'end')
                    self.parent.ent_busca.insert(0, nome)
                
            except Exception as e:
                messagebox.showerror("Erro no Banco", f"Não foi possível salvar: {e}")
            finally:
                conn.close()

    def atualizar_grid_clientes(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        conn = conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # Usei CONVERT para ser mais compatível com todas as versões do SQL Server
                cursor.execute("""
                    SELECT nome, telefone, CONVERT(VARCHAR(16), data_cadastro, 120) 
                    FROM Clientes 
                    ORDER BY id DESC
                """)
                for row in cursor.fetchall():
                    self.tree.insert("", "end", values=row)
            except Exception as e:
                print(f"Erro ao listar clientes: {e}")
            finally:
                conn.close()