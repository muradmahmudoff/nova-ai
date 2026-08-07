"""
Nova AI - Plugin Loader
===========================
`app/plugins/builtin/` qovluğundakı bütün plugin fayllarını avtomatik
tapır, import edir və qeydiyyatdan keçirir. İstifadəçi yeni plugin faylı
əlavə etdikdə, kodun heç bir yerini dəyişmədən avtomatik yüklənir.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path

from app.core.exceptions import PluginError
from app.core.logging_config import logger
from app.plugins.base import BasePlugin


class PluginRegistry:
    """Yüklənmiş bütün pluginləri saxlayan reyestr."""

    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}

    def register(self, plugin: BasePlugin) -> None:
        if plugin.name in self._plugins:
            logger.warning("Plugin adı təkrarlanır, üstünə yazılır: {}", plugin.name)
        self._plugins[plugin.name] = plugin
        logger.info("Plugin qeydiyyatdan keçdi: {}", plugin.name)

    def get(self, name: str) -> BasePlugin | None:
        return self._plugins.get(name)

    def all(self) -> list[BasePlugin]:
        return list(self._plugins.values())

    def tool_schemas(self) -> list[dict]:
        """LLM-ə göndəriləcək bütün alətlərin sxemini qaytarır."""
        return [p.to_tool_schema() for p in self._plugins.values()]

    async def execute(self, name: str, **kwargs) -> str:
        plugin = self.get(name)
        if plugin is None:
            raise PluginError(f"Plugin tapılmadı: {name}", plugin_name=name)
        try:
            return await plugin.execute(**kwargs)
        except Exception as e:
            logger.error("Plugin icrası uğursuz oldu ({}): {}", name, e)
            raise PluginError(str(e), plugin_name=name) from e


def load_plugins(package: str = "app.plugins.builtin") -> PluginRegistry:
    """`builtin` qovluğundakı bütün .py fayllarını skan edir, BasePlugin
    alt-siniflərini tapıb instansiyalaşdırır və reyestrə əlavə edir.
    """
    registry = PluginRegistry()
    pkg = importlib.import_module(package)
    pkg_path = Path(pkg.__file__).parent  # type: ignore[arg-type]

    for _, module_name, is_pkg in pkgutil.iter_modules([str(pkg_path)]):
        if is_pkg or module_name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"{package}.{module_name}")
        except Exception as e:
            logger.error("Plugin modulu yüklənə bilmədi ({}): {}", module_name, e)
            continue

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                try:
                    registry.register(obj())
                except Exception as e:
                    logger.error("Plugin instansiyalaşdırıla bilmədi ({}): {}", obj, e)

    logger.info("Cəmi {} plugin yükləndi", len(registry.all()))
    return registry


_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = load_plugins()
    return _registry
