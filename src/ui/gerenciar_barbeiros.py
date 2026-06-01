import customtkinter as ctk
from tkinter import ttk, messagebox
import re
from database.data_manager import DataManager

class GerenciarBarbeiroApp(ctk.CTkToplevel):
    def __init__(self, parent, usuario_logado, on_close_callback=None):
        super().__init__(parent)
        self.db_manager = DataManager()
        self.user = usuario_logado
        self.on_close_callback = on_close_callback
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

        sucesso = self.db_manager.save_barber(nome, senha)
        if sucesso:
            messagebox.showinfo("Sucesso", f"{nome} cadastrado!")
            self.ent_nome.delete(0, 'end')
            self.ent_senha.delete(0, 'end')
            self.atualizar_grid()
        else:
            messagebox.showerror("Erro", "Nome de usuário já existe ou ocorreu um erro de banco de dados.")

    def deletar_barbeiro(self):
        sel = self.tree.selection()
        if not sel: return
        
        id_user = self.tree.item(sel)['values'][0]
        nome_user = self.tree.item(sel)['values'][1]

        if nome_user == self.user['nome']:
            messagebox.showerror("Erro", "Você não pode se excluir!")
            return

        if messagebox.askyesno("Confirmar", f"Excluir {nome_user}?"):
            sucesso = self.db_manager.delete_barber(id_user)
            if sucesso:
                self.atualizar_grid()
            else:
                messagebox.showerror("Erro", "Não foi possível excluir o usuário.")

    def atualizar_grid(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        usuarios = self.db_manager.get_all_barbers_details()
        if usuarios:
            for row in usuarios:
                self.tree.insert("", "end", values=(row[0], row[1], row[2]))

    def destroy(self):
        """
        Sobrescreve o método de fechar a janela para garantir que a tela 
        principal seja atualizada.
        """
        if self.on_close_callback:
            self.on_close_callback()
        super().destroy()