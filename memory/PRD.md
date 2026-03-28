# mFirme Platform - Product Requirements Document

## Original Problem Statement
Construiește o platformă completă pentru afișarea firmelor românești (mFirme), bazată pe date publice agregate (1.2 milioane firme). Platforma necesită 3 zone distincte: 
- Site public (optimizat SEO, căutare rapidă)
- Zonă User (autentificare, planuri gratuite/premium, favorite)
- Zonă Admin

Trebuie inclus un sistem de abonamente cu limitări de date și plăți. Baza de date a firmelor actualizată automat nu trebuie suprascrisă de editările manuale din admin.

## Core Requirements
- Afișare firme românești cu date publice din Ministerul Finanțelor
- Dual database architecture: read-only (`justportal`) + read-write (`mfirme_app`)
- Grafice financiare multi-anuale cu date reale din colecția `bilanturi`
- Admin panel pentru overrides manuale (non-destructive)
- Sistem de coduri poștale pentru match automat cu localitățile firmelor

## Tech Stack
- **Backend**: FastAPI, PyMongo, Motor (async MongoDB)
- **Frontend**: React, Tailwind CSS, Recharts
- **Database**: MongoDB (dual DB setup)
- **Authentication**: JWT

## What's Been Implemented

### Session 1 (Previous) - Core MVP
- ✅ Basic search and company profile pages
- ✅ User authentication system
- ✅ Favorites functionality
- ✅ Admin login and basic dashboard

### Session 2 - Financial Charts + Postal Codes
**Date: March 2026**

#### Completed Features:
1. **Financial Chart with Dual Lines** (P0)
   - Displays Cifra de afaceri (Turnover) AND Profit net simultaneously on same graph
   - 3 KPI cards showing latest year data with growth percentages
   - Year-by-year data table
   - Real data from `bilanturi` collection (not approximated)

2. **Romanian Postal Codes Integration** (NEW)
   - Imported 55,123 postal codes from GitHub source
   - Created 13,856 unique localities mapping
   - Auto-matching of postal codes to company locations
   - Special handling for București sectors (SECTORUL 1 → SECTOR1)
   - API endpoints: `/api/postal/search`, `/api/postal/localities`, `/api/postal/match/company/{cui}`
   - Postal code displayed in company header and address section

3. **Bug Fixes from Previous Session**
   - Fixed Auth bug ("body stream already read")
   - Fixed Admin login redirection
   - Fixed React Helmet crash on SearchPage

### Session 3 - CAEN Codes Integration
**Date: March 2026**

#### Completed Features:
1. **CAEN Rev.2 Codes Integration** (P0) ✅
   - Imported 615 CAEN codes from ONRC website
   - Created `caen_codes` collection with: cod, denumire, sectiune (A-U), sectiune_denumire
   - Auto-lookup of CAEN description in company API endpoints
   - Display on CompanyPage: code, full description, section badge
   - 21 economic sections mapped (Agricultură, Industrie, Comerț, IT etc.)

### Session 4 (Current) - Credits System
**Date: March 2026**

#### Completed Features:
1. **Credits + Daily Free Views System** (P0) ✅
   - User credits system: 10 bonus credits at registration
   - 5 free company views per day (reset at midnight)
   - Previously viewed companies are always free
   - Credit packages: 50 (9.99 RON), 200 (29.99 RON), 500 (59.99 RON)
   - Badge în header showing available credits + free views

2. **Admin Toggle for Credits System** ✅
   - Admin can enable/disable credits system with one click
   - When disabled, all company views are unlimited
   - Admin statistics: users with credits, credits in circulation, total views

3. **New Collections Created:**
   - `user_credits`: tracks balances, daily views, viewed companies
   - `app_settings`: stores system-wide settings like credits_system_enabled
   - `credit_transactions`: logs all credit purchases

4. **New API Endpoints:**
   - `GET /api/credits/status` - User credits balance
   - `POST /api/credits/check-access` - Check if user can view company
   - `POST /api/credits/consume` - Consume credit for company view
   - `GET /api/credits/packages` - Available credit packages
   - `POST /api/admin/settings/credits-system/toggle` - Toggle credits on/off
   - `GET /api/admin/credits/stats` - Credits system statistics

5. **New Frontend Components:**
   - `CreditsContext.js` - Global credits state management
   - `NoCreditsModal.js` - Modal when credits depleted
   - `CreditsPage.js` - Page to purchase credits
   - Updated `Header.js` with credits badge
   - Updated `AdminDashboardPage.js` with toggle button

### Session 5 - Hybrid Database Architecture
**Date: March 2026**

#### Completed Features:
1. **Local MongoDB for Fast Reads** ✅
   - Aplicația rulează ÎNTOTDEAUNA pe MongoDB local
   - Cloud-ul este folosit DOAR ca sursă pentru sincronizare
   - 1.2M firme + 413K bilanțuri sincronizate cu succes

2. **Direct Sync în Backend** ✅ (NEW)
   - Endpoint `/api/admin/sync/direct-sync` pentru sincronizare directă
   - Nu mai necesită sync-service separat
   - Progress bar în timp real cu procentaj
   - Sync în background cu BackgroundTasks
   - ~50K documente/secundă viteza de sync

3. **Admin Sync Dashboard** ✅
   - Pagină dedicată `/admin/sync` cu AdminLayout
   - Afișare progress în timp real cu progress bar
   - Statistici per colecție (documente, ultima sincronizare)
   - Butoane: Sync Complet, Sync Firme, Sync Bilanțuri

4. **Architecture:**
```
Backend (FastAPI):
├── database.py (local + cloud connections)
├── routes/admin_sync_routes.py (direct sync logic)
└── All reads from local MongoDB

MongoDB:
├── mfirme_local (1.2M firme, 413K bilanturi) - PRIMARY
├── mfirme_app (users, settings)
└── Cloud Atlas (sync source only)
```

### Session 6 - Bug Fix & API Utilities
**Date: March 2026**

#### Completed Features:
1. **Fixed JSON Parsing Error** ✅
   - Fixed recurring "Body has already been consumed" error in `AdminSyncPage.js`
   - Applied safe JSON parsing pattern: parse once, use variable
   - All sync functions now handle JSON parsing errors gracefully

2. **Created API Utility Functions** ✅
   - New file: `/app/frontend/src/utils/api.js`
   - `safeJsonParse()` - Safe single-parse JSON extraction
   - `safeFetch()` - Fetch wrapper with automatic safe parsing
   - `createApiClient()` - Authenticated API client factory

### Session 7 (Current) - Dynamic SEO Templates
**Date: March 2026**

#### Completed Features:
1. **SEO Templates Admin Page** ✅
   - New admin page `/admin/seo` for managing SEO templates
   - 6 page types: Company, Search, CAEN Category, Homepage, Județ, Localitate
   - Live preview of templates with sample data
   - Toggle index/noindex per page type
   - Save and Reset to default functionality

2. **Dynamic Variables System** ✅
   - Variables: `{DENUMIRE}`, `{CUI}`, `{LOCALITATE}`, `{JUDET}`, `{CAEN}`, `{CAEN_DESCRIERE}`, `{QUERY}`, `{AN}`, `{CIFRA_AFACERI}`, `{PROFIT}`
   - Auto-replacement in title and description templates
   - Context-aware variables (each page type has relevant variables)

3. **SEO Hook for Frontend** ✅
   - New hook: `/app/frontend/src/hooks/useSeoTemplate.js`
   - Caches templates for 5 minutes
   - Applied to: HomePage, SearchPage, CompanyPage
   - Fallback to hardcoded values if API fails

4. **Backend SEO Routes** ✅
   - `GET /api/seo/templates/public` - Get all templates (public)
   - `GET /api/seo/template/{page_type}` - Get specific template
   - `PUT /api/seo/admin/template/{page_type}` - Update template (admin)
   - `POST /api/seo/admin/reset/{page_type}` - Reset to default (admin)
   - `POST /api/seo/preview` - Preview template with sample data

5. **MongoDB Collection** ✅
   - New collection: `seo_settings` in mfirme_app database
   - Stores custom templates per page type
   - Audit logging for admin changes

6. **JSON-LD Structured Data** ✅
   - **HomePage**: WebSite schema + Organization schema + SearchAction
   - **CompanyPage**: Organization/LocalBusiness schema cu adresă, CUI, contact
   - **SearchPage**: ItemList schema cu rezultatele căutării
   - Ajută Google să afișeze Rich Results în SERP

### Session 8 (Current) - Analiză Financiară pentru Contabili
**Date: March 2026**

#### Completed Features:
1. **Financial Indicators API** (`/api/financial/*`) ✅
   - `GET /api/financial/indicators/{cui}` - Toți indicatorii pentru o firmă
   - `GET /api/financial/indicators/{cui}/pdf` - Raport HTML/PDF descărcabil
   - `GET /api/financial/industry/{caen}` - Statistici agregate per industrie
   - `GET /api/financial/compare/{cui}` - Comparare firmă vs industrie
   - `GET /api/financial/admin/dashboard` - Dashboard admin

2. **Indicatori Calculați** ✅
   - **Profitabilitate**: Marja profit brut/net, ROA, ROE, Rentabilitate economică
   - **Lichiditate**: Curentă, Rapidă (Test Acid), Imediată (Cash Ratio)
   - **Solvabilitate**: Rata îndatorării, Autonomie financiară, Levier, Solvabilitate generală
   - **Eficiență**: Productivitate muncii, Profit/angajat, Rata cheltuielilor
   - **Health Score**: Scor 0-100 cu rating (Excelent/Bun/Mediu/Slab)

3. **FinancialIndicators Component** ✅
   - Secțiune nouă pe pagina firmei
   - Card gradient cu Health Score
   - 4 quick stats (Cifră afaceri, Profit, Active, Capitaluri)
   - Secțiuni expandabile pentru fiecare categorie
   - Rating color-coded pentru fiecare indicator
   - Buton "Descarcă Raport"

4. **Admin Financial Dashboard** (`/admin/financial`) ✅
   - Statistici agregate (119K firme, 196 mld RON CA, 413K angajați)
   - Pie charts pentru firme profitabile vs pierdere
   - Top 10 industrii cu CA, angajați și marjă profit
   - Top 10 județe cu grafic bară

5. **Raport PDF/HTML** ✅
   - Template HTML complet cu stilizare print-friendly
   - Toate secțiunile de indicatori
   - Interpretări și rating-uri
   - Footer cu data generării

## Database Schema

### justportal (Read-Only)
- `firme` - Company master data (time-series collection)
- `bilanturi` - Financial data (firma_id → firme.id)

### mfirme_app (Read-Write)
- `users` - User accounts
- `company_overrides` - Admin manual edits
- `audit_logs` - Admin action tracking
- `postal_codes` - 55,123 Romanian postal codes
- `localities` - 13,856 aggregated locality records
- `caen_codes` - 615 CAEN Rev.2 codes with descriptions
- `user_credits` - User credit balances and viewed companies
- `app_settings` - System-wide settings
- `credit_transactions` - Credit purchase logs

### mfirme_local (NEW - Local MongoDB for fast reads)
- `firme` - Synced from cloud (1.2M companies)
- `bilanturi` - Synced from cloud (financial data)
- `caen_codes` - Synced from cloud
- `postal_codes` - Synced from cloud
- `localities` - Synced from cloud
- `sync_status` - Tracks last sync per collection

## Key API Endpoints

### Public
- `GET /api/search` - Search companies
- `GET /api/company/cui/{cui}` - Get company by CUI (includes auto postal code)
- `GET /api/company/slug/{slug}` - Get company by slug (includes auto postal code)
- `GET /api/company/{cui}/financials` - Get multi-year financial data

### Postal Codes
- `GET /api/postal/stats` - Statistics (55,123 codes, 13,856 localities, 42 counties)
- `GET /api/postal/search` - Search by code, locality, county
- `GET /api/postal/localities` - Get localities list
- `GET /api/postal/match/company/{cui}` - Find postal code for company

### Admin
- `POST /api/admin/companies/search` - Admin company search
- `PUT /api/admin/companies/{cui}/override` - Save manual override
- `POST /api/admin/settings/credits-system/toggle` - Toggle credits on/off

### Admin Sync (NEW)
- `GET /api/admin/sync/status` - Sync status (local vs cloud)
- `POST /api/admin/sync/trigger-full` - Start full sync (background)
- `POST /api/admin/sync/trigger-collection/{name}` - Sync single collection
- `POST /api/admin/sync/switch-mode` - Switch local/cloud mode
- `GET /api/admin/sync/local-stats` - Local DB statistics

### API Keys Management (NEW - Faza 6)
- `GET /api/api-keys/plans` - Get API plans (Basic, Pro, Enterprise)
- `GET /api/api-keys/my-keys` - Get user's API keys
- `POST /api/api-keys/create` - Create new API key
- `PUT /api/api-keys/{id}` - Update key (name, active status)
- `DELETE /api/api-keys/{id}` - Revoke API key
- `POST /api/api-keys/{id}/regenerate` - Regenerate API key
- `GET /api/api-keys/{id}/usage` - Get key usage stats
- `GET /api/api-keys/admin/all` - Admin: Get all keys
- `PUT /api/api-keys/admin/{id}/toggle` - Admin: Toggle key status

### Public API v1 (NEW - Faza 6)
- `GET /api/v1/health` - API health check (no auth)
- `GET /api/v1/company/{cui}` - Get company by CUI
- `GET /api/v1/company/{cui}/financials` - Get financial data (Pro+)
- `GET /api/v1/search` - Search companies
- `POST /api/v1/companies/bulk` - Bulk company lookup (Pro+)
- `GET /api/v1/geo/judete` - Get counties (Enterprise)
- `GET /api/v1/geo/localitati` - Get localities (Enterprise)
- `GET /api/v1/caen/{code}` - Get companies by CAEN (Enterprise)

### Elasticsearch (NEW - Faza 7)
- `GET /api/elasticsearch/status` - Get ES cluster & index status
- `GET /api/elasticsearch/config` - Get ES configuration info
- `POST /api/elasticsearch/create-index` - Create companies index
- `POST /api/elasticsearch/start-indexing` - Start background indexing
- `POST /api/elasticsearch/stop-indexing` - Stop indexing
- `DELETE /api/elasticsearch/delete-index` - Delete index
- `POST /api/elasticsearch/search` - Fuzzy search companies
- `GET /api/elasticsearch/search/simple` - Simple GET search endpoint

### SEO Templates (NEW - Faza 8)
- `GET /api/seo/templates/public` - Get all SEO templates (public)
- `GET /api/seo/template/{page_type}` - Get template for page type
- `GET /api/seo/admin/templates` - Get all templates with admin info
- `PUT /api/seo/admin/template/{page_type}` - Update template (admin)
- `POST /api/seo/admin/reset/{page_type}` - Reset to default (admin)
- `POST /api/seo/admin/reset-all` - Reset all templates (admin)
- `POST /api/seo/preview` - Preview template with sample data

## Prioritized Backlog

### P0 (Critical) - DONE
- ✅ Financial chart with dual lines
- ✅ Postal codes integration
- ✅ CAEN codes integration with descriptions
- ✅ Credits system with daily free views
- ✅ Admin toggle for credits system
- ✅ API key management for premium users (Faza 6)
- ✅ Elasticsearch integration for fuzzy search (Faza 7)
- ✅ Dynamic SEO Templates with admin control (Faza 8)

### P1 (High Priority)
- [ ] Integrate Stripe checkout for credit purchases (currently simulated)
- [ ] Complete Stripe payment flow verification for subscriptions
- [ ] Admin subscription management
- [ ] Test hybrid DB in production environment with real data

### P2 (Medium Priority)
- [ ] Bulk SEO metadata editing
- [ ] Export functionality (CSV/JSON)
- [ ] AI-generated SEO text pentru firme (template-uri inteligente)

### P3 (Future/Nice to Have)
- [ ] Company comparison tool
- [ ] Industry analytics dashboard
- [ ] Mobile app

## File Structure
```
/app
├── docker-compose.production.yml (NEW - production Docker config)
├── sync-service/ (NEW)
│   ├── sync_service.py (Change Streams + full sync)
│   ├── api.py (FastAPI endpoints for sync control)
│   ├── Dockerfile
│   └── requirements.txt
├── backend/
│   ├── server.py (main FastAPI app)
│   ├── database.py (UPDATED - dual DB support with fallback)
│   ├── routes/
│   │   ├── admin_sync_routes.py (NEW)
│   │   ├── credits_routes.py
│   │   ├── postal_routes.py
│   │   ├── admin_routes.py
│   │   └── ...
│   └── scripts/
│       ├── import_postal_codes.py
│       └── import_caen_codes.py
└── frontend/
    └── src/
        ├── contexts/
        │   ├── AuthContext.js
        │   └── CreditsContext.js
        ├── components/
        │   ├── AdminLayout.js (UPDATED - sync link)
        │   ├── FinancialChart.js
        │   ├── Header.js
        │   └── NoCreditsModal.js
        └── pages/
            ├── AdminSyncPage.js (NEW)
            ├── CompanyPage.js
            ├── CreditsPage.js
            └── AdminDashboardPage.js
```

## Notes for Next Developer
1. Financial data mapping: `firme.id` → `bilanturi.firma_id`
2. Always use `venituri_totale` as fallback for `cifra_afaceri`
3. Postal code normalization handles: diacritics, "MUNICIPIUL/SECTOR" prefixes, București sectors
4. Never write to `justportal` - use `company_overrides` for admin edits
5. User speaks Romanian - keep UI text in Romanian
6. CAEN lookup: strip to 4 digits and query `caen_codes.cod`
7. PyMongo warning: Never use `if db:` - use `if db is not None:` to avoid NotImplementedError
8. **Sync Service**: The `set_cloud_url` method in `/app/sync-service/sync_service.py` allows dynamic Cloud MongoDB URL updates from Admin UI
9. **Environment**: In preview environment, MongoDB local is used via `mongodb://localhost:27017/`. For production Docker, use `mongodb://mongodb-local:27017/`
10. **JSON Parsing**: Always use safe JSON parsing pattern - parse `res.json()` ONCE into a variable, then use that variable for both success and error handling. See `/app/frontend/src/utils/api.js` for utility functions.
11. **Admin credentials**: `admin@mfirme.ro` / `Admin123!`
