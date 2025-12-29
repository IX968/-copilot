from huggingface_hub import list_repo_refs
try:
    refs = list_repo_refs("TheMelonGod/Qwen3-1.7B-exl2")
    print("Branches found:")
    for b in refs.branches:
        print(f" - {b.name}")
except Exception as e:
    print(f"Error: {e}")
