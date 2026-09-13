import os
import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Input, Static, Log, ProgressBar
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
#progress-bar { margin-top: 1; margin-bottom: 1; display: none; }
Input { border: none; background: #000000; color: #ffffff; width: 1fr; }
Input:focus { border: none; }
.system-text { color: #00ffcc; }
.title { color: #ffffff; text-style: bold; margin-bottom: 1; }
.subtitle { color: #666666; margin-top: 1; }
"""

class DummyMemory:
    def add_user_fact(self, fact): pass
    def recall_user_facts(self, q, n_results): return []

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

class JamApp(App):
    CSS = APP_CSS
    BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=True)]

    def __init__(self, language="es", **kwargs):
        super().__init__(**kwargs)
        self.lang = language
        self.memory = DummyMemory()
        self.engine = None
        self.engine_ready = False
        self.env_data = {"city": "OFFLINE", "temp": "--"}

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Sidebar(id="sidebar")
            with Vertical(id="chat-area"):
                yield Log(id="chat-log")
                yield ProgressBar(id="progress-bar", total=100, show_eta=False)
                with Container(id="input-container"):
                    yield Input(placeholder="> ESPERANDO ENTRADA...", id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "JAM"
        self.run_worker(self.init_system())

    async def init_system(self) -> None:
        log = self.query_one("#chat-log", Log)
        sidebar_env = self.query_one(Sidebar).env_info
        sidebar_hw = self.query_one(Sidebar).hw_info
        sidebar_model = self.query_one(Sidebar).model_info
        
        log.write_line("[SISTEMA] INICIALIZANDO JAM CORE...")
        
        # Env Data
        self.env_data = get_location_and_weather()
        sidebar_env.update(f"UBIC: {self.env_data['city']}\\nTMP: {self.env_data['temp']} C\\nRED: CONECTADA")
        
        # Hardware
        detector = HardwareDetector()
        report = detector.get_full_report()
        recommender = ModelRecommender(report)
        recs = recommender.get_recommendations()
        
        hw_text = f"OS: {report['os']}\\nRAM: {report['ram']['total_gb']}GB\\nVRAM: {recs['effective_vram_gb']}GB"
        sidebar_hw.update(hw_text)
        
        mng_param = recs['manager'].get('name', 'LIGHT').split('-')[1] if '-' in recs['manager'].get('name', '') else 'LIGHT'
        gen_param = recs['generator'].get('name', 'HEAVY').split(' ')[0]
        sidebar_model.update(f"MNG: {mng_param}\\nGEN: {gen_param}")
        
        # Print detected hardware to terminal
        log.write_line(f"\\n[SISTEMA] HARDWARE ENCONTRADO:")
        log.write_line(f" -> OS: {report['os']}")
        log.write_line(f" -> CPU: {report['cpu']['architecture']} ({report['cpu']['physical_cores']} cores)")
        log.write_line(f" -> RAM Total: {report['ram']['total_gb']} GB")
        log.write_line(f" -> GPU: {report['gpu']['type']} (VRAM: {report['gpu']['vram_gb']} GB)")
        log.write_line(f" -> Motor Asignado: {recs['generator']['name']}")
        
        # Start background load
        self.run_worker(self.load_ai_engine(recs))

    async def load_ai_engine(self, recs):
        log = self.query_one("#chat-log", Log)
        pb = self.query_one("#progress-bar", ProgressBar)
        
        log.write_line(f"\\n[SISTEMA] INICIANDO DESCARGA Y CARGA DE INTELIGENCIA ARTIFICIAL...")
        log.write_line(f"[SISTEMA] Se requiere descargar el modelo base desde los servidores.")
        log.write_line(f"[SISTEMA] Por favor espera, esto puede tomar varios minutos según tu internet...")
        
        # Show indeterminate progress bar
        pb.display = True
        pb.advance(50) # Just to show some bar
        
        loop = asyncio.get_event_loop()
        
        def _load():
            try:
                # Load Inference
                from core.inference import JamInferenceEngine
                self.engine = JamInferenceEngine(recs['generator'])
                
                # Callback to print to log thread-safely
                def _log_cb(msg):
                    self.call_from_thread(log.write_line, msg)
                    
                success = self.engine.load_model(log_callback=_log_cb)
                
                # Load Memory RAG
                from memory.vector_db import JamMemory
                self.memory = JamMemory()
                self.call_from_thread(log.write_line, "[SISTEMA] BASE DE DATOS VECTORIAL (RAG) COMPILADA.")
                
                return success
            except Exception as e:
                self.call_from_thread(log.write_line, f"[ERROR FATAL] Fallo al cargar dependencias pesadas: {e}")
                return False

        success = await loop.run_in_executor(None, _load)
        
        pb.display = False
        
        # Onboarding
        os.makedirs("./jam_data", exist_ok=True)
        self.is_first_time = not os.path.exists("./jam_data/onboarding_done")
        self.onboarding_step = 0
        
        if success:
            self.engine_ready = True
            if self.is_first_time:
                log.write_line(f"\\n[SISTEMA] USUARIO NUEVO DETECTADO. INICIANDO PROTOCOLO.")
                log.write_line(f"[JAM] ¿Cómo te llamas o cómo prefieres que te llame?")
                self.onboarding_step = 1
            else:
                log.write_line("\\n[JAM] Bienvenido de vuelta. Link neuronal establecido. ¿En qué te ayudo?")
        else:
            log.write_line("\\n[SISTEMA] El motor de IA falló. El sistema correrá en Modo Simulado (Demo).")
            self.engine_ready = False
            
        self.query_one("#chat-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value
        log = self.query_one("#chat-log", Log)
        input_widget = self.query_one("#chat-input", Input)
        
        if user_input.strip() == "":
            return
            
        log.write_line(f"\\n[USER] {user_input}")
        input_widget.value = ""
        
        # Onboarding Capture
        if getattr(self, "is_first_time", False) and self.engine_ready:
            if self.onboarding_step == 1:
                self.memory.add_user_fact(f"El usuario se llama: {user_input}")
                log.write_line(f"[JAM] Excelente. ¿Cuál es tu profesión o interés principal?")
                self.onboarding_step = 2
            elif self.onboarding_step == 2:
                self.memory.add_user_fact(f"La profesión/interés principal del usuario es: {user_input}")
                log.write_line(f"[JAM] Entendido. ¿Prefieres que mis respuestas sean largas o directas al grano?")
                self.onboarding_step = 3
            elif self.onboarding_step == 3:
                self.memory.add_user_fact(f"Estilo de respuesta preferido del usuario: {user_input}")
                log.write_line(f"[JAM] Perfil encriptado en RAG. ¿En qué te ayudo hoy?")
                with open("./jam_data/onboarding_done", "w") as f:
                    f.write("done")
                self.is_first_time = False
                self.onboarding_step = 0
            return
            
        # Standard AI Generation (Async to not freeze UI)
        self.run_worker(self.generate_ai_response(user_input))
        
    async def generate_ai_response(self, user_input):
        log = self.query_one("#chat-log", Log)
        
        if not self.engine_ready:
            log.write_line("[JAM] (Modo Simulado): Simulando respuesta...")
            return
            
        log.write_line("[MNG] Orquestando memoria vectorial...")
        
        loop = asyncio.get_event_loop()
        
        def _process():
            from core.orchestrator import JamOrchestrator
            
            # Simple heuristic for MNG simulation to save resources
            mock_mng = {"is_new_fact": False, "requires_search": False}
            if "me llamo" in user_input.lower() or "soy " in user_input.lower():
                mock_mng["is_new_fact"] = True
                mock_mng["fact_to_save"] = user_input
                
            orchestrator = JamOrchestrator(self.memory, self.env_data)
            pipeline_result = orchestrator.process_pipeline(user_input, mock_mng)
            
            # Print intermediate steps safely
            for step_log in pipeline_result["logs"]:
                self.call_from_thread(log.write_line, step_log)
                
            self.call_from_thread(log.write_line, "[GEN] Generando respuesta neuronal profunda...")
            
            # Real Generation!
            response = self.engine.generate(pipeline_result["gen_prompt"], max_tokens=256)
            return response
            
        ai_response = await loop.run_in_executor(None, _process)
        
        log.write_line(f"\\n[JAM] {ai_response}")
        log.write_line("="*40)
