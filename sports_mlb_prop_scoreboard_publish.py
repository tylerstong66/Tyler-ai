"""Publish only a rebuilt MLB scoreboard from current committed main; no wagers."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from sports_mlb_prop_scoreboard_feed import FEED_RELATIVE, publish_readonly_shadow_feed
from sports_mlb_prop_shadow_scoreboard import DEFAULT_ROOT


def _git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo, stderr=subprocess.PIPE)


def _push(tree):
    return subprocess.run(['git', 'push', 'origin', 'HEAD:refs/heads/main'], cwd=tree,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode


def publish_committed_feed(repository='.', *, now=None, max_attempts=3):
    """Refetch and rebuild after a rejected push; never rebase a stale snapshot.

    Each attempt uses its own detached worktree, leaving the caller's files,
    index and unpublished work intact. Only the derived scoreboard may enter
    the new commit. A normal push rejects concurrent main updates atomically.
    """
    if type(max_attempts) is not int or not 1 <= max_attempts <= 3:
        raise ValueError('One to three scoreboard publication attempts required')
    repository = Path(repository).resolve()
    for attempt in range(1, max_attempts + 1):
        _git(repository, 'fetch', '--no-tags', 'origin', 'main')
        base = _git(repository, 'rev-parse', 'FETCH_HEAD').decode().strip()
        with tempfile.TemporaryDirectory(prefix='tyler-mlb-scoreboard-') as temp:
            tree = Path(temp)/'checkout'
            _git(repository, 'worktree', 'add', '--detach', str(tree), base)
            try:
                result = publish_readonly_shadow_feed(root=tree/DEFAULT_ROOT,
                                                       repository=tree, now=now)
                _git(tree, 'add', '--', FEED_RELATIVE)
                changed = _git(tree, 'diff', '--cached', '--name-status', '-z')
                if not changed:
                    return {**result, 'publication_status': 'UNCHANGED',
                            'attempts': attempt, 'source_git_revision': base}
                allowed = FEED_RELATIVE.encode()
                if changed not in (b'A\0'+allowed+b'\0', b'M\0'+allowed+b'\0'):
                    raise ValueError('Only the public MLB scoreboard may be committed')
                _git(tree, '-c', 'user.name=github-actions[bot]', '-c',
                     'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                     'commit', '-m', 'Refresh read-only MLB hitter research scoreboard [no bets]')
                commit = _git(tree, 'rev-parse', 'HEAD').decode().strip()
                if _push(tree) == 0:
                    return {**result, 'publication_status': 'PUBLISHED',
                            'attempts': attempt, 'source_git_revision': base,
                            'publication_commit': commit}
            finally:
                _git(repository, 'worktree', 'remove', '--force', str(tree))
    raise RuntimeError('MLB scoreboard publication rejected after bounded retries; no force push')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.')
    args = parser.parse_args()
    print('PUBLIC_SCOREBOARD_ONLY_NO_WAGERS='+json.dumps(
        publish_committed_feed(args.repo), sort_keys=True, allow_nan=False))
