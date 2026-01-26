
import sys
import os

# Use local Malaya LLM path
sys.path.append(os.getcwd())

from src.chatbot.services.native_malaya import NativeMalaya

def test_integration():
    print("Testing Native Malaya Integration...")
    
    nm = NativeMalaya()
    
    # 1. Test Shortform Normalization (Fast Path)
    input_text = "aq xleh nk gi skolah esok"
    expected = "aku tak boleh nak pergi sekolah esok"
    
    # Depending on dictionary coverage, we expect at least 'xleh', 'nk' to be fixed
    result = nm.normalize(input_text)
    print(f"\n[Normalization Test]")
    print(f"Input:    {input_text}")
    print(f"Output:   {result}")
    
    if "tak boleh" in result or "tidak boleh" in result:
        print("✅ Shortform normalization working!")
    else:
        print("❌ Normalization failed to catch 'xleh'")

    # 2. Check Entity Loading (Mock check if we added logic, currently separate JSONs)
    # Just checking file existence for now
    required_files = [
        "data/dictionaries/malaya_standard.json", 
        "data/knowledge/entities_schools.json"
    ]
    
    print(f"\n[File Existence Check]")
    for f in required_files:
        if os.path.exists(f):
            print(f"✅ Found {f}")
        else:
            print(f"❌ Missing {f}")

if __name__ == "__main__":
    test_integration()
