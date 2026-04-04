"""
Test Legal Routes - Dosare & BPI API endpoints
Tests for court cases (dosare) and insolvency records (BPI) endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://rapoarte-seo.preview.emergentagent.com').rstrip('/')

# Test company CUI - AUTOMOB SOCIETATE COOPERATIVA
TEST_CUI = "2113693"
TEST_COMPANY_NAME = "AUTOMOB"


class TestLegalSummaryEndpoint:
    """Tests for GET /api/legal/summary/{cui}"""
    
    def test_legal_summary_returns_200(self):
        """Test that legal summary endpoint returns 200 for valid CUI"""
        response = requests.get(f"{BASE_URL}/api/legal/summary/{TEST_CUI}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Legal summary endpoint returns 200 for CUI {TEST_CUI}")
    
    def test_legal_summary_response_structure(self):
        """Test that legal summary returns correct JSON structure"""
        response = requests.get(f"{BASE_URL}/api/legal/summary/{TEST_CUI}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields exist
        required_fields = ['cui', 'dosare_count', 'bpi_count', 'in_insolventa', 'has_legal_issues']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(data['dosare_count'], int), "dosare_count should be int"
        assert isinstance(data['bpi_count'], int), "bpi_count should be int"
        assert isinstance(data['in_insolventa'], bool), "in_insolventa should be bool"
        assert isinstance(data['has_legal_issues'], bool), "has_legal_issues should be bool"
        
        print(f"✓ Legal summary response structure is correct")
        print(f"  - dosare_count: {data['dosare_count']}")
        print(f"  - bpi_count: {data['bpi_count']}")
        print(f"  - in_insolventa: {data['in_insolventa']}")
        print(f"  - has_legal_issues: {data['has_legal_issues']}")
    
    def test_legal_summary_with_nonexistent_cui(self):
        """Test legal summary with non-existent CUI returns proper response"""
        response = requests.get(f"{BASE_URL}/api/legal/summary/9999999999")
        assert response.status_code == 200, "Should return 200 even for non-existent CUI"
        
        data = response.json()
        # Should return zeros for non-existent company
        assert data['dosare_count'] == 0
        assert data['bpi_count'] == 0
        print("✓ Legal summary handles non-existent CUI gracefully")


class TestDosareEndpoint:
    """Tests for GET /api/legal/dosare/{cui}"""
    
    def test_dosare_returns_200(self):
        """Test that dosare endpoint returns 200 for valid CUI"""
        response = requests.get(f"{BASE_URL}/api/legal/dosare/{TEST_CUI}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Dosare endpoint returns 200 for CUI {TEST_CUI}")
    
    def test_dosare_response_structure(self):
        """Test that dosare returns correct JSON structure"""
        response = requests.get(f"{BASE_URL}/api/legal/dosare/{TEST_CUI}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields
        required_fields = ['cui', 'firma_found', 'total', 'dosare']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify dosare is a list
        assert isinstance(data['dosare'], list), "dosare should be a list"
        assert isinstance(data['total'], int), "total should be int"
        
        print(f"✓ Dosare response structure is correct")
        print(f"  - firma_found: {data['firma_found']}")
        print(f"  - total: {data['total']}")
        print(f"  - dosare count: {len(data['dosare'])}")
    
    def test_dosare_pagination_params(self):
        """Test dosare endpoint accepts pagination parameters"""
        response = requests.get(f"{BASE_URL}/api/legal/dosare/{TEST_CUI}?limit=5&skip=0")
        assert response.status_code == 200
        
        data = response.json()
        assert 'limit' in data
        assert 'skip' in data
        assert data['limit'] == 5
        assert data['skip'] == 0
        print("✓ Dosare pagination parameters work correctly")
    
    def test_dosare_with_nonexistent_cui(self):
        """Test dosare with non-existent CUI returns proper response"""
        response = requests.get(f"{BASE_URL}/api/legal/dosare/9999999999")
        assert response.status_code == 200
        
        data = response.json()
        assert data['firma_found'] == False
        assert data['total'] == 0
        assert data['dosare'] == []
        print("✓ Dosare handles non-existent CUI gracefully")


class TestBpiEndpoint:
    """Tests for GET /api/legal/bpi/{cui}"""
    
    def test_bpi_returns_200(self):
        """Test that BPI endpoint returns 200 for valid CUI"""
        response = requests.get(f"{BASE_URL}/api/legal/bpi/{TEST_CUI}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ BPI endpoint returns 200 for CUI {TEST_CUI}")
    
    def test_bpi_response_structure(self):
        """Test that BPI returns correct JSON structure"""
        response = requests.get(f"{BASE_URL}/api/legal/bpi/{TEST_CUI}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields
        required_fields = ['cui', 'total', 'records']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify records is a list
        assert isinstance(data['records'], list), "records should be a list"
        assert isinstance(data['total'], int), "total should be int"
        
        print(f"✓ BPI response structure is correct")
        print(f"  - total: {data['total']}")
        print(f"  - records count: {len(data['records'])}")
    
    def test_bpi_pagination_params(self):
        """Test BPI endpoint accepts pagination parameters"""
        response = requests.get(f"{BASE_URL}/api/legal/bpi/{TEST_CUI}?limit=10&skip=0")
        assert response.status_code == 200
        
        data = response.json()
        assert 'showing' in data
        print("✓ BPI pagination parameters work correctly")
    
    def test_bpi_with_nonexistent_cui(self):
        """Test BPI with non-existent CUI returns proper response"""
        response = requests.get(f"{BASE_URL}/api/legal/bpi/9999999999")
        assert response.status_code == 200
        
        data = response.json()
        assert data['total'] == 0
        assert data['records'] == []
        print("✓ BPI handles non-existent CUI gracefully")


class TestLichidatoriEndpoint:
    """Tests for GET /api/legal/lichidatori/{cui}"""
    
    def test_lichidatori_returns_200(self):
        """Test that lichidatori endpoint returns 200 for valid CUI"""
        response = requests.get(f"{BASE_URL}/api/legal/lichidatori/{TEST_CUI}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Lichidatori endpoint returns 200 for CUI {TEST_CUI}")
    
    def test_lichidatori_response_structure(self):
        """Test that lichidatori returns correct JSON structure"""
        response = requests.get(f"{BASE_URL}/api/legal/lichidatori/{TEST_CUI}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields
        required_fields = ['cui', 'total', 'lichidatori']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify lichidatori is a list
        assert isinstance(data['lichidatori'], list), "lichidatori should be a list"
        assert isinstance(data['total'], int), "total should be int"
        
        print(f"✓ Lichidatori response structure is correct")
        print(f"  - total: {data['total']}")
        print(f"  - lichidatori count: {len(data['lichidatori'])}")
    
    def test_lichidatori_with_nonexistent_cui(self):
        """Test lichidatori with non-existent CUI returns proper response"""
        response = requests.get(f"{BASE_URL}/api/legal/lichidatori/9999999999")
        assert response.status_code == 200
        
        data = response.json()
        assert data['total'] == 0
        assert data['lichidatori'] == []
        print("✓ Lichidatori handles non-existent CUI gracefully")


class TestCompanyPageIntegration:
    """Tests for company page that uses legal info"""
    
    def test_company_slug_endpoint_works(self):
        """Test that company slug endpoint works for test company"""
        slug = "automob-societate-cooperativa-2113693"
        response = requests.get(f"{BASE_URL}/api/company/slug/{slug}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'cui' in data
        assert data['cui'] == TEST_CUI
        print(f"✓ Company slug endpoint works for {slug}")
    
    def test_company_cui_endpoint_works(self):
        """Test that company CUI endpoint works"""
        response = requests.get(f"{BASE_URL}/api/company/cui/{TEST_CUI}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'denumire' in data
        assert TEST_COMPANY_NAME in data['denumire'].upper()
        print(f"✓ Company CUI endpoint works for {TEST_CUI}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
