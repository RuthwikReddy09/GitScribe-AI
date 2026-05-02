import logging

from fastapi import FastAPI, Header, HTTPException, Request

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.security import verify_github_signature
from app.models import ProcessPRRequest, ProcessPRResponse
from app.services.processor import PRProcessor

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
app = FastAPI(title='GitScribe', version='1.0.0')


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/process-pr', response_model=ProcessPRResponse)
def process_pr(req: ProcessPRRequest) -> ProcessPRResponse:
    try:
        return PRProcessor(settings).process(req.owner, req.repo, req.pull_number)
    except Exception as exc:
        logger.exception('PR processing failed')
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post('/webhooks/github')
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> dict[str, str]:
    body = await request.body()
    if not verify_github_signature(body, x_hub_signature_256, settings.webhook_secret):
        raise HTTPException(status_code=401, detail='Invalid GitHub webhook signature')

    payload = await request.json()
    if x_github_event != 'pull_request':
        return {'status': 'ignored', 'reason': 'not a pull_request event'}

    action = payload.get('action')
    if action not in {'opened', 'synchronize', 'reopened'}:
        return {'status': 'ignored', 'reason': f'action {action} is not handled'}

    repo_data = payload['repository']
    owner = repo_data['owner']['login']
    repo = repo_data['name']
    pull_number = payload['pull_request']['number']

    result = PRProcessor(settings).process(owner, repo, pull_number)
    return {'status': result.status, 'message': result.message}
