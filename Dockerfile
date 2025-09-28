FROM python:3.9-slim-bullseye

# Update & install required system dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    git \
    curl \
    ffmpeg \
    python3-pip \
    pkg-config \
    libcairo2-dev \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install -U pip setuptools wheel

# Copy project files
COPY . /app/
WORKDIR /app/

# Install Python dependencies
RUN pip3 install -U -r requirements.txt

# Start command
CMD ["bash", "start.sh"]