import os
from huggingface_hub import hf_hub_download

# Encapsulamos la importación en un try-except porque compilar llama-cpp-python 
# puede ser complejo dependiendo de la plataforma del usuario (CUDA vs Metal).
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False

class JamInferenceEngine:
    def __init__(self, model_recommendation, models_dir="./jam_data/models"):
        self.models_dir = models_dir
        self.model_info = model_recommendation
        self.llm = None
        os.makedirs(self.models_dir, exist_ok=True)
        
    def _get_hf_details(self, model_name):
        """
        Mapea el nombre genérico del recomendador a un repositorio y archivo exacto en HuggingFace Hub.
        """
        mapping = {
            "Qwen2.5-0.5B-Instruct-GGUF (Q4_K_M)": ("Qwen/Qwen2.5-0.5B-Instruct-GGUF", "qwen2.5-0.5b-instruct-q4_k_m.gguf"),
            "Qwen2.5-1.5B-Instruct-GGUF (Q4_K_M)": ("Qwen/Qwen2.5-1.5B-Instruct-GGUF", "qwen2.5-1.5b-instruct-q4_k_m.gguf"),
            "Llama-3.2-3B-Instruct-GGUF (Q4_K_M)": ("bartowski/Llama-3.2-3B-Instruct-GGUF", "Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
            "Qwen2.5-7B-Instruct-GGUF (Q4_K_M)": ("Qwen/Qwen2.5-7B-Instruct-GGUF", "qwen2.5-7b-instruct-q4_k_m.gguf"),
            "Qwen3 235B MoE IQ4_XS GGUF": ("Qwen/Qwen3-235B-MoE-GGUF", "qwen3-235b-moe-iq4_xs.gguf") # Dummy repo for massive tier
        }
        # Retorna el mapeo o un modelo ligero por defecto si no lo encuentra
        return mapping.get(model_name, ("Qwen/Qwen2.5-0.5B-Instruct-GGUF", "qwen2.5-0.5b-instruct-q4_k_m.gguf"))

    def load_model(self, log_callback=None):
        """
        Descarga (si es necesario) y carga el modelo GGUF en la memoria.
        """
        if not LLAMA_AVAILABLE:
            if log_callback: log_callback("[ERROR] llama-cpp-python no está instalado/compilado.")
            return False
            
        repo_id, filename = self._get_hf_details(self.model_info['name'])
        model_path = os.path.join(self.models_dir, filename)
        
        # 1. Descarga Inteligente
        if not os.path.exists(model_path):
            if log_callback: log_callback(f"[SYS] Descargando modelo: {filename} desde HuggingFace (~{self.model_info.get('memory_required', '1GB')})...")
            try:
                model_path = hf_hub_download(
                    repo_id=repo_id, 
                    filename=filename, 
                    local_dir=self.models_dir,
                    local_dir_use_symlinks=False
                )
                if log_callback: log_callback("[SYS] Descarga completada.")
            except Exception as e:
                if log_callback: log_callback(f"[ERROR] Falló la descarga: {str(e)}")
                return False

        if log_callback: log_callback(f"[SYS] Cargando {filename} en Motor de Inferencia...")
        
        # 2. Inicialización de Llama.cpp con Aceleración por Hardware
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048, # Ventana de Contexto (Expandible según hardware)
            n_gpu_layers=-1, # -1 intenta descargar TODAS las capas a la GPU (Metal o CUDA)
            flash_attn=True, # Activa Flash Attention (reduce consumo de memoria)
            verbose=False # Silencia los logs internos de C++ para no ensuciar la terminal
        )
        
        if log_callback: log_callback("[SYS] Modelo cargado y link neuronal establecido.")
        return True

    def generate(self, prompt, max_tokens=256, is_json=False):
        """
        Genera una respuesta. Soporta outputs estructurados JSON para el modelo Gestor (MNG).
        """
        if not self.llm:
            return '{"is_new_fact": false, "requires_search": false}' if is_json else "Error: Motor de inferencia offline."
            
        response = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.1 if is_json else 0.7, # Baja creatividad para el orquestador (JSON), media para el chat
            stop=["[USER]", "[JAM]", "[SYSTEM]"], # Tokens de parada
            echo=False
        )
        
        return response['choices'][0]['text'].strip()
