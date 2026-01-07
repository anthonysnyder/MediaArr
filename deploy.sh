#!/bin/bash
set -e

echo "🚀 Mediarr Deployment Script"
echo "============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOCKER_USER="swguru2004"
DOCKER_REPO="mediarr"
VERSION="latest"

echo "📋 Configuration:"
echo "   Docker Hub: ${DOCKER_USER}/${DOCKER_REPO}:${VERSION}"
echo ""

# Step 1: Push to GitHub
echo -e "${YELLOW}Step 1: Pushing to GitHub...${NC}"
git branch -M main
git push -u origin main
echo -e "${GREEN}✓ Pushed to GitHub${NC}"
echo ""

# Step 2: Docker Build and Push
echo -e "${YELLOW}Step 2: Building and pushing Docker image...${NC}"
echo "Note: Make sure you're logged in to Docker Hub (docker login)"
echo ""

# Create buildx builder if it doesn't exist
if ! docker buildx ls | grep -q "mediarr-builder"; then
    echo "Creating buildx builder for multi-arch..."
    docker buildx create --name mediarr-builder --use
else
    echo "Using existing mediarr-builder..."
    docker buildx use mediarr-builder
fi

# Build and push multi-architecture image
echo "Building for linux/amd64 and linux/arm64..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${DOCKER_USER}/${DOCKER_REPO}:${VERSION} \
    --push \
    .

echo -e "${GREEN}✓ Docker image pushed to Docker Hub${NC}"
echo ""

# Summary
echo "=============================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "📦 GitHub: https://github.com/anthonysnyder/Mediarr"
echo "🐳 Docker: ${DOCKER_USER}/${DOCKER_REPO}:${VERSION}"
echo ""
echo "To pull on your Mac Mini:"
echo "  docker pull ${DOCKER_USER}/${DOCKER_REPO}:${VERSION}"
echo ""
echo "To run:"
echo "  cd /path/to/mediarr"
echo "  docker-compose pull"
echo "  docker-compose up -d"
