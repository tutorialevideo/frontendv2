"""
Test DB Optimization Feature
Tests for admin DB stats, index creation, and optimization endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@mfirme.ro"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        # Login returns 'access_token' not 'token'
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture
def admin_headers(admin_token):
    """Headers with admin auth token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestDbStatsEndpoint:
    """Tests for GET /api/admin/db/stats endpoint"""
    
    def test_db_stats_returns_200(self, admin_headers):
        """Test that DB stats endpoint returns 200 for admin"""
        response = requests.get(f"{BASE_URL}/api/admin/db/stats", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_db_stats_has_health_score(self, admin_headers):
        """Test that response contains health_score field"""
        response = requests.get(f"{BASE_URL}/api/admin/db/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data, "Response should contain health_score"
        assert isinstance(data["health_score"], (int, float)), "health_score should be numeric"
        assert 0 <= data["health_score"] <= 100, "health_score should be between 0 and 100"
    
    def test_db_stats_has_collections(self, admin_headers):
        """Test that response contains collections array"""
        response = requests.get(f"{BASE_URL}/api/admin/db/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data, "Response should contain collections"
        assert isinstance(data["collections"], list), "collections should be a list"
        assert len(data["collections"]) > 0, "collections should not be empty"
    
    def test_db_stats_has_recommendations(self, admin_headers):
        """Test that response contains recommendations array"""
        response = requests.get(f"{BASE_URL}/api/admin/db/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data, "Response should contain recommendations"
        assert isinstance(data["recommendations"], list), "recommendations should be a list"
    
    def test_db_stats_collection_structure(self, admin_headers):
        """Test that each collection has required fields"""
        response = requests.get(f"{BASE_URL}/api/admin/db/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        for col in data["collections"]:
            assert "name" in col, "Collection should have name"
            assert "count" in col, "Collection should have count"
            assert "data_size_mb" in col, "Collection should have data_size_mb"
            assert "index_size_mb" in col, "Collection should have index_size_mb"
            assert "indexes" in col, "Collection should have indexes"
            assert "index_count" in col, "Collection should have index_count"
    
    def test_db_stats_recommendation_structure(self, admin_headers):
        """Test that each recommendation has required fields"""
        response = requests.get(f"{BASE_URL}/api/admin/db/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        for rec in data["recommendations"]:
            assert "collection" in rec, "Recommendation should have collection"
            assert "name" in rec, "Recommendation should have name"
            assert "keys" in rec, "Recommendation should have keys"
            assert "reason" in rec, "Recommendation should have reason"
            assert "exists" in rec, "Recommendation should have exists"
            assert "priority" in rec, "Recommendation should have priority"
    
    def test_db_stats_has_missing_indexes_count(self, admin_headers):
        """Test that response contains missing_indexes count"""
        response = requests.get(f"{BASE_URL}/api/admin/db/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "missing_indexes" in data, "Response should contain missing_indexes"
        assert "total_recommended" in data, "Response should contain total_recommended"
    
    def test_db_stats_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/db/stats")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"


class TestCreateAllIndexesEndpoint:
    """Tests for POST /api/admin/db/create-all-indexes endpoint"""
    
    def test_create_all_indexes_returns_200(self, admin_headers):
        """Test that create-all-indexes endpoint returns 200"""
        response = requests.post(f"{BASE_URL}/api/admin/db/create-all-indexes", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_create_all_indexes_response_structure(self, admin_headers):
        """Test that response has correct structure"""
        response = requests.post(f"{BASE_URL}/api/admin/db/create-all-indexes", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data, "Response should contain total"
        assert "created" in data, "Response should contain created"
        assert "already_existed" in data, "Response should contain already_existed"
        assert "errors" in data, "Response should contain errors"
        assert "details" in data, "Response should contain details"
    
    def test_create_all_indexes_details_structure(self, admin_headers):
        """Test that details array has correct structure"""
        response = requests.post(f"{BASE_URL}/api/admin/db/create-all-indexes", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        for detail in data["details"]:
            assert "index" in detail, "Detail should have index name"
            assert "collection" in detail, "Detail should have collection"
            assert "status" in detail, "Detail should have status"
            assert detail["status"] in ["created", "exists", "error"], f"Invalid status: {detail['status']}"
    
    def test_create_all_indexes_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/db/create-all-indexes")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"


class TestCreateSingleIndexEndpoint:
    """Tests for POST /api/admin/db/create-index endpoint"""
    
    def test_create_index_with_valid_name(self, admin_headers):
        """Test creating a single index with valid name"""
        response = requests.post(
            f"{BASE_URL}/api/admin/db/create-index",
            headers=admin_headers,
            json={"index_name": "judet_1"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Should either create or already exist
        assert "status" in data or "error" not in data or data.get("status") in ["created", "exists"]
    
    def test_create_index_missing_name(self, admin_headers):
        """Test that missing index_name returns error"""
        response = requests.post(
            f"{BASE_URL}/api/admin/db/create-index",
            headers=admin_headers,
            json={}
        )
        assert response.status_code == 200  # API returns 200 with error in body
        data = response.json()
        assert "error" in data, "Should return error for missing index_name"
    
    def test_create_index_unknown_name(self, admin_headers):
        """Test that unknown index name returns error"""
        response = requests.post(
            f"{BASE_URL}/api/admin/db/create-index",
            headers=admin_headers,
            json={"index_name": "nonexistent_index_xyz"}
        )
        assert response.status_code == 200  # API returns 200 with error in body
        data = response.json()
        assert "error" in data, "Should return error for unknown index"
    
    def test_create_index_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/admin/db/create-index",
            json={"index_name": "judet_1"}
        )
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"


class TestHealthScoreAfterIndexCreation:
    """Test that health score improves after creating indexes"""
    
    def test_health_score_after_create_all(self, admin_headers):
        """Test that health score is 100% after creating all indexes"""
        # First create all indexes
        create_response = requests.post(f"{BASE_URL}/api/admin/db/create-all-indexes", headers=admin_headers)
        assert create_response.status_code == 200
        
        # Then check stats
        stats_response = requests.get(f"{BASE_URL}/api/admin/db/stats", headers=admin_headers)
        assert stats_response.status_code == 200
        data = stats_response.json()
        
        # Health score should be 100% if all indexes exist
        assert data["health_score"] == 100, f"Expected health_score 100, got {data['health_score']}"
        assert data["missing_indexes"] == 0, f"Expected 0 missing indexes, got {data['missing_indexes']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
