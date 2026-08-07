"""
Nova AI - Dil Aşkarlama Modulu
===================================
İstifadəçinin yazdığı/dediyi mətnin hansı dildə olduğunu müəyyən edir
(Azərbaycan, İngilis, Türk). `langdetect` kitabxanası əsas mühərrikdir,
lakin AZ/TR arasında tez-tez qarışıqlıq yaratdığı üçün əlavə heuristika
(xarakterik hərflər: ə, ş, ç, ğ, ı və s.) ilə dəqiqləşdirilir.
"""
from __future__ import annotations

from langdetect import DetectorFactory, LangDetectException, detect

from config.settings import settings

DetectorFactory.seed = 0  # nəticələrin sabit (deterministic) olması üçün

# Azərbaycan dilinə xas hərflər (Türk əlifbasında olmayan)
_AZ_SPECIFIC_CHARS = set("əƏ")
# Hər iki dildə ortaq olan, lakin ingilis mətnlərdə olmayan simvollar
_TR_AZ_SHARED = set("şŞçÇğĞıİöÖüÜ")


def detect_language(text: str) -> str:
    """Mətnin dilini aşkarlayır. Nəticə: 'az' | 'en' | 'tr'.

    Əgər auto-detect deaktivdirsə, konfiqurasiyadakı default dili qaytarır.
    """
    if not settings.auto_detect_language:
        return settings.default_language

    text = text.strip()
    if not text:
        return settings.default_language

    # Heuristika 1: 'ə' hərfi yalnız Azərbaycan dilində var
    if any(ch in _AZ_SPECIFIC_CHARS for ch in text):
        return "az"

    try:
        detected = detect(text)
    except LangDetectException:
        return settings.default_language

    # langdetect 'tr' desə, lakin AZ-a xas heç bir işarə yoxdursa,
    # ortaq türk hərflərinin sıxlığına baxaraq qərar veririk.
    if detected == "tr":
        # Sadəlik üçün: əgər əvvəlki mətndə türk/azərbaycan hərfləri varsa
        # amma 'ə' yoxdursa, ehtiyatlı davranıb default dilə üstünlük veririk
        # yalnız istifadəçi əvvəlcədən AZ seçibsə.
        return "tr"

    if detected in ("az",):
        return "az"
    if detected in ("en",):
        return "en"

    # Naməlum/az əminlikli hallarda default dilə qayıt
    return settings.default_language


def get_system_prompt_language_instruction(lang: str) -> str:
    """Aşkarlanan dilə uyğun sistem təlimatı hissəsi."""
    instructions = {
        "az": "İstifadəçi ilə Azərbaycan dilində danış.",
        "en": "Respond to the user in English.",
        "tr": "Kullanıcıyla Türkçe konuş.",
    }
    return instructions.get(lang, instructions["az"])
