class ModelRecommender:
    def __init__(self, hardware_report):
        self.report = hardware_report
        self.gpu_info = self.report['gpu']
        self.gpu_vram = self.gpu_info['vram_gb']
        self.ram_total = self.report['ram']['total_gb']
        self.is_mac = self.gpu_info['type'] == 'Apple Silicon (Metal)'
        
        # Calcular memoria efectiva para LLMs
        if self.is_mac:
            # En Mac con Memoria Unificada, usualmente se puede asignar hasta ~75% de la RAM total a la GPU
            self.effective_vram = self.ram_total * 0.75
        elif isinstance(self.gpu_vram, (int, float)) and self.gpu_vram > 0:
            self.effective_vram = self.gpu_vram
        else:
            self.effective_vram = 0 # Fallback a CPU only

    def recommend_manager_model(self):
        """
        Modelo pequeño y rápido para gestionar la memoria (RAG) y orquestar.
        """
        if self.effective_vram > 4 or self.ram_total >= 8:
            return {
                "name": "Qwen2.5-1.5B-Instruct-GGUF (Q4_K_M)",
                "memory_required": "~1.2 GB",
                "role": "Orquestador RAG y Resumen Contextual"
            }
        else:
            return {
                "name": "Qwen2.5-0.5B-Instruct-GGUF (Q4_K_M)",
                "memory_required": "~0.5 GB",
                "role": "Orquestador Ligero (Bajos Recursos)"
            }

    def recommend_generator_model(self):
        """
        Modelo pesado para responder basándose en el hardware disponible.
        """
        # Nivel Ultra-Premium / Multimodal Massivo (como el que pediste)
        if self.effective_vram >= 80 or (self.is_mac and self.ram_total >= 128):
            return {
                "name": "Qwen3 235B MoE IQ4_XS GGUF",
                "memory_required": "~80 GB",
                "features": "YaRN 128K context, TurboQuant, Flash Attention 3, Paged KV Cache, Speculative Decoding, Tensor Parallelism",
                "role": "Generador Ultra-Premium (Massive Hardware)"
            }
        # Nivel Premium
        elif self.effective_vram >= 24 or (self.is_mac and self.ram_total >= 32):
            return {
                "name": "Qwen2.5-32B-Instruct-GGUF (Q4_K_M) / Llama-3.1-70B (IQ3)",
                "memory_required": "~20-22 GB",
                "features": "Flash Attention, Paged KV Cache",
                "role": "Generador Premium"
            }
        # Nivel Avanzado
        elif self.effective_vram >= 12 or (self.is_mac and self.ram_total >= 16):
            return {
                "name": "Llama-3.1-8B-Instruct-GGUF (Q6_K) / Mixtral-8x7B (Q3)",
                "memory_required": "~8-10 GB",
                "features": "Flash Attention",
                "role": "Generador Avanzado"
            }
        # Nivel Estándar
        elif self.effective_vram >= 6 or self.ram_total >= 16:
            return {
                "name": "Qwen2.5-7B-Instruct-GGUF (Q4_K_M)",
                "memory_required": "~4.5 GB",
                "role": "Generador Estándar"
            }
        # Nivel Básico (ej. Portátiles sin GPU)
        elif self.effective_vram > 0 or self.ram_total >= 8:
            return {
                "name": "Llama-3.2-3B-Instruct-GGUF (Q4_K_M)",
                "memory_required": "~2.5 GB",
                "role": "Generador Básico"
            }
        # Fallback para bajos recursos (como el entorno actual)
        else:
            return {
                "name": "Qwen2.5-1.5B-Instruct-GGUF (Q4_K_M)",
                "memory_required": "~1.2 GB",
                "role": "Generador CPU-Only (Bajos Recursos)"
            }

    def get_recommendations(self):
        return {
            "manager": self.recommend_manager_model(),
            "generator": self.recommend_generator_model(),
            "inference_engine": "llama.cpp con Flash Attention (Soporte Multiplataforma)",
            "effective_vram_gb": round(self.effective_vram, 2)
        }
