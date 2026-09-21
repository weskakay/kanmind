# KanMind API

REST backend for KanMind, a Kanban board app. Built with Django and Django
REST Framework.

Users sign up with their email address, create boards, share them with other
users, move tasks through four columns and comment on them.

The frontend is not part of this repository.

## Requirements

- Python 3.12+
- pip

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/weskakay/kanmind.git
```

**2. Enter the project folder**

```bash
cd kanmind
```

**3. Create a virtual environment**

```bash
python3 -m venv .venv
```

**4. Activate it** — macOS and Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

**5. Install the dependencies**

```bash
pip install -r requirements.txt
```

**6. Create the database**

```bash
python manage.py migrate
```

**7. Create the guest account the frontend uses**

```bash
python manage.py create_guest_user
```

**8. Start the server**

```bash
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

Every endpoint except registration and login needs a token:

```
Authorization: Token <token>
```

Registration and login both return one.

## Endpoints

### Auth

| Method | Path                 | Purpose           | Codes         |
|--------|----------------------|-------------------|---------------|
| POST   | `/api/registration/` | Create an account | 201, 400      |
| POST   | `/api/login/`        | Get a token       | 200, 400      |

### Boards

| Method | Path                    | Who              | Codes                   |
|--------|-------------------------|------------------|-------------------------|
| GET    | `/api/boards/`          | own and shared   | 200, 401                |
| POST   | `/api/boards/`          | any user         | 201, 400, 401           |
| GET    | `/api/boards/{id}/`     | owner, members   | 200, 401, 403, 404      |
| PATCH  | `/api/boards/{id}/`     | owner, members   | 200, 400, 401, 403, 404 |
| DELETE | `/api/boards/{id}/`     | owner only       | 204, 401, 403, 404      |

### Users

| Method | Path                | Purpose                  | Codes              |
|--------|---------------------|--------------------------|--------------------|
| GET    | `/api/email-check/` | Find a user by address   | 200, 400, 401, 404 |

Takes `?email=` and answers with the matching user, so the frontend can add
members by address.

### Tasks

| Method | Path                           | Who                   | Codes                   |
|--------|--------------------------------|-----------------------|-------------------------|
| POST   | `/api/tasks/`                  | board members         | 201, 400, 401, 403, 404 |
| PATCH  | `/api/tasks/{id}/`             | board members         | 200, 400, 401, 403, 404 |
| DELETE | `/api/tasks/{id}/`             | creator, board owner  | 204, 401, 403, 404      |
| GET    | `/api/tasks/assigned-to-me/`   | any user              | 200, 401                |
| GET    | `/api/tasks/reviewing/`        | any user              | 200, 401                |

Assignee and reviewer have to be members of the board. `status` is one of
`to-do`, `in-progress`, `review`, `done`; `priority` one of `low`, `medium`,
`high`.

### Comments

| Method | Path                                  | Who           | Codes                   |
|--------|---------------------------------------|---------------|-------------------------|
| GET    | `/api/tasks/{id}/comments/`           | board members | 200, 401, 403, 404      |
| POST   | `/api/tasks/{id}/comments/`           | board members | 201, 400, 401, 403, 404 |
| DELETE | `/api/tasks/{id}/comments/{cid}/`     | author only   | 204, 401, 403, 404      |

Comments come back oldest first and carry the author's full name.

## Project layout

```
core/         project settings and root urls
auth_app/     custom user model, registration and login
kanban_app/   boards, tasks and comments
```

Each app keeps its API code in an `api/` folder: serializers, views,
permissions and urls.

## Admin

```bash
python manage.py createsuperuser
```

Users, boards, tasks and comments are editable at
`http://127.0.0.1:8000/admin/`.

## Configuration

`SECRET_KEY` and `DEBUG` are read from the environment and fall back to
development defaults, so the setup above works without any configuration.

`.env.example` lists the variables. Copy it and fill in your own values:

```bash
cp .env.example .env
```

The project does not load that file on its own. Export the values before
starting the server:

```bash
set -a; source .env; set +a
```

A single variable works the same way:

```bash
export DJANGO_SECRET_KEY="your-secret"
```

```bash
export DJANGO_DEBUG=False
```

Cross origin requests are allowed from `127.0.0.1` and `localhost` on ports
5500 and 5501, which is where the frontend is usually served.

## Development

Install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the tests:

```bash
coverage run manage.py test
```

Show the coverage report:

```bash
coverage report
```

Check the code style:

```bash
flake8
```

The suite covers every endpoint with every status code of the specification.
