"""
Test Location Routes - Browse companies by Judet/Localitate (SIRUTA hierarchy)
Tests: /api/locations/judete, /api/locations/judet/{slug}, /api/locations/judet/{slug}/{localitate}
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestJudeteList:
    """Test GET /api/locations/judete - List all counties"""
    
    def test_judete_returns_200(self):
        """GET /api/locations/judete returns 200"""
        response = requests.get(f"{BASE_URL}/api/locations/judete")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/locations/judete returns 200")
    
    def test_judete_response_structure(self):
        """Response contains total and judete array"""
        response = requests.get(f"{BASE_URL}/api/locations/judete")
        data = response.json()
        
        assert "total" in data, "Response missing 'total' field"
        assert "judete" in data, "Response missing 'judete' array"
        assert isinstance(data["judete"], list), "judete should be a list"
        print(f"✓ Response structure correct: {data['total']} judete")
    
    def test_judete_count_is_42_or_more(self):
        """Romania has 42 counties (41 + Bucuresti)"""
        response = requests.get(f"{BASE_URL}/api/locations/judete")
        data = response.json()
        
        assert data["total"] >= 42, f"Expected at least 42 judete, got {data['total']}"
        print(f"✓ Total judete: {data['total']} (expected >= 42)")
    
    def test_judete_item_structure(self):
        """Each judet has name, slug, company_count"""
        response = requests.get(f"{BASE_URL}/api/locations/judete")
        data = response.json()
        
        for judet in data["judete"][:5]:  # Check first 5
            assert "name" in judet, "Judet missing 'name'"
            assert "slug" in judet, "Judet missing 'slug'"
            assert "company_count" in judet, "Judet missing 'company_count'"
            assert isinstance(judet["company_count"], int), "company_count should be int"
        print("✓ Judet item structure correct (name, slug, company_count)")
    
    def test_bucuresti_is_largest(self):
        """Bucuresti should have the most companies"""
        response = requests.get(f"{BASE_URL}/api/locations/judete")
        data = response.json()
        
        bucuresti = next((j for j in data["judete"] if j["slug"] == "bucuresti"), None)
        assert bucuresti is not None, "Bucuresti not found in judete list"
        assert bucuresti["company_count"] > 400000, f"Bucuresti should have >400k companies, got {bucuresti['company_count']}"
        print(f"✓ Bucuresti has {bucuresti['company_count']} companies (largest)")
    
    def test_harghita_exists(self):
        """Harghita county should exist"""
        response = requests.get(f"{BASE_URL}/api/locations/judete")
        data = response.json()
        
        harghita = next((j for j in data["judete"] if j["slug"] == "harghita"), None)
        assert harghita is not None, "Harghita not found in judete list"
        assert harghita["company_count"] > 20000, f"Harghita should have >20k companies"
        print(f"✓ Harghita found with {harghita['company_count']} companies")


class TestJudetLocalities:
    """Test GET /api/locations/judet/{slug} - List localities in a county"""
    
    def test_harghita_returns_200(self):
        """GET /api/locations/judet/harghita returns 200"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/locations/judet/harghita returns 200")
    
    def test_harghita_response_structure(self):
        """Response contains judet, localities, totals"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita")
        data = response.json()
        
        assert "judet" in data, "Response missing 'judet'"
        assert "judet_slug" in data, "Response missing 'judet_slug'"
        assert "total_localities" in data, "Response missing 'total_localities'"
        assert "total_companies" in data, "Response missing 'total_companies'"
        assert "localities" in data, "Response missing 'localities'"
        print(f"✓ Harghita: {data['total_localities']} localities, {data['total_companies']} companies")
    
    def test_harghita_localities_structure(self):
        """Each locality has name, slug, company_count"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita")
        data = response.json()
        
        for loc in data["localities"][:5]:
            assert "name" in loc, "Locality missing 'name'"
            assert "slug" in loc, "Locality missing 'slug'"
            assert "company_count" in loc, "Locality missing 'company_count'"
        print("✓ Locality structure correct (name, slug, company_count)")
    
    def test_toplita_in_harghita(self):
        """Toplita should be in Harghita localities"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita")
        data = response.json()
        
        toplita = next((l for l in data["localities"] if l["slug"] == "toplita"), None)
        assert toplita is not None, "Toplita not found in Harghita localities"
        assert toplita["company_count"] > 500, f"Toplita should have >500 companies"
        print(f"✓ Toplita found with {toplita['company_count']} companies")
    
    def test_bucuresti_sectors(self):
        """Bucuresti should have 6 sectors"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/bucuresti")
        data = response.json()
        
        assert data["total_localities"] >= 6, f"Bucuresti should have at least 6 sectors"
        sectors = [l for l in data["localities"] if "sectorul" in l["slug"]]
        assert len(sectors) >= 6, f"Expected 6 sectors, found {len(sectors)}"
        print(f"✓ Bucuresti has {len(sectors)} sectors")
    
    def test_invalid_judet_returns_error(self):
        """Invalid judet slug returns error"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/invalid-judet-xyz")
        data = response.json()
        
        assert "error" in data, "Expected error for invalid judet"
        print("✓ Invalid judet returns error message")


class TestLocalityCompanies:
    """Test GET /api/locations/judet/{slug}/{localitate} - List companies in locality"""
    
    def test_toplita_returns_200(self):
        """GET /api/locations/judet/harghita/toplita returns 200"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita/toplita")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/locations/judet/harghita/toplita returns 200")
    
    def test_toplita_response_structure(self):
        """Response contains judet, localitate, companies, pagination"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita/toplita")
        data = response.json()
        
        assert "judet" in data, "Response missing 'judet'"
        assert "judet_slug" in data, "Response missing 'judet_slug'"
        assert "localitate" in data, "Response missing 'localitate'"
        assert "localitate_slug" in data, "Response missing 'localitate_slug'"
        assert "total" in data, "Response missing 'total'"
        assert "skip" in data, "Response missing 'skip'"
        assert "limit" in data, "Response missing 'limit'"
        assert "companies" in data, "Response missing 'companies'"
        print(f"✓ Toplita: {data['total']} companies")
    
    def test_toplita_company_structure(self):
        """Each company has required fields"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita/toplita")
        data = response.json()
        
        assert len(data["companies"]) > 0, "No companies returned"
        company = data["companies"][0]
        
        required_fields = ["cui", "denumire", "slug"]
        for field in required_fields:
            assert field in company, f"Company missing '{field}'"
        
        # Check optional but expected fields
        expected_fields = ["anaf_stare", "anaf_cod_caen", "mf_cifra_afaceri", "dosare_count", "has_legal_issues"]
        for field in expected_fields:
            if field in company:
                print(f"  - {field}: present")
        
        print("✓ Company structure correct (cui, denumire, slug + optional fields)")
    
    def test_search_by_cui(self):
        """Search by CUI within locality works"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita/toplita?q=37044065")
        data = response.json()
        
        assert data["total"] == 1, f"Expected 1 result for CUI 37044065, got {data['total']}"
        assert data["companies"][0]["cui"] == "37044065", "Wrong company returned"
        assert "S.O.S. UTILAJE" in data["companies"][0]["denumire"], "Wrong company name"
        print(f"✓ Search by CUI 37044065 returns: {data['companies'][0]['denumire']}")
    
    def test_search_by_cui_has_legal_issues(self):
        """Company 37044065 has legal issues (dosare)"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita/toplita?q=37044065")
        data = response.json()
        
        company = data["companies"][0]
        assert company.get("has_legal_issues") == True, "Company should have legal issues"
        assert company.get("dosare_count", 0) > 0, "Company should have dosare_count > 0"
        print(f"✓ Company 37044065 has {company.get('dosare_count')} dosare (has_legal_issues=True)")
    
    def test_pagination_works(self):
        """Pagination with skip/limit works"""
        # Get first page
        response1 = requests.get(f"{BASE_URL}/api/locations/judet/harghita/toplita?skip=0&limit=10")
        data1 = response1.json()
        
        # Get second page
        response2 = requests.get(f"{BASE_URL}/api/locations/judet/harghita/toplita?skip=10&limit=10")
        data2 = response2.json()
        
        assert len(data1["companies"]) == 10, "First page should have 10 companies"
        assert len(data2["companies"]) == 10, "Second page should have 10 companies"
        
        # Companies should be different
        cuis1 = {c["cui"] for c in data1["companies"]}
        cuis2 = {c["cui"] for c in data2["companies"]}
        assert cuis1.isdisjoint(cuis2), "Pages should have different companies"
        print("✓ Pagination works (different companies on different pages)")
    
    def test_invalid_locality_returns_error(self):
        """Invalid locality slug returns error"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita/invalid-locality-xyz")
        data = response.json()
        
        assert "error" in data, "Expected error for invalid locality"
        print("✓ Invalid locality returns error message")
    
    def test_company_slug_format(self):
        """Company slug is in format: name-slug-cui"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/harghita/toplita?limit=5")
        data = response.json()
        
        for company in data["companies"]:
            slug = company.get("slug", "")
            cui = company.get("cui", "")
            assert slug.endswith(f"-{cui}"), f"Slug should end with CUI: {slug}"
        print("✓ Company slugs are in correct format (name-cui)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
