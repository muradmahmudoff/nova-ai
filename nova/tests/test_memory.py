"""Yaddaş menecerinin (SQLite hissəsi) testləri."""
import pytest

from app.memory.database import init_db
from app.memory.memory_manager import MemoryManager


@pytest.mark.asyncio
async def test_ensure_conversation_creates_new():
    await init_db()
    memory = MemoryManager()
    conv_id = await memory.ensure_conversation(None)
    assert conv_id is not None
    assert isinstance(conv_id, str)


@pytest.mark.asyncio
async def test_save_and_retrieve_history():
    await init_db()
    memory = MemoryManager()
    conv_id = await memory.ensure_conversation(None)

    await memory.save_message(conv_id, "user", "salam")
    await memory.save_message(conv_id, "assistant", "salam, necəsən?")

    history = await memory.get_recent_history(conv_id)
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"
