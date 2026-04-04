# RapoarteFirme Platform - Product Requirements Document

## Original Problem Statement
Construieste o platforma completa pentru afisarea firmelor romanesti (RapoarteFirme, domeniu: rapoartefirme.ro), bazata pe date publice agregate (1.2 milioane active, peste 3.5 milioane total). Platforma necesita 3 zone distincte: Site public, Zona User (autentificare, planuri), si Zona Admin. Sistem de abonamente cu limitari de date. Migrare catre o Arhitectura Hibrida (MongoDB local pentru viteza, sincronizat cu baza de date principala din Cloud). Adaugare API Keys management, motor de cautare Elasticsearch, sistem SEO dinamic, Generator Dinamic de Sitemap XML, analiza financiara pentru contabili, navigare pe judete/localitati si coduri CAEN, plus integrare dosare Portal JUST si date BPI pe pagina firmei.

## Tech Stack
- **Backend**: FastAPI, PyMongo, Motor (async MongoDB)
- **Frontend**: React, Tailwind CSS, Recharts, Shadcn/UI
- **Database**: MongoDB (dual DB setup - local + cloud)
- **Authentication**: JWT
- **Search**: Elasticsearch

## What's Been Implemented

### Sessions 1-10 - Core Platform
- Search, company profiles, user auth (JWT), favorites, admin dashboard
- Financial charts, KPIs, CAEN codes, postal codes
- Credits system, hybrid database architecture
- Dynamic SEO templates, financial analysis for accountants
- Legal info (JUST + BPI), locations/CAEN navigation
- Full sync Atlas->Local (2.38M firme)

### Session 11 - Bug Fixes + Rebranding + Docker
- LegalInfo expand fix, mFirme->RapoarteFirme rebranding
- Docker production setup (5 services)

### Session 12 - PageSpeed Optimization
- React.lazy() code splitting, font optimization, nginx gzip/cache

### Session 13 - Top Firme
- Top companies ranking per county/locality/CAEN with pagination and sorting

### Session 14 - DB Optimization Admin
- 12 recommended indexes, health score, diacritics normalization (ş→ș, ţ→ț)
- In-memory cache for heavy aggregations (24s→0.14s)
- Docker production tuning for 128GB RAM server

### Session 15 - CUI Type Fix + SEO
- Fix CUI int/string mismatch in MongoDB queries ($or fallback)
- Complete SEO tags (Helmet, canonical, meta descriptions) on all pages
- Sitemap XML expanded to all 2.38M companies

### Session 16 (Current) - Question Mark Normalization
**Date: April 2026**
- BACKEND: Smart heuristic function `_guess_qmark()` that determines if `?` should be `Ș` or `Ț` based on linguistic context (position, surrounding characters, Romanian language rules)
- BACKEND: `_is_real_qmark()` function that distinguishes real question marks (like "AUZI ? PRODUCTIONS SRL") from corrupted diacritics
- BACKEND: Endpoints `GET /api/admin/db/qmark-preview` and `POST /api/admin/db/qmark-normalize` with confidence levels (high/medium/low)
- FRONTEND: New "Corectare Caractere Corupte (?)" section in AdminDbOptimizePage with scan button, confidence filters, preview table, and apply button
- RESULTS: First batch fixed 230 firms automatically. Second batch identified 84 more (word-end patterns). Only 4 records with real `?` marks correctly skipped.
- Confidence: 57 high, 26 medium, 1 low (false positive: `MA + MA WHAT? SRL`)

## Database Schema

### mfirme_local (Local MongoDB - PRIMARY reads)
- `firme` - 2,381,831 companies. CUI is mixed-type (str/int). 12 custom indexes.
- `bilanturi` - Financial data (firma_id -> firme.id)
- `dosare` - Court cases
- `bpi_records` - BPI insolvency records
- `caen_codes` - 615 CAEN Rev.2 codes
- `postal_codes` - 55,123 Romanian postal codes

### mfirme_app (Read-Write)
- `users`, `company_overrides`, `audit_logs`, `user_credits`, `app_settings`, `credit_transactions`, `seo_settings`, `api_keys`

## Key API Endpoints
- `GET /api/search` - Search companies
- `GET /api/company/cui/{cui}` - Get company by CUI ($or int/str)
- `GET /api/locations/judet/{slug}/top-firme` - Top companies per county
- `GET /api/admin/db/stats` - DB statistics
- `GET /api/admin/db/qmark-preview` - Preview ? → Ș/Ț replacements
- `POST /api/admin/db/qmark-normalize` - Apply replacements
- `GET /api/sitemap/index.xml` - Sitemap index

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
- [ ] Auto-index after sync_all

## Notes for Next Developer
1. CUI queries MUST use `$or` with both `str(cui)` and `int(cui)` — Atlas stores CUI as integer
2. Use `yarn` for frontend deps (npm breaks build)
3. Admin: admin@mfirme.ro / Admin123!
4. Stripe checkout is MOCKED
5. `server.py` is 600+ lines — needs refactoring into routes/
6. Elasticsearch indexes ALL companies (not just active)
7. Question mark normalization: 230 fixed automatically, 84 remaining need admin review via Admin > Baza de Date > Optimizare DB
