"""
Test Admin CAEN Routes - CRUD operations for CAEN codes management
Tests: stats, list codes, add, edit, delete, Rev.1 update, CSV import
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@mfirme.ro"
ADMIN_PASSWORD = "Admin123!"

# Test CAEN code (use unique code to avoid corrupting real data)
TEST_CAEN_COD = "9998"
TEST_CAEN_NAME = "TEST - Activitate de testare automata"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    # Token field is 'access_token' not 'token'
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in response: {data}"
    return token


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Headers with admin auth"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestCaenStats:
    """Test GET /api/admin/caen/stats endpoint"""
    
    def test_stats_requires_auth(self):
        """Stats endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/caen/stats")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_stats_returns_data(self, auth_headers):
        """Stats endpoint returns expected fields"""
        response = requests.get(f"{BASE_URL}/api/admin/caen/stats", headers=auth_headers)
        assert response.status_code == 200, f"Stats failed: {response.text}"
        
        data = response.json()
        # Verify expected fields
        assert "total" in data, "Missing 'total' field"
        assert "valid_descriptions" in data, "Missing 'valid_descriptions' field"
        assert "generic_descriptions" in data, "Missing 'generic_descriptions' field"
        assert "used_by_firms" in data, "Missing 'used_by_firms' field"
        assert "rev1_mapping_size" in data, "Missing 'rev1_mapping_size' field"
        
        # Verify values are reasonable
        assert data["total"] > 0, "Total should be > 0"
        assert data["valid_descriptions"] >= 0
        assert data["generic_descriptions"] >= 0
        assert data["rev1_mapping_size"] > 0, "Rev1 mapping should have entries"
        
        print(f"Stats: total={data['total']}, valid={data['valid_descriptions']}, generic={data['generic_descriptions']}, used_by_firms={data['used_by_firms']}")


class TestCaenCodesList:
    """Test GET /api/admin/caen/codes endpoint"""
    
    def test_list_requires_auth(self):
        """List endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/caen/codes")
        assert response.status_code in [401, 403]
    
    def test_list_returns_codes(self, auth_headers):
        """List endpoint returns paginated codes"""
        response = requests.get(f"{BASE_URL}/api/admin/caen/codes", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "codes" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        
        # Default limit is 50
        assert len(data["codes"]) <= 50
        assert data["total"] > 0
        
        # Verify code structure
        if data["codes"]:
            code = data["codes"][0]
            assert "cod" in code, "Code should have 'cod' field"
            assert "name" in code or "denumire" in code, "Code should have name/denumire"
        
        print(f"List: {len(data['codes'])} codes returned, total={data['total']}")
    
    def test_list_pagination(self, auth_headers):
        """Test pagination with skip parameter"""
        # Get first page
        response1 = requests.get(f"{BASE_URL}/api/admin/caen/codes?skip=0&limit=10", headers=auth_headers)
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get second page
        response2 = requests.get(f"{BASE_URL}/api/admin/caen/codes?skip=10&limit=10", headers=auth_headers)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Pages should have different codes
        if data1["codes"] and data2["codes"]:
            codes1 = [c["cod"] for c in data1["codes"]]
            codes2 = [c["cod"] for c in data2["codes"]]
            assert codes1 != codes2, "Pagination should return different codes"
        
        print(f"Pagination: page1 has {len(data1['codes'])} codes, page2 has {len(data2['codes'])} codes")
    
    def test_search_by_code(self, auth_headers):
        """Test search by CAEN code"""
        response = requests.get(f"{BASE_URL}/api/admin/caen/codes?q=0111", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should find codes containing "0111"
        if data["codes"]:
            found_match = any("0111" in c.get("cod", "") for c in data["codes"])
            assert found_match, "Search should find codes containing '0111'"
        
        print(f"Search '0111': found {len(data['codes'])} codes")
    
    def test_search_by_name(self, auth_headers):
        """Test search by CAEN name"""
        response = requests.get(f"{BASE_URL}/api/admin/caen/codes?q=comert", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        print(f"Search 'comert': found {len(data['codes'])} codes")
    
    def test_filter_valid(self, auth_headers):
        """Test filter for valid descriptions"""
        response = requests.get(f"{BASE_URL}/api/admin/caen/codes?filter=valid", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Valid codes should NOT start with "Cod CAEN "
        for code in data["codes"]:
            name = code.get("name", "")
            assert not name.startswith("Cod CAEN "), f"Valid filter returned generic code: {code['cod']}"
        
        print(f"Filter 'valid': found {data['total']} codes")
    
    def test_filter_generic(self, auth_headers):
        """Test filter for generic descriptions"""
        response = requests.get(f"{BASE_URL}/api/admin/caen/codes?filter=generic", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Generic codes should start with "Cod CAEN "
        for code in data["codes"]:
            name = code.get("name", "")
            assert name.startswith("Cod CAEN "), f"Generic filter returned valid code: {code['cod']} - {name}"
        
        print(f"Filter 'generic': found {data['total']} codes")


class TestCaenCRUD:
    """Test CRUD operations for CAEN codes"""
    
    def test_add_code(self, auth_headers):
        """Test adding a new CAEN code"""
        # First, try to delete if exists (cleanup from previous test)
        requests.delete(f"{BASE_URL}/api/admin/caen/codes/{TEST_CAEN_COD}", headers=auth_headers)
        
        # Add new code
        response = requests.post(
            f"{BASE_URL}/api/admin/caen/codes",
            headers=auth_headers,
            json={"cod": TEST_CAEN_COD, "name": TEST_CAEN_NAME, "sectiune": "U"}
        )
        assert response.status_code == 200, f"Add failed: {response.text}"
        
        data = response.json()
        assert data.get("status") == "created" or "cod" in data
        print(f"Added code: {TEST_CAEN_COD}")
    
    def test_add_duplicate_fails(self, auth_headers):
        """Adding duplicate code should fail"""
        response = requests.post(
            f"{BASE_URL}/api/admin/caen/codes",
            headers=auth_headers,
            json={"cod": TEST_CAEN_COD, "name": "Duplicate test"}
        )
        # Should return error (code already exists)
        data = response.json()
        assert "error" in data or response.status_code >= 400
        print(f"Duplicate add correctly rejected")
    
    def test_add_missing_fields_fails(self, auth_headers):
        """Adding code without required fields should fail"""
        response = requests.post(
            f"{BASE_URL}/api/admin/caen/codes",
            headers=auth_headers,
            json={"cod": ""}  # Missing name
        )
        data = response.json()
        assert "error" in data
        print(f"Missing fields correctly rejected")
    
    def test_verify_added_code(self, auth_headers):
        """Verify the added code appears in list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/caen/codes?q={TEST_CAEN_COD}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        found = any(c["cod"] == TEST_CAEN_COD for c in data["codes"])
        assert found, f"Added code {TEST_CAEN_COD} not found in list"
        print(f"Verified code {TEST_CAEN_COD} exists in database")
    
    def test_update_code(self, auth_headers):
        """Test updating a CAEN code"""
        new_name = "TEST - Activitate actualizata"
        response = requests.put(
            f"{BASE_URL}/api/admin/caen/codes/{TEST_CAEN_COD}",
            headers=auth_headers,
            json={"name": new_name, "sectiune": "T"}
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        data = response.json()
        assert data.get("status") == "updated" or data.get("modified") >= 0
        print(f"Updated code {TEST_CAEN_COD}")
    
    def test_verify_update(self, auth_headers):
        """Verify the update was persisted"""
        response = requests.get(
            f"{BASE_URL}/api/admin/caen/codes?q={TEST_CAEN_COD}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        code = next((c for c in data["codes"] if c["cod"] == TEST_CAEN_COD), None)
        assert code is not None
        assert "actualizata" in code.get("name", "").lower() or "actualizata" in code.get("denumire", "").lower()
        print(f"Verified update persisted for {TEST_CAEN_COD}")
    
    def test_update_nonexistent_fails(self, auth_headers):
        """Updating non-existent code should fail"""
        response = requests.put(
            f"{BASE_URL}/api/admin/caen/codes/NONEXISTENT999",
            headers=auth_headers,
            json={"name": "Test"}
        )
        data = response.json()
        assert "error" in data
        print(f"Update non-existent correctly rejected")
    
    def test_delete_code(self, auth_headers):
        """Test deleting a CAEN code"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/caen/codes/{TEST_CAEN_COD}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Delete failed: {response.text}"
        
        data = response.json()
        assert data.get("status") == "deleted"
        print(f"Deleted code {TEST_CAEN_COD}")
    
    def test_verify_delete(self, auth_headers):
        """Verify the code was deleted"""
        response = requests.get(
            f"{BASE_URL}/api/admin/caen/codes?q={TEST_CAEN_COD}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        found = any(c["cod"] == TEST_CAEN_COD for c in data["codes"])
        assert not found, f"Deleted code {TEST_CAEN_COD} still exists"
        print(f"Verified code {TEST_CAEN_COD} was deleted")
    
    def test_delete_nonexistent_fails(self, auth_headers):
        """Deleting non-existent code should fail"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/caen/codes/NONEXISTENT999",
            headers=auth_headers
        )
        data = response.json()
        assert "error" in data
        print(f"Delete non-existent correctly rejected")


class TestRev1Update:
    """Test Rev.1 description update endpoint"""
    
    def test_rev1_requires_auth(self):
        """Rev.1 update requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/caen/update-rev1")
        assert response.status_code in [401, 403]
    
    def test_rev1_update(self, auth_headers):
        """Test Rev.1 update endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/admin/caen/update-rev1",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Rev1 update failed: {response.text}"
        
        data = response.json()
        assert "updated" in data
        assert "upserted" in data
        assert "total" in data
        assert "remaining_generic" in data
        
        print(f"Rev1 update: updated={data['updated']}, upserted={data['upserted']}, total={data['total']}, remaining_generic={data['remaining_generic']}")


class TestCsvImport:
    """Test CSV import endpoint"""
    
    def test_csv_import_requires_auth(self):
        """CSV import requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/caen/import-csv")
        assert response.status_code in [401, 403, 422]  # 422 if missing file
    
    def test_csv_import_valid(self, auth_headers):
        """Test CSV import with valid data"""
        # Create a simple CSV content
        csv_content = "cod;name;sectiune\n9997;TEST Import CSV;U\n"
        
        # First cleanup
        requests.delete(f"{BASE_URL}/api/admin/caen/codes/9997", headers=auth_headers)
        
        # Import
        files = {"file": ("test.csv", csv_content, "text/csv")}
        headers_no_content_type = {"Authorization": auth_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/caen/import-csv",
            headers=headers_no_content_type,
            files=files
        )
        assert response.status_code == 200, f"CSV import failed: {response.text}"
        
        data = response.json()
        assert "imported" in data or "updated" in data
        print(f"CSV import: imported={data.get('imported', 0)}, updated={data.get('updated', 0)}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/caen/codes/9997", headers=auth_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
