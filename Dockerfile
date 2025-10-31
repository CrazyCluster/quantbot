FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y gcc g++ libffi-dev libssl-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 10000
ENV FLASK_ENV=production
CMD ["python", "main.py"]
