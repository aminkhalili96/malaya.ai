# Malaya LLM Deployment Guide

## Overview

Yes, it is fully possible to deploy Malaya LLM to the cloud while using Qwen. Since Cloud Run is serverless (CPU-only), the key architectural decision is where the **Qwen Model** runs.

### Strategy Options

| Strategy | App Hosting | Model Hosting | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- |
| **A. API Mode** | Cloud Run | External API (Groq/Together) | Cheapest, Fastest, Zero Maintenance | Data leaves your infrastructure |
| **B. Sovereign Cloud** | Cloud Run | Google Compute Engine (GPU VM) | Full Control, Private Data | Higher Cost (~$300/mo for GPU) |
| **C. Tunnel (Dev)** | Cloud Run | Your Local Mac (via ngrok) | Free, Uses your Hardware | Requires your Mac to be on |

---

## Prerequisites

1.  **Google Cloud Project**: Created and Billing enabled.
2.  **gcloud CLI**: Installed and authenticated (`gcloud auth login`).
3.  **Docker**: Installed locally.

---

## Step 1: Containerize the Application

The application is already set up for Docker.

1.  **Build and Push the Image**
    ```bash
    # Set your Project ID
    export GOOGLE_CLOUD_PROJECT="your-project-id"
    
    # Enable Artifact Registry
    gcloud services enable artifactregistry.googleapis.com
    
    # Create a repository (if not exists)
    gcloud artifacts repositories create malaya-repo \
        --repository-format=docker \
        --location=asia-southeast1 \
        --description="Malaya LLM Repository"

    # Configure Docker auth
    gcloud auth configure-docker asia-southeast1-docker.pkg.dev

    # Build and Push
    # We use the deployment/Dockerfile
    docker build -t asia-southeast1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/malaya-repo/malaya-app:latest -f deployment/Dockerfile .
    docker push asia-southeast1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/malaya-repo/malaya-app:latest
    ```

---

## Step 2: Set Up the Model (Qwen)

Choose **Strategy A** or **Strategy B**.

### Strategy A: API Mode (Simplest)
Use a provider that hosts Qwen 2.5 (e.g., Groq, DeepInfra, Together AI).

1.  Get an API Key from the provider.
2.  **Configuration**:
    *   Provider: `openai` (most support OpenAI SDK compatibility) or `ollama` if they mimic the IP.
    *   Base URL: `https://api.groq.com/openai/v1` (example)
    *   API Key: `YOUR_KEY`

### Strategy B: Sovereign Cloud (GPU VM)
Run Qwen on your own Google Cloud GPU VM via Ollama.

1.  **Create a GPU VM**:
    ```bash
    gcloud compute instances create qwen-server \
        --machine-type=g2-standard-4 \
        --accelerator=type=nvidia-l4,count=1 \
        --zone=asia-southeast1-a \
        --image-family=common-cu118 \
        --image-project=deeplearning-platform-release \
        --maintenance-policy=TERMINATE
    ```

2.  **SSH and Install Ollama**:
    ```bash
    gcloud compute ssh qwen-server
    curl -fsSL https://ollama.com/install.sh | sh
    ollama serve
    ```

3.  **Pull Qwen**:
    ```bash
    ollama run qwen2.5:7b
    ```

4.  **Expose Securely**:
    *   **Option 1 (Private VPC)**: Connect Cloud Run to VPC via Serverless VPC Connector (Secure, Recommended).
    *   **Option 2 (Public IP - risky without auth)**: You'll need to configure a reverse proxy (Nginx) with Basic Auth.

---

## Step 3: Deploy to Cloud Run

Deploy the container and point it to your model.

### Command for Strategy A (API)
```bash
gcloud run deploy malaya-app \
    --image asia-southeast1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/malaya-repo/malaya-app:latest \
    --region asia-southeast1 \
    --allow-unauthenticated \
    --set-env-vars="OPENAI_API_KEY=your-key,OPENAI_BASE_URL=https://api.groq.com/openai/v1,MODEL_NAME=qwen-2.5-7b"
```

### Command for Strategy B (Custom VM / Ollama)
Assumption: You are using a VPC Connector or have a public IP (e.g., `http://1.2.3.4:11434`).

```bash
gcloud run deploy malaya-app \
    --image asia-southeast1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/malaya-repo/malaya-app:latest \
    --region asia-southeast1 \
    --allow-unauthenticated \
    --set-env-vars="OLLAMA_BASE_URL=http://<VM_IP_OR_HOSTNAME>:11434,MALAYA_FORCE_MOCK=0"
```

---

## Verification
1.  Open the Cloud Run URL.
2.  Go to the "Settings" or "Benchmark" tab.
3.  Send a test message ("Hello").

---

## Step 4: Continuous Deployment (CI/CD)

We use **Google Cloud Build** to automatically build and deploy the application whenever you push to GitHub.

### 1. The Configuration
The `cloudbuild.yaml` file in the root directory defines the build process:
-   Builds the Docker image for `linux/amd64`
-   Pushes it to Google Artifact Registry
-   Deploys to Cloud Run with the following **Production Overrides**:
    -   `MODEL_PROVIDER`: `openai`
    -   `MODEL_NAME`: `gpt-4o`
    -   `MALAYA_ENV`: `production`

### 2. Connect to GitHub
1.  Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers).
2.  Click **Create Trigger**.
3.  **Source**: Select your GitHub repository.
4.  **Branch**: `^main$` (so it deploys on every push to main).
5.  **Configuration**: Select "Cloud Build configuration file (yaml/json)" and point it to `cloudbuild.yaml`.
6.  **Click Create**.

### 3. Important: Secrets
For the production app to work, Cloud Run needs your API keys. since we override the model to ChatGPT, you **MUST** ensure the `OPENAI_API_KEY` is set in the Cloud Run service variables.

You can do this via the command line once:
```bash
gcloud run services update malaya-app \
    --region asia-southeast1 \
    --update-env-vars OPENAI_API_KEY=your-actual-key-here
```
Or add a Step in `cloudbuild.yaml` to fetch it from Secret Manager (more secure).
