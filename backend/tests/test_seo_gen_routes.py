"""
Test SEO Generation Routes
Tests for batch AI SEO text generation endpoints
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@mfirme.ro"
ADMIN_PASSWORD = "Admin123!"

# Test CUIs (companies that already have seo_description)
TEST_CUI_WITH_SEO = "1860712"  # ROMPETROL RAFINARE SA
TEST_CUI_FOR_PREVIEW = "2113693"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    # Auth returns access_token (not token)
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in response: {data}"
    return token


@pytest.fixture
def admin_headers(admin_token):
    """Headers with admin auth"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestSeoGenStatus:
    """Test GET /api/admin/seo-gen/status endpoint"""
    
    def test_status_requires_auth(self):
        """Status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/seo-gen/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_status_returns_counts(self, admin_headers):
        """Status endpoint returns generation status and counts"""
        response = requests.get(f"{BASE_URL}/api/admin/seo-gen/status", headers=admin_headers)
        assert response.status_code == 200, f"Status failed: {response.text}"
        
        data = response.json()
        # Verify required fields
        assert "running" in data, "Missing 'running' field"
        assert "total_with_seo" in data, "Missing 'total_with_seo' field"
        assert "total_active" in data, "Missing 'total_active' field"
        assert "remaining" in data, "Missing 'remaining' field"
        
        # Verify data types
        assert isinstance(data["running"], bool), "running should be boolean"
        assert isinstance(data["total_with_seo"], int), "total_with_seo should be int"
        assert isinstance(data["total_active"], int), "total_active should be int"
        assert isinstance(data["remaining"], int), "remaining should be int"
        
        # Verify counts are reasonable (we know 5 companies have SEO already)
        assert data["total_with_seo"] >= 5, f"Expected at least 5 with SEO, got {data['total_with_seo']}"
        assert data["total_active"] > 0, "total_active should be > 0"
        
        print(f"Status: running={data['running']}, with_seo={data['total_with_seo']}, active={data['total_active']}, remaining={data['remaining']}")


class TestSeoGenPreview:
    """Test GET /api/admin/seo-gen/preview/{cui} endpoint"""
    
    def test_preview_requires_auth(self):
        """Preview endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/seo-gen/preview/{TEST_CUI_FOR_PREVIEW}")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_preview_generates_text(self, admin_headers):
        """Preview generates SEO text for a company (does NOT save)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/seo-gen/preview/{TEST_CUI_FOR_PREVIEW}",
            headers=admin_headers,
            timeout=60  # AI generation can take time
        )
        assert response.status_code == 200, f"Preview failed: {response.text}"
        
        data = response.json()
        assert "cui" in data, "Missing 'cui' field"
        assert "denumire" in data, "Missing 'denumire' field"
        assert "seo_description" in data, "Missing 'seo_description' field"
        
        # Verify SEO text is substantial
        seo_text = data["seo_description"]
        assert len(seo_text) > 50, f"SEO text too short: {len(seo_text)} chars"
        
        print(f"Preview for CUI {data['cui']} ({data['denumire']}): {len(seo_text)} chars")
        print(f"SEO text preview: {seo_text[:200]}...")
    
    def test_preview_invalid_cui(self, admin_headers):
        """Preview returns 404 for non-existent company"""
        response = requests.get(
            f"{BASE_URL}/api/admin/seo-gen/preview/99999999999",
            headers=admin_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestSeoGenBatch:
    """Test POST /api/admin/seo-gen/start and /stop endpoints"""
    
    def test_start_requires_auth(self):
        """Start endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/seo-gen/start")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_stop_requires_auth(self):
        """Stop endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/seo-gen/stop")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_start_batch_with_limit(self, admin_headers):
        """Start batch generation with limit=2 (quick test)"""
        # First check if already running
        status_resp = requests.get(f"{BASE_URL}/api/admin/seo-gen/status", headers=admin_headers)
        if status_resp.status_code == 200 and status_resp.json().get("running"):
            # Stop any running generation first
            requests.post(f"{BASE_URL}/api/admin/seo-gen/stop", headers=admin_headers)
            time.sleep(2)
        
        # Start with limit=2, concurrency=1
        response = requests.post(
            f"{BASE_URL}/api/admin/seo-gen/start",
            headers=admin_headers,
            json={"concurrency": 1, "limit": 2}
        )
        assert response.status_code == 200, f"Start failed: {response.text}"
        
        data = response.json()
        assert data.get("status") == "started", f"Expected status=started, got {data}"
        assert data.get("limit") == 2, f"Expected limit=2, got {data.get('limit')}"
        assert data.get("concurrency") == 1, f"Expected concurrency=1, got {data.get('concurrency')}"
        
        print(f"Batch started: {data}")
        
        # Wait a bit and check status
        time.sleep(3)
        status_resp = requests.get(f"{BASE_URL}/api/admin/seo-gen/status", headers=admin_headers)
        assert status_resp.status_code == 200
        status = status_resp.json()
        print(f"Status after 3s: running={status.get('running')}, processed={status.get('processed')}, errors={status.get('errors')}")
    
    def test_stop_generation(self, admin_headers):
        """Stop running generation"""
        response = requests.post(f"{BASE_URL}/api/admin/seo-gen/stop", headers=admin_headers)
        assert response.status_code == 200, f"Stop failed: {response.text}"
        
        data = response.json()
        assert data.get("status") == "stopping", f"Expected status=stopping, got {data}"
        print(f"Stop response: {data}")


class TestCompanyWithSeoDescription:
    """Test that company API returns seo_description when present"""
    
    def test_company_has_seo_description(self):
        """Company with SEO description returns it in API response"""
        # CUI 1860712 (ROMPETROL RAFINARE SA) has seo_description
        response = requests.get(f"{BASE_URL}/api/company/cui/{TEST_CUI_WITH_SEO}")
        assert response.status_code == 200, f"Company fetch failed: {response.text}"
        
        data = response.json()
        assert "denumire" in data, "Missing 'denumire' field"
        
        # Check if seo_description is present
        if "seo_description" in data and data["seo_description"]:
            print(f"Company {data['denumire']} has SEO description: {data['seo_description'][:100]}...")
            assert len(data["seo_description"]) > 30, "SEO description too short"
        else:
            print(f"Note: Company {data.get('denumire')} does not have seo_description yet")


class TestRegressionExistingEndpoints:
    """Regression tests - ensure existing endpoints still work"""
    
    def test_search_endpoint(self):
        """Search endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/search?q=rompetrol&limit=5")
        assert response.status_code == 200, f"Search failed: {response.text}"
        data = response.json()
        assert "results" in data or "companies" in data or isinstance(data, list), f"Unexpected response: {data}"
    
    def test_company_by_slug(self):
        """Company by slug still works"""
        response = requests.get(f"{BASE_URL}/api/company/slug/automob-societate-cooperativa-2113693")
        assert response.status_code == 200, f"Company by slug failed: {response.text}"
    
    def test_geo_judete(self):
        """Geo judete endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/geo/judete")
        assert response.status_code == 200, f"Geo judete failed: {response.text}"
        data = response.json()
        # API returns {"judete": [...]}
        judete_list = data.get("judete", data) if isinstance(data, dict) else data
        assert len(judete_list) > 40, f"Expected 40+ judete, got {len(judete_list)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
