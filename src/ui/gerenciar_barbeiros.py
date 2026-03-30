import customtkinter as ctk
from tkinter import ttk, messagebox
import re
from database.connection import conectar

class GerenciarBarbeiroApp(ctk.CTkToplevel):
    def __init__(self, parent, usuario_logado):
        super().__init__(parent)
        self.user = usuario_logado
        self.title("Gerenciar Profissionais")
        self.geometry("650x750")
        self.grab_set() 
        
        self.setup_ui()
        self.atualizar_grid()

    def setup_ui(self):
        ctk.CTkLabel(self, text="CADASTRO DE BARBEIROS", font=("Roboto", 22, "bold")).pack(pady=20)

        # Container de Inputs
        f_inputs = ctk.CTkFrame(self, fg_color="transparent")
        f_inputs.pack(pady=10, padx=20, fill="x")

        self.ent_nome = ctk.CTkEntry(f_inputs, placeholder_text="Nome Completo", width=400, height=40)
        self.ent_nome.pack(pady=10)

        self.ent_senha = ctk.CTkEntry(f_inputs, placeholder_text="Senha", show="*", width=400, height=40)
        self.ent_senha.pack(pady=10)

        ctk.CTkButton(self, text="CADASTRAR", fg_color="#2fa572", height=45, 
                      command=self.salvar_barbeiro).pack(pady=10)

        # Grid de Visualização
        self.f_grid = ctk.CTkFrame(self)
        self.f_grid.pack(expand=True, fill="both", padx=20, pady=20)

        self.tree = ttk.Treeview(self.f_grid, columns=("ID", "Nome", "Acesso"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Acesso", text="Tipo")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.pack(expand=True, fill="both")

        # Botão Excluir (Só aparece para Admin)
        if self.user.get('tipo_acesso') == 'Admin':
            ctk.CTkButton(self, text="EXCLUIR SELECIONADO", fg_color="#d35b5b", 
                          command=self.deletar_barbeiro).pack(pady=10)

    def salvar_barbeiro(self):
        nome = self.ent_nome.get().strip()
        senha = self.ent_senha.get().strip()

        if not nome or not senha:
            messagebox.showwarning("Erro", "Preencha todos os campos!")
            return

        conn = conectar()
        if conn:
            try:
                cursor = conn.cursor()
                # USANDO APENAS A COLUNA 'nome' CONFORME A NOVA TABELA
                cursor.execute(
                    "INSERT INTO Usuarios (nome, senha, tipo_acesso) VALUES (?, ?, 'Barbeiro')",
                    (nome, senha)
                )
                conn.commit() # Importante se autocommit não estiver ligado
                messagebox.showinfo("Sucesso", f"{nome} cadastrado!")
                self.ent_nome.delete(0, 'end')
                self.ent_senha.delete(0, 'end')
                self.atualizar_grid()
            except Exception as e:
                print(f"Erro SQL: {e}")
                messagebox.showerror("Erro", "Nome já existe ou erro de conexão.")
            finally:
                conn.close()

    def deletar_barbeiro(self):
        sel = self.tree.selection()
        if not sel: return
        
        id_user = self.tree.item(sel)['values'][0]
        nome_user = self.tree.item(sel)['values'][1]

        if nome_user == self.user['nome']:
            messagebox.showerror("Erro", "Você não pode se excluir!")
            return

        if messagebox.askyesno("Confirmar", f"Excluir {nome_user}?"):
            conn = conectar()
            if conn:
                conn.cursor().execute("DELETE FROM Usuarios WHERE id = ?", (id_user,))
                conn.commit()
                conn.close()
                self.atualizar_grid()

    def atualizar_grid(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = conectar()
        if conn:
            cursor = conn.cursor()
            # Busca as 3 colunas que existem na nova tabela
            cursor.execute("SELECT id, nome, tipo_acesso FROM Usuarios")
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=(row[0], row[1], row[2]))
            conn.close()