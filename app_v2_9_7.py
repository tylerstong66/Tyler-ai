import ast
import os
import re
from pathlib import Path

import app_v2_9_6 as v296


# v2.9.7 grounds the Tyler AI Developer skill in the source files that are
# actually deployed with the running application. This prevents architecture
# recommendations from being based only on training examples or remembered
# descriptions of the project.
v296.base.VERSION = '2.9.7-code-grounded-developer-skill'
v296.base.VERSION_SHORT = 'v2.9.7'

SOURCE_ROOT = Path(__file__).resolve().parent
MAX_GROUNDING_CHARS = int(os.environ.get('TYLER_DEVELOPER_GROUNDING_CHARS', '15000'))
MAX_SNIPPET_CHARS = int(os.environ.get('TYLER_DEVELOPER_SNIPPET_CHARS', '1800'))
MAX_SOURCE_FILE_BYTES = int(os.environ.get('TYLER_DEVELOPER_MAX_SOURCE_BYTES', '300000'))

_ENGINE = v296.ENGINE
_ORIGINAL_RUN_SKILL = _ENGINE.run_skill

IMPORTANT_FUNCTION_TERMS = {
    'task', 'step', 'plan', 'replan', 'resume', 'persist', 'execute', 'action',
    'memory', 'email', 'n8n', 'research', 'tool', 'feedback', 'decision',
    'groq', 'supabase', 'tavily', 'status', 'project', 'skill', 'reliability',
}

REQUEST_STOPWORDS = {
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'current',
    'review', 'identify', 'highest', 'value', 'upgrade', 'build', 'next',
    'preserve', 'working', 'features', 'explain', 'why', 'should', 'come',
    'tyler', 'architecture',
}


def _norm(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _developer_skill(skill):
    return str((skill or {}).get('skill_id') or '').strip().lower() == 'tyler-ai-developer'


def _safe_source_files():
    """Return relevant text source files present in the deployed repository."""
    names = []
    try:
        for path in SOURCE_ROOT.iterdir():
            if not path.is_file():
                continue
            name = path.name
            if (
                (name.startswith('app') and name.endswith('.py'))
                or name == 'skill_engine.py'
                or name == 'requirements.txt'
                or (name.startswith('test_') and name.endswith('.py'))
            ):
                names.append(name)
    except Exception:
        return []
    return sorted(set(names))


def _read_source(name):
    path = SOURCE_ROOT / name
    try:
        if not path.is_file() or path.stat().st_size > MAX_SOURCE_FILE_BYTES:
            return ''
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return ''


def _redact_source(text):
    """Defensively remove obvious hard-coded secret literals from snippets."""
    text = str(text or '')
    patterns = [
        r"(?i)(api[_-]?key\s*=\s*)['\"][^'\"]+['\"]",
        r"(?i)(webhook[_-]?key\s*=\s*)['\"][^'\"]+['\"]",
        r"(?i)(secret\s*=\s*)['\"][^'\"]+['\"]",
        r"(?i)(password\s*=\s*)['\"][^'\"]+['\"]",
        r"(?i)(token\s*=\s*)['\"][^'\"]+['\"]",
    ]
    for pattern in patterns:
        text = re.sub(pattern, r"\1'<redacted>'", text)
    return text


def _python_index(name, text):
    """Index top-level functions/classes/constants without executing source."""
    if not name.endswith('.py') or not text:
        return {'functions': [], 'classes': [], 'constants': []}
    try:
        tree = ast.parse(text, filename=name)
    except Exception:
        return {'functions': [], 'classes': [], 'constants': []}

    functions = []
    classes = []
    constants = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            else:
                targets = [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append(target.id)
    return {
        'functions': functions,
        'classes': classes,
        'constants': constants,
    }


def _function_sources(name, text):
    """Return top-level function source blocks keyed by function name."""
    if not name.endswith('.py') or not text:
        return {}
    try:
        tree = ast.parse(text, filename=name)
        lines = text.splitlines()
    except Exception:
        return {}

    output = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        start = max(0, int(getattr(node, 'lineno', 1)) - 1)
        end = int(getattr(node, 'end_lineno', start + 1))
        block = '\n'.join(lines[start:end])
        output[node.name] = _redact_source(block)[:MAX_SNIPPET_CHARS]
    return output


def _request_terms(request_text):
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', str(request_text or '').lower())
    return {
        word
        for word in words
        if word not in REQUEST_STOPWORDS and len(word) >= 4
    }


def _function_score(function_name, request_terms):
    lower = str(function_name or '').lower()
    score = 0
    for term in request_terms:
        if term in lower:
            score += 5
    for term in IMPORTANT_FUNCTION_TERMS:
        if term in lower:
            score += 2
    if lower in {
        'groq', 'send_email_via_n8n', 'core_project_text', 'project_context',
        'save_memory', 'get_memories', 'status', 'handle_message',
    }:
        score += 4
    return score


def _developer_grounding(request_text, max_chars=None):
    """Build a verified snapshot from the code deployed beside this module."""
    max_chars = int(max_chars or MAX_GROUNDING_CHARS)
    files = _safe_source_files()
    request_terms = _request_terms(request_text)

    lines = [
        'VERIFIED LOCAL SOURCE SNAPSHOT',
        f'Runtime version: {v296.base.VERSION_SHORT}',
        'Source basis: files deployed with the running Render application.',
        'This snapshot is authoritative when it conflicts with training examples or remembered architecture descriptions.',
        'Deployed source files: ' + (', '.join(files) if files else 'unavailable'),
    ]

    indexes = {}
    function_candidates = []
    for name in files:
        if not (name.endswith('.py') or name == 'requirements.txt'):
            continue
        text = _read_source(name)
        if not text:
            continue

        if name == 'requirements.txt':
            reqs = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
            if reqs:
                lines.append('Runtime requirements: ' + ', '.join(reqs[:30]))
            continue

        index = _python_index(name, text)
        indexes[name] = index
        if name in {'app.py', 'skill_engine.py'} or name.startswith('app_v2_9'):
            if index['constants']:
                lines.append(f"{name} constants: {', '.join(index['constants'][:60])}")
            if index['functions']:
                lines.append(f"{name} functions: {', '.join(index['functions'][:140])}")
            if index['classes']:
                lines.append(f"{name} classes: {', '.join(index['classes'][:40])}")

        for fn_name, block in _function_sources(name, text).items():
            score = _function_score(fn_name, request_terms)
            if score > 0:
                function_candidates.append((score, name, fn_name, block))

    # Highest-scoring real functions are included as source, not summaries.
    function_candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    used = set()
    selected = []
    for score, name, fn_name, block in function_candidates:
        key = (name, fn_name)
        if key in used:
            continue
        used.add(key)
        selected.append((score, name, fn_name, block))
        if len(selected) >= 14:
            break

    if selected:
        lines.append('SELECTED VERIFIED SOURCE SNIPPETS:')
        for _, name, fn_name, block in selected:
            lines.append(f'--- {name} :: {fn_name} ---')
            lines.append(block)

    snapshot = '\n'.join(lines)
    return snapshot[:max_chars]


def _run_code_grounded_skill(skill_name, request_text):
    skill = _ENGINE.get_skill(skill_name)
    if not skill:
        raise ValueError(f'Skill {skill_name!r} was not found.')

    if not _developer_skill(skill):
        return _ORIGINAL_RUN_SKILL(skill_name, request_text)

    context = _ENGINE.build_context(skill['skill_id'])
    grounding = _developer_grounding(request_text)
    messages = [
        {
            'role': 'system',
            'content': (
                'You are Tyler AI running the Tyler AI Developer skill in TEXT-ONLY mode. '
                'A verified snapshot of the source files deployed with this running application is provided below. '
                'Use that source snapshot before training examples when determining what is currently implemented. '
                'Do not open with a disclaimer that read_memory, research_web, reason, GitHub, or other tools are unavailable. '
                'You are not being asked to execute those tools; you are being given verified local code context directly. '
                'Do not claim that you fetched GitHub or live documentation unless that actually occurred. '
                'Do not invent tables, environment variables, code paths, latency targets, coverage targets, APIs, or components. '
                'Do not propose a feature as new if the verified snapshot shows it is already implemented. '
                'For side-effect actions such as email, never recommend automatic retry when the external outcome could be unknown. '
                'When source evidence is insufficient, explicitly identify the detail that still requires verification instead of guessing. '
                'Any proposed change must be described as a proposal, not as already applied or deployed.\n\n'
                + context
                + '\n\n'
                + grounding
            ),
        },
        {'role': 'user', 'content': _norm(request_text)},
    ]
    return _ENGINE.complete(
        messages,
        tokens=2200,
        temperature=0.1,
        json_mode=False,
    )


_ENGINE.run_skill = _run_code_grounded_skill


app = v296.app
base = v296.base
ENGINE = v296.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
