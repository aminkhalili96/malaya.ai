import os
import urllib.request
import time

LOGOS = {
    "openai": "https://github.com/openai.png",
    "google": "https://github.com/google.png",
    "meta": "https://github.com/meta-llama.png",
    "qwen": "https://github.com/QwenLM.png",
    "deepseek": "https://github.com/deepseek-ai.png",
    "mesolitica": "https://github.com/mesolitica.png",
    "opensource": "https://github.com/OpenSourceOrg.png"
}

TARGET_DIR = "benchmark-tracker/static/logos"

def download_logos():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        print(f"Created directory: {TARGET_DIR}")

    for name, url in LOGOS.items():
        try:
            filename = f"{name}.png"
            filepath = os.path.join(TARGET_DIR, filename)
            
            print(f"Downloading {name} from {url}...")
            
            # Use a user agent to avoid basic blocking
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = response.read()
                
            with open(filepath, "wb") as f:
                f.write(data)
                
            print(f"Saved to {filepath}")
            time.sleep(0.5) # Be nice
            
        except Exception as e:
            print(f"Error downloading {name}: {e}")

if __name__ == "__main__":
    download_logos()
