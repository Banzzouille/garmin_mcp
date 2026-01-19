# Garmin MCP Server - Deployment Guide

## Configuration HTTP + Nginx

Ce guide explique comment configurer votre serveur MCP Garmin pour être accessible via HTTP et nginx.

---

## 1. Configuration des variables d'environnement

### Étape 1: Créer le fichier `.env`

Copiez `.env.example` vers `.env` et remplissez vos identifiants:

```bash
cp .env.example .env
```

Modifiez le fichier `.env` avec vos identifiants Garmin:
```env
GARMIN_EMAIL=votre-email@garmin.com
GARMIN_PASSWORD=votre-mot-de-passe
GARMIN_MCP_TRANSPORT=streamable-http  # CRITIQUE: Active le mode HTTP
```

### Configuration expliquée:

| Variable | Valeur | Explication |
|----------|--------|-------------|
| `GARMIN_MCP_TRANSPORT` | `streamable-http` | Active le serveur HTTP (au lieu de stdio) |
| `GARMIN_MCP_HOST` | `0.0.0.0` | Écoute sur toutes les interfaces du container |
| `GARMIN_MCP_PORT` | `8000` | Port interne du container |
| `GARMIN_HOST_PORT` | `9000` | Port exposé sur l'hôte (optionnel) |
| `GARMIN_MCP_BIND` | `0.0.0.0` | Permet l'accès depuis nginx |

---

## 2. Architecture et Ports

### Schéma de communication:

```
Internet → Nginx (backend_net) → garmin-mcp-server:8000
                                       ↓
                              Container interne (port 8000)
```

**IMPORTANT:** 
- ✅ Nginx utilise le port **8000** (port interne du container)
- ❌ Ne PAS utiliser le port **9000** dans nginx (c'est le port mappé sur l'hôte)

### Pourquoi port 8000 et pas 9000 ?

Dans un réseau Docker, les containers communiquent directement via leurs ports internes:
- **Port 8000**: Port EXPOSE dans le Dockerfile, accessible dans le réseau Docker
- **Port 9000**: Mapping sur l'hôte pour accès externe (pas nécessaire avec nginx Docker)

---

## 3. Configuration Nginx

### Option 1: Nginx dans Docker (Recommandé)

Le fichier `nginx.conf` fourni est configuré pour:
- Accéder au backend via `garmin-mcp-server:8000`
- SSL/HTTPS avec vos certificats existants
- Proxy buffering désactivé (important pour MCP streaming)

**Modifiez ces lignes dans votre configuration nginx existante:**

```nginx
upstream garmin_mcp_backend {
    server garmin-mcp-server:8000;  # Port 8000, pas 9000!
}

server {
    listen 443 ssl http2;
    server_name garmin-mcp.banzzai.fr;
    
    # Vos certificats SSL existants
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    
    location / {
        proxy_pass http://garmin_mcp_backend;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # IMPORTANT: Désactiver le buffering pour MCP
        proxy_buffering off;
        proxy_cache off;
        
        # Timeouts
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

---

## 4. Déploiement

### Étape 1: Vérifier la configuration

```bash
# Vérifier que le .env est bien configuré
cat .env | grep GARMIN_MCP_TRANSPORT
# Doit afficher: GARMIN_MCP_TRANSPORT=streamable-http

# Vérifier le réseau Docker
docker network inspect backend_net
```

### Étape 2: Démarrer le service

```bash
# Arrêter le service existant
docker compose down

# Démarrer avec la nouvelle configuration
docker compose up -d

# Vérifier les logs
docker logs -f garmin-mcp-server
```

### Étape 3: Vérifier que le mode HTTP est actif

Dans les logs, vous devriez voir quelque chose comme:
```
Garmin Connect client initialized successfully.
Server running on http://0.0.0.0:8000
```

### Étape 4: Recharger nginx

```bash
# Tester la configuration nginx
docker exec <nginx-container> nginx -t

# Recharger nginx
docker exec <nginx-container> nginx -s reload
```

---

## 5. Tests et Validation

### Test 1: Accès direct au container (depuis le réseau Docker)

```bash
# Tester depuis un container dans le même réseau
docker run --rm --network backend_net curlimages/curl \
    curl -v http://garmin-mcp-server:8000/
```

### Test 2: Accès via nginx

```bash
# Test HTTP (doit rediriger vers HTTPS)
curl -I http://garmin-mcp.banzzai.fr/

# Test HTTPS
curl -I https://garmin-mcp.banzzai.fr/
```

### Test 3: Vérifier les ports

```bash
# Vérifier que le container expose bien le port 8000
docker exec garmin-mcp-server netstat -tlnp | grep 8000

# Voir les ports mappés
docker ps | grep garmin-mcp
```

---

## 6. Dépannage

### Problème: "Connection refused" depuis nginx

**Cause:** Le service n'est pas en mode HTTP

**Solution:**
1. Vérifier `.env`: `GARMIN_MCP_TRANSPORT=streamable-http`
2. Redémarrer: `docker compose restart`
3. Vérifier les logs: `docker logs garmin-mcp-server`

### Problème: Nginx utilise le mauvais port

**Cause:** Configuration nginx pointe vers `:9000` au lieu de `:8000`

**Solution:** Modifier nginx pour utiliser `garmin-mcp-server:8000`

### Problème: "502 Bad Gateway"

**Causes possibles:**
1. Le container n'est pas démarré: `docker ps | grep garmin`
2. Nginx pas dans le réseau `backend_net`: `docker inspect <nginx-container>`
3. Service en mode stdio au lieu de HTTP: vérifier les logs

### Vérifier le mode de transport actif

```bash
# Les logs doivent montrer "streamable-http" ou une adresse HTTP
docker logs garmin-mcp-server 2>&1 | grep -i "http\|transport\|running"
```

---

## 7. Checklist de Déploiement

- [ ] Fichier `.env` créé avec `GARMIN_MCP_TRANSPORT=streamable-http`
- [ ] Identifiants Garmin configurés dans `.env`
- [ ] Container redémarré avec `docker compose up -d`
- [ ] Logs vérifiés: mode HTTP actif
- [ ] Configuration nginx modifiée: port **8000** (pas 9000)
- [ ] Nginx rechargé
- [ ] Test curl depuis réseau Docker réussi
- [ ] Test HTTPS depuis Internet réussi

---

## 8. Architecture Finale

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Nginx     │  Port 443 (HTTPS)
                    │  Container  │  SSL/TLS terminaison
                    └──────┬──────┘
                           │ backend_net (Docker network)
                           │
                           ▼
              ┌────────────────────────┐
              │  garmin-mcp-server     │
              │  Container             │
              │  Port 8000 (HTTP)      │
              │  Transport: HTTP       │
              └────────────────────────┘
```

---

## Support

Si vous rencontrez des problèmes:

1. Vérifier les logs: `docker logs garmin-mcp-server`
2. Vérifier les logs nginx: `docker logs <nginx-container>`
3. Tester la connectivité réseau Docker
4. Vérifier que `GARMIN_MCP_TRANSPORT=streamable-http` est bien défini
