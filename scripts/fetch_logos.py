import urllib.request
import base64
import io
import re

# Direct official logo sources (GitHub Avatars are usually high quality)
LOGOS = {
    "qwen2.5": "https://github.com/QwenLM.png",
    "qwen3": "https://github.com/QwenLM.png",
    "qwen3-vl": "https://github.com/QwenLM.png",
    
    "gemma": "https://github.com/google.png",
    "gemma3": "https://github.com/google.png",
    
    "llama": "https://github.com/meta-llama.png",
    "llama3": "https://github.com/meta-llama.png",
    "llama3.1": "https://github.com/meta-llama.png",
    "llama3.2": "https://github.com/meta-llama.png",
    
    "deepseek": "https://github.com/deepseek-ai.png",
    "deepseek-coder": "https://github.com/deepseek-ai.png",
    "deepseek-coder-v2": "https://github.com/deepseek-ai.png",
    
    "mesolitica": "https://github.com/mesolitica.png",
    
    "llava": "https://github.com/LLaVA-VL.png",
    
    "gpt-oss": "https://github.com/OpenSourceOrg.png",
    
    "openai": "https://github.com/openai.png",
    "gpt-4o": "https://github.com/openai.png",
    "gpt-4": "https://github.com/openai.png",
    "gpt-3.5": "https://github.com/openai.png"
}

def fetch_and_encode(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = response.read()
            # Basic check if it's an image
            if not data: return ""
            b64 = base64.b64encode(data).decode('utf-8')
            # GitHub avatars are PNG usually.
            return f"data:image/png;base64,{b64}"
    except Exception as e:
        print(f"Failed {url}: {e}")
        return ""

def generate_model_info():
    model_info = {}
    
    # Map families to companies
    companies = {
        "qwen": "Alibaba",
        "gemma": "Google",
        "llama": "Meta",
        "deepseek": "DeepSeek",
        "mesolitica": "Mesolitica",
        "llava": "LLaVA Team", 
        "gpt-oss": "Open Source",
        "openai": "OpenAI",
        "gpt": "OpenAI"
    }

    # Generate dictionary
    print("Fetching logos...")
    final_dict = {}
    
    # Cache processed URLs to avoid re-downloading
    cache = {}
    
    for key, url in LOGOS.items():
        if url not in cache:
            print(f"  Downloading {url}...")
            cache[url] = fetch_and_encode(url)
        
        family_key = key.split('-')[0] if '-' in key and key != "gpt-oss" else key
        if "qwen" in key: family_key = "qwen"
        if "llama" in key: family_key = "llama"
        if "gemma" in key: family_key = "gemma"
        if "deepseek" in key: family_key = "deepseek"
        
        company = companies.get(family_key, companies.get(key, "Unknown"))
        
        final_dict[key] = {
            "company": company,
            "logo": cache[url]
        }
        
    return final_dict

if __name__ == "__main__":
    new_info = generate_model_info()
    
    # Read server.py
    with open("benchmark-tracker/server.py", "r") as f:
        content = f.read()
    
    # Find MODEL_INFO = { ... } and replace it
    # We'll use a regex to match the block
    import json
    
    # Format the new dictionary as a python string
    # We want it pretty-printed to look like code
    dict_str = "MODEL_INFO = {\n"
    for k, v in new_info.items():
        # Truncate base64 for display if debugging, but here we need full
        logo_part = f'"{v["logo"]}"'
        dict_str += f'    "{k}": {{"company": "{v["company"]}", "logo": {logo_part}}},\n'
    dict_str += "}"
    
    # Regex replacement: match MODEL_INFO = \{.*?\} with dotall
    pattern = r"MODEL_INFO = \{.*?\}"
    
    # Check if we can find it
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, dict_str, content, flags=re.DOTALL)
        with open("benchmark-tracker/server.py", "w") as f:
            f.write(new_content)
        print("Updated server.py with real logos!")
    else:
        print("Could not find MODEL_INFO block in server.py")
