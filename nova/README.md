# Nova AI — Şəxsi AI Köməkçi

Nova, tam sənə məxsus, lokal işləyə bilən, istəsən bulud LLM-lərinə (OpenAI, Anthropic,
Gemini, OpenRouter) qoşula bilən, səsli danışan, yaddaşı olan, plugin-lərlə genişlənən
şəxsi AI köməkçisidir.

## Xüsusiyyətlər

- 🎙 Real-vaxt səsli danışıq (mikrofon → STT → Agent → TTS)
- 🗣 Azərbaycan / İngilis / Türk dili dəstəyi, avtomatik dil aşkarlama
- 🧠 İki qatlı yaddaş: SQLite (dəqiq tarixçə) + ChromaDB (semantik yaddaş)
- 🔌 Plugin sistemi (asanlıqla yeni "alət" əlavə edilə bilər)
- 🌐 İstəyə bağlı internet axtarışı
- 📄 PDF/DOCX/TXT/şəkil fayllarını oxuma
- 🔁 5 fərqli LLM provayder arasında keçid: local (Ollama) / OpenAI / Anthropic / Gemini / OpenRouter
- 🖥 Native desktop GUI (PySide6)
- 👂 Wake word dəstəyi ("Nova")
- 🐳 Docker dəstəyi
- ✅ Test dəsti (pytest)

## Arxitektura

```
┌─────────────┐      HTTP / WebSocket     ┌──────────────────┐
│  PySide6 GUI │◄─────────────────────────►│   FastAPI Server  │
└─────────────┘                            └─────────┬─────────┘
                          ┌──────────────────────────┼──────────────────────────┐
                          ▼                          ▼                          ▼
                 ┌─────────────────┐        ┌────────────────┐        ┌─────────────────┐
                 │ Audio Pipeline   │        │  Agent (Graph)  │        │  Memory Layer    │
                 │ STT/TTS/WakeWord │        │  LangGraph +    │        │  SQLite +        │
                 └─────────────────┘        │  Plugin router  │        │  ChromaDB        │
                                             │  LLM abstraction│        └─────────────────┘
                                             └────────┬────────┘
                                                       ▼
                                             ┌──────────────────┐
                                             │  Plugin System    │
                                             └──────────────────┘
```

## Qovluq strukturu

```
nova/
├── app/
│   ├── main.py                 # FastAPI giriş nöqtəsi
│   ├── core/                   # logging, exceptions, fayl oxuma
│   ├── llm/                    # LLM provider abstraction + adapterlər
│   │   └── providers/          # openai, anthropic, gemini, openrouter, ollama
│   ├── memory/                 # SQLite modelləri + ChromaDB + memory manager
│   ├── agent/                  # LangGraph agent, dil aşkarlama
│   ├── plugins/                # Plugin sistemi + builtin plugin-lər
│   ├── audio/                  # STT (whisper), TTS (piper), wake-word, mikrofon
│   ├── api/                    # REST + WebSocket route-ları
│   └── gui/                    # PySide6 desktop interfeys
├── config/settings.py          # Mərkəzi konfiqurasiya (.env oxuyur)
├── scripts/                    # run_server.py, run_gui.py, setup_first_run.py
├── tests/                      # pytest test dəsti
├── data/                       # SQLite DB + ChromaDB (runtime-da yaranır)
├── models/                     # Whisper/Piper/WakeWord model faylları
├── logs/                       # Log faylları (runtime-da yaranır)
├── Dockerfile / docker-compose.yml
├── pyproject.toml
└── .env.example
```

## Texnologiya seçimlərinin səbəbi

| Komponent | Seçim | Səbəb |
|---|---|---|
| Backend | FastAPI + asyncio | Nativ async dəstək, WebSocket ilə real-vaxt səs axını |
| STT | faster-whisper | Orijinal Whisper-dən ~4x sürətli, CPU-da işlək |
| TTS | Piper TTS | Tam lokal, sürətli, ONNX əsaslı |
| GUI | PySide6 | Native performans, Python ilə birbaşa inteqrasiya |
| Struktur yaddaş | SQLite | Yüngül, server tələb etmir, tam tarixçə saxlayır |
| Semantik yaddaş | ChromaDB | Lokal vektor DB, "məna baxımından" axtarış |
| Agent orkestrasiyası | LangGraph | State-machine əsaslı, aydın node/edge strukturu |
| Wake word | openWakeWord | Tam lokal, offline, custom model train edilə bilir |

## Quraşdırma

### Tələblər
- Python 3.11+
- (İstəyə bağlı) Docker
- (İstəyə bağlı, lokal LLM üçün) [Ollama](https://ollama.com)

### Addımlar

```bash
# 1. Repo-nu klonla / arxivdən çıxart
cd nova

# 2. Virtual mühit yarat
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Asılılıqları quraşdır
pip install -e .

# 4. İlk quraşdırma skriptini işə sal (qovluqlar, .env, DB)
python scripts/setup_first_run.py

# 5. .env faylını aç və istədiyin LLM provayderin API açarını doldur
#    (yaxud LLM_PROVIDER=local saxlayıb Ollama işlət)
```

### Model fayllarının endirilməsi (səsli funksiyalar üçün)

```bash
# Whisper modeli ilk işə salınanda avtomatik endirilir (models/whisper altına)

# Piper TTS modelləri (əl ilə endirilir):
#   https://github.com/rhasspy/piper/blob/master/VOICES.md
#   endirilən .onnx + .onnx.json fayllarını models/piper/ altına qoy

# Wake-word: openWakeWord-un default modelləri ilə test edə bilərsən,
# xüsusi "Nova" sözü üçün custom model train et:
#   https://github.com/dscripka/openWakeWord#training-new-models
#   nəticəni models/wakeword/nova.onnx kimi qoy
```

### Ollama ilə tam lokal işlətmək

```bash
ollama pull llama3.1
ollama serve
# .env faylında: LLM_PROVIDER=local
```

## İşə salma

```bash
# Terminal 1: Backend
python scripts/run_server.py

# Terminal 2: GUI
python scripts/run_gui.py
```

Backend `http://127.0.0.1:8000` ünvanında qalxır. API sənədləri: `http://127.0.0.1:8000/docs`

## Docker ilə işə salma

```bash
docker compose up --build
```

Qeyd: PySide6 GUI konteynerdə işləmir (native pəncərə tələb edir), yalnız backend
konteynerləşdirilib. GUI-ni host maşınında lokal işlətmək lazımdır.

## Veb sayt kimi işlətmək

Nova-nın backend-i (FastAPI) artıq `web/static/index.html` altında sadə, tam funksional
bir brauzer interfeysi ilə birlikdə gəlir (mətn söhbəti + brauzer mikrofonu ilə səsli
söhbət). Desktop GUI-yə ehtiyac olmadan, server işə düşən kimi `http://server-ünvanı:8000`
ünvanına daxil olub veb saytdan istifadə edə bilərsən.

### 1) Lokal test (öz kompüterində)

```bash
python scripts/run_server.py
# brauzerdə aç: http://127.0.0.1:8000
```

### 2) İnternetə çıxarmaq (real veb sayt kimi)

Ən sadə yol — kiçik bir VPS (DigitalOcean, Hetzner, AWS EC2 və s.) icarəyə götürüb
üzərində Docker və ya birbaşa Python ilə işə salmaqdır.

**Addım-addım:**

1. **VPS al və domenini ona yönləndir** (DNS-də A-record → server IP-si)
2. **Serverə qoşul və layihəni köçür:**
   ```bash
   scp -r nova-ai.zip user@your-server-ip:/opt/
   ssh user@your-server-ip
   cd /opt && unzip nova-ai.zip && cd nova
   ```
3. **Docker ilə işə sal** (ən asan yol):
   ```bash
   docker compose up -d --build
   ```
   və ya Docker-siz, systemd ilə (bax `deploy/nova-ai.service`):
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e .
   sudo cp deploy/nova-ai.service /etc/systemd/system/
   sudo systemctl daemon-reload && sudo systemctl enable --now nova-ai
   ```
4. **Nginx qur** (domeni backend-ə yönləndirmək və HTTPS üçün):
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx
   sudo cp deploy/nginx.conf /etc/nginx/sites-available/nova-ai
   # faylda "your-domain.com" yerinə öz domenini yaz
   sudo ln -s /etc/nginx/sites-available/nova-ai /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```
5. **Pulsuz SSL sertifikatı al** (HTTPS olmadan brauzer mikrofona icazə vermir!):
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```
6. Hazırdır → `https://your-domain.com` ünvanından hər yerdən daxil ola bilərsən.

> ⚠️ **Vacib:** Brauzerlər mikrofon girişinə yalnız **HTTPS** (və ya `localhost`) üzərindən
> icazə verir. Sadə HTTP ilə uzaq serverdə səsli söhbət işləməyəcək — Certbot addımını
> mütləq tamamla.

### 3) Vercel + Railway hibrid (Vercel-də istəyənlər üçün)

Vercel yalnız serverless funksiyalar dəstəklədiyi üçün (WebSocket, fasiləsiz proses,
lokal fayl saxlama yoxdur), Nova-nın ağır backend hissəsi (audio, yaddaş, agent) orada
işləyə bilmir. Ona görə tövsiyə olunan struktur:

- **Vercel** → yalnız veb interfeys (statik HTML/JS), `deploy/vercel-frontend/` qovluğu
- **Railway/Render/VPS** → tam FastAPI backend (bax yuxarıdakı bölmələr)

Addımlar `deploy/vercel-frontend/README.md`-də ətraflı yazılıb, qısaca:

```bash
# 1. Əvvəlcə backend-i Railway-ə deploy et (Dockerfile-ı avtomatik tapıb build edir)
#    Railway sənə https://xxx.up.railway.app kimi bir URL verəcək

# 2. deploy/vercel-frontend/index.html-də bu sətri backend URL-inlə əvəz et:
#    window.NOVA_API_BASE = "https://xxx.up.railway.app";

# 3. Vercel-ə deploy et
npm install -g vercel
cd deploy/vercel-frontend
vercel --prod

# 4. Backend-də CORS-u Vercel domeninə məhdudlaşdır (.env-də):
#    CORS_ALLOWED_ORIGINS=https://sənin-domenin.vercel.app
```

### 4) Daha sürətli alternativ: PaaS platformaları

Öz serverini idarə etmək istəməsən, Railway, Render və ya Fly.io kimi platformalarda
`Dockerfile`-ı olduğu kimi deploy edə bilərsən (onların hamısı avtomatik HTTPS verir):
- Railway/Render: repo-nu qoş, "Docker" build tipini seç, `PORT` env-i onlar özü verir
  (`config/settings.py`-də `server_port`-u `PORT` env-dən oxumaq üçün kiçik dəyişiklik lazım
  ola bilər), API açarlarını onların "Environment Variables" bölməsində doldur.

### Təhlükəsizlik qeydləri (production üçün)

- `app/main.py`-də CORS hazırda `allow_origins=["*"]` — production-da bunu öz domeninlə
  məhdudlaşdır.
- API açarlarını heç vaxt frontend koduna (`web/static/`) yazma — onlar yalnız server-side
  `.env`-də qalmalıdır (hazırkı struktur artıq bunu təmin edir).
- Çoxistifadəçili sayt planlaşdırırsansa, autentifikasiya (login) qatı əlavə etmək lazımdır
  — hazırkı versiya tək-istifadəçili şəxsi köməkçi kimi nəzərdə tutulub.

## İstifadə qaydası

- **Mətnlə söhbət**: GUI-də input xəttinə yaz, Enter bas
- **Səslə söhbət**: mikrofon düyməsini (🎙) bas, danış, yenidən bas ki, dayansın
- **Wake word**: `.env`-də `WAKE_WORD_ENABLED=true` olduqda "Nova" deyərək aktivləşdirə bilərsən
- **Fayl yükləmə**: `/api/chat/upload` endpoint-inə PDF/DOCX/TXT/şəkil göndər, çıxarılan
  mətni sonra `/api/chat`-a kontekst kimi ötür
- **Provayder dəyişmək**: GUI-də Parametrlər → LLM Provayder, yaxud
  `POST /api/settings/provider {"provider": "anthropic"}`
- **Yaddaşı təmizləmək**: Parametrlər → "Yaddaşı təmizlə" (yalnız semantik yaddaş silinir,
  söhbət tarixçəsi qalır)

## Yeni Plugin yazmaq

```python
# app/plugins/builtin/my_plugin.py
from app.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    description = "Nə etdiyini LLM-ə izah et"
    parameters = {
        "type": "object",
        "properties": {"param1": {"type": "string"}},
        "required": ["param1"],
    }

    async def execute(self, param1: str) -> str:
        return f"Nəticə: {param1}"
```
Fayl `app/plugins/builtin/` qovluğuna qoyulan kimi avtomatik yüklənir — heç bir əlavə
qeydiyyat lazım deyil.

## Testlərin işlədilməsi

```bash
pip install -e ".[dev]"
pytest -v
```

## Gələcək inkişaf (arxitektura hazırdır)

- **Kamera görüntüsü analizi**: `app/core/file_reader.py`-dəki `describe_image()`
  funksiyası artıq "vision" interfeysi kimi qurulub; canlı kamera kadrları eyni
  funksiyaya ötürülə bilər, əlavə arxitektur dəyişiklik lazım deyil.
- **Yeni dillər**: `app/agent/language_detector.py`-də `_LANG_MODEL_MAP`
  strukturuna yeni dil əlavə etmək kifayətdir.
- **Yeni LLM provayder**: `app/llm/base.py`-dəki `BaseLLMProvider`-dən miras alıb
  `app/llm/factory.py`-də qeydiyyatdan keçir.

## Məhdudiyyətlər / Qeydlər

- Piper-in rəsmi Azərbaycan dili modeli yoxdur; TR modelindən fonetik yaxınlıq
  səbəbiylə fallback kimi istifadə olunur, ya da öz fine-tune modelini
  `models/piper/az.onnx` yoluna qoya bilərsən.
- Wake-word üçün "Nova" sözünə xüsusi model train edilməlidir (default modellər
  test məqsədlidir).
- Tool-calling provayder-aqnostik JSON-protokol üzərindən işləyir (bax `app/agent/graph.py`),
  çünki OpenAI/Anthropic/Gemini-nin nativ tool-calling formatları fərqlidir və bu üsul
  bütün provayderlərlə (lokal modellər daxil) eyni cür işləyir.

## Lisenziya

Bu, sənin şəxsi layihəndir — istədiyin kimi dəyişdir və istifadə et.
