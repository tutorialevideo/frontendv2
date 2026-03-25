# mFirme — plan.md

## 1) Objectives
- Prove the **core workflow** works at scale: **MongoDB → Elasticsearch index → autocomplete/typo search + filters** with **<200ms** responses.
- Deliver an SEO-first MVP: homepage search, results, company profile, county/locality/CAEN pages, sitemaps, structured data.
- Establish a clean foundation for: accounts + subscriptions, admin overrides, and paid API.

---

## 2) Implementation Steps

### Phase 1 — Core Search POC (isolation; do not proceed until green)
**User stories**
1. As a developer, I can connect to MongoDB Atlas (`justportal.firme`) and stream documents reliably.
2. As a developer, I can run Elasticsearch in Docker and confirm health + index creation.
3. As a developer, I can bulk-index 10k companies with correct mappings/analyzers.
4. As a developer, I can query autocomplete with typo tolerance and get relevant results.
5. As a developer, I can apply filters (judet/localitate/CAEN) and get correct counts.
6. As a developer, I can measure p95 latency and confirm <200ms for typical queries.

**Steps**
- Web research: ES best practices for autocomplete + typo tolerance (edge-ngram vs completion suggester; multi-field analyzers; fuzziness).
- Docker compose: `elasticsearch` (+ `kibana` optional) + `redis`.
- Define ES index mapping:
  - Fields: `denumire`, `denumire_normalized`, `cui`, `cod_inregistrare`, `judet`, `localitate`, `anaf_cod_caen`, plus sortable numeric fields (`mf_cifra_afaceri`, `mf_profit_net`, `mf_numar_angajati`, `mf_an_bilant`).
  - Multi-fields for `denumire`: `search` (standard/romanian), `autocomplete` (edge-ngram), `keyword`.
  - Add normalizers for diacritics-folding where needed.
- Write `poc_index.py`:
  - Read 10k docs from MongoDB (projection of index fields only).
  - Transform + generate `slug` (name + cui) and canonical ids.
  - Bulk index with refresh disabled during ingest; then enable.
- Write `poc_query.py`:
  - Autocomplete endpoint simulation (prefix + fuzziness) + filters.
  - Capture timings, p50/p95; validate result relevance manually.
- Iterate until: relevance good, typo tolerance acceptable, latency budget met.

**Exit criteria (must pass)**
- Bulk index 10k docs completes without errors.
- Autocomplete returns results in <200ms p95 (local dev) for common queries.
- Filters work correctly and combine (judet+localitate+CAEN).

---

### Phase 2 — V1 Public MVP App (no auth yet; build around proven core)
**User stories**
1. As a visitor, I can search from the homepage with instant suggestions.
2. As a visitor, I can search by CUI / registration number and jump to the right firm.
3. As a visitor, I can filter results by judet/localitate/CAEN and keep the query in URL.
4. As a visitor, I can open a company profile page with clean sections and fast load.
5. As a visitor, I see masked premium fields with a clear “Upgrade” CTA.
6. As a visitor, I can browse `/judet/[slug]`, `/localitate/[slug]`, `/caen/[code]` pages.

**Backend (FastAPI)**
- Endpoints:
  - `GET /api/search/suggest?q=` (top 10)
  - `GET /api/search?q=&filters...&page=`
  - `GET /api/company/{cui}` and `GET /api/company/slug/{slug}`
  - `GET /api/geo/judete`, `GET /api/geo/localitati?judet=`
  - `GET /api/seo/sitemap-index.xml` + chunked sitemaps
- Implement **computed_profile** response layer:
  - `raw_data` from Mongo + later `manual_overrides`; for now just raw + masking rules.
  - Masking helpers for public tier (phone/admin etc.).
- Caching:
  - Redis cache for popular queries + category pages.
  - Basic rate limiting (public) to protect ES.

**Frontend (React)**
- Pages:
  - Home (hero search)
  - Results (filters sidebar, pagination, empty/loading states)
  - Company profile (tabs/sections; breadcrumbs)
  - County/Locality/CAEN listing pages
- SEO:
  - Per-route meta tags (title/description/canonical), JSON-LD (Organization/LocalBusiness + Breadcrumb).
  - Generate sitemaps via backend and link in `robots.txt`.

**Phase exit testing**
- One end-to-end pass: search → results → filters → profile → category pages.
- Performance spot-check: repeated searches under load (basic concurrency).

---

### Phase 3 — Accounts + Subscriptions + Premium gating
**User stories**
1. As a visitor, I can register/login and keep my session secure.
2. As a free user, I can save favorites and view them later.
3. As a free user, I see premium fields locked with upgrade prompts.
4. As a premium user, I can see unmasked fields and export results.
5. As a premium user, I get higher rate limits and faster cached responses.

**Steps**
- Auth: email/password + JWT (access/refresh) + password reset.
- Plans/entitlements model in Mongo; middleware for field-level gating.
- Payments POC first (Stripe) + webhook handling; then wire subscriptions.
- Rate limiting by tier (Redis) for web + search endpoints.

**Phase exit testing**
- E2E flows: register/login/reset, upgrade, premium unlock, export, limits.

---

### Phase 4 — Admin panel + override system + audit
**User stories**
1. As an admin, I can view raw vs overrides vs computed profile.
2. As an admin, I can edit fields without touching raw_data.
3. As an admin, I can mark fields public/premium/hidden.
4. As an admin, I can verify a company and add website/email/description.
5. As an admin, I can see audit history of changes and sync events.

**Steps**
- Data model: add `manual_overrides`, `field_visibility`, `verified`, `audit_log`.
- Admin UI: company search, edit form, diff viewer, user management basics.
- Reindex pipeline: when overrides change → update ES doc.

**Phase exit testing**
- Admin edit → computed changes reflected → ES updated → public page shows correct gating.

---

### Phase 5 — Private API + API keys + monetization
**User stories**
1. As a customer, I can generate/revoke API keys.
2. As an API client, I can search and fetch company details by CUI.
3. As an API client, I get rate-limited per plan with clear errors.
4. As an admin, I can view/revoke keys and set custom limits.
5. As a customer, I can view usage stats and billing.

**Steps**
- API key issuance + hashed storage + scopes.
- Dedicated `/api/v1` routes; tiered fields identical to web entitlements.
- Usage logs + per-key rate limits (Redis) + basic analytics.

---

## 3) Next Actions (immediate)
1. Create `docker-compose.yml` for Elasticsearch + Redis (dev).
2. Implement ES index mapping + analyzers for autocomplete + fuzziness.
3. Write and run `poc_index.py` to ingest 10k docs from `justportal.firme`.
4. Write and run `poc_query.py` to validate relevance + <200ms p95.
5. Only after POC passes: start Phase 2 app skeleton (FastAPI + React) wired to ES.

---

## 4) Success Criteria
- **POC:** stable indexing + relevant autocomplete + typo tolerance + filters; p95 <200ms on dev.
- **V1 MVP:** fast public UX, clean design, correct masking, working SEO metas + JSON-LD + sitemaps.
- **Subscriptions:** premium unlock + reliable billing state + tiered rate limits.
- **Admin overrides:** non-destructive edits + audit + ES reindex correctness.
- **API:** secure keys, scoped access, predictable limits, and usage visibility.
