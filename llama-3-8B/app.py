import os
import time
import requests
import json
import re
from datetime import datetime

INFO_FILE = "info.txt"

# [MİMARİ KONTROL] info.txt varlığı ve parse edilmesi
if not os.path.exists(INFO_FILE):
    print(f"\033[91m[-] KRİTİK HATA: '{INFO_FILE}' yapılandırma dosyası bulunamadı!")
    print("[!] Lütfen info.txt dosyasını oluşturun ve parametreleri tanımlayın.\033[0m")
    exit(1)

# info.txt içeriğini dinamik olarak oku
config = {}
with open(INFO_FILE, "r", encoding="utf-8") as config_file:
    for line in config_file:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()

# Dinamik Değişken Atamaları
COMPANY = config.get("COMPANY_NAME", "Stux6 Tech")
SYSTEM = config.get("SYSTEM_NAME", "Audit Tool")
MODEL_NAME = config.get("MODEL_NAME", "deepseek-r1:14b")
LOG_FILE = config.get("LOG_FILE_NAME", "boteg_thought_log.txt")
PROMPT_FILE = config.get("PROMPT_FILE_NAME", "prompt.txt")
OLLAMA_URL = "http://localhost:11434/api/generate"

# Terminal Renk Kodları (ANSI)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

print(f"{CYAN}{BOLD}[+] {COMPANY} - {SYSTEM} Başlatıldı.{RESET}")
print(f"[+] Dinamik Altyapı Aktif | Model: '{MODEL_NAME}'")
print(f"[+] Senaryo Havuzu: '{PROMPT_FILE}' | Adli Raporlama: '{LOG_FILE}'")
print("==========================================================================")

def query_ollama(prompt_text):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_text,
        "stream": True
    }
    
    full_response = ""
    print(f"[✔] STATUS: {YELLOW}{MODEL_NAME} akıl yürütüyor (Düşünme logları arka plana yazılıyor)...{RESET}")
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True)
        if response.status_code != 200:
            return None, f"Ollama Sunucu Hatası ({response.status_code})"
            
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                text_chunk = chunk.get("response", "")
                full_response += text_chunk
                
        return full_response, None
    except Exception as e:
        return None, str(e)

# prompt.txt kontrolü
if not os.path.exists(PROMPT_FILE):
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write("# Denetlenecek senaryoyu buraya girin.")

last_modified = os.path.getmtime(PROMPT_FILE)

while True:
    try:
        time.sleep(1)
        current_modified = os.path.getmtime(PROMPT_FILE)
        
        if current_modified != last_modified:
            print(f"\n{YELLOW}[!] Yeni Girdi Tespit Edildi! Analiz süreci tetiklendi...{RESET}")
            last_modified = current_modified
            
            with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                prompt_content = f.read()
            
            start_time = time.time()
            output, error = query_ollama(prompt_content)
            end_time = time.time()
            
            if error:
                print(f"{RED}[- Kesinti Hatası]: {error}{RESET}")
                continue
                
            # Arka plan düşünme logunu (<think>...</think>) ayıkla
            thinking_process = ""
            final_output = output
            
            think_match = re.search(r'<think>(.*?)</think>', output, re.DOTALL)
            if think_match:
                thinking_process = think_match.group(1).strip()
                final_output = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL).strip()
            
            # Format Doğrulama Denetimi (Regex tabanlı)
            has_kilitle = bool(re.search(r'\bKİLİTLE\b', final_output, re.IGNORECASE))
            has_ac = bool(re.search(r'\bAÇ\b', final_output, re.IGNORECASE))
            
            format_status = f"{RED}BAŞARISIZ (Format İhlali Yapıldı){RESET}"
            if (has_kilitle or has_ac) and not (has_kilitle and has_ac):
                format_status = f"{GREEN}BAŞARILI (Tekil Karar Algılandı){RESET}"
            elif has_kilitle and has_ac:
                format_status = f"{RED}BAŞARISIZ (Çelişkili Çıktı / İki Kelime de Mevcut){RESET}"

            # Temiz Terminal Arayüzü
            print(f"\n{CYAN}=== DENETİM ANALİZ RAPORU ==={RESET}")
            print(f"[+] Format Uyumluluğu : {format_status}")
            print(f"[+] Toplam İşlem Süresi: {round(end_time - start_time, 2)} saniye.")
            print(f"--------------------------------------------------")
            print(f"{BOLD}NİHAİ MODEL ÇIKTISI:{RESET}\n{GREEN}{final_output}{RESET}")
            print(f"{CYAN}============================={RESET}\n")
            
            # Gizli Dosya Günlüğü (C Seçeneği: Harfi Harfine Dosyaya Yazım)
            with open(LOG_FILE, "a", encoding="utf-8") as log:
                log.write(f"\n============================================================\n")
                log.write(f"DENEY TARİHİ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log.write(f"ŞİRKET/SİSTEM: {COMPANY} - {SYSTEM}\n")
                log.write(f"DENETLENEN MODEL: {MODEL_NAME}\n")
                log.write(f"------------------------------------------------------------\n")
                log.write(f"PROMPT İÇERİĞİ:\n{prompt_content}\n")
                log.write(f"------------------------------------------------------------\n")
                log.write(f"FİLTRESİZ HAM DÜŞÜNME LOGU (<think>):\n{thinking_process if thinking_process else 'Düşünme bloğu algılanamadı.'}\n")
                log.write(f"------------------------------------------------------------\n")
                log.write(f"NİHAİ TEMİZ ÇIKTI:\n{final_output}\n")
                log.write(f"============================================================\n")
                
    except KeyboardInterrupt:
        print(f"\n{RED}[-] Denetim altyapısı kontrollü olarak kapatıldı. Sinyal: SIGINT{RESET}")
        break