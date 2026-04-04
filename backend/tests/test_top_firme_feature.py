"""
Test Top Firme Feature - Sorting and Pagination on Judet, Localitate, and CAEN pages
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestJudetTopFirme:
    """Tests for /api/locations/judet/{slug}/top-firme endpoint"""
    
    def test_top_firme_default_sort_cifra_afaceri(self):
        """Top firme should default sort by cifra_afaceri descending"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/teleorman/top-firme?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "companies" in data
        assert "total" in data
        assert "judet" in data
        assert data["sort"] == "cifra_afaceri"
        
        companies = data["companies"]
        assert len(companies) > 0
        
        # Verify descending order by cifra_afaceri
        for i in range(len(companies) - 1):
            curr = companies[i].get("mf_cifra_afaceri") or 0
            next_val = companies[i+1].get("mf_cifra_afaceri") or 0
            assert curr >= next_val, f"Companies not sorted by cifra_afaceri: {curr} < {next_val}"
    
    def test_top_firme_sort_by_angajati(self):
        """Top firme should sort by angajati when specified"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/teleorman/top-firme?limit=5&sort=angajati")
        assert response.status_code == 200
        
        data = response.json()
        assert data["sort"] == "angajati"
        
        companies = data["companies"]
        assert len(companies) > 0
        
        # Verify descending order by angajati
        for i in range(len(companies) - 1):
            curr = companies[i].get("mf_numar_angajati") or 0
            next_val = companies[i+1].get("mf_numar_angajati") or 0
            assert curr >= next_val, f"Companies not sorted by angajati: {curr} < {next_val}"
    
    def test_top_firme_sort_by_profit(self):
        """Top firme should sort by profit when specified"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/teleorman/top-firme?limit=5&sort=profit")
        assert response.status_code == 200
        
        data = response.json()
        assert data["sort"] == "profit"
        
        companies = data["companies"]
        assert len(companies) > 0
        
        # Verify descending order by profit
        for i in range(len(companies) - 1):
            curr = companies[i].get("mf_profit_net") or 0
            next_val = companies[i+1].get("mf_profit_net") or 0
            assert curr >= next_val, f"Companies not sorted by profit: {curr} < {next_val}"
    
    def test_top_firme_has_rank(self):
        """Top firme companies should have rank field"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/teleorman/top-firme?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        companies = data["companies"]
        
        for i, company in enumerate(companies):
            assert "rank" in company
            assert company["rank"] == i + 1
    
    def test_top_firme_pagination(self):
        """Top firme should support pagination"""
        # First page
        response1 = requests.get(f"{BASE_URL}/api/locations/judet/teleorman/top-firme?skip=0&limit=3")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second page
        response2 = requests.get(f"{BASE_URL}/api/locations/judet/teleorman/top-firme?skip=3&limit=3")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify different companies
        cuis1 = [c["cui"] for c in data1["companies"]]
        cuis2 = [c["cui"] for c in data2["companies"]]
        
        assert len(set(cuis1) & set(cuis2)) == 0, "Pagination returned duplicate companies"
        
        # Verify ranks continue
        assert data2["companies"][0]["rank"] == 4


class TestLocalitateSort:
    """Tests for /api/locations/judet/{slug}/{localitate} sort parameter"""
    
    def test_localitate_default_sort_cifra_afaceri(self):
        """Localitate should default sort by cifra_afaceri"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/teleorman/alexandria?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert data["sort"] == "cifra_afaceri"
        
        companies = data["companies"]
        assert len(companies) > 0
        
        # Verify descending order
        for i in range(len(companies) - 1):
            curr = companies[i].get("mf_cifra_afaceri") or 0
            next_val = companies[i+1].get("mf_cifra_afaceri") or 0
            assert curr >= next_val
    
    def test_localitate_sort_by_angajati(self):
        """Localitate should sort by angajati when specified"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/teleorman/alexandria?limit=5&sort=angajati")
        assert response.status_code == 200
        
        data = response.json()
        assert data["sort"] == "angajati"
        
        companies = data["companies"]
        for i in range(len(companies) - 1):
            curr = companies[i].get("mf_numar_angajati") or 0
            next_val = companies[i+1].get("mf_numar_angajati") or 0
            assert curr >= next_val
    
    def test_localitate_sort_alfabetic(self):
        """Localitate should sort alphabetically when specified"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/teleorman/alexandria?limit=5&sort=alfabetic")
        assert response.status_code == 200
        
        data = response.json()
        assert data["sort"] == "alfabetic"
        
        companies = data["companies"]
        for i in range(len(companies) - 1):
            curr = companies[i].get("denumire", "").lower()
            next_val = companies[i+1].get("denumire", "").lower()
            assert curr <= next_val, f"Not alphabetically sorted: {curr} > {next_val}"


class TestCaenSort:
    """Tests for /api/caen/code/{cod} sort parameter"""
    
    def test_caen_default_sort_cifra_afaceri(self):
        """CAEN should default sort by cifra_afaceri"""
        response = requests.get(f"{BASE_URL}/api/caen/code/4932?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        # Note: CAEN endpoint doesn't return sort field in response, but should sort by cifra_afaceri
        
        companies = data["companies"]
        assert len(companies) > 0
        
        # Verify descending order
        for i in range(len(companies) - 1):
            curr = companies[i].get("mf_cifra_afaceri") or 0
            next_val = companies[i+1].get("mf_cifra_afaceri") or 0
            assert curr >= next_val
    
    def test_caen_sort_by_angajati(self):
        """CAEN should sort by angajati when specified"""
        response = requests.get(f"{BASE_URL}/api/caen/code/4932?limit=5&sort=angajati")
        assert response.status_code == 200
        
        data = response.json()
        companies = data["companies"]
        
        for i in range(len(companies) - 1):
            curr = companies[i].get("mf_numar_angajati") or 0
            next_val = companies[i+1].get("mf_numar_angajati") or 0
            assert curr >= next_val
    
    def test_caen_sort_alfabetic(self):
        """CAEN should sort alphabetically when specified"""
        response = requests.get(f"{BASE_URL}/api/caen/code/4932?limit=5&sort=alfabetic")
        assert response.status_code == 200
        
        data = response.json()
        companies = data["companies"]
        
        for i in range(len(companies) - 1):
            curr = companies[i].get("denumire", "").lower()
            next_val = companies[i+1].get("denumire", "").lower()
            assert curr <= next_val, f"Not alphabetically sorted: {curr} > {next_val}"
    
    def test_caen_has_top_judete(self):
        """CAEN should return top_judete for filtering"""
        response = requests.get(f"{BASE_URL}/api/caen/code/4932?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "top_judete" in data
        assert len(data["top_judete"]) > 0
        
        for judet in data["top_judete"]:
            assert "judet" in judet
            assert "count" in judet
    
    def test_caen_filter_by_judet(self):
        """CAEN should filter by judet"""
        response = requests.get(f"{BASE_URL}/api/caen/code/4932?limit=5&judet=București")
        assert response.status_code == 200
        
        data = response.json()
        companies = data["companies"]
        
        for company in companies:
            assert "București" in company.get("judet", "")


class TestJudetLocalities:
    """Tests for /api/locations/judet/{slug} localities endpoint"""
    
    def test_judet_returns_localities(self):
        """Judet endpoint should return localities list"""
        response = requests.get(f"{BASE_URL}/api/locations/judet/teleorman?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "localities" in data
        assert "judet" in data
        assert "total_companies" in data
        assert "total_localities" in data
        
        localities = data["localities"]
        assert len(localities) > 0
        
        for loc in localities:
            assert "name" in loc
            assert "slug" in loc
            assert "company_count" in loc
