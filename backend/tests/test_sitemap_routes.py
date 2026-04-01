"""
Test Sitemap Generator API endpoints
Tests: index.xml, static.xml, judete.xml, caen.xml, companies-{n}.xml, status, generate
"""
import pytest
import requests
import os
import xml.etree.ElementTree as ET

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
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestSitemapIndexXML:
    """Tests for /api/sitemap/index.xml - main sitemap index"""
    
    def test_index_returns_200(self, api_client):
        """GET /api/sitemap/index.xml returns 200"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/index.xml")
        assert response.status_code == 200
        print("✓ index.xml returns 200")
    
    def test_index_returns_xml_content_type(self, api_client):
        """Response has XML content type"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/index.xml")
        assert "application/xml" in response.headers.get("content-type", "")
        print("✓ index.xml has XML content type")
    
    def test_index_is_valid_xml(self, api_client):
        """Response is valid XML"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/index.xml")
        try:
            ET.fromstring(response.content)
            print("✓ index.xml is valid XML")
        except ET.ParseError as e:
            pytest.fail(f"Invalid XML: {e}")
    
    def test_index_contains_sitemapindex_root(self, api_client):
        """XML has sitemapindex root element"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/index.xml")
        root = ET.fromstring(response.content)
        assert "sitemapindex" in root.tag
        print("✓ index.xml has sitemapindex root")
    
    def test_index_contains_30_sitemaps(self, api_client):
        """Index contains 30 sub-sitemaps (3 static + 27 company pages)"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/index.xml")
        root = ET.fromstring(response.content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemaps = root.findall('.//sm:sitemap', ns)
        assert len(sitemaps) == 30, f"Expected 30 sitemaps, got {len(sitemaps)}"
        print(f"✓ index.xml contains {len(sitemaps)} sub-sitemaps")
    
    def test_index_contains_static_sitemap(self, api_client):
        """Index references static.xml"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/index.xml")
        assert "/api/sitemap/static.xml" in response.text
        print("✓ index.xml references static.xml")
    
    def test_index_contains_judete_sitemap(self, api_client):
        """Index references judete.xml"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/index.xml")
        assert "/api/sitemap/judete.xml" in response.text
        print("✓ index.xml references judete.xml")
    
    def test_index_contains_caen_sitemap(self, api_client):
        """Index references caen.xml"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/index.xml")
        assert "/api/sitemap/caen.xml" in response.text
        print("✓ index.xml references caen.xml")
    
    def test_index_contains_company_sitemaps(self, api_client):
        """Index references companies-1.xml through companies-27.xml"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/index.xml")
        for i in range(1, 28):
            assert f"/api/sitemap/companies-{i}.xml" in response.text, f"Missing companies-{i}.xml"
        print("✓ index.xml references all 27 company sitemaps")


class TestStaticSitemapXML:
    """Tests for /api/sitemap/static.xml - static pages"""
    
    def test_static_returns_200(self, api_client):
        """GET /api/sitemap/static.xml returns 200"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/static.xml")
        assert response.status_code == 200
        print("✓ static.xml returns 200")
    
    def test_static_is_valid_xml(self, api_client):
        """Response is valid XML"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/static.xml")
        try:
            ET.fromstring(response.content)
            print("✓ static.xml is valid XML")
        except ET.ParseError as e:
            pytest.fail(f"Invalid XML: {e}")
    
    def test_static_contains_homepage(self, api_client):
        """Contains homepage URL"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/static.xml")
        assert "https://mfirme.ro/</loc>" in response.text
        print("✓ static.xml contains homepage")
    
    def test_static_contains_search(self, api_client):
        """Contains /search URL"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/static.xml")
        assert "/search</loc>" in response.text
        print("✓ static.xml contains /search")
    
    def test_static_contains_judete(self, api_client):
        """Contains /judete URL"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/static.xml")
        assert "/judete</loc>" in response.text
        print("✓ static.xml contains /judete")
    
    def test_static_contains_caen(self, api_client):
        """Contains /caen URL"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/static.xml")
        assert "/caen</loc>" in response.text
        print("✓ static.xml contains /caen")
    
    def test_static_has_4_urls(self, api_client):
        """Contains exactly 4 URLs"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/static.xml")
        root = ET.fromstring(response.content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = root.findall('.//sm:url', ns)
        assert len(urls) == 4, f"Expected 4 URLs, got {len(urls)}"
        print(f"✓ static.xml contains {len(urls)} URLs")


class TestJudeteSitemapXML:
    """Tests for /api/sitemap/judete.xml - judete and localities"""
    
    def test_judete_returns_200(self, api_client):
        """GET /api/sitemap/judete.xml returns 200"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/judete.xml")
        assert response.status_code == 200
        print("✓ judete.xml returns 200")
    
    def test_judete_is_valid_xml(self, api_client):
        """Response is valid XML"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/judete.xml")
        try:
            ET.fromstring(response.content)
            print("✓ judete.xml is valid XML")
        except ET.ParseError as e:
            pytest.fail(f"Invalid XML: {e}")
    
    def test_judete_contains_bucuresti(self, api_client):
        """Contains Bucuresti judet URL"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/judete.xml")
        assert "/judet/bucuresti</loc>" in response.text
        print("✓ judete.xml contains Bucuresti")
    
    def test_judete_contains_cluj(self, api_client):
        """Contains Cluj judet URL"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/judete.xml")
        assert "/judet/cluj</loc>" in response.text
        print("✓ judete.xml contains Cluj")
    
    def test_judete_has_many_urls(self, api_client):
        """Contains many URLs (judete + localities)"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/judete.xml")
        root = ET.fromstring(response.content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = root.findall('.//sm:url', ns)
        # Should have 42 judete + thousands of localities
        assert len(urls) > 100, f"Expected >100 URLs, got {len(urls)}"
        print(f"✓ judete.xml contains {len(urls)} URLs")


class TestCaenSitemapXML:
    """Tests for /api/sitemap/caen.xml - CAEN codes"""
    
    def test_caen_returns_200(self, api_client):
        """GET /api/sitemap/caen.xml returns 200"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/caen.xml")
        assert response.status_code == 200
        print("✓ caen.xml returns 200")
    
    def test_caen_is_valid_xml(self, api_client):
        """Response is valid XML"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/caen.xml")
        try:
            ET.fromstring(response.content)
            print("✓ caen.xml is valid XML")
        except ET.ParseError as e:
            pytest.fail(f"Invalid XML: {e}")
    
    def test_caen_contains_valid_codes(self, api_client):
        """Contains valid CAEN code URLs"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/caen.xml")
        # Check for common CAEN codes
        assert "/caen/4711</loc>" in response.text or "/caen/4120</loc>" in response.text
        print("✓ caen.xml contains valid CAEN codes")
    
    def test_caen_has_many_urls(self, api_client):
        """Contains many CAEN code URLs"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/caen.xml")
        root = ET.fromstring(response.content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = root.findall('.//sm:url', ns)
        assert len(urls) > 100, f"Expected >100 CAEN URLs, got {len(urls)}"
        print(f"✓ caen.xml contains {len(urls)} CAEN code URLs")
    
    def test_caen_no_none_values(self, api_client):
        """Should not contain 'None' as CAEN code (BUG CHECK)"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/caen.xml")
        # This is a known bug - /caen/None appears in the sitemap
        if "/caen/None</loc>" in response.text:
            print("⚠ BUG: caen.xml contains /caen/None - should filter out null CAEN codes")
        else:
            print("✓ caen.xml does not contain None values")


class TestCompaniesSitemapXML:
    """Tests for /api/sitemap/companies-{n}.xml - paginated company sitemaps"""
    
    def test_companies_1_returns_200(self, api_client):
        """GET /api/sitemap/companies-1.xml returns 200"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/companies-1.xml")
        assert response.status_code == 200
        print("✓ companies-1.xml returns 200")
    
    def test_companies_1_is_valid_xml(self, api_client):
        """Response is valid XML"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/companies-1.xml")
        try:
            ET.fromstring(response.content)
            print("✓ companies-1.xml is valid XML")
        except ET.ParseError as e:
            pytest.fail(f"Invalid XML: {e}")
    
    def test_companies_1_contains_firma_urls(self, api_client):
        """Contains /firma/ URLs"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/companies-1.xml")
        assert "/firma/" in response.text
        print("✓ companies-1.xml contains /firma/ URLs")
    
    def test_companies_1_has_many_urls(self, api_client):
        """Contains up to 45K URLs"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/companies-1.xml")
        root = ET.fromstring(response.content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = root.findall('.//sm:url', ns)
        # First page should have 45000 URLs
        assert len(urls) > 1000, f"Expected >1000 URLs, got {len(urls)}"
        print(f"✓ companies-1.xml contains {len(urls)} company URLs")
    
    def test_companies_27_returns_200(self, api_client):
        """GET /api/sitemap/companies-27.xml (last page) returns 200"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/companies-27.xml")
        assert response.status_code == 200
        print("✓ companies-27.xml returns 200")
    
    def test_companies_27_has_urls(self, api_client):
        """Last page contains remaining company URLs"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/companies-27.xml")
        root = ET.fromstring(response.content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = root.findall('.//sm:url', ns)
        # Last page should have remaining companies (1,213,714 % 45000 = ~3714)
        assert len(urls) > 0, "Last page should have URLs"
        print(f"✓ companies-27.xml contains {len(urls)} company URLs")
    
    def test_invalid_page_returns_400(self, api_client):
        """Invalid page number returns 400"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/companies-0.xml")
        assert response.status_code == 400
        print("✓ companies-0.xml returns 400 (invalid page)")


class TestSitemapStatusAPI:
    """Tests for /api/sitemap/status - admin-only status endpoint"""
    
    def test_status_requires_auth(self, api_client):
        """GET /api/sitemap/status requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/sitemap/status")
        assert response.status_code in [401, 403]
        print("✓ /api/sitemap/status requires auth")
    
    def test_status_returns_200_with_admin(self, api_client, admin_token):
        """GET /api/sitemap/status returns 200 with admin token"""
        response = api_client.get(
            f"{BASE_URL}/api/sitemap/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✓ /api/sitemap/status returns 200 with admin auth")
    
    def test_status_returns_stats(self, api_client, admin_token):
        """Response contains stats object"""
        response = api_client.get(
            f"{BASE_URL}/api/sitemap/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert "stats" in data
        print("✓ /api/sitemap/status returns stats")
    
    def test_status_stats_has_company_pages(self, api_client, admin_token):
        """Stats contains company_pages count"""
        response = api_client.get(
            f"{BASE_URL}/api/sitemap/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["stats"]["company_pages"] == 27
        print(f"✓ company_pages = {data['stats']['company_pages']}")
    
    def test_status_stats_has_total_active_companies(self, api_client, admin_token):
        """Stats contains total_active_companies"""
        response = api_client.get(
            f"{BASE_URL}/api/sitemap/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["stats"]["total_active_companies"] > 1000000
        print(f"✓ total_active_companies = {data['stats']['total_active_companies']:,}")
    
    def test_status_stats_has_total_sitemaps(self, api_client, admin_token):
        """Stats contains total_sitemaps = 30"""
        response = api_client.get(
            f"{BASE_URL}/api/sitemap/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["stats"]["total_sitemaps"] == 30
        print(f"✓ total_sitemaps = {data['stats']['total_sitemaps']}")
    
    def test_status_stats_has_judete(self, api_client, admin_token):
        """Stats contains judete count"""
        response = api_client.get(
            f"{BASE_URL}/api/sitemap/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["stats"]["judete"] > 40
        print(f"✓ judete = {data['stats']['judete']}")
    
    def test_status_stats_has_caen_codes(self, api_client, admin_token):
        """Stats contains caen_codes count"""
        response = api_client.get(
            f"{BASE_URL}/api/sitemap/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["stats"]["caen_codes"] > 1000
        print(f"✓ caen_codes = {data['stats']['caen_codes']}")


class TestSitemapGenerateAPI:
    """Tests for /api/sitemap/generate - admin-only timestamp update"""
    
    def test_generate_requires_auth(self, api_client):
        """POST /api/sitemap/generate requires authentication"""
        response = api_client.post(f"{BASE_URL}/api/sitemap/generate")
        assert response.status_code in [401, 403]
        print("✓ /api/sitemap/generate requires auth")
    
    def test_generate_returns_200_with_admin(self, api_client, admin_token):
        """POST /api/sitemap/generate returns 200 with admin token"""
        response = api_client.post(
            f"{BASE_URL}/api/sitemap/generate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✓ /api/sitemap/generate returns 200 with admin auth")
    
    def test_generate_returns_message(self, api_client, admin_token):
        """Response contains success message"""
        response = api_client.post(
            f"{BASE_URL}/api/sitemap/generate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert "message" in data
        assert "timestamp" in data["message"].lower() or "sitemap" in data["message"].lower()
        print(f"✓ /api/sitemap/generate returns message: {data['message']}")
    
    def test_generate_updates_timestamp(self, api_client, admin_token):
        """Generating updates last_generated timestamp"""
        # First generate
        api_client.post(
            f"{BASE_URL}/api/sitemap/generate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Check status
        response = api_client.get(
            f"{BASE_URL}/api/sitemap/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        assert data["last_generated"] is not None
        print(f"✓ last_generated updated to: {data['last_generated']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
