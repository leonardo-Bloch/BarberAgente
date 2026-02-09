import sys
import os

# Adiciona a pasta 'src' ao sistema para que os imports funcionem de qualquer lugar
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Agora importamos o seu app do calendário
try:
    from ui.calendario import BarberAgenteApp
    
    if __name__ == "__main__":
        app = BarberAgenteApp()
        app.mainloop()
except ImportError as e:
    print(f"Erro ao carregar os módulos: {e}")
    print("Certifique-se de que a estrutura de pastas src/ui e src/database está correta.")