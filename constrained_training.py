"""Constrained champion mutation for Tyler AI v2.19.2.

Each candidate may change exactly one existing instruction or success criterion from
the verified champion. The parent profile remains immutable, tool permissions may not
change, and an auditable mutation diff is persisted before any benchmark is run.
"""

from difflib import SequenceMatcher

from champion_training import ChampionSkillTrainer
from skill_lab import _as_list, _hash, _norm

SKILL_MUTATION_DIFF_CATEGORY = "skill_mutation_diff"
SKILL_CONSTRAINED_CATEGORIES = {SKILL_MUTATION_DIFF_CATEGORY}


class ConstrainedChampionTrainer(ChampionSkillTrainer):
    """Champion trainer with deterministic single-edit drift protection."""

    def __init__(
        self,
        lab,
        get_rows,
        save_row,
        now_fn=None,
        max_rounds=6,
        consistency_tolerance=10.0,
        max_replacement_chars=280,
        min_line_similarity=0.15,
    ):
        super().__init__(
            lab,
            get_rows,
            save_row,
            now_fn=now_fn,
            max_rounds=max_rounds,
            consistency_tolerance=consistency_tolerance,
        )
        self.max_replacement_chars = max(80, min(int(max_replacement_chars), 600))
        self.min_line_similarity = max(0.0, min(float(min_line_similarity), 1.0))

    def mutation_target(self, active, parent):
        """Pick the weakest benchmark case for the exact immutable parent profile."""
        if parent.get("candidate_id"):
            runs = self._valid_candidate_runs(active, parent)
            run = runs[0] if runs else None
        else:
            run = self.lab._valid_eval(active, "active")
        if not run:
            raise ValueError("A fresh benchmark for the mutation parent is required.")

        cases = list(run.get("case_results") or [])
        if not cases:
            raise ValueError("Mutation parent benchmark has no case results.")
        cases.sort(key=lambda item: (
            int(item.get("score") or 0),
            1 if item.get("passed") else 0,
            str(item.get("case_id") or ""),
        ))
        case = cases[0]
        weaknesses = [_norm(x) for x in (case.get("weaknesses") or []) if _norm(x)]
        focus = (
            (weaknesses[0] if weaknesses else "")
            or _norm(case.get("improvement"))
            or _norm(case.get("expected_behavior"))
            or "Improve this benchmark case without weakening other behavior."
        )
        return {
            "case_id": _norm(case.get("case_id")) or "unknown-case",
            "case_score": int(case.get("score") or 0),
            "case_passed": bool(case.get("passed")),
            "weakness": focus[:900],
            "input": _norm(case.get("input"))[:900],
            "expected_behavior": _norm(case.get("expected_behavior"))[:900],
        }

    def preflight_single_edit(
        self,
        parent_instructions,
        parent_criteria,
        child_instructions,
        child_criteria,
        allowed_tools_before,
        allowed_tools_after,
        target,
    ):
        """Reject profile drift before the expensive benchmark stage."""
        p_i = _as_list(parent_instructions)
        p_c = _as_list(parent_criteria)
        c_i = _as_list(child_instructions)
        c_c = _as_list(child_criteria)
        before_tools = _as_list(allowed_tools_before)
        after_tools = _as_list(allowed_tools_after)

        reasons = []
        changes = []
        if len(p_i) != len(c_i) or len(p_c) != len(c_c):
            reasons.append("profile_line_count_changed")
        else:
            for index, (before, after) in enumerate(zip(p_i, c_i)):
                if before != after:
                    changes.append(("instruction", index, before, after))
            for index, (before, after) in enumerate(zip(p_c, c_c)):
                if before != after:
                    changes.append(("criterion", index, before, after))

        if before_tools != after_tools:
            reasons.append("tool_permissions_changed")
        if len(changes) != 1:
            reasons.append("mutation_must_change_exactly_one_line")

        similarity = None
        if len(changes) == 1:
            section, index, before, after = changes[0]
            if not _norm(after):
                reasons.append("replacement_is_empty")
            if len(after) > self.max_replacement_chars:
                reasons.append("replacement_too_long")
            max_growth = max(len(before) * 3, len(before) + 160, 80)
            if len(after) > max_growth:
                reasons.append("replacement_expands_line_too_far")
            similarity = round(
                SequenceMatcher(None, before.lower(), after.lower()).ratio(), 3
            )
            if before and similarity < self.min_line_similarity:
                reasons.append("replacement_drift_too_large")
            if self.lab.sensitive_fn(after):
                reasons.append("replacement_contains_sensitive_literal")
        else:
            section = index = before = after = None

        total_lines = max(1, len(p_i) + len(p_c))
        changed_count = len(changes)
        drift_percent = round(100.0 * changed_count / total_lines, 1)
        passed = not reasons
        return {
            "kind": "skill_mutation_diff",
            "target_case_id": (target or {}).get("case_id"),
            "target_case_score": (target or {}).get("case_score"),
            "target_weakness": (target or {}).get("weakness"),
            "section": section,
            "index": index,
            "before": before,
            "after": after,
            "changed_line_count": changed_count,
            "total_profile_lines": total_lines,
            "profile_line_drift_percent": drift_percent,
            "line_similarity": similarity,
            "tools_unchanged": before_tools == after_tools,
            "rollback_safe": bool(passed and len(changes) == 1),
            "preflight_passed": bool(passed),
            "rejection_reasons": reasons,
        }

    def save_mutation_audit(self, payload, importance=8):
        record = dict(payload or {})
        record.setdefault("kind", "skill_mutation_diff")
        record.setdefault("created_at", self._now().isoformat())
        return self._save(SKILL_MUTATION_DIFF_CATEGORY, record, importance)

    def profile_signature(self, instructions, criteria):
        return _hash({
            "instructions": _as_list(instructions),
            "success_criteria": _as_list(criteria),
        })

    def status(self, skill_name=None):
        out = super().status(skill_name)
        out.update({
            "constrained_champion_mutation": True,
            "single_edit_mutations_only": True,
            "prebenchmark_drift_gate": True,
            "mutation_diff_audit": True,
            "max_replacement_chars": self.max_replacement_chars,
            "min_line_similarity": self.min_line_similarity,
            "automatic_activation": False,
            "human_promotion_required": True,
        })
        return out
