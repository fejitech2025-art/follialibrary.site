# Follia Django API

This is the Django REST Framework backend for Follia. `DB_ENGINE` selects the database backend (the settings default is MySQL; set it to `django.db.backends.sqlite3` for local SQLite development). This application does not connect to Supabase or migrate production data.

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

## Media storage

Profile avatars, Book Club avatars, resource covers, and post images/videos use
the shared media storage configured in `config/settings.py`. With the R2
variables below set, Django uploads those files to Cloudflare R2. Without R2
credentials, local debug mode uses `django/media/`; production media uploads
are rejected until R2 is configured. Downloadable resource files continue to
use the existing local file storage. Videos are limited to 40 MB per file on
regular-post create and edit endpoints.

Set these variables in `django/.env` for local R2 use and in the backend
hosting provider's environment settings for production:

```text
R2_BUCKET_NAME=your-r2-bucket
R2_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=replace-with-r2-access-key-id
R2_SECRET_ACCESS_KEY=replace-with-r2-secret-access-key
R2_REGION=auto
R2_PUBLIC_DOMAIN=
```

`R2_PUBLIC_DOMAIN` is optional and should contain only the hostname of a
custom domain connected to this bucket. When configured, media URLs use that
domain without query signatures, so the bucket/domain must allow public reads.
Leave it blank for a private bucket; Django will return short-lived signed
URLs using the S3-compatible endpoint. R2 credentials belong only in the
backend environment, never in Vue environment variables.

## Authentication

Follia uses Google sign-in for both new and returning users. Local email/password
sign-in and sign-up endpoints are not exposed. Existing user records remain in
the database; when a Google account returns a verified email matching an
existing account, Allauth connects that Google identity to the existing user.

Create a Google OAuth web client. Set `GOOGLE_CLIENT_ID` and
`GOOGLE_CLIENT_SECRET` in the backend environment, and add the backend callback
URL to the client's **Authorized redirect URIs**:

```text
http://localhost:8000/accounts/google/login/callback/
https://<your-api-host>/accounts/google/login/callback/
```

Set `FRONTEND_URL` to the deployed Vue origin. The frontend starts Google login
with a CSRF-protected POST to `/accounts/google/login/`; Allauth validates OAuth
state and redirects to the requested local frontend path (or `FRONTEND_URL/`).
For a cross-site frontend/API deployment, serve both over HTTPS and set
`SESSION_COOKIE_SAMESITE=None` and `CSRF_COOKIE_SAMESITE=None`; Django enables
secure cookies for those settings. Keep the Google client secret in the backend
only.

Also set `DJANGO_ALLOWED_HOSTS` to the API host and set both
`CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` to the exact frontend origin,
for example `https://library.example.com`. This allows the CSRF-protected
cross-origin login POST and Allauth's safe redirect back to that origin.

## Local settings

Set the frontend origin if it differs from Vite's default:

```powershell
$env:FRONTEND_URL = "http://localhost:5173"
$env:DJANGO_SECRET_KEY = "use-a-local-secret"
```

Set the credentials before starting Django:

```powershell
$env:GOOGLE_CLIENT_ID = "your-client-id"
$env:GOOGLE_CLIENT_SECRET = "your-client-secret"
python manage.py runserver
```

## Browser push notifications

Push delivery requires a VAPID key pair and HTTPS in production. Generate a
pair with a Web Push VAPID key generator, then configure these backend-only
environment variables:

```text
VAPID_PUBLIC_KEY=<public-key>
VAPID_PRIVATE_KEY=<private-key>
VAPID_SUBJECT=mailto:<an-address-you-monitor>
```

Install the backend requirements (including `pywebpush`) when deploying. The
public key is returned by `/api/push/public-key/`; the private key is never
sent to the frontend. The Vue PWA build extends its generated service worker
with `public/follia-push-sw.js`. Users enable push from Notifications after
signing in; permission is requested only after their explicit action. A
missing key, denied permission, unsupported browser, or non-HTTPS context leaves
in-app notifications available and shows a suitable status.

Delivery configuration has not been verified for a production domain or VAPID
key pair. Web Push support depends on the browser and device.

## Email

The current settings use SMTP for email. Configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `EMAIL_USE_TLS` when email delivery is needed; Google sign-in does not use the removed manual email-verification flow.

## Apps and models

- `accounts`: Profile, Follow, Notification, PushSubscription, and profile endpoints.
- `library`: Resource, ResourceLike, ResourceBookmark, ResourceComment, ResourceCommentLike.
- `social`: Post, PostMedia, PostLike, PostBookmark, PostComment, PostCommentLike, ContentReport.
- `clubs`: BookClub, BookClubMembership, BookClubResource, BookClubMessage.

Book Club resources are join records. Removing a `BookClubResource` link leaves the library resource untouched.

## API routes

- `/api/auth/csrf/`, `/api/auth/me/`, `/api/auth/logout/`
- `/accounts/google/login/` and the Google OAuth callback handled by django-allauth
- `/api/me/profile/`, `/api/users/`, `/api/users/<id>/`, `/api/users/<id>/follow/`, `/followers/`, `/following/`
- `/api/feed/`, `/api/posts/`, `/api/posts/<id>/`, `/like/`, `/save/`, `/comments/`, `/report/`
- `/api/posts/<id>/file/` and `/api/posts/<id>/media/<media_id>/file/` for watermarked media downloads
- `/api/resources/`, `/api/resources/<id>/`, `/like/`, `/save/`, `/comments/`, `/preview/`, `/file/`, `/report/`, `/api/bookmarks/`
- `/api/search/?q=...`, `/api/notifications/`, `/api/notifications/unread-count/`, `/api/notifications/<id>/read/`
- `/api/push/public-key/`, `/api/push/subscriptions/`
- `/api/clubs/`, `/api/clubs/<id>/`, `/membership/`, `/join/`, `/messages/`, `/resources/`, `/members/<id>/`
- `ws://localhost:8000/ws/clubs/<club_id>/` for authenticated Book Club message delivery

## Realtime chat

HTTP endpoints create, delete, and pin group messages. Django Channels broadcasts those changes to the authenticated club's WebSocket group. The development channel layer is in memory, which keeps local setup small and is suitable for one Django process. Use a shared channel layer before running multiple app processes in production.

## Checks and migrations

Set `FRONTEND_URL` to the deployed Follia Library website origin. Watermark links use
`FOLLIA_PUBLIC_URL` when set and otherwise use `FRONTEND_URL`. Install the Python
dependencies in `requirements.txt` for image and PDF watermarking. Video downloads
also require FFmpeg on the Django host; set `FFMPEG_BINARY` if its executable is not
on `PATH`. Video watermarking runs when a download is requested and uses temporary
files that are removed after the response finishes.

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

The project intentionally has no direct-message endpoints, no Redis, and no production data import.
