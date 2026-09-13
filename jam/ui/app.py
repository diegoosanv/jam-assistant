import os
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Input, Static, Log
from textual.binding import Binding

from hardware.detector import HardwareDetector
from core.recommender import ModelRecommender
from core.environment import get_location_and_weather

APP_CSS = """
Screen { background: #000000; }
#sidebar { width: 35; border-right: solid #333333; padding: 1; background: #000000; color: #888888; }
#chat-area { width: 1fr; height: 1fr; border: none; background: #000000; }
#chat-log { height: 1fr; border: none; color: #cccccc; scrollbar-background: #000000; scrollbar-color: #333333; }
#input-container { height: 3; border-top: solid #333333; background: #000000; }
Input { border: none; background: #000000; color: #ffffff; width: 1fr; }
Input:focus { border: none; }
.system-text { color: #00ffcc; }
.title { color: #ffffff; text-style: bold; margin-bottom: 1; }
.subtitle { color: #666666; margin-top: 1; }
"""

class Sidebar(Static):
    def compose(self) -> ComposeResult:
        yield Static("JAM CORE v1.0", classes="title")
        self.sys_status = Static("SYSTEM: ONLINE", classes="system-text")
        yield self.sys_status
        
        self.env_title = Static("[ENV / COMMS]", classes="subtitle")
        yield self.env_title
        self.env_info = Static("FETCHING...")
        yield self.env_info
        
        self.hw_title = Static("[HARDWARE]", classes="subtitle")
        yield self.hw_title
        self.hw_info = Static("SCANNING...")
        yield self.hw_info
        
        self.model_title = Static("[MODELS]", classes="subtitle")
        yield self.model_title
        self.model_info = Static("AWAITING DATA...")
        yield self.model_info

# Dummy Memory class for UI demo purposes
class DummyMemory:
    def add_user_fact(self, fact): pass
    def recall_user_facts(self, q, n_results): return []

class JamApp(App):
    CSS = APP_CSS
    BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=True)]

    def __init__(self, language="es", **kwargs):
        super().__init__(**kwargs)
        self.lang = language
        self.memory = DummyMemory() # Aquí se inicializaría JamMemory real
        
        self.t = {
            "es": {
                "sys_init": "[SISTEMA] INICIALIZANDO JAM CORE...",
                "sys_online": "SISTEMA: EN LÍNEA",
                "env_title": "[ENTORNO / COMMS]",
                "hw_title": "[HARDWARE]",
                "model_title": "[MODELOS]",
                "loc": "UBIC",
                "net_conn": "RED: CONECTADO",
                "scanning": "ESCANEANDO...",
                "await_data": "ESPERANDO DATOS...",
                "mem_online": "[SISTEMA] BASE DE DATOS VECTORIAL EN LÍNEA.",
                "welcome": "[JAM] Bienvenido de vuelta. Link neuronal establecido.",
                "encrypt": "[JAM] (Todo lo que me digas será encriptado y vectorizado en mi memoria local).",
                "placeholder": "> ESPERANDO ENTRADA...",
                "saving": "[JAM] (Guardando en memoria vectorizada...)",
                "gen": "[GEN] (Generando respuesta basada en el prompt enriquecido...)",
                "new_fact": "Nuevo dato encriptado y guardado:",
                "prompt_transferred": "Prompt enriquecido transferido al modelo GEN.",
                # Onboarding
                "first_time_msg": "DETECTANDO USUARIO NUEVO. INICIANDO PROTOCOLO DE ONBOARDING.",
                "q1_name": "¿Cómo te llamas o cómo prefieres que te llame?",
                "q2_prof": "Excelente. ¿Cuál es tu profesión o interés principal? (Para adaptar mis respuestas)",
                "q3_style": "Entendido. ¿Prefieres que mis respuestas sean explicaciones largas y detalladas, o cortas y directas al grano?",
                "onboard_done": "Perfil encriptado y guardado en RAG. Integración completada. ¿En qué te ayudo hoy?"
            },
            "en": {
                "sys_init": "[SYSTEM] INITIALIZING JAM CORE...",
                "sys_online": "SYSTEM: ONLINE",
                "env_title": "[ENV / COMMS]",
                "hw_title": "[HARDWARE]",
                "model_title": "[MODELS]",
                "loc": "LOC",
                "net_conn": "NET: CONNECTED",
                "scanning": "SCANNING...",
                "await_data": "AWAITING DATA...",
                "mem_online": "[SYSTEM] VECTOR DATABASE ONLINE.",
                "welcome": "[JAM] Welcome back. Neural link established.",
                "encrypt": "[JAM] (Everything you say will be encrypted and vectorized in my local memory).",
                "placeholder": "> AWAITING INPUT...",
                "saving": "[JAM] (Saving to vectorized memory...)",
                "gen": "[GEN] (Generating response based on enriched prompt...)",
                "new_fact": "New fact encrypted and saved:",
                "prompt_transferred": "Enriched prompt transferred to GEN model.",
                # Onboarding
                "first_time_msg": "NEW USER DETECTED. INITIATING ONBOARDING PROTOCOL.",
                "q1_name": "What is your name, or how should I call you?",
                "q2_prof": "Excellent. What is your profession or main interest? (To adapt my answers)",
                "q3_style": "Understood. Do you prefer long detailed explanations, or short and straight to the point?",
                "onboard_done": "Profile encrypted and saved to RAG. Integration complete. How can I help you today?"
            }
        }
        
    def get_text(self, key):
        return self.t[self.lang][key]

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Sidebar(id="sidebar")
            with Vertical(id="chat-area"):
                yield Log(id="chat-log")
                with Container(id="input-container"):
                    yield Input(placeholder=self.get_text("placeholder"), id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "JAM"
        sidebar = self.query_one(Sidebar)
        sidebar.sys_status.update(self.get_text("sys_online"))
        sidebar.env_title.update(self.get_text("env_title"))
        sidebar.hw_title.update(self.get_text("hw_title"))
        sidebar.model_title.update(self.get_text("model_title"))
        sidebar.hw_info.update(self.get_text("scanning"))
        sidebar.model_info.update(self.get_text("await_data"))
        self.run_worker(self.init_system())

    async def init_system(self) -> None:
        log = self.query_one("#chat-log", Log)
        sidebar_env = self.query_one(Sidebar).env_info
        sidebar_hw = self.query_one(Sidebar).hw_info
        sidebar_model = self.query_one(Sidebar).model_info
        
        log.write_line(self.get_text("sys_init"))
        
        env_data = get_location_and_weather()
        env_text = f"{self.get_text('loc')}: {env_data['city']}\\nTMP: {env_data['temp']} C\\n{self.get_text('net_conn')}"
        sidebar_env.update(env_text)
        
        detector = HardwareDetector()
        report = detector.get_full_report()
        recommender = ModelRecommender(report)
        recs = recommender.get_recommendations()
        
        mng_param = recs['manager'].get('name', 'LIGHT').split('-')[1] if '-' in recs['manager'].get('name', '') else 'LIGHT'
        gen_param = recs['generator'].get('name', 'HEAVY').split(' ')[0]
        
        hw_text = f"OS: {report['os']}\\nRAM: {report['ram']['total_gb']}GB\\nVRAM: {recs['effective_vram_gb']}GB"
        sidebar_hw.update(hw_text)
        mod_text = f"MNG: {mng_param}\\nGEN: {gen_param}"
        sidebar_model.update(mod_text)
        
        log.write_line(self.get_text("mem_online"))
        
        # ONBOARDING LOGIC
        os.makedirs("./jam_data", exist_ok=True)
        self.is_first_time = not os.path.exists("./jam_data/onboarding_done")
        self.onboarding_step = 0
        
        if self.is_first_time:
            log.write_line(f"\\n[SYSTEM] {self.get_text('first_time_msg')}")
            log.write_line(f"[JAM] {self.get_text('q1_name')}")
            self.onboarding_step = 1
        else:
            log.write_line(f"\\n{self.get_text('welcome')}")
            
        self.query_one("#chat-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value
        log = self.query_one("#chat-log", Log)
        input_widget = self.query_one("#chat-input", Input)
        
        if user_input.strip() == "":
            return
            
        log.write_line(f"\\n[USER] {user_input}")
        input_widget.value = ""
        
        # Handle Onboarding Flow
        if getattr(self, "is_first_time", False):
            if self.onboarding_step == 1:
                self.memory.add_user_fact(f"El usuario se llama: {user_input}")
                log.write_line(f"[JAM] {self.get_text('q2_prof')}")
                self.onboarding_step = 2
            elif self.onboarding_step == 2:
                self.memory.add_user_fact(f"La profesión/interés principal del usuario es: {user_input}")
                log.write_line(f"[JAM] {self.get_text('q3_style')}")
                self.onboarding_step = 3
            elif self.onboarding_step == 3:
                self.memory.add_user_fact(f"Estilo de respuesta preferido del usuario: {user_input}")
                log.write_line(f"[JAM] {self.get_text('onboard_done')}")
                with open("./jam_data/onboarding_done", "w") as f:
                    f.write("done")
                self.is_first_time = False
                self.onboarding_step = 0
            return
        
        # Standard Chat Flow
        mock_mng = {"is_new_fact": False, "requires_search": False}
        from core.orchestrator import JamOrchestrator
        from core.environment import get_location_and_weather
        
        orchestrator = JamOrchestrator(self.memory, get_location_and_weather())
        pipeline_result = orchestrator.process_pipeline(user_input, mock_mng)
        
        if mock_mng["is_new_fact"]:
            log.write_line(f"[MNG] {self.get_text('new_fact')} {user_input}")
        log.write_line(f"[MNG] {self.get_text('prompt_transferred')}")
        log.write_line(self.get_text("gen"))
