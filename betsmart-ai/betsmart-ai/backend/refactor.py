import os
import glob
import re

structure = {
    "data": ["rag_data.txt"],
    "agents": ["agents.py", "coordinator.py", "llm_engine.py"],
    "services": ["odds_fetcher.py", "arbitrage.py", "casino.py", "decision_engine.py", "sports_genres.py"],
    "utils": ["ev_calculator.py", "simulation.py", "probability_engine.py", "vector_store.py"],
    "core": ["config.py", "prompts.py"]
}

# File to module mapping
module_mapping = {}
for folder, files in structure.items():
    if not os.path.exists(folder):
        os.makedirs(folder)
        open(os.path.join(folder, "__init__.py"), "a").close()
    for f in files:
        if os.path.exists(f):
            module_name = f.replace(".py", "")
            module_mapping[module_name] = f"{folder}.{module_name}"

def move_files():
    for folder, files in structure.items():
        for f in files:
            if os.path.exists(f):
                os.rename(f, os.path.join(folder, f))

def fix_imports_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    
    # We replace 'from X import' with 'from folder.X import'
    for old_mod, new_mod in module_mapping.items():
        # Match 'from old_mod import'
        # Also match 'import old_mod'
        content = re.sub(rf"^from {old_mod} import", f"from {new_mod} import", content, flags=re.MULTILINE)
        content = re.sub(rf"^import {old_mod}\b", f"import {new_mod}", content, flags=re.MULTILINE)
        
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)

# Move files
move_files()

# Fix all python files
py_files = []
for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            py_files.append(os.path.join(root, file))

for py_file in py_files:
    fix_imports_in_file(py_file)

# Extract schemas from main.py and put them in models/schemas.py
os.makedirs("models", exist_ok=True)
open("models/__init__.py", "a").close()

with open("main.py", "r", encoding="utf-8") as f:
    main_py = f.read()

schemas_match = re.search(r"(class .*?BaseModel\):.*?)(?=@app)", main_py, re.DOTALL | re.MULTILINE)
if schemas_match:
    schemas_code = schemas_match.group(1).strip()
    with open("models/schemas.py", "w", encoding="utf-8") as f:
        f.write("from pydantic import BaseModel\nfrom typing import List, Optional\n\n" + schemas_code + "\n")
    
    # Remove from main.py
    main_py = main_py.replace(schemas_code, "from models.schemas import *\n")
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(main_py)

print("Refactoring complete.")
