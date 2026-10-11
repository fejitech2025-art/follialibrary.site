# Follia Django API

This is the local Django REST Framework backend for Follia. It uses Django's default SQLite database. It does not connect to Supabase or migrate production data.

## Start the backend (PowerShell)

From the repository root:

```powershell
cd .\django
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API runs at `http://localhost:8000`. Uploaded files are stored under `django/media/`.

## Local settings

Set the frontend origin if it differs from Vite's default:

```powershell
$env:FRONTEND_URL = "http://localhost:5173"
$env:DJANGO_SECRET_KEY = "use-a-local-secret"
```

For Google sign-in, create a Google OAuth web client and allow this callback URL:

```text
http://localhost:8000/accounts/google/login/callback/
```

Then set the credentials before starting Django:

```powershell
$env:GOOGLE_CLIENT_ID = "your-client-id"
$env:GOOGLE_CLIENT_SECRET = "your-client-secret"
python manage.py runserver
```

Email is written to the terminal by default, so signup verification and password-reset flows work locally without an email provider. Set `DJANGO_EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `EMAIL_USE_TLS` when connecting a real SMTP provider.

## Apps and models

- `accounts`: Profile, Follow, Notification; email/password API and profile endpoints.
- `library`: Resource, ResourceLike, ResourceBookmark, ResourceComment.
- `social`: Post, PostLike, PostBookmark, PostComment, ContentReport.
- `clubs`: BookClub, BookClubMembership, BookClubResource, BookClubMessage.

Book Club resources are join records. Removing a `BookClubResource` link leaves the library resource untouched.

## API routes

- `/api/auth/csrf/`, `/api/auth/me/`, `/api/auth/register/`, `/api/auth/login/`, `/api/auth/logout/`
- `/accounts/google/login/` and the other django-allauth account routes
- `/api/me/profile/`, `/api/users/`, `/api/users/<id>/`, `/api/users/<id>/follow/`, `/followers/`, `/following/`
- `/api/feed/`, `/api/posts/`, `/api/posts/<id>/`, `/like/`, `/save/`, `/comments/`, `/report/`
- `/api/resources/`, `/api/resources/<id>/`, `/like/`, `/save/`, `/comments/`, `/file/`, `/api/bookmarks/`
- `/api/search/?q=...`, `/api/notifications/`, `/api/notifications/<id>/read/`
- `/api/clubs/`, `/api/clubs/<id>/`, `/membership/`, `/join/`, `/messages/`, `/resources/`, `/members/<id>/`
- `ws://localhost:8000/ws/clubs/<club_id>/` for authenticated Book Club message delivery

## Realtime chat

HTTP endpoints create, delete, and pin group messages. Django Channels broadcasts those changes to the authenticated club's WebSocket group. The development channel layer is in memory, which keeps local setup small and is suitable for one Django process. Use a shared channel layer before running multiple app processes in production.

## Checks and migrations

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

The project intentionally has no direct-message endpoints, no Redis, and no production data import.
