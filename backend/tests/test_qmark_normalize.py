"""
Test Question-Mark to Ș/Ț Normalization Feature
Tests for qmark-preview and qmark-normalize endpoints
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
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture
def admin_headers(admin_token):
    """Headers with admin auth token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestQmarkPreviewEndpoint:
    """Tests for GET /api/admin/db/qmark-preview endpoint"""
    
    def test_qmark_preview_returns_200(self, admin_headers):
        """Test that qmark-preview endpoint returns 200 for admin"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_qmark_preview_response_structure(self, admin_headers):
        """Test that response has correct structure with totals and items"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total" in data, "Response should contain total"
        assert "high_confidence" in data, "Response should contain high_confidence"
        assert "medium_confidence" in data, "Response should contain medium_confidence"
        assert "low_confidence" in data, "Response should contain low_confidence"
        assert "items" in data, "Response should contain items"
        
        # Verify counts are integers
        assert isinstance(data["total"], int), "total should be integer"
        assert isinstance(data["high_confidence"], int), "high_confidence should be integer"
        assert isinstance(data["medium_confidence"], int), "medium_confidence should be integer"
        assert isinstance(data["low_confidence"], int), "low_confidence should be integer"
    
    def test_qmark_preview_confidence_counts_sum(self, admin_headers):
        """Test that confidence counts sum to total"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        expected_total = data["high_confidence"] + data["medium_confidence"] + data["low_confidence"]
        assert data["total"] == expected_total, f"Total {data['total']} should equal sum of confidence counts {expected_total}"
    
    def test_qmark_preview_item_structure(self, admin_headers):
        """Test that each item has required fields"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["total"] > 0:
            for item in data["items"][:10]:  # Check first 10 items
                assert "cui" in item, "Item should have cui"
                assert "old_denumire" in item, "Item should have old_denumire"
                assert "new_denumire" in item, "Item should have new_denumire"
                assert "changes" in item, "Item should have changes"
                assert "confidence" in item, "Item should have confidence"
                assert item["confidence"] in ["high", "medium", "low"], f"Invalid confidence: {item['confidence']}"
    
    def test_qmark_preview_changes_structure(self, admin_headers):
        """Test that changes array has correct structure"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        if data["total"] > 0:
            for item in data["items"][:5]:
                for change in item["changes"]:
                    assert "pos" in change, "Change should have pos"
                    assert "replacement" in change, "Change should have replacement"
                    assert "confidence" in change, "Change should have confidence"
                    assert "context" in change, "Change should have context"
                    assert change["replacement"] in ["Ș", "Ț"], f"Invalid replacement: {change['replacement']}"
    
    def test_qmark_preview_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview")
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"


class TestQmarkHeuristicCorrectness:
    """Tests for heuristic correctness of ? → Ș/Ț replacements"""
    
    def test_serban_becomes_serban_with_s_cedilla(self, admin_headers):
        """Test that ?ERBAN → ȘERBAN (high confidence)"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Find items with ERBAN pattern
        serban_items = [i for i in data["items"] if "ERBAN" in i["old_denumire"] and i["old_denumire"].startswith("?")]
        if serban_items:
            for item in serban_items[:3]:
                assert item["new_denumire"].startswith("Ș"), f"?ERBAN should become ȘERBAN, got {item['new_denumire']}"
                assert item["confidence"] == "high", f"?ERBAN should be high confidence, got {item['confidence']}"
    
    def test_stefan_becomes_stefan_with_s_cedilla(self, admin_headers):
        """Test that ?TEFAN → ȘTEFAN (high confidence)"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Find items with TEFAN pattern
        stefan_items = [i for i in data["items"] if "TEFAN" in i["old_denumire"] and "?" in i["old_denumire"]]
        if stefan_items:
            for item in stefan_items[:3]:
                assert "ȘTEFAN" in item["new_denumire"], f"?TEFAN should become ȘTEFAN, got {item['new_denumire']}"
    
    def test_doruta_becomes_doruta_with_t_cedilla(self, admin_headers):
        """Test that DORU?A → DORUȚA (high confidence)"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Find items with DORU?A pattern
        doruta_items = [i for i in data["items"] if "DORU?A" in i["old_denumire"]]
        if doruta_items:
            for item in doruta_items:
                assert "DORUȚA" in item["new_denumire"], f"DORU?A should become DORUȚA, got {item['new_denumire']}"
    
    def test_gheorghita_becomes_gheorghita_with_t_cedilla(self, admin_headers):
        """Test that GHEORGHI?A → GHEORGHIȚA (high confidence)"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Find items with GHEORGHI?A pattern
        gheorghita_items = [i for i in data["items"] if "GHEORGHI?A" in i["old_denumire"]]
        if gheorghita_items:
            for item in gheorghita_items:
                assert "GHEORGHIȚA" in item["new_denumire"], f"GHEORGHI?A should become GHEORGHIȚA, got {item['new_denumire']}"
    
    def test_tigan_becomes_tigan_with_t_cedilla(self, admin_headers):
        """Test that ?IGAN → ȚIGAN (high confidence)"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Find items with IGAN pattern at start
        tigan_items = [i for i in data["items"] if i["old_denumire"].startswith("?IGAN")]
        if tigan_items:
            for item in tigan_items:
                assert item["new_denumire"].startswith("ȚIGAN"), f"?IGAN should become ȚIGAN, got {item['new_denumire']}"
                assert item["confidence"] == "high", f"?IGAN should be high confidence, got {item['confidence']}"
    
    def test_taran_becomes_taran_with_t_cedilla(self, admin_headers):
        """Test that ?ĂRAN → ȚĂRAN (high confidence)"""
        response = requests.get(f"{BASE_URL}/api/admin/db/qmark-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Find items with ĂRAN pattern at start
        taran_items = [i for i in data["items"] if i["old_denumire"].startswith("?ĂRAN")]
        if taran_items:
            for item in taran_items:
                assert item["new_denumire"].startswith("ȚĂRAN"), f"?ĂRAN should become ȚĂRAN, got {item['new_denumire']}"
                assert item["confidence"] == "high", f"?ĂRAN should be high confidence, got {item['confidence']}"


class TestQmarkNormalizeEndpoint:
    """Tests for POST /api/admin/db/qmark-normalize endpoint"""
    
    def test_qmark_normalize_returns_200(self, admin_headers):
        """Test that qmark-normalize endpoint returns 200 for admin"""
        response = requests.post(
            f"{BASE_URL}/api/admin/db/qmark-normalize",
            headers=admin_headers,
            json={}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_qmark_normalize_response_structure(self, admin_headers):
        """Test that response has correct structure"""
        response = requests.post(
            f"{BASE_URL}/api/admin/db/qmark-normalize",
            headers=admin_headers,
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total_processed" in data, "Response should contain total_processed"
        assert "updated" in data, "Response should contain updated"
        assert "errors" in data, "Response should contain errors"
        assert "details" in data, "Response should contain details"
        
        # Verify types
        assert isinstance(data["total_processed"], int), "total_processed should be integer"
        assert isinstance(data["updated"], int), "updated should be integer"
        assert isinstance(data["errors"], int), "errors should be integer"
        assert isinstance(data["details"], list), "details should be list"
    
    def test_qmark_normalize_details_structure(self, admin_headers):
        """Test that details array has correct structure"""
        response = requests.post(
            f"{BASE_URL}/api/admin/db/qmark-normalize",
            headers=admin_headers,
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["details"]:
            for detail in data["details"][:10]:
                assert "cui" in detail, "Detail should have cui"
                assert "old" in detail, "Detail should have old"
                assert "new" in detail, "Detail should have new"
                assert "status" in detail, "Detail should have status"
                assert detail["status"] in ["ok", "not_found", "error"], f"Invalid status: {detail['status']}"
    
    def test_qmark_normalize_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/db/qmark-normalize", json={})
        assert response.status_code in [401, 403, 422], f"Expected auth error, got {response.status_code}"
    
    def test_qmark_normalize_with_overrides(self, admin_headers):
        """Test that overrides parameter is accepted"""
        response = requests.post(
            f"{BASE_URL}/api/admin/db/qmark-normalize",
            headers=admin_headers,
            json={"overrides": {"12345": "TEST COMPANY NAME"}}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestExistingDiacriticsNormalization:
    """Tests for existing diacritics normalization (ş→ș, ţ→ț) still works"""
    
    def test_normalize_preview_returns_200(self, admin_headers):
        """Test that normalize-preview endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/admin/db/normalize-preview", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_normalize_preview_response_structure(self, admin_headers):
        """Test that normalize-preview has correct structure"""
        response = requests.get(f"{BASE_URL}/api/admin/db/normalize-preview", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "changes" in data, "Response should contain changes"
        assert "total_changes" in data, "Response should contain total_changes"
        assert "total_affected_docs" in data, "Response should contain total_affected_docs"
    
    def test_normalize_diacritics_returns_200(self, admin_headers):
        """Test that normalize-diacritics endpoint returns 200"""
        response = requests.post(
            f"{BASE_URL}/api/admin/db/normalize-diacritics",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_normalize_diacritics_response_structure(self, admin_headers):
        """Test that normalize-diacritics has correct structure"""
        response = requests.post(
            f"{BASE_URL}/api/admin/db/normalize-diacritics",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_modified" in data, "Response should contain total_modified"
        assert "details" in data, "Response should contain details"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
