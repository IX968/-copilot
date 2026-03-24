"""
全局配置加载器
"""
import os
import yaml
from pathlib import Path
from typing import Any, Optional


class Config:
    """全局配置单例"""

    _instance: Optional['Config'] = None
    _config_path: Optional[Path] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._config: dict = {}
            self._initialized = True
            self.load()

    @classmethod
    def set_config_path(cls, path: str):
        """设置配置文件路径"""
        cls._config_path = Path(path)
        # 重置单例以重新加载
        cls._instance = None

    def load(self) -> bool:
        """
        加载配置文件

        搜索顺序:
        1. 环境变量 CONFIG_PATH
        2. 类变量 _config_path
        3. ./config/config.yaml
        4. 项目根目录/config/config.yaml
        """
        # 确定配置文件路径
        if os.environ.get('CONFIG_PATH'):
            config_path = Path(os.environ['CONFIG_PATH'])
        elif self._config_path:
            config_path = self._config_path
        else:
            # 尝试当前目录
            config_path = Path('config/config.yaml')
            if not config_path.exists():
                # 尝试项目根目录（上级目录）
                config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'

        if not config_path.exists():
            print(f"警告：配置文件未找到 {config_path}，使用默认配置")
            self._load_defaults()
            return False

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            print(f"配置已加载：{config_path}")
            return True
        except Exception as e:
            print(f"错误：加载配置文件失败：{e}")
            self._load_defaults()
            return False

    def _load_defaults(self):
        """加载默认配置"""
        self._config = {
            'engine': {
                'type': 'transformer',
                'model_path': 'Qwen/Qwen3-1.7B-Base',
            },
            'generation': {
                'temperature': 0.7,
                'max_tokens': 64,
                'top_k': 40,
                'top_p': 0.9,
                'repetition_penalty': 1.1,
            },
            'trigger': {
                'debounce_ms': 300,
                'accept_key': 'tab',
                'reject_key': 'esc',
                'auto_trigger': {
                    'enabled': True,
                    'min_context_length': 3,
                }
            },
            'server': {
                'host': '127.0.0.1',
                'port': 7891,
                'reload': False,
            },
            'desktop': {
                'enabled': True,
                'ghost_text': {
                    'alpha': 0.8,
                    'font_size': 14,
                    'color': '#aaaaaa',
                },
                'context': {
                    'max_length': 8000,
                    'use_mouse_position': True,
                }
            },
            'memory': {
                'enabled': True,
                'db_path': 'data/copilot.db',
                'max_history': 1000,
            },
            'logging': {
                'level': 'INFO',
                'file': 'data/logs/copilot.log',
            }
        }

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        获取配置值

        用法:
            config.get('engine', 'type')
            config.get('server', 'port')
            config.get('nonexistent', default=42)
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, *keys: str, value: Any) -> bool:
        """
        设置配置值（仅内存，不保存到文件）

        用法:
            config.set('engine', 'type', value='exllama')
        """
        if len(keys) < 1:
            return False

        current = self._config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
        return True

    def save(self, path: Optional[str] = None) -> bool:
        """保存配置到文件"""
        save_path = Path(path) if path else self._config_path
        if not save_path:
            save_path = Path('config/config.yaml')

        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
            print(f"配置已保存：{save_path}")
            return True
        except Exception as e:
            print(f"错误：保存配置失败：{e}")
            return False

    def all(self) -> dict:
        """获取完整配置"""
        return self._config.copy()

    def reload(self) -> bool:
        """重新加载配置"""
        return self.load()


# 全局配置实例
config = Config()


# 便捷函数
def get_config(*keys: str, default=None):
    """获取配置值的便捷函数"""
    return config.get(*keys, default=default)


def set_config(*keys: str, value):
    """设置配置值的便捷函数"""
    return config.set(*keys, value=value)
