#!/bin/bash

# ===========================================
# mFirme Elasticsearch Setup Script
# ===========================================

echo "=========================================="
echo "   mFirme Elasticsearch Setup"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker nu este instalat!"
    echo ""
    echo "Instalează Docker:"
    echo "  Ubuntu/Debian: curl -fsSL https://get.docker.com | sh"
    echo "  macOS: brew install docker"
    echo "  Windows: https://docs.docker.com/desktop/install/windows-install/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose nu este instalat!"
    exit 1
fi

echo "✓ Docker detectat"

# Navigate to docker directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Start Elasticsearch
echo ""
echo "Pornesc Elasticsearch..."
docker compose -f docker-compose.elasticsearch.yml up -d

# Wait for Elasticsearch to be ready
echo ""
echo "Aștept ca Elasticsearch să pornească..."
for i in {1..60}; do
    if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
        echo "✓ Elasticsearch este gata!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "❌ Timeout - Elasticsearch nu a pornit în 60 secunde"
        exit 1
    fi
    echo "  Aștept... ($i/60)"
    sleep 1
done

# Show status
echo ""
echo "=========================================="
echo "   Status Elasticsearch"
echo "=========================================="
curl -s http://localhost:9200/_cluster/health?pretty

echo ""
echo "=========================================="
echo "   Informații"
echo "=========================================="
echo "Elasticsearch: http://localhost:9200"
echo "Kibana:        http://localhost:5601"
echo ""
echo "Pentru a opri: docker compose -f docker-compose.elasticsearch.yml down"
echo "Pentru logs:   docker logs mfirme-elasticsearch"
echo ""
echo "Acum mergi în Admin -> Elasticsearch pentru a indexa firmele!"
