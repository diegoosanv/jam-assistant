import chromadb
import uuid

class JamMemory:
    def __init__(self, db_path="./jam_data/memory"):
        # chromadb.PersistentClient will save sqlite/parquet files locally
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Colecciones: Una para hechos sobre el usuario y otra para el historial del chat
        self.user_collection = self.client.get_or_create_collection(name="user_persona")
        self.chat_collection = self.client.get_or_create_collection(name="chat_history")
        
    def add_user_fact(self, fact_text):
        """Almacena información clave del usuario en la memoria a largo plazo."""
        fact_id = str(uuid.uuid4())
        self.user_collection.add(
            documents=[fact_text],
            ids=[fact_id]
        )
        return fact_id
        
    def add_chat_message(self, message):
        """Almacena el historial de conversación general."""
        msg_id = str(uuid.uuid4())
        self.chat_collection.add(
            documents=[message],
            ids=[msg_id]
        )
        return msg_id
        
    def recall_user_facts(self, query, n_results=3):
        """El modelo MNG busca información relevante del usuario antes de responder."""
        if self.user_collection.count() == 0:
            return []
            
        n_results = min(n_results, self.user_collection.count())
        results = self.user_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if results and 'documents' in results and len(results['documents']) > 0:
            return results['documents'][0]
        return []

    def recall_chat_history(self, query, n_results=5):
        if self.chat_collection.count() == 0:
            return []
            
        n_results = min(n_results, self.chat_collection.count())
        results = self.chat_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if results and 'documents' in results and len(results['documents']) > 0:
            return results['documents'][0]
        return []
