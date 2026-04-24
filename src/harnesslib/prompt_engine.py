"""PromptEngine — Prompt模板加载/渲染/版本追踪。

通用机制（harnesslib提供），模板内容由项目层提供。
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptEngine:
    """Prompt模板加载与渲染引擎。

    通用机制：
    - Jinja2模板加载和渲染
    - 模板版本追踪（文件hash），记录到Event中便于回溯
    """

    def __init__(self, template_dir: str | Path) -> None:
        self._template_dir = Path(template_dir)
        self._env = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=select_autoescape([]),
            keep_trailing_newline=True,
        )

    def render(self, template_name: str, context: dict) -> str:
        """渲染模板，返回完整prompt字符串。"""
        template = self._env.get_template(template_name)
        return template.render(**context)

    def get_version(self, template_name: str) -> str:
        """返回模板的版本标识（文件内容sha256前8位）。"""
        path = self._template_dir / template_name
        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()[:8]

    def list_templates(self) -> list[str]:
        """列出所有可用模板。"""
        return self._env.list_templates()