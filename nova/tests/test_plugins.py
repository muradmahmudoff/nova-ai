"""Plugin sisteminin testləri."""
import pytest

from app.plugins.base import BasePlugin
from app.plugins.loader import PluginRegistry


class DummyPlugin(BasePlugin):
    name = "dummy"
    description = "Test üçün saxta plugin"

    async def execute(self, **kwargs) -> str:
        return "dummy nəticə"


@pytest.mark.asyncio
async def test_plugin_registration_and_execution():
    registry = PluginRegistry()
    registry.register(DummyPlugin())

    assert registry.get("dummy") is not None
    result = await registry.execute("dummy")
    assert result == "dummy nəticə"


@pytest.mark.asyncio
async def test_unknown_plugin_raises():
    from app.core.exceptions import PluginError

    registry = PluginRegistry()
    with pytest.raises(PluginError):
        await registry.execute("olmayan_plugin")


def test_tool_schema_format():
    plugin = DummyPlugin()
    schema = plugin.to_tool_schema()
    assert schema["name"] == "dummy"
    assert "description" in schema
    assert "parameters" in schema
