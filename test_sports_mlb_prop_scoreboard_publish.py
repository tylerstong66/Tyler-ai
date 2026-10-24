"""Real offline Git races must rebuild the current ledger without force pushes."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import sports_mlb_prop_scoreboard_publish as publisher
from sports_mlb_prop_prospective import freeze_pregame_hit_props, write_exclusive_json, _verify, _seal
from test_sports_mlb_prop_prospective import OfficialReader

NOW = '2026-10-16T04:00:00Z'


def git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo, stderr=subprocess.PIPE)


class CommittedPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root/'remote.git'; self.remote.mkdir()
        git(self.remote, 'init', '--bare', '--initial-branch=main', '-q')
        self.writer = self.root/'writer'
        git(self.root, 'clone', str(self.remote), str(self.writer))
        self.record = freeze_pregame_hit_props(849810, 683734, 'away', reader=OfficialReader())
        self.original = Path(publisher.DEFAULT_ROOT)/'predictions'/'849810_683734.json'
        write_exclusive_json(self.writer/self.original, self.record)
        (self.writer/'README.md').write_text('Original repository\n')
        self.commit_and_push('Original frozen ledger')
        self.client = self.root/'client'
        git(self.root, 'clone', str(self.remote), str(self.client))

    def commit_and_push(self, message):
        git(self.writer, 'add', '-A')
        git(self.writer, '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
            'commit', '-qm', message)
        git(self.writer, 'push', 'origin', 'main')
        return git(self.writer, 'rev-parse', 'HEAD').decode().strip()

    def remote_head(self):
        return git(self.remote, 'rev-parse', 'main').decode().strip()

    def remote_feed(self):
        return json.loads(git(self.remote, 'show', 'main:'+publisher.FEED_RELATIVE))

    def test_concurrent_ledger_commit_retries_and_rebuilds_correct_provenance(self):
        original_push = publisher._push; upstream = []; calls = []
        before = (self.writer/self.original).read_bytes()
        def race(tree):
            calls.append(tree)
            if len(calls) == 1:
                core = _verify(self.record); core['hitter_id'] = 700001
                write_exclusive_json(self.writer/self.original.with_name('849810_700001.json'), _seal(core))
                upstream.append(self.commit_and_push('Another collector advances main'))
            return original_push(tree)
        with patch.object(publisher, '_push', side_effect=race):
            result = publisher.publish_committed_feed(self.client, now=NOW)
        self.assertEqual(result['attempts'], 2)
        feed = self.remote_feed()
        self.assertEqual(feed['benchmark']['frozen_player_game_forecasts'], 2)
        self.assertEqual(feed['source_git_revision'], upstream[0])
        self.assertEqual(git(self.remote, 'show', 'main:'+str(self.original)), before)
        changed = git(self.remote, 'diff-tree', '--no-commit-id', '--name-only', '-r', 'main').decode().splitlines()
        self.assertEqual(changed, [publisher.FEED_RELATIVE])
        self.assertTrue(feed['no_wagers'])
        self.assertEqual(len(git(self.client, 'worktree', 'list', '--porcelain').decode().split('worktree '))-1, 1)

    def test_success_and_unchanged_heartbeat_preserve_dirty_caller_workspace(self):
        (self.client/'README.md').write_text('Unpublished user edit\n')
        git(self.client, 'add', 'README.md')
        before = git(self.client, 'status', '--porcelain')
        head = git(self.client, 'rev-parse', 'HEAD')
        first = publisher.publish_committed_feed(self.client, now=NOW)
        published = self.remote_head()
        second = publisher.publish_committed_feed(self.client, now=NOW)
        self.assertEqual(first['publication_status'], 'PUBLISHED')
        self.assertEqual(second['publication_status'], 'UNCHANGED')
        self.assertEqual(self.remote_head(), published)
        self.assertEqual(git(self.client, 'status', '--porcelain'), before)
        self.assertEqual(git(self.client, 'rev-parse', 'HEAD'), head)
        self.assertEqual((self.client/'README.md').read_text(), 'Unpublished user edit\n')
        self.assertEqual(git(self.remote, 'show', 'main:README.md'), b'Original repository\n')

    def test_exhausted_retries_leave_remote_and_original_forecasts_unchanged(self):
        before = self.remote_head()
        with patch.object(publisher, '_push', return_value=1) as push:
            with self.assertRaisesRegex(RuntimeError, 'bounded retries'):
                publisher.publish_committed_feed(self.client, now=NOW)
        self.assertEqual(push.call_count, 3)
        self.assertEqual(self.remote_head(), before)
        self.assertEqual(git(self.client, 'status', '--porcelain'), b'')
        self.assertEqual(len(git(self.client, 'worktree', 'list', '--porcelain').decode().split('worktree '))-1, 1)

    def test_unexpected_staged_file_is_rejected_before_push(self):
        original = publisher.publish_readonly_shadow_feed
        def extra(**kwargs):
            result = original(**kwargs); tree = kwargs['repository']
            (tree/'unexpected.txt').write_text('must not publish')
            git(tree, 'add', 'unexpected.txt')
            return result
        before = self.remote_head()
        with patch.object(publisher, 'publish_readonly_shadow_feed', side_effect=extra), \
             patch.object(publisher, '_push') as push:
            with self.assertRaisesRegex(ValueError, 'Only the public MLB scoreboard'):
                publisher.publish_committed_feed(self.client, now=NOW)
        push.assert_not_called()
        self.assertEqual(self.remote_head(), before)

    def test_invalid_retry_budget_never_fetches(self):
        with patch.object(publisher, '_git') as invoke:
            for attempts in (False, 0, 4, 1.0):
                with self.assertRaises(ValueError):
                    publisher.publish_committed_feed(self.client, max_attempts=attempts)
        invoke.assert_not_called()


if __name__ == '__main__': unittest.main()
