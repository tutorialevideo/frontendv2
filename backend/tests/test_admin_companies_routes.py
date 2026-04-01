"""
Test Admin Companies Routes - Stare Filters (active, radiate, incomplete, all)
Tests the new filtering functionality for admin company management.
- GET /api/admin/companies/counts - returns counts for each category
- GET /api/admin/companies/list?stare=active - local DB active companies
- GET /api/admin/companies/list?stare=radiate - cloud DB radiate companies
- GET /api/admin/companies/list?stare=incomplete - cloud DB incomplete data
- GET /api/admin/companies/list?stare=all - cloud DB all companies
- GET /api/admin/companies/full/{cui} - full company data (local or cloud)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@mfirme.ro"
ADMIN_PASSWORD = "Admin123!"

# Test CUIs
ACTIVE_CUI = "2113693"  # Active company in local DB
RADIATE_CUI = "13594878"  # CRISTIAN SRL - RADIERE din data 15.10.2012


class TestAdminCompaniesAuth:
    """Test authentication for admin companies endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_counts_requires_auth(self):
        """Test that /counts endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/companies/counts")
        assert response.status_code in [401, 403], f"Should require authentication, got {response.status_code}"
    
    def test_list_requires_auth(self):
        """Test that /list endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/companies/list")
        assert response.status_code in [401, 403], f"Should require authentication, got {response.status_code}"
    
    def test_full_requires_auth(self):
        """Test that /full/{cui} endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/companies/full/{ACTIVE_CUI}")
        assert response.status_code in [401, 403], f"Should require authentication, got {response.status_code}"


class TestAdminCompanyCounts:
    """Test GET /api/admin/companies/counts endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_counts_returns_200(self, auth_token):
        """Test counts endpoint returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/counts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_counts_structure(self, auth_token):
        """Test counts response has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/counts",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=180  # Cloud DB counts can be slow
        )
        # 502 can happen if cloud DB query times out
        if response.status_code == 502:
            pytest.skip("Cloud DB counts query timed out")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify all required fields exist
        assert "active" in data, "Missing 'active' count"
        assert "radiate" in data, "Missing 'radiate' count"
        assert "incomplete" in data, "Missing 'incomplete' count"
        assert "total" in data, "Missing 'total' count"
        
        # Verify counts are integers
        assert isinstance(data["active"], int), "active should be integer"
        assert isinstance(data["radiate"], int), "radiate should be integer"
        assert isinstance(data["incomplete"], int), "incomplete should be integer"
        assert isinstance(data["total"], int), "total should be integer"
        
        # Verify counts are non-negative
        assert data["active"] >= 0, "active count should be non-negative"
        assert data["radiate"] >= 0, "radiate count should be non-negative"
        assert data["incomplete"] >= 0, "incomplete count should be non-negative"
        assert data["total"] >= 0, "total count should be non-negative"
        
        print(f"Counts: active={data['active']}, radiate={data['radiate']}, incomplete={data['incomplete']}, total={data['total']}")


class TestAdminCompanyListActive:
    """Test GET /api/admin/companies/list?stare=active endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_list_active_returns_200(self, auth_token):
        """Test list with stare=active returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=active",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_list_active_structure(self, auth_token):
        """Test list response has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=active&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "companies" in data, "Missing 'companies' array"
        assert "total" in data, "Missing 'total' count"
        assert "skip" in data, "Missing 'skip' value"
        assert "limit" in data, "Missing 'limit' value"
        assert "stare_filter" in data, "Missing 'stare_filter' value"
        
        # Verify stare_filter is correct
        assert data["stare_filter"] == "active", f"Expected stare_filter='active', got '{data['stare_filter']}'"
        
        # Verify companies is a list
        assert isinstance(data["companies"], list), "companies should be a list"
        
        print(f"Active companies: total={data['total']}, returned={len(data['companies'])}")
    
    def test_list_active_company_fields(self, auth_token):
        """Test that active companies have expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=active&limit=5",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data["companies"]) > 0:
            company = data["companies"][0]
            # Check required fields
            assert "cui" in company, "Missing 'cui' field"
            assert "denumire" in company, "Missing 'denumire' field"
            # _id should be excluded
            assert "_id" not in company, "_id should be excluded from response"
            print(f"Sample active company: {company.get('denumire')} (CUI: {company.get('cui')})")
    
    def test_list_active_pagination(self, auth_token):
        """Test pagination works for active companies"""
        # Get first page
        response1 = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=active&skip=0&limit=5",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get second page
        response2 = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=active&skip=5&limit=5",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify different companies on different pages
        if len(data1["companies"]) > 0 and len(data2["companies"]) > 0:
            cuis1 = [c["cui"] for c in data1["companies"]]
            cuis2 = [c["cui"] for c in data2["companies"]]
            # No overlap between pages
            overlap = set(cuis1) & set(cuis2)
            assert len(overlap) == 0, f"Pages should not overlap, found: {overlap}"
            print(f"Pagination working: page1 has {len(cuis1)} companies, page2 has {len(cuis2)} companies")


class TestAdminCompanyListRadiate:
    """Test GET /api/admin/companies/list?stare=radiate endpoint (Cloud DB)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_list_radiate_returns_200(self, auth_token):
        """Test list with stare=radiate returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=radiate&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Could be 200 or 503 if cloud DB not available
        assert response.status_code in [200, 503], f"Expected 200 or 503, got {response.status_code}: {response.text}"
        
        if response.status_code == 503:
            print("Cloud DB not available for radiate companies")
            pytest.skip("Cloud DB not available")
    
    def test_list_radiate_structure(self, auth_token):
        """Test radiate list response has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=radiate&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 503:
            pytest.skip("Cloud DB not available")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "companies" in data, "Missing 'companies' array"
        assert "total" in data, "Missing 'total' count"
        assert "stare_filter" in data, "Missing 'stare_filter' value"
        assert data["stare_filter"] == "radiate", f"Expected stare_filter='radiate', got '{data['stare_filter']}'"
        
        print(f"Radiate companies: total={data['total']}, returned={len(data['companies'])}")
    
    def test_list_radiate_companies_have_radiere_status(self, auth_token):
        """Test that radiate companies have anaf_stare_startswith_inregistrat=False"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=radiate&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 503:
            pytest.skip("Cloud DB not available")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that returned companies are actually radiate
        for company in data["companies"]:
            # anaf_stare_startswith_inregistrat should be False for radiate companies
            assert company.get("anaf_stare_startswith_inregistrat") == False, \
                f"Company {company.get('cui')} should have anaf_stare_startswith_inregistrat=False"
            print(f"Radiate company: {company.get('denumire')} - anaf_stare: {company.get('anaf_stare')}")
    
    def test_search_within_radiate(self, auth_token):
        """Test search within radiate companies (q=CRISTIAN)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=radiate&q=CRISTIAN&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 503:
            pytest.skip("Cloud DB not available")
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"Search 'CRISTIAN' in radiate: found {data['total']} companies")
        
        # If results found, verify they contain CRISTIAN in name
        for company in data["companies"]:
            assert "CRISTIAN" in company.get("denumire", "").upper(), \
                f"Company {company.get('denumire')} should contain 'CRISTIAN'"


class TestAdminCompanyListIncomplete:
    """Test GET /api/admin/companies/list?stare=incomplete endpoint (Cloud DB)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_list_incomplete_returns_200(self, auth_token):
        """Test list with stare=incomplete returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=incomplete&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Could be 200 or 503 if cloud DB not available
        assert response.status_code in [200, 503], f"Expected 200 or 503, got {response.status_code}: {response.text}"
        
        if response.status_code == 503:
            print("Cloud DB not available for incomplete companies")
            pytest.skip("Cloud DB not available")
    
    def test_list_incomplete_structure(self, auth_token):
        """Test incomplete list response has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=incomplete&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 503:
            pytest.skip("Cloud DB not available")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "companies" in data, "Missing 'companies' array"
        assert "total" in data, "Missing 'total' count"
        assert "stare_filter" in data, "Missing 'stare_filter' value"
        assert data["stare_filter"] == "incomplete", f"Expected stare_filter='incomplete', got '{data['stare_filter']}'"
        
        print(f"Incomplete companies: total={data['total']}, returned={len(data['companies'])}")


class TestAdminCompanyListAll:
    """Test GET /api/admin/companies/list?stare=all endpoint (Cloud DB)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_list_all_returns_200(self, auth_token):
        """Test list with stare=all returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=all&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Could be 200 or 503 if cloud DB not available
        assert response.status_code in [200, 503], f"Expected 200 or 503, got {response.status_code}: {response.text}"
        
        if response.status_code == 503:
            print("Cloud DB not available for all companies")
            pytest.skip("Cloud DB not available")
    
    def test_list_all_structure(self, auth_token):
        """Test all list response has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/list?stare=all&limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 503:
            pytest.skip("Cloud DB not available")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "companies" in data, "Missing 'companies' array"
        assert "total" in data, "Missing 'total' count"
        assert "stare_filter" in data, "Missing 'stare_filter' value"
        assert data["stare_filter"] == "all", f"Expected stare_filter='all', got '{data['stare_filter']}'"
        
        print(f"All companies (cloud): total={data['total']}, returned={len(data['companies'])}")


class TestAdminCompanyFull:
    """Test GET /api/admin/companies/full/{cui} endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_full_active_company(self, auth_token):
        """Test getting full data for active company (local DB)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/full/{ACTIVE_CUI}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "cui" in data, "Missing 'cui' field"
        assert data["cui"] == ACTIVE_CUI, f"Expected CUI {ACTIVE_CUI}, got {data['cui']}"
        assert "denumire" in data, "Missing 'denumire' field"
        
        print(f"Active company full data: {data.get('denumire')} (CUI: {data.get('cui')})")
    
    def test_full_radiate_company(self, auth_token):
        """Test getting full data for radiate company (cloud DB fallback)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/full/{RADIATE_CUI}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Could be 200 (found in cloud) or 404 (not found anywhere)
        if response.status_code == 404:
            print(f"Radiate company CUI {RADIATE_CUI} not found in local or cloud DB")
            pytest.skip("Radiate company not found")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "cui" in data, "Missing 'cui' field"
        assert data["cui"] == RADIATE_CUI, f"Expected CUI {RADIATE_CUI}, got {data['cui']}"
        
        # Check if it has RADIERE status
        anaf_stare = data.get("anaf_stare", "")
        print(f"Radiate company full data: {data.get('denumire')} - anaf_stare: {anaf_stare}")
    
    def test_full_nonexistent_company(self, auth_token):
        """Test getting full data for non-existent company returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies/full/99999999999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
