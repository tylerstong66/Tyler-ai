"""Fixed-repository server timestamps and exact JSON/source archive blobs; no model use."""
import base64
from datetime import datetime
import hashlib
import json
import os
import re

import requests

REPOSITORY = 'tylerstong66/Tyler-ai'
API = 'https://api.github.com/repos/' + REPOSITORY
PATH = re.compile(r'benchmarks/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.json(?:\.gz)?')
SHA = re.compile(r'[0-9a-f]{40}')


def _path(path):
    if (not isinstance(path, str) or not PATH.fullmatch(path)
            or any(segment in ('.', '..') for segment in path.split('/'))):
        raise ValueError('Invalid original benchmark JSON or JSON archive path')


def _sha(sha):
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise ValueError('Immutable Git commit SHA required')


def fetch_json(url):
    if not isinstance(url, str) or not url.startswith(API+'/'):
        raise ValueError('Unapproved publication evidence URL')
    tail = url[len(API)+1:]
    if tail.startswith('contents/'):
        bits = tail[len('contents/'):].split('?ref=')
        if len(bits) != 2: raise ValueError('Immutable original file reference required')
        _path(bits[0]); _sha(bits[1])
    elif not re.fullmatch(r'actions/runs/[1-9][0-9]*', tail):
        raise ValueError('Unapproved publication evidence endpoint')
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Tyler-AI-feature-chronology'}
    token = os.environ.get('GITHUB_TOKEN')
    if token: headers['Authorization'] = 'Bearer '+token
    with requests.get(url, headers=headers, timeout=(10, 30), stream=True, allow_redirects=False) as response:
        response.raise_for_status()
        if response.status_code != 200: raise ValueError('GitHub evidence did not return HTTP 200')
        parts = []; size = 0
        for part in response.iter_content(65536):
            size += len(part)
            if size > 1_000_000: raise ValueError('Oversized GitHub publication evidence')
            parts.append(part)
    value = json.loads(b''.join(parts))
    if not isinstance(value, dict): raise ValueError('GitHub evidence JSON object required')
    return value


def run_observation(run_id, *, now, workflow, events, fetch=fetch_json):
    if type(run_id) is not int or run_id <= 0: raise ValueError('Positive integer GitHub run ID required')
    if now.tzinfo is None: raise ValueError('Aware server evidence clock required')
    run = fetch(API+'/actions/runs/'+str(run_id))
    if (not isinstance(run, dict) or type(run.get('id')) is not int or run['id'] != run_id
            or run.get('repository', {}).get('full_name') != REPOSITORY
            or run.get('head_repository', {}).get('full_name') != REPOSITORY
            or run.get('path') != workflow or run.get('event') not in events):
        raise ValueError('Wrong GitHub repository, workflow, event or run')
    _sha(run.get('head_sha'))
    created = run.get('created_at')
    if not isinstance(created, str): raise ValueError('Missing server creation timestamp')
    observed = datetime.fromisoformat(created.replace('Z', '+00:00'))
    if observed.tzinfo is None or observed > now: raise ValueError('Naive or future GitHub server timestamp')
    return {'run_id': run_id, 'head_sha': run['head_sha'], 'workflow_path': workflow,
            'event': run['event'], 'server_created_at_utc': created}


def verify_blob(path, raw, head_sha, *, fetch=fetch_json):
    _path(path); _sha(head_sha)
    if not isinstance(raw, bytes) or len(raw) > 1_000_000:
        raise ValueError('Bounded original benchmark bytes required')
    blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    item = fetch(API+'/contents/'+path+'?ref='+head_sha)
    if (not isinstance(item, dict) or item.get('type') != 'file' or item.get('path') != path
            or item.get('sha') != blob or type(item.get('size')) is not int or item['size'] != len(raw)
            or item.get('encoding') != 'base64' or not isinstance(item.get('content'), str)):
        raise ValueError('Immutable GitHub commit does not contain expected original benchmark blob')
    if base64.b64decode(''.join(item['content'].split()), validate=True) != raw:
        raise ValueError('Immutable GitHub original benchmark bytes differ')
    return blob
