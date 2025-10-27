# ---------------------------------------------------------
# Dockerfile für quantbot-ai (Variante A: Paper-Trading)
# ---------------------------------------------------------

# 1️⃣ Verwende eine leichte Python-Version als Basis
FROM python:3.11-slim

# 2️⃣ Vermeide interaktive Installationsfragen
ENV DEBIAN_FRONTEND=noninteractive

# 3️⃣ Setze Arbeitsverzeichnis im Container
WORKDIR /app

# 4️⃣ Kopiere Projektdateien in den Container
COPY . /app

# 5️⃣ Installiere Systempakete (z. B. für Matplotlib / NumPy)
RUN apt-get update && apt-get install -y \
    gcc g++ libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 6️⃣ Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# 7️⃣ Exponiere Flask-Port (muss zu main.py passen)
EXPOSE 10000

# 8️⃣ Setze Standardumgebung auf „production“
ENV FLASK_ENV=production

# 9️⃣ Starte den Trading-Bot
CMD ["python", "main.py"]
