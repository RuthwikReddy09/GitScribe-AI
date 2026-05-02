import base64
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
import jwt

from app.core.config import Settings


@dataclass
class ChangedFile:
    filename: str
    status: str
    patch: str | None = None


class GitHubClient:
    API = 'https://api.github.com'

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = httpx.Client(timeout=30)

    def _jwt(self) -> str:
        if not self.settings.github_app_id or not self.settings.github_private_key_path:
            raise RuntimeError('GitHub App ID/private key are required for GitHub App auth')
        private_key = Path(self.settings.github_private_key_path).read_text()
        now = int(time.time())
        payload = {'iat': now - 60, 'exp': now + 540, 'iss': self.settings.github_app_id}
        return jwt.encode(payload, private_key, algorithm='RS256')

    def _installation_token(self) -> str:
        if not self.settings.github_installation_id:
            raise RuntimeError('GITHUB_INSTALLATION_ID is required')
        url = f'{self.API}/app/installations/{self.settings.github_installation_id}/access_tokens'
        headers = {'Authorization': f'Bearer {self._jwt()}', 'Accept': 'application/vnd.github+json'}
        r = self._client.post(url, headers=headers)
        r.raise_for_status()
        return r.json()['token']

    def _headers(self) -> dict[str, str]:
        token = self.settings.github_token or self._installation_token()
        return {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

    def get_pull(self, owner: str, repo: str, pull_number: int) -> dict:
        url = f'{self.API}/repos/{owner}/{repo}/pulls/{pull_number}'
        r = self._client.get(url, headers=self._headers())
        r.raise_for_status()
        return r.json()

    def list_changed_files(self, owner: str, repo: str, pull_number: int) -> list[ChangedFile]:
        files: list[ChangedFile] = []
        page = 1
        while True:
            url = f'{self.API}/repos/{owner}/{repo}/pulls/{pull_number}/files'
            r = self._client.get(url, headers=self._headers(), params={'page': page, 'per_page': 100})
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            files.extend(ChangedFile(filename=f['filename'], status=f['status'], patch=f.get('patch')) for f in batch)
            page += 1
        return files

    def get_file(self, owner: str, repo: str, path: str, ref: str) -> tuple[str | None, str | None]:
        url = f'{self.API}/repos/{owner}/{repo}/contents/{path}'
        r = self._client.get(url, headers=self._headers(), params={'ref': ref})
        if r.status_code == 404:
            return None, None
        r.raise_for_status()
        data = r.json()
        if data.get('type') != 'file':
            return None, data.get('sha')
        content = base64.b64decode(data['content']).decode('utf-8', errors='replace')
        return content, data.get('sha')

    def put_file(self, owner: str, repo: str, path: str, branch: str, content: str, message: str) -> str:
        _, sha = self.get_file(owner, repo, path, branch)
        payload = {
            'message': message,
            'content': base64.b64encode(content.encode()).decode(),
            'branch': branch,
        }
        if sha:
            payload['sha'] = sha
        url = f'{self.API}/repos/{owner}/{repo}/contents/{path}'
        r = self._client.put(url, headers=self._headers(), json=payload)
        r.raise_for_status()
        return r.json()['commit']['sha']

    def create_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> None:
        url = f'{self.API}/repos/{owner}/{repo}/issues/{issue_number}/comments'
        r = self._client.post(url, headers=self._headers(), json={'body': body})
        r.raise_for_status()
