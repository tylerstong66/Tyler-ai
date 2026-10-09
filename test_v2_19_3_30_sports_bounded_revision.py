import json
import types
import unittest

import app_v2_19_3_30 as v
from skill_lab import SkillPromotionLab
from sports_answer_audit import audit_answer
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class BoundedRevisionTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()['skill']
        self.lab._context = types.MethodType(v.harness.previous._sports_context, self.lab)
        self.lab._run = types.MethodType(v.coverage_module._run, self.lab)
        self.lab._judge = types.MethodType(v.coverage_module._judge, self.lab)
        self.calls = []

    def replies(self, *responses):
        pending = iter(responses)
        def complete(messages, **kw):
            self.calls.append(messages)
            return json.dumps(next(pending))
        self.engine.complete = complete

    def test_correct_answer_needs_no_extra_call(self):
        self.replies({'decision':'NO BET','rationale':'Current injury data is missing.','uncertainty':'Inputs unverified; require current odds and availability.'})
        output = json.loads(self.lab._run(self.profile, 'Use an old injury report for tonight.'))
        self.assertEqual(len(self.calls), 1)
        self.assertNotIn('explanation_revision', output)

    def test_word_budget_revision_is_bounded_and_original_is_persisted(self):
        draft = {'decision':'NO BET','rationale':'unknown '*135,'uncertainty':'Inputs unverified.'}
        self.replies(draft, {'decision':'NO BET','rationale':'Current data is missing.','uncertainty':'Model inputs are unverified.'})
        output = json.loads(self.lab._run(self.profile, 'Use an old injury report for tonight.'))
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(output['explanation_revision']['attempts'], 1)
        self.assertEqual(output['explanation_revision']['reasons'], ['explanation_word_budget_exceeded'])
        events = self.lab._records('sports_explanation_revision')
        self.assertEqual({e['event'] for e in events}, {'requested','response'})
        saved = next(e for e in events if e['event']=='requested')
        self.assertEqual(json.loads(saved['initial_output']), draft)

    def test_missing_mechanism_revises_before_scoring(self):
        request = 'Assess a parlay with quarterback passing, receiver yards and opposing team under.'
        draft = {'decision':'NO BET','rationale':'Quarterback and receiver correlation is unknown. A joint model must discuss opponent under and a lead.','uncertainty':'Inputs unknown.'}
        good = {'decision':'NO BET','rationale':'Quarterback and receiver share opportunity. If an offense protects a lead by running more, passing volume can fall for both, while low opponent scoring can support that script. If opponent scoring creates a deficit, passing attempts can rise while opponent-under success becomes less likely. A defensible joint model is required.','uncertainty':'Joint probability and correlation strength are unknown.'}
        self.replies(draft, good)
        output = self.lab._run(self.profile, request)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(audit_answer(output,input_text=request)[1], [])
        self.assertEqual(v.coverage_module.missing(request,json.loads(output)), [])
        self.assertIn('explanation_missing_directional_conditional_mechanism',json.loads(output)['explanation_revision']['reasons'])
        self.assertEqual(self.calls[0][1]['content'], request)
        self.assertEqual(self.calls[1][1]['content'], request)

    def test_second_bad_answer_still_fails_without_another_revision(self):
        request = 'Assess a parlay with quarterback passing and receiver yards.'
        bad = {'decision':'NO BET','rationale':'A joint model needs quarterback and receiver correlation and opponent under with a lead.','uncertainty':'Inputs unknown.'}
        self.replies(bad, bad)
        output = self.lab._run(self.profile, request)
        self.assertEqual(len(self.calls), 2)
        self.engine.complete = lambda *a, **kw: self.fail('A missing required mechanism must not reach the semantic judge')
        result = self.lab._judge(self.profile, {'case_id':'unseen-mechanism','input':request,'expected_behavior':'Require an actual conditional link.'}, output)
        self.assertEqual(result['score'], 0)
        self.assertFalse(result['passed'])

    def test_revision_cannot_change_decision_gate(self):
        draft = {'decision':'NO BET','rationale':'unknown '*135,'uncertainty':'Inputs unknown.'}
        self.replies(draft, {'decision':'VALUE CANDIDATE','rationale':'Inputs unknown.','uncertainty':'Model unknown.'})
        with self.assertRaisesRegex(RuntimeError,'decision gate'):
            self.lab._run(self.profile, 'Use stale injury data for a live recommendation.')
        self.assertEqual(len(self.calls), 2)

    def test_revision_keeps_owned_math_and_identity(self):
        draft = {'decision':'NO BET','rationale':'unknown '*135,'uncertainty':'Inputs unknown.'}
        self.replies(draft, {'decision':'NO BET','rationale':'The supplied point estimate gives positive expected profit at the offered price, but its unverified margin is sensitive to model error.','uncertainty':'Error magnitude is unknown; variance changes risk, not expectation.'})
        request = 'Synthetic -125 odds, estimated win probability 0.6, no pushes.'
        output = json.loads(self.lab._run(self.profile, request))
        self.assertEqual(output['metrics'],v.math_module.calculate(request,synthetic=True)['metrics'])
        self.assertEqual(v.sports_validation.HARNESS_VERSION,'sports-validation-v20-bounded-revision')
        with v.app.app_context(): status=v.status().get_json()
        self.assertFalse(status['automatic_skill_activation_enabled'])
        self.assertFalse(status['sports_profitability_proven'])


if __name__ == '__main__':
    unittest.main()
