import sys
from ui.app import JamApp

def main():
    print("=== JAM (Just Another Mind) ===")
    print("Select Language / Selecciona el idioma de la interfaz:")
    print("[1] Español (Predeterminado)")
    print("[2] English")
    
    try:
        lang_choice = input("> ").strip()
    except EOFError:
        lang_choice = "1"
        
    language = "en" if lang_choice == "2" else "es"
    
    # Initialize the Textual App with the selected language
    app = JamApp(language=language)
    app.run()

if __name__ == "__main__":
    main()
