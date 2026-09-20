# KanMind API

REST backend for KanMind, a Kanban board app. Built with Django and Django REST Framework.

The frontend is not part of this repository.

## Requirements

- Python 3.12+
- pip

## Setup

```bash
git clone https://github.com/weskakay/kanmind.git
cd kanmind
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py create_guest_user
python manage.py runserver
```

The API runs at `http://127.0.0.1:8000/api/`.

## Guest user

The frontend offers a guest login with fixed credentials. Create that
account once with:

```bash
python manage.py create_guest_user
```

It creates `kevin@kovacsi.de` with the password `asdasdasd`. Running the
command twice does nothing.

## Authentication

Users register and log in with their email address. Both endpoints return a
token that has to be sent with every further request:

```
Authorization: Token <token>
```

| Method | Path                 | Purpose              |
|--------|----------------------|----------------------|
| POST   | `/api/registration/` | Create an account    |
| POST   | `/api/login/`        | Get a token          |

## Configuration

`SECRET_KEY` and `DEBUG` are read from the environment and fall back to
development defaults:

```bash
export DJANGO_SECRET_KEY="your-secret"
export DJANGO_DEBUG=False
```

## Development

```bash
pip install -r requirements-dev.txt
coverage run manage.py test
coverage report
flake8
```
