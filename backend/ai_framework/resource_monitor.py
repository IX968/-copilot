"""
资源监控器
监控 GPU、CPU、内存等资源使用情况
"""
import psutil
import torch
from typing import Dict, Any, Optional


class ResourceMonitor:
    """
    资源监控器

    职责:
    - 监控 GPU 使用率和显存占用
    - 监控 CPU 使用率和内存占用
    - 提供资源状态快照
    """

    def __init__(self):
        """初始化资源监控器"""
        self._has_gpu = torch.cuda.is_available()
        self._gpu_name = ""
        self._gpu_total_memory = 0

        if self._has_gpu:
            try:
                self._gpu_name = torch.cuda.get_device_name(0)
                self._gpu_total_memory = torch.cuda.get_device_properties(0).total_memory
            except Exception:
                self._has_gpu = False

        # 缓存进程实例并预热 cpu_percent（首次调用始终返回 0）
        self._process = psutil.Process()
        self._process.cpu_percent()

    def get_gpu_status(self) -> Dict[str, Any]:
        """
        获取 GPU 状态

        Returns:
            Dict: GPU 状态信息
        """
        if not self._has_gpu:
            return {
                "available": False,
                "error": "未检测到 GPU"
            }

        try:
            # 显存使用情况
            allocated = torch.cuda.memory_allocated(0)
            reserved = torch.cuda.memory_reserved(0)

            return {
                "available": True,
                "name": self._gpu_name,
                "usage_percent": torch.cuda.utilization(0) if hasattr(torch.cuda, 'utilization') else 0,
                "memory_allocated_gb": round(allocated / (1024 ** 3), 2),
                "memory_reserved_gb": round(reserved / (1024 ** 3), 2),
                "memory_total_gb": round(self._gpu_total_memory / (1024 ** 3), 2),
                "memory_used_percent": round(allocated / self._gpu_total_memory * 100, 1) if self._gpu_total_memory > 0 else 0,
            }
        except Exception as e:
            return {
                "available": True,
                "error": f"获取 GPU 状态失败：{e}"
            }

    def get_cpu_status(self) -> Dict[str, Any]:
        """
        获取 CPU 状态

        Returns:
            Dict: CPU 状态信息
        """
        try:
            return {
                "usage_percent": psutil.cpu_percent(interval=0.1),
                "cores_physical": psutil.cpu_count(logical=False),
                "cores_logical": psutil.cpu_count(logical=True),
            }
        except Exception as e:
            return {
                "error": f"获取 CPU 状态失败：{e}"
            }

    def get_memory_status(self) -> Dict[str, Any]:
        """
        获取系统内存状态

        Returns:
            Dict: 内存状态信息
        """
        try:
            mem = psutil.virtual_memory()
            return {
                "total_gb": round(mem.total / (1024 ** 3), 2),
                "available_gb": round(mem.available / (1024 ** 3), 2),
                "used_gb": round(mem.used / (1024 ** 3), 2),
                "used_percent": mem.percent,
            }
        except Exception as e:
            return {
                "error": f"获取内存状态失败：{e}"
            }

    def get_process_status(self) -> Dict[str, Any]:
        """
        获取当前进程资源使用

        Returns:
            Dict: 进程资源信息
        """
        try:
            process = self._process
            mem_info = process.memory_info()

            result = {
                "memory_rss_gb": round(mem_info.rss / (1024 ** 3), 2),
                "memory_vms_gb": round(mem_info.vms / (1024 ** 3), 2),
                "cpu_percent": process.cpu_percent(),
                "threads": process.num_threads(),
            }

            if self._has_gpu:
                # 获取进程的 GPU 使用情况（需要额外库支持）
                # 这里仅提供 PyTorch 分配的显存
                result["gpu_memory_allocated_gb"] = round(
                    torch.cuda.memory_allocated(0) / (1024 ** 3), 2
                )

            return result
        except Exception as e:
            return {
                "error": f"获取进程状态失败：{e}"
            }

    def get_full_status(self) -> Dict[str, Any]:
        """
        获取完整资源状态

        Returns:
            Dict: 完整资源信息
        """
        return {
            "gpu": self.get_gpu_status(),
            "cpu": self.get_cpu_status(),
            "memory": self.get_memory_status(),
            "process": self.get_process_status(),
        }

    def is_gpu_available(self) -> bool:
        """GPU 是否可用"""
        return self._has_gpu

    def get_gpu_memory_free(self) -> float:
        """获取 GPU 剩余显存（GB）"""
        if not self._has_gpu:
            return 0.0

        try:
            allocated = torch.cuda.memory_allocated(0)
            return round((self._gpu_total_memory - allocated) / (1024 ** 3), 2)
        except Exception:
            return 0.0


# 全局监控器实例
_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """获取全局资源监控器实例"""
    global _monitor
    if _monitor is None:
        _monitor = ResourceMonitor()
    return _monitor
