from huggingface_hub import list_repo_refs
try:
    refs = list_repo_refs("TheMelonGod/Qwen3-1.7B-exl2")
    print("找到的分支：")
    for b in refs.branches:
        print(f" - {b.name}")
except Exception as e:
    print(f"错误：{e}")
