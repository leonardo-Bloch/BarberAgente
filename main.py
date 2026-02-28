import sys
import os
import ctypes
from PIL import Image, ImageTk

# 1. Ajuste de Caminhos para evitar ModuleNotFoundError
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'src'))

from ui.login import LoginApp
from ui.calendario import BarberAgenteApp

def configurar_identidade_windows():
    """Garante que o ícone apareça na barra de tarefas do Windows"""
    try:
        myappid = u'leo.barberagente.agendador.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

def iniciar_sistema():
    configurar_identidade_windows()
    
    # Caminho do ícone
    CAMINHO_ICONE = r"C:\Users\Windows 10\Documents\BarberProject\public\img\icon.ico"

    def abrir_calendario(usuario_logado):
        """Inicia o calendário passando o nome do usuário validado no login"""
        # Agora o BarberAgenteApp recebe quem logou para decidir se permite excluir barbeiros
        app_calendario = BarberAgenteApp(usuario_atual=usuario_logado, on_logout=iniciar_sistema)
        
        # Aplicando o ícone na janela do calendário
        if os.path.exists(CAMINHO_ICONE):
            try:
                img = Image.open(CAMINHO_ICONE)
                icon_tk = ImageTk.PhotoImage(img)
                app_calendario.wm_iconphoto(True, icon_tk)
                app_calendario.iconbitmap(CAMINHO_ICONE)
                # Mantemos uma referência para evitar que o Garbage Collector limpe a imagem
                app_calendario._icon_ref = icon_tk 
            except: pass
            
        app_calendario.mainloop()

    # Inicia a tela de login. 
    # O LoginApp deve ser modificado para passar o nome do usuário no callback.
    app_login = LoginApp(on_login_success=abrir_calendario)
    
    if os.path.exists(CAMINHO_ICONE):
        try:
            img_login = Image.open(CAMINHO_ICONE)
            icon_login = ImageTk.PhotoImage(img_login)
            app_login.wm_iconphoto(True, icon_login)
            app_login.iconbitmap(CAMINHO_ICONE)
            app_login._icon_ref = icon_login
        except: pass
        
    app_login.mainloop()

if __name__ == "__main__":
    iniciar_sistema()