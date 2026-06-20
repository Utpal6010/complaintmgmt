FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y build-essential libpq-dev gcc --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . /app/

# collect static (if you use whitenoise or similar in production, otherwise optional)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["bash", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
