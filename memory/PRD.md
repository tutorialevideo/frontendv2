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

### Session 1 - Core MVP
- Basic search and company profile pages
- User authentication system (JWT)
- Favorites functionality
- Admin login and basic dashboard

### Session 2 - Financial Charts + Postal Codes
- Financial Chart with Dual Lines (Cifra de afaceri + Profit net)
- 3 KPI cards showing latest year data with growth percentages
- Romanian Postal Codes Integration (55,123 codes)

### Session 3 - CAEN Codes Integration
- 615 CAEN Rev.2 codes from ONRC
- Auto-lookup of CAEN description in company API

### Session 4 - Credits System
- Credits + Daily Free Views System (10 bonus credits at registration, 5 free/day)
- Admin Toggle for Credits System
- Credit packages (50/200/500 credits)

### Session 5 - Hybrid Database Architecture
- Local MongoDB for Fast Reads (1.2M firme + 413K bilanturi)
- Direct Sync endpoint
- Admin Sync Dashboard

### Session 6 - Bug Fix & API Utilities
- Fixed JSON Parsing Error
- Created API Utility Functions (safeJsonParse, safeFetch, createApiClient)

### Session 7 - Dynamic SEO Templates
- SEO Templates Admin Page (6 page types)
- Dynamic Variables System
- SEO Hook for Frontend
- JSON-LD Structured Data (HomePage, CompanyPage, SearchPage)

### Session 8 - Analiza Financiara pentru Contabili
- Financial Indicators API (ROA, ROE, lichiditate, solvabilitate, etc.)
- Health Score 0-100
- FinancialIndicators Component pe pagina firmei
- Admin Financial Dashboard
- Raport PDF/HTML descarcabil

### Session 9 - Legal Info Integration + Admin Filters
- LegalInfo Component on CompanyPage (Dosare JUST + BPI)
- Admin: Filtrare Firme Radiate & Date Incomplete (4 filtre)
- 4 API endpoints legal

### Session 10 - Locations, CAEN Nav, Legal Flags, Full Sync
- Navigare Firme pe Judete/Localitati (pagini dedicate)
- Browsing Firme pe Coduri CAEN
- Pre-compute legal flags (has_dosare, dosare_count, has_bpi, bpi_count)
- Sync complet Atlas -> Local (2.38M firme, 3.5M dosare, 235K bpi)
- Linkuri clickabile judet/localitate/CAEN din profilul firmei
- Generator Dinamic Sitemap XML

### Session 11 (Current) - Bug Fix LegalInfo Expand + Rebranding + Docker Production
**Date: April 2026**
- FIX: Backend legal_routes.py - mapare corecta campuri (stadiu, categorie, materie, data_modificare)
- FIX: Frontend LegalInfo.js - expand dosar arata acum Categorie, Stadiu, Materie, Ultima actualizare
- FIX: Mesaj informativ cand parti/sedinte lipsesc din DB
- FIX: Timeline sedinte cu design vertical (border-left + cercuri)
- REBRANDING: mFirme -> RapoarteFirme (rapoartefirme.ro)
  - Header logo: R + RapoarteFirme
  - Footer: RapoarteFirme
  - Admin: RapoarteFirme Admin
  - Toate titlurile paginilor actualizate (| RapoarteFirme)
  - JSON-LD: rapoartefirme.ro
  - SEO templates default: RapoarteFirme.ro
  - Sitemap URL: rapoartefirme.ro
  - robots.txt: rapoartefirme.ro
  - Backend API title: RapoarteFirme API
  - Raport financiar footer: RapoarteFirme.ro
  - Stripe plan name: RapoarteFirme
  - Nu s-au schimbat: DB names (mfirme_local, mfirme_app), email admin (admin@mfirme.ro), ES index (mfirme_companies)
- DOCKER PRODUCTION READY:
  - docker-compose.production.yml - 5 servicii: MongoDB, Elasticsearch, Backend, Frontend, Nginx
  - backend/Dockerfile.production - Python 3.11, uvicorn cu 4 workers
  - frontend/Dockerfile.production - yarn build + nginx alpine
  - nginx/nginx.conf - Reverse proxy cu sitemap URL masking, rate limiting, SSL ready
  - frontend/nginx.conf - SPA fallback + API proxy + sitemap proxy
  - requirements.docker.txt - Dependinte actualizate si curate
  - .env.example - Template producție
  - setup-production.sh - Script one-command setup
  - DEPLOYMENT.md - Ghid complet deployment, SSL, backup/restore

### Session 12 - PageSpeed Optimization
**Date: April 2026**
- CODE SPLITTING: React.lazy() + Suspense pe toate cele 25+ pagini din App.js
- LAZY LOADING: FinancialChart (Recharts), LegalInfo, FinancialIndicators se incarca on-demand pe CompanyPage
- FONT OPTIMIZATION: Mutat Google Fonts din CSS @import (render-blocking) in HTML link tags cu preconnect
- NGINX GZIP: Redus gzip_min_length de la 1024 la 256, adaugat gzip_comp_level 6, extins gzip_types
- NGINX CACHE: Adaugat Cache-Control headers (1y, immutable) pentru assets statice in nginx.conf productie
- CLEANUP: Eliminat badge Emergent din index.html, eliminat font Inter nefolosit, setat lang="ro"
- Bundle main.js redus la ~278K (de la estimat 600K+ monolitic), Recharts in chunk separat 380K

### Session 13 - Top Firme pe Judete/Localitati/CAEN
**Date: April 2026**
- BACKEND: Endpoint nou GET /api/locations/judet/{slug}/top-firme cu paginare si sortare (cifra_afaceri, profit, angajati)
- BACKEND: Parametru sort adaugat pe /api/locations/judet/{slug}/{localitate} si /api/caen/code/{cod}
- FRONTEND JudetPage: Sistem tab-uri (Top Firme / Localitati), tabel rankat cu medalii podium top 3, paginare top 100/pagina
- FRONTEND LocalitatePage: Butoane sortare (Cifra afaceri, Angajati, A-Z), implicit sortare dupa cifra afaceri
- FRONTEND CaenPage: Butoane sortare (Cifra afaceri, Angajati, A-Z), implicit sortare dupa cifra afaceri

### Session 14 - Optimizare DB Admin Page + Indexuri Auto
**Date: April 2026**
- BACKEND: Endpoint-uri noi GET /api/admin/db/stats, POST /api/admin/db/create-index, POST /api/admin/db/create-all-indexes
- BACKEND: 12 indexuri recomandate predefinite (judet, localitate, caen, cifra_afaceri, profit, angajati, compuse, dosare.cui, bpi.cui, users.email)
- FRONTEND: Pagina AdminDbOptimizePage cu scor sanatate, carduri statistici, lista indexuri lipsa/active, detalii colectii expandabile
- SIDEBAR: 'Sincronizare DB' transformat in dropdown 'Baza de Date' cu sub-items: Sincronizare + Optimizare DB
- Toate 12 indexurile au fost create cu succes dupa testare, scor sanatate 100%
- Raspuns la intrebarea user: Top Firme se sincronizeaza automat dupa fiecare import (sortarea e dinamica)

## Database Schema

### mfirme_local (Local MongoDB - PRIMARY reads)
- `firme` - Company data + pre-computed flags (has_dosare, dosare_count, has_bpi, bpi_count, has_legal_issues)
- `bilanturi` - Financial data (firma_id -> firme.id)
- `dosare` - Court cases (firma_id, numar_dosar, institutie, obiect, stadiu, categorie, materie)
- `bpi_records` - BPI insolvency records
- `lichidatori` - Liquidators
- `caen_codes` - 615 CAEN Rev.2 codes
- `postal_codes` - 55,123 Romanian postal codes
- `localities` - 13,856 aggregated locality records
- `sync_status` - Tracks last sync per collection

### mfirme_app (Read-Write)
- `users` - User accounts
- `company_overrides` - Admin manual edits
- `audit_logs` - Admin action tracking
- `user_credits` - User credit balances and viewed companies
- `app_settings` - System-wide settings
- `credit_transactions` - Credit purchase logs
- `seo_settings` - SEO templates per page type
- `api_keys` - API keys for premium users

## Key API Endpoints
- `GET /api/search` - Search companies
- `GET /api/company/cui/{cui}` - Get company by CUI
- `GET /api/company/{cui}/financials` - Get multi-year financial data
- `GET /api/legal/summary/{cui}` - Legal summary
- `GET /api/legal/dosare/{cui}` - Court cases with details
- `GET /api/legal/bpi/{cui}` - BPI records
- `GET /api/financial/indicators/{cui}` - Financial indicators
- `GET /api/locations/judete` - Counties
- `GET /api/locations/judet/{slug}/top-firme` - Top companies per county (sorted, paginated)
- `GET /api/caen/codes` - CAEN codes
- `GET /api/seo/templates/public` - SEO templates
- `GET /api/sitemap/index.xml` - Sitemap index

## Prioritized Backlog

### P1 (High Priority)
- [ ] Integrate Stripe checkout for credit purchases (currently MOCKED)
- [ ] Complete Stripe payment flow verification
- [ ] Admin subscription management

### P2 (Medium Priority)
- [ ] AI-generated SEO text for companies
- [ ] Export CSV/JSON
- [ ] Bulk SEO metadata editing
- [ ] VPC Architecture (separate DB server)

### P3 (Future/Nice to Have)
- [ ] Email alerts for company indicator changes
- [x] "Top Firme" sorting on judet/localitate/CAEN pages
- [ ] Badge rosu/verde on search cards for has_legal_issues
- [ ] Company comparison tool
- [ ] Industry analytics dashboard
- [ ] Automate precompute_legal_flags.py post-sync

## Notes for Next Developer
1. Financial data mapping: `firme.id` -> `bilanturi.firma_id`
2. Always use `venituri_totale` as fallback for `cifra_afaceri`
3. Postal code normalization handles: diacritics, MUNICIPIUL/SECTOR prefixes
4. Never write to `justportal` - use `company_overrides` for admin edits
5. User speaks Romanian - keep UI text in Romanian
6. CAEN lookup: strip to 4 digits and query `caen_codes.cod`
7. PyMongo warning: Never use `if db:` - use `if db is not None:`
8. JSON Parsing: Always use safe JSON parsing pattern (parse once into variable)
9. Admin credentials: admin@mfirme.ro / Admin123!
10. Dosare in local DB have fields: id, firma_id, numar_dosar, institutie, obiect, data_dosar, stadiu, categorie, materie. Fields `parti` and `sedinte` are NOT currently populated.
11. Stripe checkout is MOCKED - not yet integrated with real Stripe API
