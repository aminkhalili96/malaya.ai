#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="malaya-llm"
REGION="asia-southeast1" # Change as needed
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying to Google Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region:  $REGION"

# 1. Build & Push Image
echo "📦 Building container image..."
gcloud builds submit --tag "${IMAGE_NAME}" .

# 2. Deploy to Cloud Run
echo "🚀 Deploying service..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY},OPENAI_API_KEY=${OPENAI_API_KEY},TAVILY_API_KEY=${TAVILY_API_KEY}"

echo "✅ Deployment complete!"
gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${REGION}" --format 'value(status.url)'
