# Dockerfile for vanna-ai Flask application
FROM python:3.11-slim

# Install system dependencies for pyodbc and ODBC Driver
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		gcc \
		g++ \
		unixodbc-dev \
		curl \
		gnupg2 \
		apt-transport-https \
	&& mkdir -p /etc/apt/keyrings \
	&& curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/keyrings/microsoft.gpg \
	&& echo "deb [signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" | tee /etc/apt/sources.list.d/mssql-release.list \
	&& apt-get update \
	&& ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_RUN_HOST=0.0.0.0

CMD ["python", "app.py"]
