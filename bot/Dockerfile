FROM python:3.13-slim

WORKDIR /app

COPY ./chujlib ./chujlib

RUN mkdir -p ./data \
   ./data/jsons \
   ./data/images \
   ./data/logs \
   ./data/logs/errors \
   ./data/logs/songs \
   ./data/logs/episodes

RUN chmod 2777 ./data \
   ./data/jsons \
   ./data/images \
   ./data/logs \
   ./data/logs/errors \
   ./data/logs/songs \
   ./data/logs/episodes

COPY logger_config.json ./data/jsons

COPY requirements.txt CHUJ.py ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "CHUJ.py"]