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
- `user_credits` - User credit balances and viewed companies (NEW)
- `app_settings` - System-wide settings (NEW)
- `credit_transactions` - Credit purchase logs (NEW)

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

## Prioritized Backlog

### P0 (Critical) - DONE
- ✅ Financial chart with dual lines
- ✅ Postal codes integration
- ✅ CAEN codes integration with descriptions
- ✅ Credits system with daily free views
- ✅ Admin toggle for credits system

### P1 (High Priority)
- [ ] Integrate Stripe checkout for credit purchases (currently simulated)
- [ ] Complete Stripe payment flow verification for subscriptions
- [ ] API key management for premium users
- [ ] Admin subscription management

### P2 (Medium Priority)
- [ ] Advanced search engine migration (Elasticsearch)
- [ ] Bulk SEO metadata editing
- [ ] Export functionality

### P3 (Future/Nice to Have)
- [ ] Company comparison tool
- [ ] Industry analytics dashboard
- [ ] Mobile app

## File Structure
```
/app
├── backend/
│   ├── server.py (main FastAPI app)
│   ├── database.py (dual DB connections)
│   ├── routes/
│   │   ├── credits_routes.py (NEW - credits system)
│   │   ├── postal_routes.py
│   │   ├── admin_routes.py (UPDATED - toggle + stats)
│   │   └── ...
│   └── scripts/
│       ├── import_postal_codes.py
│       └── import_caen_codes.py
└── frontend/
    └── src/
        ├── contexts/
        │   ├── AuthContext.js
        │   └── CreditsContext.js (NEW)
        ├── components/
        │   ├── FinancialChart.js
        │   ├── Header.js (UPDATED - credits badge)
        │   └── NoCreditsModal.js (NEW)
        └── pages/
            ├── CompanyPage.js (UPDATED - credit consumption)
            ├── CreditsPage.js (NEW)
            └── AdminDashboardPage.js (UPDATED - toggle)
```

## Notes for Next Developer
1. Financial data mapping: `firme.id` → `bilanturi.firma_id`
2. Always use `venituri_totale` as fallback for `cifra_afaceri`
3. Postal code normalization handles: diacritics, "MUNICIPIUL/SECTOR" prefixes, București sectors
4. Never write to `justportal` - use `company_overrides` for admin edits
5. User speaks Romanian - keep UI text in Romanian
6. CAEN lookup: strip to 4 digits and query `caen_codes.cod`
7. PyMongo warning: Never use `if db:` - use `if db is not None:` to avoid NotImplementedError
