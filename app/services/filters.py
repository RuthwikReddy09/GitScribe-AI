from pathlib import Path

SUPPORTED_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.java', '.rb', '.rs', '.php',
    '.cs', '.cpp', '.c', '.h', '.hpp', '.swift', '.kt', '.scala', '.sh',
    '.yml', '.yaml', '.toml', '.json', '.md', '.rst'
}
SKIP_NAMES = {'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'uv.lock'}
SKIP_DIR_PARTS = {'.git', 'node_modules', 'dist', 'build', '.venv', 'venv', '__pycache__'}


def should_document(path: str) -> bool:
    p = Path(path)
    if p.name in SKIP_NAMES:
        return False
    if any(part in SKIP_DIR_PARTS for part in p.parts):
        return False
    return p.suffix.lower() in SUPPORTED_EXTENSIONS
