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
python manage.py runserver
```

The API runs at `http://127.0.0.1:8000/api/`.

## Development

```bash
pip install -r requirements-dev.txt
coverage run manage.py test
coverage report
flake8
```
