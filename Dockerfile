# Malaya LLM v2 - Full Mode Container
# ==========================================
# Resolves TensorFlow/Numpy incompatibility on macOS ARM64
# by running in a stable Linux environment.

FROM python:3.10-slim

WORKDIR /app

# 1. System Dependencies (for Malaya Speech/Audio)
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Python Dependencies
COPY requirements.txt .

# Force Numpy < 2.0 for TensorFlow compatibility
RUN sed -i 's/numpy>=1.24.0/numpy<2.0.0/' requirements.txt

# Install dependencies
# Using --no-cache-dir to keep image small
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 3. Application Code
COPY . .

# 4. Environment Configuration
ENV HOST=0.0.0.0
ENV PORT=8000
# Ensure Malaya uses Full Mode
ENV MALAYA_FORCE_MOCK=0
# Disable CUDA (CPU only mode)
ENV CUDA_VISIBLE_DEVICES=-1

# 5. Start Server
EXPOSE 8000
CMD ["python", "benchmark-tracker/server.py"]
