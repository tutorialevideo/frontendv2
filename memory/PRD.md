# RapoarteFirme Platform - Product Requirements Document

## Original Problem Statement
Construieste o platforma completa pentru afisarea firmelor romanesti (RapoarteFirme, domeniu: rapoartefirme.ro), bazata pe date publice agregate (1.2 milioane active, peste 3.5 milioane total). Platforma necesita 3 zone distincte: Site public, Zona User (autentificare, planuri), si Zona Admin. Sistem de abonamente, Arhitectura Hibrida, API Keys, Elasticsearch, SEO dinamic, Sitemap XML, analiza financiara, navigare judete/CAEN, integrare dosare Portal JUST si BPI.

## Tech Stack
- **Backend**: FastAPI, PyMongo, Motor (async MongoDB)
- **Frontend**: React, Tailwind CSS, Recharts, Shadcn/UI
- **Database**: MongoDB (dual DB setup - local + cloud)
- **Authentication**: JWT
- **Search**: Elasticsearch
- **AI**: Gemini 2.5 Flash (via emergentintegrations library)

## Architecture
```
/app/backend/
  server.py              (~115 lines - orchestration only)
  database.py, auth.py, utils.py
  routes/
    search_routes.py     (search + suggest)
    company_routes.py    (company CUI/slug/financials)
    geo_routes.py        (judete/localitati/caen/stats)
    seo_gen_routes.py    (AI SEO text generation - Gemini Flash)
    admin_sync_routes.py (sync + auto-indexing)
    admin_db_routes.py   (DB optimization + qmark normalization)
    location_routes.py, caen_routes.py, financial_routes.py
    legal_routes.py, sitemap_routes.py, seo_routes.py
    auth_routes.py, user_routes.py, admin_routes.py, etc.
/app/frontend/
  src/pages/
    AdminSeoGenPage.js   (AI SEO generation admin page)
    AdminDbOptimizePage.js, CompanyPage.js, SearchPage.js, etc.
```

## What's Been Implemented (Session 17 - Feb 2026)

### 5. CAEN Codes Import & Cleanup
- Imported CAEN Rev.2 & Rev.3 codes (615 -> 1330 docs, script: `import_caen_codes.py`)
- Updated 380 CAEN Rev.1 descriptions from generic to proper Romanian (script: `update_caen_rev1_descriptions.py`)
- Upserted 15 new Rev.1 codes missing from DB
- Final: 1345 total CAEN codes, 1066 with valid descriptions
- 279 remaining generic = section/division-level codes (not used by any firm)

### 6. Admin CAEN Management Page (`/admin/caen`)
- **Stats dashboard**: Total codes, valid descriptions, generic, used by firms
- **Rev.1 Update button**: Run batch update from UI (replaces generic with proper Romanian descriptions)
- **CAEN codes table**: Paginated (50/page, 27 pages), searchable by cod/denumire, filterable (Toate/Valide/Generice)
- **Inline editing**: Click edit icon -> modify name/sectiune -> save
- **Add new code**: Form with cod, denumire, sectiune (auto-detect section letter)
- **Delete with confirmation**: Two-step delete (click -> confirm)
- **CSV Import**: Upload CSV with cod;name;sectiune columns, auto-detect delimiter (comma/semicolon/tab), template download
- Backend: `/app/backend/routes/admin_caen_routes.py` (7 endpoints)
- Frontend: `/app/frontend/src/pages/AdminCaenPage.js`
- Navigation: Sidebar -> Baza de Date -> Coduri CAEN

## What's Been Implemented (Session 16 - April 2026)

### 1. Question Mark Normalization (? -> S/T)
- Smart heuristic `_guess_qmark()` with Romanian linguistic rules
- Endpoints: preview + normalize
- 230 firms auto-fixed, 84 more identified with word-end patterns

### 2. server.py Refactoring (603 -> 115 lines)
- Extracted to: search_routes.py, company_routes.py, geo_routes.py
- Clean separation of concerns

### 3. Auto-Indexing After Sync
- After run_full_sync(), 12 RECOMMENDED_INDEXES auto-created

### 4. AI SEO Text Generation (Gemini Flash)
- Batch processing with configurable concurrency (1-10 parallel)
- Background async task with start/stop/status
- Preview per company (no save)
- Companies processed by revenue (biggest first)
- SEO text displayed on company page + used as meta description
- Admin page: /admin/seo-gen with stats, progress bar, ETA, preview
- 7 companies successfully generated (test runs)
- User's own Google API key configured

## Key API Endpoints
- `GET /api/search` - Search companies
- `GET /api/company/cui/{cui}` - Company by CUI ($or int/str)
- `GET /api/admin/seo-gen/status` - Generation status
- `POST /api/admin/seo-gen/start` - Start batch ({concurrency, limit})
- `POST /api/admin/seo-gen/stop` - Stop generation
- `GET /api/admin/seo-gen/preview/{cui}` - Preview for one company
- `GET /api/admin/db/qmark-preview` - Preview qmark fixes
- `POST /api/admin/db/qmark-normalize` - Apply qmark fixes

## Prioritized Backlog

### P1 (High Priority)
- [ ] Integrate Stripe checkout for credits (currently MOCKED)
- [ ] Script preluare detalii dosare Portal JUST (parti/sedinte)

### P2 (Medium Priority)
- [ ] Admin subscription management
- [ ] Export CSV/JSON

### P3 (Future)
- [ ] Email alerts
- [ ] Company comparison tool
- [ ] Industry analytics dashboard

## Notes for Next Developer
1. CUI queries: MUST use `$or` with `str(cui)` and `int(cui)`
2. Frontend: use `yarn` only (npm breaks build)
3. Admin: admin@mfirme.ro / Admin123!
4. Stripe checkout: MOCKED
5. Elasticsearch indexes ALL companies (not just active)
6. Auto-indexing runs after every sync
7. Gemini API key: configured in backend/.env as GEMINI_API_KEY
8. SEO batch generation: runs as background task, survives only within same process (restarts reset state)
