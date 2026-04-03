# RapoarteFirme - Ghid Deployment Productie

## Cerinte

- **Docker** si **Docker Compose** instalate
- Minim **4GB RAM** (2GB Elasticsearch, 1GB MongoDB, 1GB aplicatie)
- **20GB** spatiu disk (pentru date si indexuri)
- Port **80** liber (si **443** pentru SSL)

## Deployment Rapid

```bash
# 1. Cloneaza repo-ul
git clone <repository-url>
cd rapoartefirme

# 2. Copiaza si editeaza .env
cp .env.example .env
nano .env  # Seteaza SECRET_KEY, DOMAIN_URL, CLOUD_MONGO_URL

# 3. Porneste totul
chmod +x setup-production.sh
./setup-production.sh
```

**Gata!** Aplicatia ruleaza pe http://localhost

## Deployment Manual

### 1. Creaza fisierul .env

```bash
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DOMAIN_URL=https://rapoartefirme.ro
CLOUD_MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/justportal
STRIPE_API_KEY=sk_live_xxx
EOF
```

### 2. Porneste serviciile

```bash
# Seteaza vm.max_map_count pentru Elasticsearch
sudo sysctl -w vm.max_map_count=262144

# Build si start
docker compose -f docker-compose.production.yml up -d --build
```

### 3. Verifica status

```bash
docker compose -f docker-compose.production.yml ps
```

## Dupa Deployment

### 1. Logheaza-te ca Admin

- URL: http://localhost/admin
- Email: `admin@mfirme.ro`
- Parola: `Admin123!`

### 2. Sincronizeaza datele

- Admin -> **Sync** -> Click "Sync Complet"
- Asteapta pana se sincronizeaza toate colectiile

### 3. Configureaza Elasticsearch

- Admin -> **Elasticsearch** -> "Creeaza Index"
- Click "Porneste Indexare"
- Asteapta indexarea (~10-30 min pentru 1.2M firme)

### 4. Configureaza SEO

- Admin -> **SEO** -> Verifica template-urile
- Admin -> **Sitemap** -> Genereaza sitemap
- Adauga `https://rapoartefirme.ro/sitemap.xml` in Google Search Console

## Arhitectura Servicii

| Serviciu | Container | Port Intern | Port Extern |
|----------|-----------|-------------|-------------|
| MongoDB | rapoartefirme-mongodb | 27017 | 27099 |
| Elasticsearch | rapoartefirme-elasticsearch | 9200 | 9200 |
| Backend (FastAPI) | rapoartefirme-backend | 8001 | 8002 |
| Frontend (React+Nginx) | rapoartefirme-frontend | 80 | 3000 |
| Nginx (Reverse Proxy) | rapoartefirme-nginx | 80/443 | 80/443 |

## URL-uri Disponibile

| Serviciu | URL |
|----------|-----|
| Site public | https://rapoartefirme.ro |
| API | https://rapoartefirme.ro/api |
| Swagger Docs | http://localhost:8002/docs |
| Elasticsearch | http://localhost:9200 |

## Comenzi Utile

```bash
# Logs in timp real
docker compose -f docker-compose.production.yml logs -f

# Logs doar backend
docker compose -f docker-compose.production.yml logs -f backend

# Restart toate serviciile
docker compose -f docker-compose.production.yml restart

# Restart un serviciu
docker compose -f docker-compose.production.yml restart backend

# Opreste totul
docker compose -f docker-compose.production.yml down

# Rebuild dupa git pull
docker compose -f docker-compose.production.yml up -d --build

# Activeaza Kibana (optional)
docker compose -f docker-compose.production.yml --profile debug up kibana -d
```

## SSL/HTTPS cu Let's Encrypt

```bash
# 1. Instaleaza certbot
sudo apt install certbot

# 2. Obtine certificat (opreste nginx temporar)
docker compose -f docker-compose.production.yml stop nginx
sudo certbot certonly --standalone -d rapoartefirme.ro -d www.rapoartefirme.ro

# 3. Copiaza certificatele
sudo cp /etc/letsencrypt/live/rapoartefirme.ro/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/rapoartefirme.ro/privkey.pem nginx/ssl/key.pem

# 4. Activeaza HTTPS in nginx/nginx.conf (decommenteaza blocul SSL)
# 5. Restart
docker compose -f docker-compose.production.yml up -d --build nginx
```

## Backup & Restore

### Backup MongoDB
```bash
docker exec rapoartefirme-mongodb mongodump --archive --gzip > backup_$(date +%Y%m%d).archive.gz
```

### Restore MongoDB
```bash
docker exec -i rapoartefirme-mongodb mongorestore --archive --gzip < backup_20260401.archive.gz
```

## Troubleshooting

### Elasticsearch nu porneste
```bash
docker logs rapoartefirme-elasticsearch
# Fix: sudo sysctl -w vm.max_map_count=262144
```

### Backend nu se conecteaza la MongoDB
```bash
docker exec rapoartefirme-mongodb mongosh --eval "db.runCommand('ping')"
docker compose -f docker-compose.production.yml restart backend
```

### Port 80 ocupat
```bash
sudo lsof -i :80
sudo systemctl stop apache2  # sau nginx daca ruleaza separat
```

### Rebuild complet
```bash
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml up -d --build --force-recreate
```
