import asyncio
import websockets
import json
import os
import threading
from src.core.asr import asr_engine
try:
    from src.core.llm import LLMEngine
except ImportError:
    LLMEngine = None  # Handle partial initialization if needed

# Global state for server
CLIENTS = set()
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".a8qingyu_config.json")

# Default Config
DEFAULT_CONFIG = {
    "asr_model": "large-v3",
    "llm_enabled": True,
    "llm_model": "Qwen2.5-Coder-7B-Instruct-GGUF",
    "use_cloud": False,
    "user_dict": ["Python", "PySide6", "LLM", "A8轻语"],
    "hotkey": "ctrl+left_win",
    "sound_enabled": False,
    "overlay_enabled": True,
    "asr_prompt": "请准确识别以下语音内容，注意准确识别专业术语和中英文混合表达。",
    "llm_prompt": """你是一个语音转录校正助手。
你的任务：
1. 修正转录文本中的同音字错误、错别字和标点符号问题。
2. 保持原意，不添加或删除信息。
3. 严格遵循 [用户词典] 中的专业术语。

[用户词典]
{user_dict}

仅输出校正后的文本，不要输出任何解释。""",
    "models_status": {}
}

current_config = DEFAULT_CONFIG.copy()

def load_config():
    global current_config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                current_config.update(saved)
                print(f"Loaded config from {CONFIG_FILE}")
        except Exception as e:
            print(f"Failed to load config: {e}")
    check_models_status()

def save_config():
    try:
        # Don't save models_status
        save_data = {k: v for k, v in current_config.items() if k != 'models_status'}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        print(f"Saved config to {CONFIG_FILE}")
    except Exception as e:
        print(f"Failed to save config: {e}")

def check_models_status():
    base_dir = os.path.join(os.getcwd(), "models")
    for size in ["large-v3", "medium", "small"]:
        path = os.path.join(base_dir, f"faster-whisper-{size}")
        current_config["models_status"][size] = (
            os.path.exists(os.path.join(path, "config.json")) and 
            os.path.exists(os.path.join(path, "model.bin"))
        )

def get_vram_gb():
    try:
        import torch
        if torch.cuda.is_available():
            mem_bytes = torch.cuda.get_device_properties(0).total_memory
            return mem_bytes / (1024**3)
    except Exception:
        pass
    return 0.0

async def broadcast(message):
    if not CLIENTS:
        return
    if isinstance(message, dict):
        message = json.dumps(message)
    # Filter out closed clients
    to_remove = set()
    for client in CLIENTS:
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            to_remove.add(client)
    for client in to_remove:
        CLIENTS.remove(client)

async def handler(websocket):
    CLIENTS.add(websocket)
    print("New WebSocket client connected")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get("action")
                payload = data.get("payload", {})
                
                if action == "getConfig":
                    check_models_status()
                    await websocket.send(json.dumps({"type": "config", "data": current_config}))
                    # Also send VRAM
                    await websocket.send(json.dumps({"type": "vram", "data": get_vram_gb()}))
                
                elif action == "saveConfig":
                    new_config = payload
                    if "models_status" in new_config:
                        del new_config["models_status"]
                    current_config.update(new_config)
                    save_config()
                    await broadcast({"type": "config", "data": current_config})
                    
                elif action == "downloadModel":
                    # Start download in thread
                    size = payload.get("model_size")
                    threading.Thread(target=download_worker, args=(size,), daemon=True).start()

                elif action == "downloadLLM":
                     threading.Thread(target=download_llm_worker, daemon=True).start()
                     
                elif action == "checkLLM":
                     path = os.path.join(os.getcwd(), "models", "qwen2.5-coder-7b-instruct-q4_k_m.gguf")
                     exists = os.path.exists(path)
                     await websocket.send(json.dumps({"type": "llm_status", "exists": exists}))

            except json.JSONDecodeError:
                print(f"Invalid JSON: {message}")
            except Exception as e:
                print(f"Error handling message: {e}")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CLIENTS.remove(websocket)
        print("Client disconnected")

def start_server(host="127.0.0.1", port=9000):
    load_config()
    print(f"Starting WebSocket server on ws://{host}:{port}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(handler, host, port)
    loop.run_until_complete(start_server)
    loop.run_forever()

# --- Workers ---
# We need an async wrapper to send updates back to the loop/websocket
# But since websockets is async, and we are in a thread, we might need a thread-safe way to broadcast.
# Actually, the simplest way for this mixed sync/async app is to run the loop in a separate thread 
# OR just have the workers update a queue that the main loop checks. 
# However, for simplicity, we'll just run a fire-and-forget sender if we can access the loop.
# But 'broadcast' is async.
# Solution: Use run_coroutine_threadsafe.

def send_update_sync(message):
    """Helper to broadcast from a thread"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast(message), loop)
        else:
            # If we are in a thread where there is no loop, we need to get the loop from the server thread.
            # For now, let's assume this is called from threads spawn by handlers which have access to global loop?
            # Actually, asyncio.get_event_loop() might fail in a new thread.
            # We'll need a reference to the loop. 
            pass
    except Exception as e:
        print(f"Send update failed: {e}")

# We need a global reference to the loop to send messages from threads
SERVER_LOOP = None

def start_server_wrapper():
    global SERVER_LOOP
    load_config()
    print("Starting WebSocket server...")
    
    async def serve():
        global SERVER_LOOP
        SERVER_LOOP = asyncio.get_running_loop()
        async with websockets.serve(handler, "127.0.0.1", 9000):
            print("WebSocket Server Listening on port 9000")
            await asyncio.Future()  # run forever

    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass


# Robust Messaging
def emit_status(type_str, data):
    """
    Thread-safe emit to all clients.
    Attempts to schedule the broadcast on the running event loop.
    """
    global SERVER_LOOP
    if SERVER_LOOP and SERVER_LOOP.is_running():
        try:
             asyncio.run_coroutine_threadsafe(broadcast({"type": type_str, "data": data}), SERVER_LOOP)
        except Exception as e:
            print(f"Emit failed: {e}")
    else:
        print(f"Warning: Event loop not ready. Dropped message: {type_str}")

# Re-implement download workers using emit_status
def download_worker(model_size):
    from huggingface_hub import snapshot_download
    
    repo_id = f"Systran/faster-whisper-{model_size}"
    save_dir = os.path.join(os.getcwd(), "models", f"faster-whisper-{model_size}")
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    
    emit_status("model_progress", {"model": model_size, "progress": 0.01})
    
    try:
        snapshot_download(repo_id=repo_id, local_dir=save_dir, max_workers=4, resume_download=True)
        check_models_status()
        
        # Init engine
        try:
             asr_engine.initialize(model_size=model_size)
        except Exception as e:
             print(f"Auto-init warning: {e}")
             
        emit_status("config", current_config)
        emit_status("model_progress", {"model": model_size, "progress": 1.0})
    except Exception as e:
        print(f"Download failed: {e}")
        emit_status("model_progress", {"model": model_size, "progress": -1.0})

def download_llm_worker():
    from huggingface_hub import hf_hub_download
    repo_id = "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
    filename = "qwen2.5-coder-7b-instruct-q4_k_m.gguf"
    save_dir = os.path.join(os.getcwd(), "models")
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    
    emit_status("llm_progress", 0.01)
    try:
        hf_hub_download(repo_id=repo_id, filename=filename, local_dir=save_dir, resume_download=True)
        emit_status("llm_progress", 1.0)
    except Exception as e:
        emit_status("llm_progress", -1.0)

if __name__ == "__main__":
    start_server_wrapper()
