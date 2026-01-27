# Use Python 3.9
FROM python:3.9-slim

# 1. Install basic tools
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Google Chrome (Direct Download Method)
# This bypasses the "apt-key not found" error
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && apt-get clean

# 3. Set Working Directory
WORKDIR /app

# 4. Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy App Files
COPY . .

# 6. Set Environment Variables
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PORT=10000

# 7. Start the App
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]