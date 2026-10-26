"""Create a source-only Replit import ZIP using an explicit file allowlist."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    '.replit', '.gitignore', 'AGENTS.md', 'README.md', 'replit.md', 'app.py',
    'requirements.txt', 'requirements-api.txt',
    'frontend/package.json', 'frontend/package-lock.json',
    'frontend/vite.config.js', 'frontend/index.html',
    'data/knowledge.json', 'data/demo_student.json',
    'data/career_world_details.json',
    'careerquest/assets/fonts/NotoSans-Regular.ttf',
    'careerquest/assets/fonts/NotoSans-Bold.ttf',
    'careerquest/assets/fonts/LICENSE', 'careerquest/assets/fonts/SOURCES.json',
    'docs/REACT_REPLIT_SETUP.md', 'docs/REPLIT_VERIFICATION.md', 'docs/SPEC_INCREMENT_1.md',
    'docs/reference/UI_SPECIFICATION.txt',
    'scripts/replit-setup.sh', 'scripts/replit-run.sh',
    'scripts/replit-production.sh','scripts/account_admin.py','scripts/verify_postgres.py',
    'docs/CLOUD_DEPLOYMENT.md',
    'docs/REPLIT_IMPORT_VERIFICATION.md',
    'scripts/package_replit.py', 'scripts/smoke_core.py',
)
SOURCE_TREES = {
    'careerquest': {'.py'}, 'tests': {'.py'},
    'frontend/src': {'.js', '.jsx', '.css'}, 'frontend/tests': {'.js'},
}


def source_files(root=ROOT):
    paths = set(FILES)
    for directory, suffixes in SOURCE_TREES.items():
        for path in (root / directory).rglob('*'):
            if path.suffix in suffixes and not any(
                part.startswith('.') or part == '__pycache__'
                for part in path.relative_to(root).parts
            ):
                paths.add(path.relative_to(root).as_posix())
    for name in sorted(paths):
        path = root / name
        if path.is_symlink() or path.resolve() != root.resolve() / name:
            raise ValueError(f'Refusing linked source: {name}')
        if not path.is_file():
            raise FileNotFoundError(name)
        yield path, name


def package(output):
    entries = list(source_files())
    if output.resolve() in {path.resolve() for path, _ in entries}:
        raise ValueError('Output must not overwrite a source file')
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for path, name in entries:
            archive.write(path, name)
    print(f'Created {output}: {len(entries)} source files; no local secrets or database files included.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'exports' / 'careerquest-replit.zip')
    package(parser.parse_args().output)
