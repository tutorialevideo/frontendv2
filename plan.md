# mFirme — plan.md (updated)

## 1) Objectives
- Stabilize and ship the **current MVP** (FastAPI + React + MongoDB dual DB) with a reliable UX and test suite.
- Finalize **subscriptions & premium gating** with **Stripe (sandbox first)**: checkout, status sync, and webhook handling.
- Ensure the **Admin Dashboard** is reliable (no timeouts) and extend it with **Phase 4: manual overrides + audit**.
- Reduce frontend noise: eliminate **React console warnings** and improve perceived performance.
- Prepare a clean foundation for: **admin overrides → computed profile**, and later **paid API**.

---

## 2) Implementation Steps

### Phase 1 — Core search/data workflow (DONE / superseded)
**Status:** Completed enough to support the current MVP.

**What exists now**
- Production-style app is already running (no longer only a POC):
  - FastAPI backend + React frontend
  - Dual DB: `justportal` (readonly firms) + `mfirme_app` (users/sessions/subscriptions)
  - Search + company profiles implemented

**Notes**
- The original MongoDB → Elasticsearch POC plan is no longer the immediate blocker; performance work will be handled as incremental optimization.

**Exit criteria**
- ✅ Core search and profile pages functional in the running MVP

---

### Phase 2 — V1 Public MVP App (DONE)
**Status:** Implemented.

**Delivered user stories**
1. ✅ Visitor can search firms
2. ✅ Visitor can open company profile
3. ✅ Premium fields are masked for free users with upgrade prompts (where applicable)

**Backend (FastAPI)**
- ✅ Core endpoints for search and company profile
- ✅ Masking rules applied at response layer

**Frontend (React)**
- ✅ Search and company profile pages
- ✅ User flows integrated with auth where needed

**Phase exit testing**
- ✅ Manual end-to-end flow exists (Search → Profile)
- ⏳ Add/strengthen automated smoke tests as part of Phase 3/4 hardening

---

### Phase 3 — Accounts + Subscriptions + Premium gating (IN PROGRESS)
**Status:** Auth & gating implemented; Stripe needs completion/hardening.

**User stories**
1. ✅ Register/login and secure session (JWT)
2. ✅ Favorites and user dashboard
3. ✅ Premium data masking for non-paying tiers
4. ⏳ Paid upgrade unlock via Stripe (sandbox)

**What is already implemented**
- ✅ JWT auth flow
- ✅ Tier concept (`free`/`plus`/`premium`) and UI gating/masking
- ✅ Subscription endpoints exist (`/api/subscriptions/*`), with plan definitions
- ⚠️ Stripe flow is partial and requires sandbox configuration + verification

**Immediate steps (P0)**
1. **Admin Dashboard reliability fix (P0)**
   - Reproduce the automated test timeout.
   - Ensure the “Tranzacții” tab is discoverable and stable:
     - Add stable `data-testid` attributes for tab buttons and key table elements.
     - Ensure loading state completes even if one endpoint fails (graceful degradation + error UI).
   - Confirm `/api/admin/stats`, `/api/admin/users`, `/api/admin/transactions` are fast and return expected shapes.

2. **Stripe Sandbox completion (P0)**
   - Configure backend env:
     - `STRIPE_API_KEY` (test secret key)
     - (If using signature verification) `STRIPE_WEBHOOK_SECRET`
   - Make checkout fully deterministic:
     - Confirm `success_url`/`cancel_url` work across environments.
     - Ensure transaction document is created and updated correctly.
   - Webhook hardening:
     - Verify signature (if supported by integration library).
     - On `checkout.session.completed`, mark transaction paid and set subscription active (avoid relying only on polling `/status/{session_id}`).
   - Add a clear reconciliation path:
     - If webhook missed, `/status/{session_id}` can still upgrade the user.

3. **React warnings cleanup (P2)**
   - Identify and remove hydration/deprecation warnings affecting SearchPage/CompanyPage.
   - Ensure loading states and conditional rendering do not cause mismatched markup.

**Phase exit testing**
- E2E (manual + basic automation):
  - register/login → open pricing → checkout (sandbox) → return success → premium fields unmasked
  - cancel flow leaves user tier unchanged
  - webhook (or polling fallback) updates DB reliably

---

### Phase 4 — Admin panel + override system + audit (NEXT)
**Status:** Admin Dashboard exists; overrides system not yet implemented.

**User stories**
1. As an admin, I can view **raw vs computed vs overrides** for a company.
2. As an admin, I can **edit fields non-destructively** (overrides stored separately from raw data).
3. As an admin, I can mark fields **public/premium/hidden**.
4. As an admin, I can **verify** a company and add curated fields (website/email/description).
5. As an admin, I can see an **audit history** of changes.

**Steps**
1. **Data model changes (mfirme_app)**
   - Add collections (or embed documents) for:
     - `company_overrides` (by firm identifier e.g., CUI)
     - `field_visibility`
     - `audit_log`
   - Define a canonical company identifier mapping between `justportal` firms and app overrides.

2. **Computed profile pipeline**
   - Backend merges:
     - `raw_data` (readonly firm doc)
     - `manual_overrides` (admin)
     - `visibility` (public/premium/hidden)
   - Ensure masking rules apply after merge, based on user tier.

3. **Admin UI**
   - Add Admin company search + open company editor.
   - Implement diff viewer (raw vs override) and save flow.
   - Audit log viewer.

4. **Operational safeguards**
   - Role-based access checks (admin-only routes).
   - Validation and schema normalization for overrides.

**Phase exit testing**
- Admin edits a field → computed profile changes → public page reflects change with correct tier gating.
- Audit log shows who/what/when.

---

### Phase 5 — Private API + API keys + monetization (LATER)
**Status:** Planned.

**User stories**
1. Customers can generate/revoke API keys.
2. API clients can search and fetch company details.
3. Tiered rate limits and field entitlements.

**Steps**
- API keys (hashed) + scopes.
- `/api/v1` routes mirroring web entitlements.
- Usage logs + rate limiting.

---

## 3) Next Actions (immediate)
1. **P0:** Reproduce and fix Admin Dashboard test timeout; add `data-testid` to tabs and key admin elements.
2. **P0:** Configure Stripe sandbox (`STRIPE_API_KEY`, webhook secret if needed) and complete checkout + webhook reconciliation.
3. **P2:** Remove React console warnings in SearchPage/CompanyPage.
4. **NEXT:** Start Phase 4 implementation: overrides data model → computed profile merge → admin editor + audit.

---

## 4) Success Criteria
- **MVP stability:** No Admin Dashboard timeouts; reliable loading states; key flows covered by smoke tests.
- **Subscriptions:** Sandbox payments reliably upgrade tier; webhook/polling reconciliation prevents desync; transactions recorded correctly.
- **Frontend quality:** No critical console warnings; consistent rendering and predictable navigation.
- **Admin overrides:** Non-destructive edits with audit trail; computed profile correctly merges raw + overrides + visibility; public gating remains correct.
- **Foundation for monetization:** Clear entitlement model reusable for future paid API.
