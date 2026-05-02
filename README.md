# GitScribe

GitScribe is a production-ready AI documentation agent for GitHub repositories. It listens to pull request events, analyzes changed source files, updates documentation with an LLM, commits the documentation changes back to the PR branch, and comments on the PR.

## Features

- FastAPI webhook server
- GitHub App authentication with installation tokens
- Personal access token fallback for local testing
- Pull request file diff collection
- LLM-based documentation updates
- Safe file filtering and file size limits
- Commits generated docs directly to the PR branch
- Posts a PR comment summarizing updates

## 1. Create a GitHub App

Go to GitHub Settings > Developer settings > GitHub Apps > New GitHub App.

Use these permissions:

- Contents: Read and write
- Pull requests: Read and write
- Metadata: Read-only

Subscribe to these webhook events:

- Pull request

Set the webhook URL to:

```text
https://YOUR_DOMAIN.com/webhooks/github
```

Generate a private key and save it as `private-key.pem`.

Install the app on your repository and copy the installation ID.

## 2. Configure environment

Copy the example file:

```bash
cp .env.example .env
```

Fill in:

```bash
WEBHOOK_SECRET=your_github_webhook_secret
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY_PATH=./private-key.pem
GITHUB_INSTALLATION_ID=your_installation_id
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini
```

For local testing only, you may use:

```bash
GITHUB_TOKEN=github_pat_or_fine_grained_token
```

## 3. Run locally

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## 4. Test with a manual PR request

This bypasses GitHub webhooks and is useful while developing.

```bash
curl -X POST http://localhost:8000/process-pr \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "YOUR_ORG_OR_USER",
    "repo": "YOUR_REPO",
    "pull_number": 1
  }'
```

## 5. Expose local webhook with ngrok

```bash
ngrok http 8000
```

Use the ngrok HTTPS URL as your GitHub App webhook URL:

```text
https://YOUR_NGROK_DOMAIN/webhooks/github
```

## 6. Run with Docker

```bash
docker build -t gitscribe .
docker run --env-file .env -p 8000:8000 gitscribe
```

## 7. Deploy

You can deploy this to Render, Railway, Fly.io, AWS ECS, Azure Container Apps, or GCP Cloud Run.

Minimum production requirements:

- HTTPS endpoint
- Environment variables configured securely
- GitHub private key mounted as a secret file
- Webhook secret configured in GitHub App and `.env`

## 8. Optional GitHub Action trigger

The included `.github/workflows/gitscribe.yml` can call a deployed GitScribe API from PR events instead of relying only on GitHub App webhooks.

Repository secrets required:

```text
GITSCRIBE_API_URL=https://YOUR_DOMAIN.com
GITSCRIBE_API_TOKEN=some-shared-token-if-you-add-auth
```

## API endpoints

```text
GET  /health
POST /webhooks/github
POST /process-pr
```
