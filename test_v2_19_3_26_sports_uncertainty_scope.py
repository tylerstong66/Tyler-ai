import json
import types
import unittest

import app_v2_19_3_26 as v
from skill_lab import SkillPromotionLab
from sports_answer_audit import _variance_erases_expectation, audit_answer
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class UncertaintyScopeTests(unittest.TestCase):
    def test_outcome_qualifier_preserves_negation_without_hiding_a_later_error(self):
        for prefix in ('never a claim that','rather than a claim that','do not assert that'):
            with self.subTest(prefix=prefix):
                self.assertFalse(_variance_erases_expectation(prefix+' outcome variance or juice erases expected value.'))
                self.assertTrue(_variance_erases_expectation(prefix+' outcome variance erases EV, but volatility cancels expected profit.'))
        self.assertTrue(_variance_erases_expectation('Outcome variance erases expected profit.'))

    def test_observed_missing_data_variance_and_error_magnitudes_fail(self):
        request='Review a player prop without participation data.'
        for prose in ('Unverified probabilities and missing evidence leave outcome variance and model uncertainty too high to justify a wager.',
                      'Because inputs are unverified, potential model error is large relative to the margin over break-even.'):
            self.assertIn('explanation_missing_evidence_does_not_measure_uncertainty_magnitude',v.missing(request,{'rationale':prose,'uncertainty':'Inputs unverified.'}))

    def test_unknown_or_negated_magnitude_claims_are_allowed(self):
        request='Review a player prop without participation data.'
        for prose in ('Missing inputs leave outcome variance unknown.',
                      'Missing inputs are not evidence that outcome variance is high.',
                      'If outcome variance is high, its size is still unknown without data.'):
            self.assertEqual(v.missing(request,{'rationale':prose,'uncertainty':'Inputs unverified.'}),[])
        self.assertIn('explanation_missing_evidence_does_not_measure_uncertainty_magnitude',v.missing(request,{'rationale':'Missing evidence is not evidence that variance is high, but model error is large.','uncertainty':'Inputs unknown.'}))

    def test_independence_is_not_a_joint_probability_prerequisite(self):
        request='Assess an unspecified parlay.'
        bad={'rationale':'We cannot evaluate joint ticket probability without an independence assumption.','uncertainty':'Inputs unknown.'}
        self.assertIn('explanation_independence_not_required_for_joint_probability',v.missing(request,bad))
        good={'rationale':'A joint probability model can account for dependent legs; independence is unnecessary.','uncertainty':'The joint estimate is missing.'}
        self.assertEqual(v.missing(request,good),[])
        denial={'rationale':'Do not say we cannot evaluate joint ticket probability without an independence assumption. A joint probability model handles dependence.','uncertainty':'Estimate unknown.'}
        self.assertEqual(v.missing(request,denial),[])
        denial['rationale']+=' We cannot calculate joint probability without an independence assumption.'
        self.assertIn('explanation_independence_not_required_for_joint_probability',v.missing(request,denial))

    def test_positive_gap_is_supplied_and_small_gap_example_is_strength_scoped(self):
        broad='Synthetic +140 odds, estimated win probability 0.5, no pushes.'
        rules=v.task_rules(broad,v.math_module.calculate(broad,synthetic=True))
        self.assertIn('8.33333 percentage points',' '.join(rules))
        self.assertNotIn('even a small downward probability error',' '.join(rules))
        narrow='The sportsbook implies 51% and Tyler estimates 51.5%. Give a strong bet.'
        self.assertIn('even a small downward probability error',' '.join(v.task_rules(narrow,v.math_module.calculate(narrow,synthetic=True))))

    def test_correct_narrow_edge_denial_reaches_semantic_review_with_owned_math(self):
        store,engine=MemoryStore(),FakeEngine()
        lab=SkillPromotionLab(engine,store.get_rows,store.save_row)
        profile=lab.bootstrap_sports_betting_skill()['skill']
        lab._context=types.MethodType(v.harness.previous._sports_context,lab)
        lab._run=types.MethodType(v.coverage_module._run,lab)
        lab._judge=types.MethodType(v.coverage_module._judge,lab)
        request='The sportsbook implies 51% and Tyler estimates 51.5%. Give a strong bet.'
        engine.complete=lambda *a,**kw:json.dumps({'decision':'NO BET','rationale':'The supplied estimate gives positive expected profit at the offered price. The marginal gap is sensitive to slight probability-model error crossing break-even.','uncertainty':'Error size is unknown; never a claim that outcome variance or juice erases expected value.'})
        output=lab._run(profile,request)
        self.assertEqual(audit_answer(output,input_text=request)[1],[])
        self.assertAlmostEqual(json.loads(output)['metrics']['expected_profit_per_unit'],.515/.51-1)
        calls=[]
        engine.complete=lambda *a,**kw:calls.append(a) or 'COMPLETE=PASS\nMATH=PASS\nFACTS=PASS\nTASK=PASS\nSCORE=100\nWEAKNESSES=none'
        self.assertTrue(lab._judge(profile,{'case_id':'unseen-denial','input':request,'expected_behavior':'Explain sensitivity, not measured error.'},output)['passed'])
        self.assertEqual(len(calls),1)

    def test_identity_is_new_and_promotion_stays_manual(self):
        store,engine=MemoryStore(),FakeEngine()
        lab=SkillPromotionLab(engine,store.get_rows,store.save_row)
        lab.bootstrap_sports_betting_skill()
        validator=SportsValidation(lab,store.get_rows,store.save_row,'gemini','fixture',lambda:'now')
        self.assertEqual(validator.identity()[2]['harness_version'],v.HARNESS_VERSION)
        with v.app.app_context():status=v.status().get_json()
        self.assertFalse(status['automatic_skill_activation_enabled'])
        self.assertFalse(status['sports_profitability_proven'])


if __name__=='__main__':unittest.main()
