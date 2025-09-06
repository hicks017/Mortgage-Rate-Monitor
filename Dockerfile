# Development Dockerfile
FROM python:3.13.7-slim-trixie

# Set working directory
WORKDIR /app
COPY . /app

# Install development dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y git procps \
    && rm -rf /var/lib/apt/lists/* \
    && pip install -r requirements.txt

# Verifies that the scheduler is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD pgrep -f "python main.py" > /dev/null || exit 1

# Launch the app
CMD ["python", "main.py"]