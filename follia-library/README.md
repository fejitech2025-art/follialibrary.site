# Follia

Follia is a social discovery platform with a strong library and Book Club experience: **Discover anything.**

The existing Vue 3 application is in this folder. Its data/auth layer now talks to the Django REST Framework API in the sibling `django/` folder. The backend uses SQLite for local development. The PWA configuration, install prompt, composable, manifest and assets remain in place.

## Run Django

In PowerShell from the repository root:

```powershell
cd .\django
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Django runs at `http://localhost:8000`. New accounts use django-allauth email confirmation. In development, verification and reset emails print to the Django terminal. For Google sign-in, set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` before starting Django. Google’s local callback is `http://localhost:8000/accounts/google/login/callback/`.

## Run Vue

In a second PowerShell terminal from the repository root:

```powershell
cd .\follia-library
npm install
npm run dev
```

Vite runs at `http://localhost:5173`. The API base defaults to `http://localhost:8000`. To change it, copy `.env.example` to `.env.local` and update `VITE_API_BASE_URL`.

## Packages

Backend packages:

- Already present before this migration: `Django==6.1.2`.
- Newly required and listed in `django/requirements.txt`: `djangorestframework`, `django-allauth[socialaccount]`, `django-cors-headers`, `channels`, and `daphne`.

Install the backend packages with `pip install -r requirements.txt` from `django/`.

Frontend packages already in the project: Vue 3, Vue Router, Pinia, Lucide Vue Next, Vite, the Vue Vite plugin, vite-plugin-pwa, Vue DevTools and Prettier. This migration adds no frontend packages. The unused Supabase client dependency was removed.

## Product areas

- Home is a mixed social feed of posts and Follia resources, with For you and Following views.
- Explore searches people, posts, resources and Book Clubs.
- The centered create action lets people create a post or upload a separate library resource.
- Profiles show posts, resources, followers and following. Profile actions use Follow and Following.
- Book Clubs keep member roles, resource links, chat, replies, pinning and moderation.
- Book Club chat writes use the DRF API and message updates are delivered over Django Channels WebSockets. The local channel layer is in memory for a single development server.

Existing Supabase production data has not been modified or imported. The new SQLite database starts empty; account/resource migration is a separate task.
