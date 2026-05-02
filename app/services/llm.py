from openai import OpenAI

from app.core.config import Settings


class DocumentationGenerator:
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise RuntimeError('OPENAI_API_KEY is required')
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(self, repo_full_name: str, changed_files: dict[str, str], existing_docs: dict[str, str | None]) -> dict[str, str]:
        file_blocks = []
        for path, content in changed_files.items():
            file_blocks.append(f'FILE: {path}\n```\n{content[:12000]}\n```')

        doc_blocks = []
        for path, content in existing_docs.items():
            doc_blocks.append(f'DOC: {path}\n```markdown\n{content or ""}\n```')

        prompt = f'''
You are GitScribe, a senior software documentation agent.

Repository: {repo_full_name}

Update the documentation using the changed source files. Preserve accurate existing content. Do not invent APIs. If a target doc is empty, create useful concise documentation.

Return a strict JSON object where keys are documentation file paths and values are complete Markdown file contents.
Only include these target docs: {list(existing_docs.keys())}

Changed files:
{chr(10).join(file_blocks)}

Existing documentation:
{chr(10).join(doc_blocks)}
'''
        resp = self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {'role': 'system', 'content': 'Return only valid JSON. No Markdown fences.'},
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.2,
            response_format={'type': 'json_object'},
        )
        import json
        data = json.loads(resp.choices[0].message.content or '{}')
        return {k: v for k, v in data.items() if k in existing_docs and isinstance(v, str)}
