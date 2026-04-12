import os
import re

structure = {
    "agents": ["agents.py", "coordinator.py", "llm_engine.py"],
    "services": ["odds_fetcher.py", "arbitrage.py", "casino.py", "decision_engine.py", "sports_genres.py"],
    "utils": ["ev_calculator.py", "simulation.py", "probability_engine.py", "vector_store.py"],
    "core": ["config.py", "prompts.py"]
}

module_mapping = {}
for folder, files in structure.items():
    for f in files:
        module_name = f.replace(".py", "")
        module_mapping[module_name] = f"{folder}.{module_name}"

def fix_imports_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    
    for old_mod, new_mod in module_mapping.items():
        # Match 'from old_mod import' with any leading spaces
        content = re.sub(rf"^[ \t]*from {old_mod} import", f"from {new_mod} import", content, flags=re.MULTILINE)
        content = re.sub(rf"^[ \t]*import {old_mod}\b", f"import {new_mod}", content, flags=re.MULTILINE)
        
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)

py_files = []
for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            py_files.append(os.path.join(root, file))

for py_file in py_files:
    fix_imports_in_file(py_file)
    
print("Imports fixed.")
