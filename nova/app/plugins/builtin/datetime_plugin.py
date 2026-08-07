"""Plugin: Cari tarix və vaxt məlumatı."""
from __future__ import annotations

from datetime import datetime

from app.plugins.base import BasePlugin

_AZ_GUNLER = ["Bazar ertəsi", "Çərşənbə axşamı", "Çərşənbə", "Cümə axşamı", "Cümə", "Şənbə", "Bazar"]
_AZ_AYLAR = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "İyun",
    "İyul", "Avqust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr",
]


class DateTimePlugin(BasePlugin):
    name = "get_current_datetime"
    description = "Cari tarix, saat və gün haqqında məlumat almaq üçün istifadə et."
    parameters = {"type": "object", "properties": {}, "required": []}

    async def execute(self) -> str:
        now = datetime.now()
        gun = _AZ_GUNLER[now.weekday()]
        ay = _AZ_AYLAR[now.month - 1]
        return f"{now.day} {ay} {now.year}, {gun}, saat {now.strftime('%H:%M')}"
