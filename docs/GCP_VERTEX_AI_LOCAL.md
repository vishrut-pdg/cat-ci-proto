# Local Vertex AI setup for Ask Katty

Ask Katty uses the Google Gen AI SDK with Vertex AI. The backend automatically falls back to a
deterministic database-grounded answer when Vertex AI is not configured or cannot be reached.

## 1. Prepare a Google Cloud project

You need a project with billing enabled and permission to use Vertex AI.

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com
```

Your user or service account needs `roles/aiplatform.user`. A project administrator can grant it:

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/aiplatform.user"
```

## 2. Create local Application Default Credentials

For local development, use your Google identity rather than downloading a long-lived key:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

On macOS and Linux this normally creates:

```text
$HOME/.config/gcloud/application_default_credentials.json
```

Confirm that an access token can be issued:

```bash
gcloud auth application-default print-access-token >/dev/null
```

## 3. Configure the repository `.env`

Copy the example if needed:

```bash
cp .env.example .env
```

Set these values in the repository-root `.env`:

```dotenv
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_APPLICATION_CREDENTIALS_HOST=/Users/YOUR_USER/.config/gcloud/application_default_credentials.json
GEMINI_MODEL=gemini-2.5-flash
```

Use an absolute host path for `GOOGLE_APPLICATION_CREDENTIALS_HOST`. Compose mounts that file
read-only inside the backend container at `/credentials/google-credentials.json`.

The local demo resets its synthetic database whenever the backend starts. To retain workflow
changes while configuring Vertex AI, also set:

```dotenv
RESET_DEMO_DATA_ON_START=false
```

## 4. Rebuild the backend

```bash
docker compose up -d --build --force-recreate backend
docker compose logs -f backend
```

The backend should become healthy without a credentials error. Ask Katty shows `Vertex AI` after
the first successful model response. If Vertex AI fails, the UI shows the reason and uses the
grounded local response instead.

## 5. Verify credentials inside Docker

This check confirms the mounted credential can obtain a token without printing it:

```bash
docker compose exec backend uv run python -c \
  "import google.auth; from google.auth.transport.requests import Request; c,p=google.auth.default(); c.refresh(Request()); print('ADC project:', p or 'quota-project credential')"
```

## Service-account alternative

For a shared non-personal environment, create a dedicated service account with
`roles/aiplatform.user`, keep its JSON key outside the repository, and point
`GOOGLE_APPLICATION_CREDENTIALS_HOST` to that file. Never copy the key into an image or commit it.

## Common failures

- `DefaultCredentialsError`: the host path is wrong or the ADC file was not mounted. Use an
  absolute path and recreate the backend container.
- `403 PermissionDenied`: enable `aiplatform.googleapis.com`, confirm billing, and grant
  `roles/aiplatform.user` to the active identity.
- Model/location error: keep `GOOGLE_CLOUD_LOCATION=global` and verify that the configured
  `GEMINI_MODEL` is available to the project.
- Quota-project warning: run `gcloud auth application-default set-quota-project YOUR_PROJECT_ID`.
