"""Harmless source target used only by Tyler AI's safe maintenance-execution drill.

The production value in this file must remain ``base``. The v2.14.1 drill
publishes a proposal that changes it only on a newly-created review branch.
"""

DRILL_MARKER = "review-branch-test"


def drill_marker():
    return DRILL_MARKER
