# Nova AI - Vercel Frontend

Bu qovluq Nova-nın veb interfeysini Vercel-də deploy etmək üçündür.
Backend (FastAPI - chat, audio, yaddaş) BURADA DEYİL, ayrıca Railway/Render/VPS-də işləməlidir.

## Quraşdırma addımları

### 1. Əvvəlcə backend-i deploy et (məsələn Railway)

Ana layihə qovluğunu (nova/) Railway-ə deploy et:
  - https://railway.app -> New Project -> Deploy from GitHub (yaxud "Empty project" + CLI ilə yüklə)
  - Railway avtomatik Dockerfile-ı tapıb build edəcək
  - Environment Variables bölməsində .env-dəki dəyişənləri (API açarları və s.) doldur
  - Deploy bitdikdən sonra sənə bir URL verəcək, məsələn:
      https://nova-ai-production.up.railway.app

### 2. index.html-də backend URL-ini yaz

`index.html` faylını aç, bu sətri tap:

    window.NOVA_API_BASE = "https://your-backend-url.up.railway.app";

və öz Railway (və ya Render/VPS) URL-inlə əvəz et.

### 3. Vercel-ə deploy et

Vercel CLI ilə:

    npm install -g vercel
    cd deploy/vercel-frontend
    vercel --prod

Və ya Vercel dashboard-dan:
  - https://vercel.com/new
  - Bu qovluğu (deploy/vercel-frontend) GitHub-a push et, Vercel-də "Import" et
  - Heç bir build əmri lazım deyil (statik sayt), "Root Directory" = deploy/vercel-frontend

### 4. Backend-də CORS-u tənzimlə

Ana layihədəki `app/main.py`-də CORS hazırda "*" (hamısına açıq). Production üçün
Vercel domenini müəyyən et:

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://sənin-vercel-domenin.vercel.app"],
        ...
    )

### Nəticə

  - Frontend: https://sənin-domenin.vercel.app  (Vercel, pulsuz, avtomatik HTTPS)
  - Backend:  https://nova-ai-production.up.railway.app  (Railway/Render/VPS)

Səsli söhbət işləməsi üçün backend mütləq HTTPS olmalıdır (Railway/Render bunu
avtomatik verir). Öz VPS-indədirsə, Certbot ilə SSL qur (əsas README-də izah var).
