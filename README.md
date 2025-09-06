# Mortgage-Rate-Monitor

A Docker image that uses Python to obtain and store mortgage rates and stock prices of mortgage-backed bonds.

## Overview

Knowing current mortgage rates, and values of mortgage-backed bonds ($MBB) can be useful in identifying favorable environments for taking on new loans or refinancing existing loans. I found myself manually searching for this information more frequently than I preferred, so this package provides a solution that removes nearly all effort required to obtain this information on a regular cadence.

This project simply obtains and stores data. Using the data for visualization or notifications is not included.

## Features

- Scrapes data from https://www.mortgagenewsdaily.com/ each day at 6:40 AM America/Los_Angeles
- Fetches real-time stock prices via the `yfinance` Python package
- Stores results in either SQLite (default) or a user-provided PostgreSQL database
- Fully containerized with a `Dockerfile`
- Development environment via `.devcontainer` and `Dockerfile.dev`

## Prerequisites

- Docker
- Optional: PostgreSQL server
- Optional: VS Code with Dev Containers

## Docker Compose Configurations

For default settings with a self-contained database:

```yml
services:
  ratemonitor:
    image: ghcr.io/hicks017/mortgage-rate-monitor
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

---

For connecting to a pre-existing database on a PostgreSQL server:

```yml
services:
  ratemonitor:
    image: ghcr.io/hicks017/mortgage-rate-monitor
    environment:
      PG_HOST: your_host_ip
      PG_PORT: your_host_port
      PG_USER: your_user
      PG_PASSWORD: your_password
      PG_DB: your_db_name
    restart: unless-stopped
```

---

For hosting a new PostgreSQL server during the app build:

```yml
services:
  ratemonitor:
    image: ghcr.io/hicks017/mortgage-rate-monitor
    environment:
      PG_HOST: db
      PG_PORT: 5432
      PG_USER: rates
      PG_PASSWORD: changeme
      PG_DB: rates_db
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
  db:
    image: postgres:17
    environment:
      POSTGRES_USER: rates
      POSTGRES_PASSWORD: changeme
      POSTGRES_DB: rates_db
    volumes:
      - ./db:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -h localhost -U $$POSTGRES_USER"]
      interval: 2s
      start_period: 30s
```

---
