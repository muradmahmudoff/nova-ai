"""
Nova AI - Xüsusi İstisna (Exception) Sinifləri
==================================================
Layihə boyu istifadə olunan strukturlu xəta tipləri.
Bunlar sayəsində xətaları həm log-da, həm API cavabında dəqiq təsnif etmək olur.
"""


class NovaException(Exception):
    """Bütün Nova xətalarının əsas sinfi."""

    def __init__(self, message: str, *, code: str = "NOVA_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class LLMProviderError(NovaException):
    """LLM provayderi ilə əlaqədə (API açarı, şəbəkə, rate-limit və s.) yaranan xəta."""

    def __init__(self, message: str, provider: str = "unknown"):
        self.provider = provider
        super().__init__(message, code="LLM_PROVIDER_ERROR")


class MemoryError_(NovaException):
    """Yaddaş (SQLite/ChromaDB) əməliyyatlarında yaranan xəta."""

    def __init__(self, message: str):
        super().__init__(message, code="MEMORY_ERROR")


class PluginError(NovaException):
    """Plugin yüklənməsi və ya icrası zamanı yaranan xəta."""

    def __init__(self, message: str, plugin_name: str = "unknown"):
        self.plugin_name = plugin_name
        super().__init__(message, code="PLUGIN_ERROR")


class AudioError(NovaException):
    """STT/TTS/Wake-word əməliyyatlarında yaranan xəta."""

    def __init__(self, message: str):
        super().__init__(message, code="AUDIO_ERROR")


class ConfigurationError(NovaException):
    """Konfiqurasiya (məs. API açarı çatışmır) xətası."""

    def __init__(self, message: str):
        super().__init__(message, code="CONFIG_ERROR")
