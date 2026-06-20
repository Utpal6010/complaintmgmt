# AC Complaint Support Portal

This repository contains the AC Complaint Support Portal — a Django application with role-based access control, SLA tracking, REST APIs, and audit logging.

This README explains how to run the project locally and with Docker.

## Prerequisites

- Docker & Docker Compose installed (for containerized setup)
- Python 3.12 (for local development)

## Quickstart — Docker (recommended)

1. Build and start services (web + MongoDB + mongo-express):

```bash
docker-compose up --build
```

2. The Django app will be available at `http://localhost:8000`.
	- Mongo Express UI for MongoDB is at `http://localhost:8081` (user: `admin`, pass: `admin123`).

3. To create a superuser or run management commands in the web container:

```bash
docker-compose run --rm web python manage.py createsuperuser
docker-compose run --rm web python manage.py migrate
docker-compose run --rm web python manage.py seed_support_data
```

4. To stop and remove containers:

```bash
docker-compose down -v
```

## Local development (without Docker)

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run migrations and seed data:

```bash
python manage.py migrate
python manage.py seed_support_data
```

4. Run the development server:

```bash
python manage.py runserver 0.0.0.0:8000
```

## Environment variables

The Docker Compose setup uses simple defaults for development. For production, set the following environment variables in a secure way (e.g., Docker secrets, environment, or an orchestration tool):

- `DEBUG` (0/1)
- `SECRET_KEY`
- `ALLOWED_HOSTS`

## Running tests

Locally:

```bash
python manage.py test hello_world.support
```

Or inside the container:

```bash
docker-compose run --rm web python manage.py test hello_world.support
```

## Reports and documentation

The repository includes generated reports:

- `TEST_REPORT.md` — functional test summary
- `SECURITY_AND_TEST_REPORT.md` — OWASP Top 10 analysis and recommendations
- `PROJECT_COMPLETION_SUMMARY.md` — project features and status
- `DELIVERABLES.md` — deliverables checklist

## Notes

- This Docker configuration is intended for development and staging. For production use, configure a proper WSGI server (Gunicorn), a production-grade database, HTTPS termination, and persistent storage.

---

If you want, I can help produce a production-ready `docker-compose.prod.yml` and add a `nginx` + `gunicorn` setup.

## Production single-click deployment

This repository includes a `docker-compose.prod.yml` to deploy a production-ready stack using `gunicorn` and `nginx`.

1. Build and start the production stack (example with environment variables):

```bash
export SECRET_KEY="<generate-strong-secret>"
export ALLOWED_HOSTS="yourdomain.com"
docker-compose -f docker-compose.prod.yml up --build -d
```

2. The application will be available on port 80. Static files are served by `nginx` and the application runs under `gunicorn`.

3. To view logs:

```bash
docker-compose -f docker-compose.prod.yml logs -f
```

4. To stop and remove the production stack:

```bash
docker-compose -f docker-compose.prod.yml down -v
```

Notes:
- `docker-compose.prod.yml` uses `static_volume` to share collected static files between the `web` and `nginx` services.
- Ensure you set strong values for `SECRET_KEY` and restrict `ALLOWED_HOSTS` before exposing to the public internet.
