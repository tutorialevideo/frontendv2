# RapoarteFirme Platform - Product Requirements Document

## Original Problem Statement
Construieste o platforma completa pentru afisarea firmelor romanesti (RapoarteFirme, domeniu: rapoartefirme.ro), bazata pe date publice agregate (1.2 milioane active, peste 3.5 milioane total). Platforma necesita 3 zone distincte: Site public, Zona User (autentificare, planuri), si Zona Admin. Sistem de abonamente cu limitari de date. Migrare catre o Arhitectura Hibrida (MongoDB local pentru viteza, sincronizat cu baza de date principala din Cloud). Adaugare API Keys management, motor de cautare Elasticsearch, sistem SEO dinamic, Generator Dinamic de Sitemap XML, analiza financiara pentru contabili, navigare pe judete/localitati si coduri CAEN, plus integrare dosare Portal JUST si date BPI pe pagina firmei.

## Tech Stack
- **Backend**: FastAPI, PyMongo, Motor (async MongoDB)
- **Frontend**: React, Tailwind CSS, Recharts, Shadcn/UI
- **Database**: MongoDB (dual DB setup - local + cloud)
- **Authentication**: JWT
- **Search**: Elasticsearch

## Architecture (after refactoring)
```
/app/backend/
  server.py              (~107 lines - orchestration only)
  database.py            (DB connections)
  auth.py                (JWT auth)
  utils.py               (helpers)
  routes/
    search_routes.py     (NEW - search + suggest)
    company_routes.py    (NEW - company CUI/slug/financials)
    geo_routes.py        (NEW - judete/localitati/caen/stats)
    admin_sync_routes.py (+ auto-indexing after sync)
    admin_db_routes.py   (DB optimization + qmark normalization)
    location_routes.py   (location pages + top firme)
    caen_routes.py       (CAEN pages)
    financial_routes.py  (financial detail routes)
    legal_routes.py      (legal/court/BPI routes)
    sitemap_routes.py    (XML sitemap generation)
    seo_routes.py        (SEO templates)
    auth_routes.py       (login/register)
    ... (other admin/user routes)
```

## What's Been Implemented

### Sessions 1-15 - Core Platform + All Features
(See previous PRD entries)

### Session 16 - Question Mark Normalization + Refactoring
**Date: April 2026**

#### Question Mark Normalization (? -> S/T)
- Smart heuristic `_guess_qmark()` with linguistic context rules
- `_is_real_qmark()` to skip real question marks
- Endpoints: `GET /api/admin/db/qmark-preview`, `POST /api/admin/db/qmark-normalize`
- Frontend: "Corectare Caractere Corupte (?)" section in Admin DB Optimize
- Results: 230 firms auto-fixed, 84 more identified (word-end patterns)

#### server.py Refactoring (603 -> 107 lines)
- Extracted search endpoints to `routes/search_routes.py`
- Extracted company endpoints to `routes/company_routes.py`
- Extracted geo/stats endpoints to `routes/geo_routes.py`
- server.py now contains only app creation, middleware, router includes, and sitemap aliases

#### Auto-Indexing After Sync
- After `run_full_sync()` completes, all 12 RECOMMENDED_INDEXES are auto-created
- Only creates indexes that don't already exist (safe for re-runs)
- Logged in sync state for admin visibility

## Key API Endpoints
- `GET /api/search` - Search companies (search_routes.py)
- `GET /api/search/suggest` - Autocomplete (search_routes.py)
- `GET /api/company/cui/{cui}` - Company by CUI (company_routes.py)
- `GET /api/company/slug/{slug}` - Company by slug (company_routes.py)
- `GET /api/company/{cui}/financials` - Financial data (company_routes.py)
- `GET /api/geo/judete` - Counties list (geo_routes.py)
- `GET /api/geo/localitati` - Localities list (geo_routes.py)
- `GET /api/caen/top` - Top CAEN codes (geo_routes.py)
- `GET /api/stats/overview` - Platform stats (geo_routes.py)
- `GET /api/admin/db/stats` - DB health (admin_db_routes.py)
- `GET /api/admin/db/qmark-preview` - Preview qmark fixes (admin_db_routes.py)
- `POST /api/admin/db/qmark-normalize` - Apply qmark fixes (admin_db_routes.py)
- `GET /api/sitemap.xml` - Sitemap index

## Database Schema
- `firme`: 2,381,831 companies. CUI mixed-type (str/int). 12+ indexes.
- `bilanturi`: Financial data
- `dosare`: Court cases
- `bpi_records`: BPI insolvency
- `caen_codes`: 615 CAEN Rev.2 codes
- `postal_codes`: 55,123 postal codes

## Prioritized Backlog

### P1 (High Priority)
- [ ] Integrate Stripe checkout for credit purchases (currently MOCKED)
- [ ] Script preluare detalii dosare Portal JUST (parti/sedinte)

### P2 (Medium Priority)
- [ ] AI-generated SEO text for companies
- [ ] Admin subscription management
- [ ] Export CSV/JSON

### P3 (Future/Nice to Have)
- [ ] Email alerts for company indicator changes
- [ ] Company comparison tool
- [ ] Industry analytics dashboard

## Notes for Next Developer
1. CUI queries MUST use `$or` with both `str(cui)` and `int(cui)` — Atlas stores CUI as integer
2. Use `yarn` for frontend deps (npm breaks build)
3. Admin: admin@mfirme.ro / Admin123!
4. Stripe checkout is MOCKED
5. Elasticsearch indexes ALL companies (not just active)
6. Auto-indexing runs after every sync (RECOMMENDED_INDEXES from admin_db_routes.py)
