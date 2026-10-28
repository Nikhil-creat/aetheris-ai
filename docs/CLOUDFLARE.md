# Deploying on Cloudflare
Frontend: Cloudflare Pages (build output directory `frontend`, no build command).
API: Cloudflare Worker from `worker/` (Workers Builds, root directory `worker`).
Secrets (dashboard > Worker > Settings > Variables and Secrets): GROQ_API_KEY, GEMINI_API_KEY, ADMIN_KEY.
Optional: KV namespace CACHE and Vectorize index aetheris-kb (768 dimensions, cosine); uncomment them in wrangler.toml, push, then POST /api/admin/ingest with header X-Admin-Key.
After deploying, set `window.AETHERIS_API` in frontend/config.js to the Worker URL.
