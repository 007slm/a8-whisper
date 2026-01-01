import os
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    print("Warning: llama_cpp not available. Local LLM will be disabled.")
    Llama = None
    LLAMA_CPP_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    print("Warning: openai not available. Cloud LLM will be disabled.")
    openai = None
    OPENAI_AVAILABLE = False

SYSTEM_PROMPT_TEMPLATE = """You are a helpful voice transcription correction assistant.
Your task:
1. Correct homophones, typos, and punctuation errors in the transcribed text.
2. Keep the original meaning; do not add or remove information.
3. Strictly follow the terminology in the [User Dictionary] below if applicable.

[User Dictionary]
{user_dict}

Strictly output ONLY the corrected text. Do not output any explanation.
"""

class LLMEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMEngine, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.mode = "LOCAL" # LOCAL or CLOUD
            cls._instance.api_client = None
        return cls._instance

    def initialize_local(self, model_path, n_gpu_layers=-1, n_ctx=2048):
        """Initialize Local GGUF Model"""
        if not LLAMA_CPP_AVAILABLE:
            print("Local LLM initialization skipped: llama_cpp not available")
            return
            
        print(f"Loading LLM (Local): {model_path}")
        try:
            self.model = Llama(
                model_path=model_path,
                n_gpu_layers=n_gpu_layers, # -1 = all
                n_ctx=n_ctx,
                verbose=False
            )
            self.mode = "LOCAL"
            print("Local LLM Loaded.")
        except Exception as e:
            print(f"Failed to load Local LLM: {e}")
            raise e

    def initialize_cloud(self, api_key, base_url="https://api.openai.com/v1", model_name="gpt-3.5-turbo"):
        """Initialize Cloud API"""
        if not OPENAI_AVAILABLE:
            print("Cloud LLM initialization skipped: openai not available")
            return
            
        print("Initializing Cloud LLM...")
        self.api_client = openai.Client(api_key=api_key, base_url=base_url)
        self.cloud_model_name = model_name
        self.mode = "CLOUD"
        print("Cloud LLM Initialized.")

    def correct_text(self, text, user_dict_list=[], system_prompt_template=None):
        """
        Correct the transcribed text.
        text: Input string.
        user_dict_list: List of strings (terminology).
        system_prompt_template: Optional custom system prompt with {user_dict} placeholder.
        """
        user_dict_str = "\n".join(user_dict_list)
        template = system_prompt_template if system_prompt_template else SYSTEM_PROMPT_TEMPLATE
        system_prompt = template.replace("{user_dict}", user_dict_str)
        
        user_message = f"原始文本: {text}"

        if self.mode == "LOCAL" and self.model:
            output = self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1024,
                temperature=0.1
            )
            return output['choices'][0]['message']['content'].strip()
            
        elif self.mode == "CLOUD" and self.api_client:
            response = self.api_client.chat.completions.create(
                model=self.cloud_model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
            
        else:
            return text # Fallback: return original
