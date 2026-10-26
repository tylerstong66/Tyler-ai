"""Publish historical research originals without rebasing stale derived coverage.

The capture checkout is read-only to this publisher. A detached worktree based
on fresh origin/main is verified and rebuilt on each bounded push attempt.
No model, result grading, wager, or production action is performed.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile

import sports_expansion_historical_capture as history
import sports_ncaa_historical_owned as fbs
import sports_ncaa_d1_historical_owned as d1
import sports_nba_historical_owned as nba
import sports_historical_content_seal as frozen
import sports_historical_extension_seal as extension
import sports_expansion_observer as observer
from sports_expansion_audit import strict_json_loads, MAX_BLOB_SIZE

ROOT = history.ROOT
COVERAGE = ROOT / 'COVERAGE.latest.json'
ORIGINAL_ROOTS = (ROOT/'sources', fbs.ROOT, d1.ROOT, nba.ROOT)


def git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo, stderr=subprocess.PIPE)


def expected_originals():
    result = set()
    for league, splits in history.dates_by_league().items():
        for split, days in splits.items():
            for day in days:
                for suffix in ('.json.gz', '.receipt.json'):
                    result.add(ROOT/'sources'/league/split/(day+suffix))
    for split in fbs.YEARS:
        for week in fbs.WEEKS:
            for suffix in ('.json.gz', '.receipt.json'):
                result.add(fbs.ROOT/split/(f'week-{week:02d}'+suffix))
    for split, days in d1.DATES.items():
        for day in days:
            for suffix in ('.json.gz', '.receipt.json'):
                result.add(d1.ROOT/split/(day+suffix))
    for split in nba.YEARS:
        for suffix in ('.json.gz', '.receipt.json'):
            result.add(nba.ROOT/split/(nba.season(split)+suffix))
    return result


def safe_file(base, relative):
    path = base / relative
    if any((base / parent).is_symlink() for parent in (relative, *relative.parents)):
        raise ValueError('Historical source symlink prohibited')
    if not path.is_file() or path.stat().st_size > MAX_BLOB_SIZE:
        raise ValueError('Historical source must be a bounded regular file')
    return path


def validate_archive(base, *, now):
    """Verify every retained original pair, immutable frozen indexes and scope."""
    expected = expected_originals()
    for root in ORIGINAL_ROOTS:
        folder = base / root
        if folder.exists():
            for item in folder.rglob('*'):
                if item.is_symlink():
                    raise ValueError('Historical source symlink prohibited')
                if item.is_file() and item.relative_to(base) not in expected:
                    raise ValueError('Unexpected historical original archive path')
    frozen.verify(base)
    extension.verify(base)
    counts = {}
    for league, splits in history.dates_by_league().items():
        retained = 0
        total = 0
        for split, days in splits.items():
            for day in days:
                total += 1
                retained += bool(history.verify_existing(base, league, split, day, as_of=now))
        counts[league] = (retained, total)
    for split in fbs.YEARS:
        for week in fbs.WEEKS:
            fbs.verify(base, split, week, now=now)
    for split, days in d1.DATES.items():
        for day in days:
            d1.verify(base, split, day, now=now)
    for split in nba.YEARS:
        nba.verify(base, split, now=now)
    return counts


def candidates(repo, *, include_fbs, include_d1, include_nba):
    """Only newly created original archive components may be copied."""
    expected = expected_originals()
    changed = set()
    for args in (('diff', '--name-only', '-z'), ('diff', '--cached', '--name-only', '-z')):
        changed.update(Path(x.decode()) for x in git(repo, *args).split(b'\0') if x)
    if any(path in expected for path in changed):
        raise ValueError('Previously tracked historical original modified or deleted')
    untracked = {Path(x.decode()) for x in git(repo, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if x}
    incoming = set()
    for path in untracked:
        if not any(path.is_relative_to(root) for root in ORIGINAL_ROOTS):
            continue
        if path not in expected:
            raise ValueError('Unplanned historical original cannot be published')
        if path.is_relative_to(fbs.ROOT) and not include_fbs:
            raise ValueError('Unsuccessful FBS acquisition has unpublished originals')
        if path.is_relative_to(d1.ROOT) and not include_d1:
            raise ValueError('Unsuccessful D1 acquisition has unpublished originals')
        if path.is_relative_to(nba.ROOT) and not include_nba:
            raise ValueError('Unsuccessful NBA acquisition has unpublished originals')
        safe_file(repo, path)
        incoming.add(path)
    for path in incoming:
        companion = (path.with_name(path.name[:-13]+'.json.gz')
                     if path.name.endswith('.receipt.json')
                     else path.with_name(path.name[:-8]+'.receipt.json'))
        if companion not in incoming and not (repo/companion).is_file():
            raise ValueError('Unpaired historical original candidate')
    return sorted(incoming)


def rebuild_coverage(base, counts, now, *, changed):
    path = safe_file(base, COVERAGE)
    previous = strict_json_loads(path.read_bytes())
    if (previous.get('schema') != 'college-nba-time-split-historical-provider-source-v1'
            or previous.get('source_provider') != 'ESPN_MEDIA_DATA_NOT_INDEPENDENT_OFFICIAL'
            or previous.get('NO_BET') is not True
            or type(previous.get('actual_wagers')) is not int or previous['actual_wagers'] != 0
            or type(previous.get('historical_backfilled_forecasts')) is not int
            or previous['historical_backfilled_forecasts'] != 0
            or any(previous.get(k) is not False for k in
                   ('training_allowed', 'live_forecasts_allowed', 'promotion_allowed'))
            or set(previous.get('sport_day_status', {})) != set(history.ORDER)):
        raise ValueError('Historical derived coverage research guard changed')
    result = dict(previous)
    status = {}
    for league in history.ORDER:
        retained, total = counts[league]
        status[league] = {'expected_source_dates': total,
                          'archived_source_dates': retained,
                          'remaining_source_dates': total-retained,
                          'all_declared_dates_retrieved': retained == total,
                          'official_result_completeness_verified': False}
    result['sport_day_status'] = status
    if changed or status != previous['sport_day_status']:
        result['as_of_utc'] = now.astimezone(timezone.utc).isoformat()
        path.write_bytes(observer.canonical(result))
    return result


def publish(repo='.', *, include_fbs=False, include_d1=False, include_nba=False,
            max_attempts=3, now=None, push=None):
    if type(max_attempts) is not int or not 1 <= max_attempts <= 3:
        raise ValueError('One to three publication attempts required')
    repo = Path(repo).resolve()
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware publication time required')
    incoming = candidates(repo, include_fbs=include_fbs, include_d1=include_d1,
                          include_nba=include_nba)
    validate_archive(repo, now=now)
    for attempt in range(1, max_attempts+1):
        git(repo, 'fetch', '--no-tags', 'origin', 'main')
        base = git(repo, 'rev-parse', 'FETCH_HEAD').decode().strip()
        with tempfile.TemporaryDirectory(prefix='tyler-history-publish-') as temp:
            tree = Path(temp)/'checkout'
            git(repo, 'worktree', 'add', '--detach', str(tree), base)
            try:
                copied = 0
                for relative in incoming:
                    source = safe_file(repo, relative)
                    dest = tree/relative
                    if dest.exists() or dest.is_symlink():
                        if safe_file(tree, relative).read_bytes() != source.read_bytes():
                            raise ValueError('Conflicting historical original on current main')
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        if any((tree/p).is_symlink() for p in relative.parents):
                            raise ValueError('Historical source ancestor symlink')
                        with dest.open('xb') as out:
                            out.write(source.read_bytes())
                        copied += 1
                counts = validate_archive(tree, now=now)
                rebuild_coverage(tree, counts, now, changed=bool(copied))
                git(tree, 'add', '--', str(COVERAGE), *(str(x) for x in incoming))
                staged = {Path(x.decode()) for x in git(tree, 'diff', '--cached', '--name-only', '-z').split(b'\0') if x}
                if not staged:
                    return {'status':'UNCHANGED', 'attempts':attempt, 'source_revision':base, 'NO_BET':True}
                if not staged.issubset(set(incoming)|{COVERAGE}):
                    raise ValueError('Unexpected historical publication staging')
                git(tree, '-c', 'user.name=github-actions[bot]', '-c',
                    'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                    'commit', '-m', 'Publish verified append-only historical research sources [no bets]')
                commit = git(tree, 'rev-parse', 'HEAD').decode().strip()
                result = (push or (lambda cwd: subprocess.run(
                    ['git','push','origin','HEAD:refs/heads/main'], cwd=cwd,
                    capture_output=True, text=True)))(tree)
                if result.returncode == 0:
                    return {'status':'PUBLISHED','attempts':attempt,'source_revision':base,
                            'commit':commit,'original_files_added':copied,'NO_BET':True}
                message = result.stderr.lower()
                if not any(term in message for term in ('fetch first','non-fast-forward','stale info')):
                    raise RuntimeError('Historical publication push failed for non-race reason')
            finally:
                git(repo, 'worktree', 'remove', '--force', str(tree))
    raise RuntimeError('Historical publication race exhausted bounded retries; no force push')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.')
    parser.add_argument('--include-fbs', action='store_true')
    parser.add_argument('--include-d1', action='store_true')
    parser.add_argument('--include-nba', action='store_true')
    args = parser.parse_args()
    print(json.dumps(publish(args.repo, include_fbs=args.include_fbs,
                             include_d1=args.include_d1, include_nba=args.include_nba), sort_keys=True))
