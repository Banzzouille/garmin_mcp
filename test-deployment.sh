#!/bin/bash
# Script de test pour vérifier le déploiement du serveur MCP Garmin

set -e

echo "======================================"
echo "Test de déploiement Garmin MCP Server"
echo "======================================"
echo ""

# Couleurs pour l'affichage
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Vérifier que le container tourne
echo "1. Vérification du container..."
if docker ps | grep -q garmin-mcp-server; then
    echo -e "${GREEN}✓${NC} Container garmin-mcp-server est en cours d'exécution"
    docker ps | grep garmin-mcp-server
else
    echo -e "${RED}✗${NC} Container garmin-mcp-server n'est pas en cours d'exécution"
    exit 1
fi
echo ""

# Test 2: Vérifier les variables d'environnement
echo "2. Vérification des variables d'environnement..."
ENV_VARS=$(docker inspect garmin-mcp-server --format='{{range .Config.Env}}{{println .}}{{end}}' | grep GARMIN_MCP)
echo "$ENV_VARS"

if echo "$ENV_VARS" | grep -q "GARMIN_MCP_TRANSPORT=streamable-http"; then
    echo -e "${GREEN}✓${NC} Transport HTTP configuré"
else
    echo -e "${RED}✗${NC} Transport HTTP non configuré"
    exit 1
fi
echo ""

# Test 3: Vérifier les logs
echo "3. Vérification des logs (dernières 30 lignes)..."
echo -e "${YELLOW}---${NC}"
docker logs --tail 30 garmin-mcp-server 2>&1
echo -e "${YELLOW}---${NC}"
echo ""

# Vérifier si le serveur HTTP est mentionné dans les logs
if docker logs --tail 50 garmin-mcp-server 2>&1 | grep -q "Starting HTTP server\|streamable-http\|Transport mode: streamable-http"; then
    echo -e "${GREEN}✓${NC} Mode HTTP détecté dans les logs"
else
    echo -e "${YELLOW}⚠${NC} Mode HTTP non mentionné dans les logs (vérifiez manuellement)"
fi
echo ""

# Test 4: Test de connexion directe dans le réseau Docker
echo "4. Test de connexion directe (réseau Docker backend_net)..."
if docker run --rm --network backend_net curlimages/curl curl -s -o /dev/null -w "%{http_code}" http://garmin-mcp-server:8000/ | grep -q "200\|404\|405"; then
    echo -e "${GREEN}✓${NC} Container accessible sur le réseau Docker (port 8000)"
else
    echo -e "${RED}✗${NC} Container NON accessible sur le réseau Docker"
    echo "Ceci indique que le serveur n'écoute pas en HTTP sur le port 8000"
    exit 1
fi
echo ""

# Test 5: Test via nginx
echo "5. Test de connexion via Nginx Proxy Manager..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://garmin-mcp.banzzai.fr/ || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ] || [ "$HTTP_CODE" = "405" ]; then
    echo -e "${GREEN}✓${NC} Accessible via https://garmin-mcp.banzzai.fr/ (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "502" ]; then
    echo -e "${RED}✗${NC} Erreur 502 Bad Gateway - Nginx ne peut pas atteindre le container"
    echo "Vérifiez la configuration NPM (port 8000, pas 9000)"
else
    echo -e "${RED}✗${NC} Erreur HTTP $HTTP_CODE"
fi
echo ""

# Test 6: Vérifier le port exposé
echo "6. Vérification du mapping de ports..."
docker port garmin-mcp-server
echo ""

# Résumé
echo "======================================"
echo "Résumé des tests"
echo "======================================"
echo ""
echo "Si tous les tests sont ✓ verts, votre serveur MCP est correctement configuré !"
echo ""
echo "Configuration Nginx Proxy Manager attendue:"
echo "  - Forward Hostname/IP: garmin-mcp-server"
echo "  - Forward Port: 8000"
echo "  - Scheme: http"
echo ""
echo "Pour tester manuellement:"
echo "  curl -v https://garmin-mcp.banzzai.fr/"
echo ""
