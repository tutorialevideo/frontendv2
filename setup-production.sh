#!/bin/bash

# ===========================================
# mFirme Production Setup Script
# ===========================================

set -e

echo "=========================================="
echo "   mFirme Production Setup"
echo "=========================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker nu este instalat!"
    echo "Instalează: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose nu este instalat!"
    exit 1
fi

echo "✓ Docker detectat"

# Create .env if not exists
if [ ! -f .env ]; then
    echo ""
    echo "Creez fișierul .env..."
    cat > .env << EOF
# mFirme Production Environment
SECRET_KEY=$(openssl rand -hex 32)
DOMAIN_URL=http://localhost
EOF
    echo "✓ Fișier .env creat"
    echo "⚠️  Editează .env și setează DOMAIN_URL pentru producție!"
fi

# Build and start
echo ""
echo "Construiesc și pornesc serviciile..."
docker compose -f docker-compose.production.yml build --no-cache
docker compose -f docker-compose.production.yml up -d

# Wait for services
echo ""
echo "Aștept ca serviciile să pornească..."
sleep 10

# Check services
echo ""
echo "=========================================="
echo "   Status Servicii"
echo "=========================================="
docker compose -f docker-compose.production.yml ps

# Test connections
echo ""
echo "=========================================="
echo "   Test Conexiuni"
echo "=========================================="

# Test MongoDB
if curl -s http://localhost:27017 > /dev/null 2>&1 || docker exec mfirme-mongodb mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
    echo "✓ MongoDB: OK"
else
    echo "⚠️  MongoDB: Checking..."
fi

# Test Elasticsearch
if curl -s http://localhost:9200 | grep -q "cluster_name"; then
    echo "✓ Elasticsearch: OK"
else
    echo "⚠️  Elasticsearch: Starting..."
fi

# Test Backend
if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "✓ Backend: OK"
else
    echo "⚠️  Backend: Starting..."
fi

# Test Frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Frontend: OK"
else
    echo "⚠️  Frontend: Starting..."
fi

echo ""
echo "=========================================="
echo "   Aplicația este pregătită!"
echo "=========================================="
echo ""
echo "🌐 Frontend:      http://localhost"
echo "🔧 Backend API:   http://localhost/api"
echo "🔍 Elasticsearch: http://localhost:9200"
echo "📊 Kibana:        docker compose -f docker-compose.production.yml --profile debug up kibana"
echo ""
echo "Comenzi utile:"
echo "  Logs:     docker compose -f docker-compose.production.yml logs -f"
echo "  Stop:     docker compose -f docker-compose.production.yml down"
echo "  Restart:  docker compose -f docker-compose.production.yml restart"
echo ""
echo "După pornire, mergi în Admin -> Elasticsearch pentru a indexa firmele!"
