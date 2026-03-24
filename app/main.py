"""
Global AI Copilot - 主启动脚本
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              🚀 Global AI Copilot                         ║
║                                                           ║
║     本地 AI 补全工具 - 支持任意 Windows 应用                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

使用说明:
  1. 启动 API 服务器：
     python -m uvicorn backend.api.server:app --host 127.0.0.1 --port 7891

  2. 启动桌面服务 (新终端):
     python desktop/service.py

  3. 或使用启动脚本:
     run.bat

Web 控制台：http://127.0.0.1:7891
API 文档：http://127.0.0.1:7891/api/docs
""")


def main():
    """主函数 - 显示使用帮助"""
    print("请使用 run.bat 启动完整服务，或分别启动 API 服务器和桌面服务。")


if __name__ == "__main__":
    main()
