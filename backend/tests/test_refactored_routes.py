"""
Test Refactored Routes - Verifies no regressions after server.py refactoring
Tests search_routes.py, company_routes.py, geo_routes.py endpoints
Also verifies auto-indexing code path in admin_sync_routes.py
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@mfirme.ro"
ADMIN_PASSWORD = "Admin123!"

# Test data
TEST_CUI = "20413044"  # Known CUI stored as int in MongoDB
TEST_CUI_INT = 2113693  # Another test CUI
TEST_SLUG = "automob-societate-cooperativa-2113693"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for admin"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")  # Note: returns access_token, not token
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestHealthEndpoint:
    """Basic health check - verifies server is running after refactoring"""
    
    def test_health_returns_200(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✓ Health endpoint working")


class TestSearchRoutes:
    """Tests for /api/search and /api/search/suggest endpoints (search_routes.py)"""
    
    def test_search_text_query(self, api_client):
        """Test text search with 'persoana fizica'"""
        response = api_client.get(f"{BASE_URL}/api/search", params={"q": "persoana fizica", "limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert data["total"] > 0, "Should find companies with 'persoana fizica'"
        print(f"✓ Text search found {data['total']} results")
    
    def test_search_cui_query(self, api_client):
        """Test CUI search with numeric query (tests int/string type matching)"""
        response = api_client.get(f"{BASE_URL}/api/search", params={"q": TEST_CUI, "limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # CUI search should find at least one result
        assert data["total"] >= 1, f"Should find company with CUI {TEST_CUI}"
        print(f"✓ CUI search found {data['total']} results for CUI {TEST_CUI}")
    
    def test_search_suggest_autocomplete(self, api_client):
        """Test autocomplete suggestions"""
        response = api_client.get(f"{BASE_URL}/api/search/suggest", params={"q": "auto"})
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0, "Should return suggestions for 'auto'"
        # Verify suggestion structure
        suggestion = data["suggestions"][0]
        assert "type" in suggestion
        assert "label" in suggestion
        assert "slug" in suggestion
        print(f"✓ Autocomplete returned {len(data['suggestions'])} suggestions")
    
    def test_search_with_judet_filter(self, api_client):
        """Test search with judet filter"""
        # Note: Judet is stored as "București" with diacritics in DB
        response = api_client.get(f"{BASE_URL}/api/search", params={"judet": "București", "limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["total"] > 0, "Should find companies in București"
        print(f"✓ Judet filter found {data['total']} results in București")
    
    def test_search_pagination(self, api_client):
        """Test search pagination"""
        response = api_client.get(f"{BASE_URL}/api/search", params={"page": 2, "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["limit"] == 10
        print("✓ Pagination working correctly")


class TestCompanyRoutes:
    """Tests for /api/company/* endpoints (company_routes.py)"""
    
    def test_company_by_cui(self, api_client):
        """Test get company by CUI (tests int/str $or fallback)"""
        response = api_client.get(f"{BASE_URL}/api/company/cui/{TEST_CUI}")
        assert response.status_code == 200
        data = response.json()
        assert "denumire" in data
        assert "cui" in data
        # CUI might be returned as int or string
        assert str(data["cui"]) == TEST_CUI or data["cui"] == int(TEST_CUI)
        print(f"✓ Company by CUI: {data.get('denumire', 'N/A')}")
    
    def test_company_by_slug(self, api_client):
        """Test get company by slug"""
        response = api_client.get(f"{BASE_URL}/api/company/slug/{TEST_SLUG}")
        assert response.status_code == 200
        data = response.json()
        assert "denumire" in data
        assert "cui" in data
        assert "slug" in data
        print(f"✓ Company by slug: {data.get('denumire', 'N/A')}")
    
    def test_company_financials(self, api_client):
        """Test get company financials"""
        response = api_client.get(f"{BASE_URL}/api/company/{TEST_CUI_INT}/financials")
        assert response.status_code == 200
        data = response.json()
        assert "years" in data
        assert "data" in data
        # May or may not have financial data
        print(f"✓ Financials endpoint returned {len(data.get('years', []))} years of data")
    
    def test_company_not_found(self, api_client):
        """Test 404 for non-existent company"""
        response = api_client.get(f"{BASE_URL}/api/company/cui/99999999999")
        assert response.status_code == 404
        print("✓ Company not found returns 404")
    
    def test_invalid_slug_format(self, api_client):
        """Test 400 for invalid slug format"""
        response = api_client.get(f"{BASE_URL}/api/company/slug/invalid-slug-no-cui")
        # Should return 400 or 404 depending on implementation
        assert response.status_code in [400, 404]
        print("✓ Invalid slug format handled correctly")


class TestGeoRoutes:
    """Tests for /api/geo/* endpoints (geo_routes.py)"""
    
    def test_get_judete(self, api_client):
        """Test get counties list - should return 42 judete"""
        response = api_client.get(f"{BASE_URL}/api/geo/judete")
        assert response.status_code == 200
        data = response.json()
        assert "judete" in data
        judete_count = len(data["judete"])
        # Romania has 41 counties + Bucuresti = 42
        assert judete_count >= 40, f"Expected ~42 judete, got {judete_count}"
        # Verify structure
        if data["judete"]:
            judet = data["judete"][0]
            assert "judet" in judet
            assert "count" in judet
        print(f"✓ Judete endpoint returned {judete_count} counties")
    
    def test_get_localitati(self, api_client):
        """Test get localities list"""
        response = api_client.get(f"{BASE_URL}/api/geo/localitati")
        assert response.status_code == 200
        data = response.json()
        assert "localitati" in data
        assert len(data["localitati"]) > 0
        # Verify structure
        loc = data["localitati"][0]
        assert "localitate" in loc
        assert "judet" in loc
        assert "count" in loc
        print(f"✓ Localitati endpoint returned {len(data['localitati'])} localities")
    
    def test_get_localitati_filtered_by_judet(self, api_client):
        """Test get localities filtered by county"""
        response = api_client.get(f"{BASE_URL}/api/geo/localitati", params={"judet": "CLUJ"})
        assert response.status_code == 200
        data = response.json()
        assert "localitati" in data
        # All results should be from CLUJ
        for loc in data["localitati"]:
            assert loc["judet"] == "CLUJ", f"Expected CLUJ, got {loc['judet']}"
        print(f"✓ Localitati filtered by CLUJ: {len(data['localitati'])} results")
    
    def test_caen_top(self, api_client):
        """Test get top CAEN codes"""
        response = api_client.get(f"{BASE_URL}/api/caen/top", params={"limit": 20})
        assert response.status_code == 200
        data = response.json()
        assert "caen_codes" in data
        assert len(data["caen_codes"]) > 0
        # Verify structure
        caen = data["caen_codes"][0]
        assert "caen" in caen
        assert "count" in caen
        print(f"✓ CAEN top returned {len(data['caen_codes'])} codes")
    
    def test_stats_overview(self, api_client):
        """Test platform statistics - should return total 2381831"""
        response = api_client.get(f"{BASE_URL}/api/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_companies" in data
        assert "active_companies" in data
        assert "counties" in data
        assert "with_financials" in data
        # Verify expected total
        assert data["total_companies"] == 2381831, f"Expected 2381831, got {data['total_companies']}"
        print(f"✓ Stats overview: {data['total_companies']} total companies")


class TestAdminDbRoutes:
    """Tests for admin DB endpoints (verifies existing functionality still works)"""
    
    def test_db_stats_requires_auth(self, api_client):
        """Test that DB stats requires authentication"""
        # Remove auth header if present
        api_client.headers.pop("Authorization", None)
        response = api_client.get(f"{BASE_URL}/api/admin/db/stats")
        # Returns 401 (no token) or 403 (invalid/expired token)
        assert response.status_code in [401, 403]
        print("✓ DB stats requires authentication")
    
    def test_db_stats_returns_data(self, authenticated_client):
        """Test DB stats endpoint returns proper data"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/db/stats")
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert "recommendations" in data
        assert "health_score" in data
        print(f"✓ DB stats: health_score={data['health_score']}%")
    
    def test_qmark_preview_returns_data(self, authenticated_client):
        """Test qmark preview endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/db/qmark-preview")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "high_confidence" in data
        assert "items" in data
        print(f"✓ Qmark preview: {data['total']} items")


class TestAutoIndexingCodePath:
    """Verify auto-indexing code path exists in admin_sync_routes.py"""
    
    def test_recommended_indexes_imported(self):
        """Verify RECOMMENDED_INDEXES is importable from admin_db_routes"""
        from routes.admin_db_routes import RECOMMENDED_INDEXES
        assert len(RECOMMENDED_INDEXES) > 0
        # Verify structure
        idx = RECOMMENDED_INDEXES[0]
        assert "collection" in idx
        assert "name" in idx
        assert "keys" in idx
        print(f"✓ RECOMMENDED_INDEXES has {len(RECOMMENDED_INDEXES)} indexes defined")
    
    def test_auto_indexing_code_in_sync_routes(self):
        """Verify auto-indexing code exists in admin_sync_routes.py"""
        import inspect
        from routes import admin_sync_routes
        
        # Get source code of run_full_sync function
        source = inspect.getsource(admin_sync_routes.run_full_sync)
        
        # Verify auto-indexing code is present
        assert "RECOMMENDED_INDEXES" in source, "run_full_sync should import RECOMMENDED_INDEXES"
        assert "Auto-create" in source or "auto" in source.lower(), "Should have auto-indexing comment"
        print("✓ Auto-indexing code path verified in run_full_sync")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
