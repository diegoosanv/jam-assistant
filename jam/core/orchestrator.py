import json

class JamOrchestrator:
    def __init__(self, memory_db, env_data):
        self.memory = memory_db
        self.env_data = env_data
        
    def analyze_intent_prompt(self, user_text):
        """
        Genera el prompt que leerá el modelo ligero (MNG) para clasificar la intención.
        Obliga al modelo pequeño a devolver un JSON estructurado.
        """
        prompt = f"""[SYSTEM]
You are JAM-MNG, the fast orchestrator of the JAM system.
Your job is to analyze the user's input and extract structured data.
Do NOT answer the user's question. Output ONLY a valid JSON object.

User Input: "{user_text}"

Determine if the user is providing a new fact about themselves, or asking something that requires internet access.

Format required:
{{
    "is_new_fact": true/false,
    "fact_to_save": "The extracted fact in 3rd person or null",
    "requires_search": true/false,
    "search_query": "Optimized search query or null"
}}
"""
        return prompt

    def build_generator_prompt(self, user_text, extracted_facts, web_context=""):
        """
        Construye el prompt final inyectando la memoria para el modelo pesado (GEN).
        """
        env_context = f"Location: {self.env_data['city']} | Temp: {self.env_data['temp']} C"
        
        system_prompt = f"""[SYSTEM]
You are JAM (Just Another Mind), an advanced local AI assistant.
You are running on the user's local hardware. Keep answers concise, technical, and accurate.

CRITICAL RULE: Always reply in the same language the user uses in their prompt. 
If the user writes in Spanish, you MUST reply in Spanish. If English, reply in English.

[ENVIRONMENT DATA]
{env_context}

[USER MEMORY / CONTEXT]
{extracted_facts}
"""
        if web_context:
            system_prompt += f"\n[WEB CONTEXT]\n{web_context}\n"
            
        final_prompt = f"{system_prompt}\n[USER]\n{user_text}\n[JAM]\n"
        return final_prompt
        
    def process_pipeline(self, user_text, mock_mng_response=None):
        """
        Ejecuta el pipeline completo de orquestación.
        (mock_mng_response se usa para probar la lógica antes de conectar llama.cpp).
        """
        # 1. El modelo MNG analiza el texto (simulado por ahora)
        if not mock_mng_response:
            # En producción, aquí mandamos 'analyze_intent_prompt()' al modelo MNG
            mock_mng_response = {
                "is_new_fact": False,
                "fact_to_save": None,
                "requires_search": False,
                "search_query": None
            }
            
        logs = []
            
        # 2. Guardar en memoria vectorial si hay nuevos datos personales
        if mock_mng_response.get("is_new_fact") and mock_mng_response.get("fact_to_save"):
            self.memory.add_user_fact(mock_mng_response["fact_to_save"])
            logs.append(f"[MNG] Nuevo dato encriptado y guardado: {mock_mng_response['fact_to_save']}")
            
        # 3. Recuperar contexto de la memoria vectorial basado en el input actual
        recalled_context = self.memory.recall_user_facts(user_text, n_results=2)
        facts_str = "\n".join(recalled_context) if recalled_context else "No prior context relevant."
        if recalled_context:
            logs.append(f"[MNG] Memoria recuperada ({len(recalled_context)} registros).")
            
        # 4. Búsqueda web si es necesario (se conectará a una API como DuckDuckGo)
        web_str = ""
        if mock_mng_response.get("requires_search"):
            query = mock_mng_response["search_query"]
            logs.append(f"[MNG] Ejecutando búsqueda web silenciosa: '{query}'...")
            web_str = "Simulated Web Results: ..."
            
        # 5. Construir el prompt enriquecido final para el modelo pesado (GEN)
        gen_prompt = self.build_generator_prompt(user_text, facts_str, web_str)
        logs.append("[MNG] Prompt enriquecido transferido al modelo GEN.")
        
        return {
            "gen_prompt": gen_prompt,
            "logs": logs
        }
