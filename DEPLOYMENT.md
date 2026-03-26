# mFirme - Ghid Deployment Producție

## Cerințe

- **Docker** și **Docker Compose** instalate
- Minim **4GB RAM** (2GB pentru Elasticsearch, 1GB pentru MongoDB, 1GB pentru aplicație)
- **20GB** spațiu disk (pentru date și indexuri)

## Deployment Rapid (O singură comandă)

```bash
# 1. Clonează repo-ul
git clone <repository-url>
cd mfirme

# 2. Pornește totul
chmod +x setup-production.sh
./setup-production.sh
```

**Gata!** Aplicația rulează pe http://localhost

## Deployment Manual

### 1. Creează fișierul .env

```bash
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DOMAIN_URL=http://your-domain.com
EOF
```

### 2. Pornește serviciile

```bash
docker compose -f docker-compose.production.yml up -d --build
```

### 3. Verifică status

```bash
docker compose -f docker-compose.production.yml ps
```

## După Deployment

### Configurează Elasticsearch

1. Accesează aplicația în browser
2. Loghează-te ca admin: `admin@mfirme.ro` / `Admin123!`
3. Mergi la **Admin → Elasticsearch**
4. Click **"Creează Index"**
5. Click **"Pornește Indexare"**
6. Așteaptă să se indexeze toate firmele (~10-30 min pentru 1.2M)

### Importă datele existente (dacă ai backup)

```bash
# Restaurează MongoDB din backup
docker exec -i mfirme-mongodb mongorestore --archive < backup.archive
```

## URL-uri Disponibile

| Serviciu | URL | Descriere |
|----------|-----|-----------|
| Frontend | http://localhost | Aplicația principală |
| Backend API | http://localhost/api | API endpoints |
| Swagger Docs | http://localhost:8001/docs | Documentație API |
| Elasticsearch | http://localhost:9200 | Direct ES access |
| Kibana | http://localhost:5601 | ES Dashboard (trebuie activat) |

## Comenzi Utile

```bash
# Vezi logs în timp real
docker compose -f docker-compose.production.yml logs -f

# Logs doar pentru un serviciu
docker compose -f docker-compose.production.yml logs -f backend

# Restart toate serviciile
docker compose -f docker-compose.production.yml restart

# Restart un serviciu specific
docker compose -f docker-compose.production.yml restart backend

# Oprește totul
docker compose -f docker-compose.production.yml down

# Oprește și șterge datele (ATENȚIE!)
docker compose -f docker-compose.production.yml down -v

# Activează Kibana (optional, pentru debug)
docker compose -f docker-compose.production.yml --profile debug up kibana -d
```

## Structura Fișiere

```
mfirme/
├── docker-compose.production.yml   # Configurare Docker
├── setup-production.sh             # Script setup automat
├── .env                            # Variabile environment
├── backend/
│   ├── Dockerfile.production       # Docker build backend
│   ├── server.py                   # FastAPI app
│   └── routes/
│       └── elasticsearch_routes.py # ES endpoints
├── frontend/
│   ├── Dockerfile.production       # Docker build frontend
│   └── nginx.conf                  # Nginx config
└── nginx/
    └── nginx.conf                  # Reverse proxy config
```

## Troubleshooting

### Elasticsearch nu pornește
```bash
# Verifică logs
docker logs mfirme-elasticsearch

# Crește limita de memorie virtuală (Linux)
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

### Backend nu se conectează la MongoDB
```bash
# Verifică dacă MongoDB e healthy
docker exec mfirme-mongodb mongosh --eval "db.runCommand('ping')"

# Restart backend
docker compose -f docker-compose.production.yml restart backend
```

### Port 80 ocupat
```bash
# Găsește ce folosește portul
sudo lsof -i :80

# Oprește Apache/Nginx dacă rulează
sudo systemctl stop apache2
sudo systemctl stop nginx
```

## Backup & Restore

### Backup MongoDB
```bash
docker exec mfirme-mongodb mongodump --archive --gzip > backup_$(date +%Y%m%d).archive.gz
```

### Restore MongoDB
```bash
docker exec -i mfirme-mongodb mongorestore --archive --gzip < backup_20240101.archive.gz
```

### Backup Elasticsearch
```bash
# Creează snapshot repository și snapshot din Kibana sau API
curl -X PUT "localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backup"
  }
}'
```

## SSL/HTTPS (Producție)

Pentru HTTPS, adaugă în `nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... restul configurației
}
```

Și montează certificatele în docker-compose.yml.

---

## Suport

Pentru probleme sau întrebări, verifică logurile:
```bash
docker compose -f docker-compose.production.yml logs -f 2>&1 | tee debug.log
```
