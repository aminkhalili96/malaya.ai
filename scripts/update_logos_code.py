import re
import os

# New MODEL_INFO with local paths
NEW_MODEL_INFO = """MODEL_INFO = {
    "qwen": {"company": "Alibaba Cloud", "logo": "/static/logos/qwen.png"},
    "qwen2.5": {"company": "Alibaba Cloud", "logo": "/static/logos/qwen.png"},
    "qwen3": {"company": "Alibaba Cloud", "logo": "/static/logos/qwen.png"},
    "gemma": {"company": "Google DeepMind", "logo": "/static/logos/google.png"},
    "gemma2": {"company": "Google DeepMind", "logo": "/static/logos/google.png"},
    "gemma3": {"company": "Google DeepMind", "logo": "/static/logos/google.png"},
    "llama": {"company": "Meta", "logo": "/static/logos/meta.png"},
    "llama3": {"company": "Meta", "logo": "/static/logos/meta.png"},
    "llama3.1": {"company": "Meta", "logo": "/static/logos/meta.png"},
    "llama3.2": {"company": "Meta", "logo": "/static/logos/meta.png"},
    "deepseek": {"company": "DeepSeek", "logo": "/static/logos/deepseek.png"},
    "deepseek-coder": {"company": "DeepSeek", "logo": "/static/logos/deepseek.png"},
    "deepseek-coder-v2": {"company": "DeepSeek", "logo": "/static/logos/deepseek.png"},
    "mesolitica": {"company": "Mesolitica", "logo": "/static/logos/mesolitica.png"},
    "gpt-oss": {"company": "Open Source", "logo": "/static/logos/opensource.png"},
    "openai": {"company": "OpenAI", "logo": "/static/logos/openai.png"},
    "gpt": {"company": "OpenAI", "logo": "/static/logos/openai.png"},
    "gpt-4": {"company": "OpenAI", "logo": "/static/logos/openai.png"},
    "gpt-4o": {"company": "OpenAI", "logo": "/static/logos/openai.png"},
    "mistral": {"company": "Mistral AI", "logo": "/static/logos/opensource.png"} 
}"""

def update_server():
    server_path = "benchmark-tracker/server.py"
    
    if not os.path.exists(server_path):
        print(f"Error: {server_path} not found")
        return

    with open(server_path, "r") as f:
        content = f.read()

    # Regex to find MODEL_INFO block
    # Matches MODEL_INFO = { ... } potentially taking up multiple lines
    pattern = r"MODEL_INFO = \{.*?\}"
    
    # Check if we can find it
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, NEW_MODEL_INFO, content, flags=re.DOTALL)
        with open(server_path, "w") as f:
            f.write(new_content)
        print("Successfully updated MODEL_INFO in server.py")
    else:
        print("Could not find MODEL_INFO block in server.py")

if __name__ == "__main__":
    update_server()
