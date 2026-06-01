import customtkinter as ctk
from tkinter import ttk, messagebox
from database.data_manager import DataManager

class GerenciarServicosApp(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.db_manager = DataManager()
        self.title("Gerenciar Serviços")
        self.geometry("650x600")
        self.grab_set()
        
        self.setup_ui()
        self.atualizar_grid()

    def setup_ui(self):
        ctk.CTkLabel(self, text="CADASTRO DE SERVIÇOS", font=("Roboto", 22, "bold")).pack(pady=20)

        f_inputs = ctk.CTkFrame(self, fg_color="transparent")
        f_inputs.pack(pady=10, padx=20, fill="x")

        self.ent_nome = ctk.CTkEntry(f_inputs, placeholder_text="Nome do Serviço", width=400, height=40)
        self.ent_nome.pack(pady=10)

        self.ent_preco = ctk.CTkEntry(f_inputs, placeholder_text="Preço (ex: 35.50)", width=400, height=40)
        self.ent_preco.pack(pady=10)

        self.ent_duracao = ctk.CTkEntry(f_inputs, placeholder_text="Duração em minutos (ex: 30)", width=400, height=40)
        self.ent_duracao.pack(pady=10)

        ctk.CTkButton(self, text="CADASTRAR SERVIÇO", fg_color="#2fa572", height=45, 
                      command=self.salvar_servico).pack(pady=10)

        self.f_grid = ctk.CTkFrame(self)
        self.f_grid.pack(expand=True, fill="both", padx=20, pady=20)

        self.tree = ttk.Treeview(self.f_grid, columns=("ID", "Nome", "Preço", "Duração"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Preço", text="Preço (R$)")
        self.tree.heading("Duração", text="Duração (min)")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Duração", width=100, anchor="center")
        self.tree.column("Preço", width=100, anchor="e")
        self.tree.pack(expand=True, fill="both")

        ctk.CTkButton(self, text="EXCLUIR SELECIONADO", fg_color="#d35b5b", 
                      command=self.deletar_servico).pack(pady=10)

    def salvar_servico(self):
        nome = self.ent_nome.get().strip()
        preco_str = self.ent_preco.get().strip().replace(',', '.')
        duracao_str = self.ent_duracao.get().strip()

        if not nome or not preco_str or not duracao_str:
            messagebox.showwarning("Erro", "Preencha todos os campos!")
            return

        try:
            preco = float(preco_str)
            duracao = int(duracao_str)
        except ValueError:
            messagebox.showerror("Erro de Formato", "Preço e Duração devem ser números válidos.")
            return

        sucesso = self.db_manager.save_service(nome, preco, duracao)
        if sucesso:
            messagebox.showinfo("Sucesso", f"Serviço '{nome}' cadastrado!")
            self.ent_nome.delete(0, 'end')
            self.ent_preco.delete(0, 'end')
            self.ent_duracao.delete(0, 'end')
            self.atualizar_grid()
        else:
            messagebox.showerror("Erro de Banco", "Este nome de serviço já existe ou ocorreu um erro.")

    def deletar_servico(self):
        sel = self.tree.selection()
        if not sel: return
        
        id_servico = self.tree.item(sel)['values'][0]
        nome_servico = self.tree.item(sel)['values'][1]

        if messagebox.askyesno("Confirmar", f"Excluir o serviço '{nome_servico}'?"):
            try:
                if self.db_manager.check_service_in_use(id_servico):
                    messagebox.showerror("Erro", "Não é possível excluir um serviço que já está em uso em agendamentos.")
                    return

                if self.db_manager.delete_service(id_servico):
                    self.atualizar_grid()
                else:
                    messagebox.showerror("Erro", "Falha ao excluir o serviço.")
            except Exception as e:
                messagebox.showerror("Erro Crítico", f"Falha ao excluir: {e}")

    def atualizar_grid(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        servicos = self.db_manager.get_all_services_details()
        if servicos:
            for row in servicos:
                self.tree.insert("", "end", values=row)

        # Atualiza a lista de serviços na tela principal, se ela estiver aberta
        if hasattr(self.master, 'carregar_servicos'):
            self.master.carregar_servicos()

    def destroy(self):
        # Garante que a tela principal seja atualizada ao fechar
        if hasattr(self.master, 'carregar_servicos'):
            self.master.carregar_servicos()
        super().destroy()