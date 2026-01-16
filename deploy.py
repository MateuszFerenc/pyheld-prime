import os
import subprocess
from pathlib import Path

# --- KONFIGURACJA ---
SOURCE_DIR = "."  # Folder z Twoim kodem
BUILD_DIR = "build"  # Folder na skompilowane pliki .mpy
# Pliki, których NIE chcemy kompilować (np. skrypt wdrożeniowy)
EXCLUDE_FILES = ["deploy.py", "boot.py"] 
# Pliki, które mają zostać jako .py (opcjonalnie main.py)
KEEP_AS_PY = ["main.py"] 

def run_command(cmd):
    """Pomocnicza funkcja do uruchamiania komend systemowych."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas wykonywania: {cmd}\n{e.stderr}")
        return None

def compile_and_deploy():
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    print("--- Faza 1: Kompilacja (mpy-cross) ---")
    files_to_upload = []

    for path in Path(SOURCE_DIR).glob("*.py"):
        filename = path.name
        if filename in EXCLUDE_FILES:
            continue

        target_file = Path(BUILD_DIR) / filename
        
        # Jeśli plik ma być skompilowany do .mpy
        if filename not in KEEP_AS_PY:
            target_file = target_file.with_suffix(".mpy")
            
            # Kompiluj tylko jeśli źródło jest nowsze niż istniejący .mpy
            if not target_file.exists() or path.stat().st_mtime > target_file.stat().st_mtime:
                print(f"Kompilowanie: {filename} -> {target_file.name}")
                run_command(f"mpy-cross {path} -o {target_file}")
            else:
                print(f"Aktualny: {target_file.name}")
        else:
            # Dla plików .py po prostu kopiujemy do folderu build, by mieć komplet
            if not target_file.exists() or path.stat().st_mtime > target_file.stat().st_mtime:
                print(f"Przygotowanie: {filename}")
                with open(path, 'rb') as src, open(target_file, 'wb') as dst:
                    dst.write(src.read())

        files_to_upload.append(target_file)

    print("\n--- Faza 2: Przesyłanie (mpremote) ---")
    # mpremote cp ma flagę do przesyłania wielu plików, ale my chcemy 
    # wysyłać tylko te z folderu build
    for f in files_to_upload:
        # mpremote cp automatycznie nadpisuje pliki, ale robi to szybko
        print(f"Wgrywanie {f.name}...")
        run_command(f"mpremote cp {f} :{f.name}")

    print("\nGotowe! Resetowanie urządzenia...")
    run_command("mpremote reset")

if __name__ == "__main__":
    compile_and_deploy()