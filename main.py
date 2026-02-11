import sys
import os
import ctypes
from PIL import Image, ImageTk  # <--- Faltava isso!

# 1. Ajuste de Caminhos para evitar ModuleNotFoundError
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'src'))

# Agora o Python consegue encontrar estes módulos dentro de src/ui
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
    
    # Caminho do ícone com 'r' para evitar erro de unicodeescape
    CAMINHO_ICONE = r"C:\Users\Windows 10\Documents\BarberProject\public\img\icon.ico"

    def abrir_calendario():
        """Inicia o calendário e configura o ícone dele"""
        app_calendario = BarberAgenteApp(on_logout=iniciar_sistema)
        
        # Aplicando o ícone na janela do calendário
        if os.path.exists(CAMINHO_ICONE):
            img = Image.open(CAMINHO_ICONE)
            icon_tk = ImageTk.PhotoImage(img)
            app_calendario.wm_iconphoto(True, icon_tk)
            app_calendario.iconbitmap(CAMINHO_ICONE)
            
        app_calendario.mainloop()

    # Inicia a tela de login
    app_login = LoginApp(on_login_success=abrir_calendario)
    
    # Aplicando o ícone na janela de login
    if os.path.exists(CAMINHO_ICONE):
        img_login = Image.open(CAMINHO_ICONE)
        icon_login = ImageTk.PhotoImage(img_login)
        app_login.wm_iconphoto(True, icon_login)
        app_login.iconbitmap(CAMINHO_ICONE)
        
    app_login.mainloop()

if __name__ == "__main__":
    iniciar_sistema()