"""Plugin: İnternetdən məlumat axtarışı (DuckDuckGo HTML nəticələri üzərindən)."""
from __future__ import annotations

import httpx

from app.plugins.base import BasePlugin


class WebSearchPlugin(BasePlugin):
    name = "web_search"
    description = (
        "İnternetdə cari, tarixdən sonrakı və ya real-vaxt məlumat axtarmaq üçün istifadə et "
        "(məsələn xəbərlər, qiymətlər, hava, yeni faktlar)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Axtarış sorğusu"},
        },
        "required": ["query"],
    }

    async def execute(self, query: str) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Nova-AI)"},
            )
        if resp.status_code != 200:
            return f"Axtarış uğursuz oldu (status: {resp.status_code})"

        # Sadə parsing - production-da BeautifulSoup istifadə etmək tövsiyə olunur
        text = resp.text
        snippets = []
        marker = 'class="result__snippet"'
        idx = 0
        while len(snippets) < 5:
            idx = text.find(marker, idx)
            if idx == -1:
                break
            start = text.find(">", idx) + 1
            end = text.find("</a>", start)
            if end == -1:
                end = text.find("</div>", start)
            snippet = text[start:end].strip()
            # HTML tag-larını təmizlə
            import re
            snippet = re.sub(r"<[^>]+>", "", snippet)
            if snippet:
                snippets.append(snippet)
            idx = end

        if not snippets:
            return "Heç bir nəticə tapılmadı."
        return "\n".join(f"- {s}" for s in snippets)
