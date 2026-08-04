FROM python:3.13-slim

RUN apt-get update && apt-get install --no-install-recommends -y cron && \
   apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt check_blacklist.py ./

RUN pip install --no-cache-dir -r requirements.txt

COPY cronjob /etc/cron.d/cronjob

RUN chmod 0644 /etc/cron.d/cronjob

RUN crontab /etc/cron.d/cronjob

CMD ["/bin/sh", "-c", "printenv > /etc/environment && cron -f"]