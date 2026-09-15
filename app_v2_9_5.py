import os
import re

import app_v2_9_4 as v294


# v2.9.5 prevents domain-specific deterministic checks from leaking into
# unrelated skill tests. In v2.9.4, an answer that merely mentioned n8n could
# accidentally trigger email-authentication checks even when the user asked
# about Render deployment. Checks are now activated from the USER REQUEST,
# never from incidental terms in the candidate answer.
v294.base.VERSION = '2.9.5-contextual-check-routing'
v294.base.VERSION_SHORT = 'v2.9.5'

_original_architecture_checks = v294.v293.v292._architecture_checks


def _norm(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip().lower()


def _email_check_relevant(test_input):
    """True only when the user's request is actually about Tyler AI email/n8n auth."""
    request = _norm(test_input)
    if not request:
        return False

    # Direct email/Gmail/send-function requests are unambiguously email-domain.
    if any(term in request for term in [
        'email',
        'gmail',
        'send_email_via_n8n',
        'send email',
        'sending mail',
    ]):
        return True

    # n8n is broader than email, so require an auth/webhook/send signal too.
    if 'n8n' in request and any(term in request for term in [
        'unauthorized',
        'authorization',
        'authentication',
        'auth',
        'webhook',
        'header',
        'api key',
        'key',
        'send',
    ]):
        return True

    return False


def _contextual_architecture_checks(skill, test_input, output):
    """Run email-specific deterministic checks only for email-domain requests."""
    if not v294.v293.v292._developer_skill(skill):
        return {}

    if not _email_check_relevant(test_input):
        return {}

    return _original_architecture_checks(skill, test_input, output)


# v2.9.4 resolves this function dynamically through v292, so replacing it here
# changes the live evaluator without duplicating the whole scoring system.
v294.v293.v292._architecture_checks = _contextual_architecture_checks


app = v294.app
base = v294.base
ENGINE = v294.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
