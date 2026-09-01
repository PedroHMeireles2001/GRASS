import os
import threading
from google import genai  # Nova SDK
import time
from typing import List, Dict

class Chat:
    def __init__(self, system_prompt: str, initial_message: str, api_key: str, game):
        self.game = game
        
        # --- API Key Resolution Logic ---
        gemini_env = os.getenv("GEMINI_API_KEY")
        google_env = os.getenv("GOOGLE_API_KEY")

        if gemini_env:
            resolved_key = gemini_env
            print("[INFO] Using GEMINI_API_KEY from environment variables.")
        elif google_env:
            resolved_key = google_env
            print("[INFO] GEMINI_API_KEY not found. Falling back to GOOGLE_API_KEY.")
        else:
            resolved_key = api_key
            print("[INFO] No API keys found in environment. Using fallback constructor key.")

        # 1. Configuração do Cliente with prioritized key
        self.client = genai.Client(api_key=resolved_key)
        self.model_name = "gemini-3.1-flash-lite-preview"
        self.system_prompt = system_prompt
        
        # 2. Atributos de estado que você já usava
        self.history = []
        self.token_queue = [] # Mantido para compatibilidade se necessário
        self.is_generating = False
        
        # 3. Tratamento da mensagem inicial
        if initial_message:
            # Na nova SDK, apenas adicionamos ao histórico manual
            self.history.append({"role": "user", "parts": [{"text": initial_message}]})
            # Alimenta a fila de tokens se o seu TypewriterManager ainda ler daqui
            for char in initial_message:
                self.token_queue.append(char)

    def send_message(self, text: str, callback=None):
        """Envia a mensagem em uma thread para não travar o Pygame"""
        if self.is_generating: return
        self.is_generating = True
        thread = threading.Thread(target=self._generate_response, args=(text, callback))
        thread.start()

    def _generate_response(self, text: str, callback=None):
        try:
            # 4. Chamada da API usando a nova sintaxe
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=self.history + [{"role": "user", "parts": [{"text": text}]}],
                config={'system_instruction': self.system_prompt}
            )
            
            full_text = response.text
            
            # 5. Atualiza o histórico manualmente
            self.history.append({"role": "user", "parts": [{"text": text}]})
            self.history.append({"role": "model", "parts": [{"text": full_text}]})
            
            # Callback para a ChatScene (onde o TypewriterManager reside)
            if callback:
                callback(full_text)
                
            print(f"[DEBUG] API Gemini: {full_text[:50]}...")
            
        except Exception as e:
            error_msg = f"[Erro na API: {str(e)}]"
            print(f"[ERROR] {error_msg}")
            if callback: callback(error_msg)
        finally:
            self.is_generating = False

    # --- FUNÇÕES QUE VOCÊ TINHA E NÃO PODEM SER PERDIDAS ---

    def get_history_data(self) -> List[Dict]:
        """Extrai o histórico para salvar em arquivo (JSON)"""
        return self.history

    def load_history_data(self, data: List[Dict]):
        """Restaura o histórico salvou"""
        self.history = data