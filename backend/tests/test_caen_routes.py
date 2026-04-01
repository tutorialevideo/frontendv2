"""
Test CAEN Routes - Browse companies by CAEN activity code
Tests: /api/caen/codes, /api/caen/sections, /api/caen/code/{cod}
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCaenSections:
    """Test CAEN sections endpoint (A, B, C, etc.)"""
    
    def test_get_sections_returns_200(self):
        """GET /api/caen/sections returns 200"""
        response = requests.get(f"{BASE_URL}/api/caen/sections")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/caen/sections returns 200")
    
    def test_sections_response_structure(self):
        """Response contains total and sections array"""
        response = requests.get(f"{BASE_URL}/api/caen/sections")
        data = response.json()
        assert "total" in data, "Response missing 'total' field"
        assert "sections" in data, "Response missing 'sections' field"
        assert isinstance(data["sections"], list), "sections should be a list"
        print(f"✓ Response has total={data['total']} and sections array")
    
    def test_sections_have_required_fields(self):
        """Each section has sectiune, denumire, codes_count"""
        response = requests.get(f"{BASE_URL}/api/caen/sections")
        data = response.json()
        assert len(data["sections"]) > 0, "No sections returned"
        for section in data["sections"][:5]:  # Check first 5
            assert "sectiune" in section, f"Section missing 'sectiune': {section}"
            assert "denumire" in section, f"Section missing 'denumire': {section}"
            assert "codes_count" in section, f"Section missing 'codes_count': {section}"
        print(f"✓ Sections have required fields (checked {min(5, len(data['sections']))} sections)")
    
    def test_section_i_exists(self):
        """Section I (Hoteluri si restaurante) exists"""
        response = requests.get(f"{BASE_URL}/api/caen/sections")
        data = response.json()
        section_i = next((s for s in data["sections"] if s["sectiune"] == "I"), None)
        assert section_i is not None, "Section I not found"
        print(f"✓ Section I found: {section_i['denumire']} ({section_i['codes_count']} codes)")


class TestCaenCodes:
    """Test CAEN codes list endpoint"""
    
    def test_get_codes_returns_200(self):
        """GET /api/caen/codes returns 200"""
        response = requests.get(f"{BASE_URL}/api/caen/codes", timeout=60)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/caen/codes returns 200")
    
    def test_codes_response_structure(self):
        """Response contains total and codes array"""
        response = requests.get(f"{BASE_URL}/api/caen/codes", timeout=60)
        data = response.json()
        assert "total" in data, "Response missing 'total' field"
        assert "codes" in data, "Response missing 'codes' field"
        assert isinstance(data["codes"], list), "codes should be a list"
        print(f"✓ Response has total={data['total']} codes")
    
    def test_codes_have_required_fields(self):
        """Each code has cod, denumire, sectiune, company_count"""
        response = requests.get(f"{BASE_URL}/api/caen/codes", timeout=60)
        data = response.json()
        assert len(data["codes"]) > 0, "No codes returned"
        for code in data["codes"][:5]:  # Check first 5
            assert "cod" in code, f"Code missing 'cod': {code}"
            assert "denumire" in code, f"Code missing 'denumire': {code}"
            assert "company_count" in code, f"Code missing 'company_count': {code}"
        print(f"✓ Codes have required fields (checked {min(5, len(data['codes']))} codes)")
    
    def test_filter_by_section_i(self):
        """GET /api/caen/codes?sectiune=I filters by section"""
        response = requests.get(f"{BASE_URL}/api/caen/codes?sectiune=I", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert len(data["codes"]) > 0, "No codes returned for section I"
        for code in data["codes"]:
            assert code["sectiune"] == "I", f"Code {code['cod']} has wrong section: {code['sectiune']}"
        print(f"✓ Section I filter returns {len(data['codes'])} codes, all with sectiune=I")
    
    def test_search_caen_codes(self):
        """GET /api/caen/codes?q=cazare searches CAEN codes"""
        response = requests.get(f"{BASE_URL}/api/caen/codes?q=cazare", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert len(data["codes"]) > 0, "No codes found for 'cazare'"
        # Check that results contain 'cazare' in denumire or cod
        found_match = False
        for code in data["codes"]:
            if "cazare" in code.get("denumire", "").lower() or "cazare" in code.get("cod", "").lower():
                found_match = True
                break
        assert found_match, "Search results don't contain 'cazare'"
        print(f"✓ Search 'cazare' returns {len(data['codes'])} codes")
    
    def test_caen_5520_exists(self):
        """CAEN code 5520 (Facilitati de cazare pentru vacante) exists"""
        response = requests.get(f"{BASE_URL}/api/caen/codes?q=5520", timeout=60)
        assert response.status_code == 200
        data = response.json()
        code_5520 = next((c for c in data["codes"] if c["cod"] == "5520"), None)
        assert code_5520 is not None, "CAEN 5520 not found"
        assert code_5520["company_count"] > 0, "CAEN 5520 has no companies"
        print(f"✓ CAEN 5520 found: {code_5520['denumire']} ({code_5520['company_count']} companies)")


class TestCaenCodeCompanies:
    """Test companies by CAEN code endpoint"""
    
    def test_get_companies_by_caen_returns_200(self):
        """GET /api/caen/code/5520 returns 200"""
        response = requests.get(f"{BASE_URL}/api/caen/code/5520")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/caen/code/5520 returns 200")
    
    def test_companies_response_structure(self):
        """Response contains caen, total, companies, top_judete"""
        response = requests.get(f"{BASE_URL}/api/caen/code/5520")
        data = response.json()
        assert "caen" in data, "Response missing 'caen' field"
        assert "total" in data, "Response missing 'total' field"
        assert "companies" in data, "Response missing 'companies' field"
        assert "top_judete" in data, "Response missing 'top_judete' field"
        assert isinstance(data["companies"], list), "companies should be a list"
        assert isinstance(data["top_judete"], list), "top_judete should be a list"
        print(f"✓ Response has caen info, total={data['total']}, companies and top_judete")
    
    def test_caen_info_correct(self):
        """CAEN info contains cod, denumire, sectiune"""
        response = requests.get(f"{BASE_URL}/api/caen/code/5520")
        data = response.json()
        caen = data["caen"]
        assert caen["cod"] == "5520", f"Expected cod=5520, got {caen['cod']}"
        assert "denumire" in caen, "CAEN info missing 'denumire'"
        print(f"✓ CAEN info: {caen['cod']} - {caen.get('denumire', 'N/A')}")
    
    def test_companies_have_required_fields(self):
        """Each company has cui, denumire, slug, judet"""
        response = requests.get(f"{BASE_URL}/api/caen/code/5520")
        data = response.json()
        assert len(data["companies"]) > 0, "No companies returned"
        for company in data["companies"][:5]:  # Check first 5
            assert "cui" in company, f"Company missing 'cui': {company}"
            assert "denumire" in company, f"Company missing 'denumire': {company}"
            assert "slug" in company, f"Company missing 'slug': {company}"
        print(f"✓ Companies have required fields (checked {min(5, len(data['companies']))} companies)")
    
    def test_top_judete_structure(self):
        """Top judete has judet and count fields"""
        response = requests.get(f"{BASE_URL}/api/caen/code/5520")
        data = response.json()
        assert len(data["top_judete"]) > 0, "No top_judete returned"
        for judet in data["top_judete"]:
            assert "judet" in judet, f"Judet missing 'judet': {judet}"
            assert "count" in judet, f"Judet missing 'count': {judet}"
        print(f"✓ Top judete: {[j['judet'] for j in data['top_judete'][:5]]}")
    
    def test_filter_by_judet(self):
        """GET /api/caen/code/5520?judet=Brasov filters by judet"""
        response = requests.get(f"{BASE_URL}/api/caen/code/5520?judet=Brasov")
        assert response.status_code == 200
        data = response.json()
        # All returned companies should be from Brasov
        for company in data["companies"]:
            assert "brasov" in company.get("judet", "").lower(), f"Company not from Brasov: {company.get('judet')}"
        print(f"✓ Judet filter returns {data['total']} companies from Brasov")
    
    def test_search_by_cui(self):
        """GET /api/caen/code/5520?q=37044065 searches by CUI"""
        response = requests.get(f"{BASE_URL}/api/caen/code/5520?q=37044065")
        assert response.status_code == 200
        data = response.json()
        # Should find the specific company
        if data["total"] > 0:
            found = any(c.get("cui") == "37044065" for c in data["companies"])
            assert found, "CUI 37044065 not found in results"
            print(f"✓ Search by CUI 37044065 found company")
        else:
            print(f"⚠ CUI 37044065 not found with CAEN 5520 (may have different CAEN)")
    
    def test_pagination(self):
        """Pagination works (skip/limit)"""
        response1 = requests.get(f"{BASE_URL}/api/caen/code/5520?skip=0&limit=10")
        response2 = requests.get(f"{BASE_URL}/api/caen/code/5520?skip=10&limit=10")
        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        # Different companies on different pages
        if len(data1["companies"]) > 0 and len(data2["companies"]) > 0:
            cuis1 = {c["cui"] for c in data1["companies"]}
            cuis2 = {c["cui"] for c in data2["companies"]}
            assert cuis1 != cuis2, "Same companies on different pages"
            print(f"✓ Pagination works: page 1 has {len(data1['companies'])} companies, page 2 has {len(data2['companies'])} different companies")
        else:
            print("⚠ Not enough companies to test pagination")
    
    def test_invalid_caen_code(self):
        """GET /api/caen/code/99999 returns empty results"""
        response = requests.get(f"{BASE_URL}/api/caen/code/99999")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0, f"Expected 0 companies for invalid CAEN, got {data['total']}"
        print("✓ Invalid CAEN code returns 0 companies")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
