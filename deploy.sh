#!/bin/bash
# deploy.sh: Automates Docker Build & Kubernetes Deployment

echo "🚀 Starting Malaya.ai Deployment..."

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first."
    exit 1
fi

# 2. Build Docker Image
echo "📦 Building Docker Image..."
docker build -t malaya-ai .

# 3. Check for Kubernetes
if command -v kubectl &> /dev/null; then
    echo "☸️  Deploying to Kubernetes..."
    
    # Create Secrets (Simulated for local dev)
    # Note: In prod, use a Vault or sealed secrets
    if [ -f .env ]; then
        export $(cat .env | xargs)
        kubectl create secret generic malaya-secrets \
            --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
            --from-literal=TAVILY_API_KEY="$TAVILY_API_KEY" \
            --dry-run=client -o yaml | kubectl apply -f -
    else
        echo "⚠️  .env file not found. Secrets might be missing."
    fi

    # Apply Manifests
    kubectl apply -f kubernetes/deployment.yaml
    kubectl apply -f kubernetes/service.yaml
    
    echo "✅ Deployed! Access via: http://localhost"
else
    echo "⚠️  Kubectl not found. Running with Docker only..."
    docker run -d -p 8502:8501 --env-file .env --name malaya-container malaya-ai
    echo "✅ Running in Docker! Access via: http://localhost:8502"
fi
