#!/bin/bash

# ===========================================
# RapoarteFirme Production Setup Script
# ===========================================

set -e

echo "=========================================="
echo "   RapoarteFirme - Setup Productie"
echo "=========================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Docker nu este instalat!"
    echo "Instaleaza: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Docker Compose nu este instalat!"
    exit 1
fi

echo "Docker detectat"

# Create .env if not exists
if [ ! -f .env ]; then
    echo ""
    echo "Creez fisierul .env..."
    cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DOMAIN_URL=https://rapoartefirme.ro
CLOUD_MONGO_URL=
STRIPE_API_KEY=
EOF
    echo "Fisier .env creat"
    echo "IMPORTANT: Editeaza .env si seteaza CLOUD_MONGO_URL si DOMAIN_URL!"
fi

# Create SSL directory
mkdir -p nginx/ssl

# Elasticsearch vm.max_map_count
echo ""
echo "Verificare vm.max_map_count pentru Elasticsearch..."
CURRENT_MAP_COUNT=$(sysctl -n vm.max_map_count 2>/dev/null || echo "0")
if [ "$CURRENT_MAP_COUNT" -lt 262144 ]; then
    echo "Setez vm.max_map_count=262144..."
    sudo sysctl -w vm.max_map_count=262144
    echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf > /dev/null
    echo "vm.max_map_count setat"
else
    echo "vm.max_map_count OK ($CURRENT_MAP_COUNT)"
fi

# Build and start
echo ""
echo "Construiesc si pornesc serviciile..."
docker compose -f docker-compose.production.yml build --no-cache
docker compose -f docker-compose.production.yml up -d

# Wait for services
echo ""
echo "Astept ca serviciile sa porneasca..."
sleep 15

# Check services
echo ""
echo "=========================================="
echo "   Status Servicii"
echo "=========================================="
docker compose -f docker-compose.production.yml ps

echo ""
echo "=========================================="
echo "   Test Conexiuni"
echo "=========================================="

# Test MongoDB
if docker exec rapoartefirme-mongodb mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
    echo "MongoDB: OK"
else
    echo "MongoDB: Se porneste..."
fi

# Test Elasticsearch
if curl -s http://localhost:9200 | grep -q "cluster_name" 2>/dev/null; then
    echo "Elasticsearch: OK"
else
    echo "Elasticsearch: Se porneste..."
fi

# Test Backend
if curl -s http://localhost:8002/api/health | grep -q "ok" 2>/dev/null; then
    echo "Backend: OK"
else
    echo "Backend: Se porneste..."
fi

# Test Frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend: OK"
else
    echo "Frontend: Se porneste..."
fi

echo ""
echo "=========================================="
echo "   RapoarteFirme este pregatit!"
echo "=========================================="
echo ""
echo "Frontend:      http://localhost (sau https://rapoartefirme.ro)"
echo "Backend API:   http://localhost/api"
echo "Elasticsearch: http://localhost:9200"
echo "Kibana:        docker compose -f docker-compose.production.yml --profile debug up kibana -d"
echo ""
echo "Admin login: admin@mfirme.ro / Admin123!"
echo ""
echo "Comenzi utile:"
echo "  Logs:     docker compose -f docker-compose.production.yml logs -f"
echo "  Stop:     docker compose -f docker-compose.production.yml down"
echo "  Restart:  docker compose -f docker-compose.production.yml restart"
echo ""
echo "Dupa pornire:"
echo "  1. Admin -> Sync -> Sincronizeaza datele din Cloud"
echo "  2. Admin -> Elasticsearch -> Creeaza Index -> Porneste Indexare"
echo ""
