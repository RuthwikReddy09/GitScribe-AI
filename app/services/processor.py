import logging

from app.core.config import Settings
from app.models import ProcessPRResponse
from app.services.filters import should_document
from app.services.github import GitHubClient
from app.services.llm import DocumentationGenerator

logger = logging.getLogger(__name__)


class PRProcessor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.github = GitHubClient(settings)
        self.generator = DocumentationGenerator(settings)

    def process(self, owner: str, repo: str, pull_number: int) -> ProcessPRResponse:
        pull = self.github.get_pull(owner, repo, pull_number)
        branch = pull['head']['ref']
        repo_full_name = f'{owner}/{repo}'

        changed = self.github.list_changed_files(owner, repo, pull_number)
        selected = [f for f in changed if f.status != 'removed' and should_document(f.filename)]
        selected = selected[: self.settings.max_files_per_pr]

        changed_contents: dict[str, str] = {}
        for f in selected:
            content, _ = self.github.get_file(owner, repo, f.filename, branch)
            if content and len(content.encode()) <= self.settings.max_file_bytes:
                changed_contents[f.filename] = content

        if not changed_contents:
            return ProcessPRResponse(status='skipped', updated_files=[], message='No supported changed files found.')

        existing_docs: dict[str, str | None] = {}
        for doc in self.settings.doc_target_list:
            content, _ = self.github.get_file(owner, repo, doc, branch)
            existing_docs[doc] = content

        updates = self.generator.generate(repo_full_name, changed_contents, existing_docs)
        if not updates:
            return ProcessPRResponse(status='skipped', updated_files=[], message='LLM produced no documentation updates.')

        commit_sha = None
        updated_files: list[str] = []
        for path, content in updates.items():
            if content.strip():
                commit_sha = self.github.put_file(
                    owner, repo, path, branch, content,
                    'docs: update documentation with GitScribe'
                )
                updated_files.append(path)

        if updated_files:
            self.github.create_issue_comment(
                owner, repo, pull_number,
                'GitScribe updated documentation for this PR:\n\n' + '\n'.join(f'- `{p}`' for p in updated_files),
            )

        return ProcessPRResponse(status='success', updated_files=updated_files, commit_sha=commit_sha, message='Documentation updated.')
