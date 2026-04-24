"""Resources — 持久化资源管理。

对应Anthropic架构中的 [{source_ref, mount_path}]。
Tools通过ResourceManager获取所需资源，不硬编码文件路径。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ResourceRef(BaseModel):
    """资源引用。"""

    name: str
    source: str  # 文件路径 / URI
    description: str | None = None


class ResourceManager:
    """管理所有持久化资源的注册和访问。"""

    def __init__(self) -> None:
        self._refs: dict[str, ResourceRef] = {}
        self._cache: dict[str, Any] = {}

    def register(self, ref: ResourceRef) -> None:
        """注册一个资源引用。"""
        self._refs[ref.name] = ref

    def get_ref(self, name: str) -> ResourceRef:
        """获取资源引用（元信息）。"""
        if name not in self._refs:
            raise KeyError(f"Resource not registered: {name}")
        return self._refs[name]

    def get_path(self, name: str) -> str:
        """获取资源的source路径。便捷方法。"""
        return self.get_ref(name).source

    def list_resources(self) -> list[ResourceRef]:
        """列出所有已注册的资源。"""
        return list(self._refs.values())