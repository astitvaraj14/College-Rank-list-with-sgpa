# Use Python 3.9 Slim (Lightweight)
FROM python:3.9-slim

# 1. Install Chromium and Chromedriver
# This installs the browser AND the driver automatically
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 2. Set Working Directory
WORKDIR /app

# 3. Copy Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy App Files
COPY . .

# 5. Set Environment Variables for Selenium
# Tell Python where Chromium lives
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PORT=10000

# 6. Start the App
CMD ["gunicorn", "run_app:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]