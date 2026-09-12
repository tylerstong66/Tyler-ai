import os
import re
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)


# =========================================================
# CONFIG
# =========================================================

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
TYLER_API_KEY = os.environ.get("TYLER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
TYLER_DEFAULT_EMAIL = os.environ.get("TYLER_DEFAULT_EMAIL")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

GROQ_MODEL = os.environ.get(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

MAX_AGENT_ACTIONS = 5


# =========================================================
# SECURITY
# =========================================================

def authorized():
    supplied = request.headers.get("X-Tyler-Key")

    return bool(
        TYLER_API_KEY
        and supplied
        and supplied == TYLER_API_KEY
    )


# =========================================================
# HELPERS
# =========================================================

def clamp(value, low, high):
    try:
        value = int(value)
    except Exception:
        value = low

    return max(low, min(high, value))


def normalize_text(value):
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value)
    ).strip()


def parse_json_object(text):
    if not text:
        return None

    text = str(text).strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:
        parsed = json.loads(text)

        if isinstance(parsed, dict):
            return parsed

    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        try:
            parsed = json.loads(
                text[start:end + 1]
            )

            if isinstance(parsed, dict):
                return parsed

        except Exception:
            pass

    return None


# =========================================================
# GROQ
# =========================================================

def call_groq(
    system_prompt,
    user_prompt,
    max_tokens=700,
    temperature=0.2,
    response_format=None,
):
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured"
        )

    payload = {
        "model":
            GROQ_MODEL,

        "messages": [
            {
                "role":
                    "system",

                "content":
                    system_prompt,
            },
            {
                "role":
                    "user",

                "content":
                    user_prompt,
            },
        ],

        "temperature":
            temperature,

        "max_tokens":
            max_tokens,
    }

    if response_format:
        payload["response_format"] = (
            response_format
        )

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",

        headers={
            "Authorization":
                f"Bearer {GROQ_API_KEY}",

            "Content-Type":
                "application/json",
        },

        json=payload,

        timeout=90,
    )

    try:
        result = response.json()

    except Exception:
        raise RuntimeError(
            f"Groq returned "
            f"{response.status_code}: "
            f"{response.text[:500]}"
        )

    if not response.ok:
        error = result.get(
            "error",
            {}
        )

        if isinstance(error, dict):
            message = error.get(
                "message",
                str(error)
            )

        else:
            message = str(error)

        raise RuntimeError(
            message
        )

    content = (
        result.get(
            "choices",
            [{}]
        )[0]
        .get(
            "message",
            {}
        )
        .get(
            "content",
            ""
        )
    )

    return str(content).strip()


# =========================================================
# STRICT AGENT DECISION SCHEMA
# =========================================================

AGENT_DECISION_SCHEMA = {
    "type":
        "json_schema",

    "json_schema": {
        "name":
            "tyler_next_action",

        "strict":
            True,

        "schema": {
            "type":
                "object",

            "properties": {
                "tool": {
                    "type":
                        "string",

                    "enum": [
                        "read_memory",
                        "research_web",
                        "reason",
                        "save_memory",
                        "send_email",
                        "finish",
                    ],
                },

                "instruction": {
                    "type":
                        "string",
                },

                "why": {
                    "type":
                        "string",
                },
            },

            "required": [
                "tool",
                "instruction",
                "why",
            ],

            "additionalProperties":
                False,
        },
    },
}


# =========================================================
# SUPABASE
# =========================================================

def supabase_headers():
    if not SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_KEY is not configured"
        )

    return {
        "apikey":
            SUPABASE_KEY,

        "Authorization":
            f"Bearer {SUPABASE_KEY}",

        "Content-Type":
            "application/json",
    }


def get_memories(limit=20):
    if not SUPABASE_URL:
        return []

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/memories",

        headers=
            supabase_headers(),

        params={
            "select":
                "id,created_at,memories,"
                "category,importance",

            "order":
                "importance.desc,created_at.desc",

            "limit":
                limit,
        },

        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase read failed: "
            f"{response.status_code} "
            f"{response.text[:500]}"
        )

    return response.json()


def save_memory(
    text,
    category="general",
    importance=5
):
    if not SUPABASE_URL:
        raise RuntimeError(
            "SUPABASE_URL is not configured"
        )

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/memories",

        headers={
            **supabase_headers(),

            "Prefer":
                "return=representation",
        },

        json={
            "memories":
                text,

            "category":
                category,

            "importance":
                clamp(
                    importance,
                    1,
                    10
                ),
        },

        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase save failed: "
            f"{response.status_code} "
            f"{response.text[:500]}"
        )

    return response.json()


def memory_exists(text):
    target = normalize_text(
        text
    ).lower()

    try:
        memories = get_memories(
            50
        )

    except Exception:
        return False

    for item in memories:
        existing = normalize_text(
            item.get(
                "memories",
                ""
            )
        ).lower()

        if existing == target:
            return True

    return False


def compact_memory_context(limit=8):
    try:
        memories = get_memories(
            limit
        )

    except Exception:
        return ""

    lines = []

    for item in memories:
        text = normalize_text(
            item.get(
                "memories",
                ""
            )
        )[:240]

        category = item.get(
            "category",
            "general"
        )

        lines.append(
            f"- [{category}] {text}"
        )

    return "\n".join(
        lines
    )[:1600]


# =========================================================
# MEMORY SAFETY
# =========================================================

def looks_sensitive(text):
    lower = str(
        text
    ).lower()

    blocked_terms = [
        "password",
        "api key",
        "apikey",
        "secret key",
        "access token",
        "auth token",
        "bearer token",
        "credit card",
        "cvv",
        "social security",
        "ssn",
        "bank account",
        "routing number",
        "private key",
    ]

    return any(
        term in lower
        for term in blocked_terms
    )


# =========================================================
# PERMISSIONS
# =========================================================

def user_allows_email(message):
    lower = message.lower()

    phrases = [
        "email me",
        "email the result",
        "email the results",
        "send me an email",
        "send it to my email",
        "send the result to my email",
        "send the results to my email",
    ]

    return any(
        phrase in lower
        for phrase in phrases
    )


def user_allows_memory_write(message):
    lower = message.lower()

    phrases = [
        "remember that",
        "remember this",
        "remember which",
        "remember the recommendation",
        "remember my choice",
        "save to memory",
        "save it to memory",
        "save this to memory",
        "save that recommendation",
        "save the recommendation",
        "save this recommendation",
        "store this",
        "don't forget",
        "do not forget",
    ]

    return any(
        phrase in lower
        for phrase in phrases
    )


# =========================================================
# EXPLICIT MEMORY FAST PATH
# =========================================================

def explicit_memory_request(message):
    lower = message.lower().strip()

    starts = [
        "remember that ",
        "remember this ",
        "save this to memory ",
        "save that to memory ",
        "store this ",
        "don't forget ",
        "do not forget ",
    ]

    return any(
        lower.startswith(item)
        for item in starts
    )


def clean_explicit_memory(message):
    text = message.strip()

    patterns = [
        r"^remember that\s+",
        r"^remember this[:\s]+",
        r"^save this to memory[:\s]+",
        r"^save that to memory[:\s]+",
        r"^store this[:\s]+",
        r"^don't forget(?: that)?\s+",
        r"^do not forget(?: that)?\s+",
    ]

    for pattern in patterns:
        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE
        )

    return text.strip()


def guess_memory_category(text):
    lower = text.lower()

    if any(
        x in lower
        for x in [
            "favorite",
            "prefer",
            "i like",
        ]
    ):
        return "preference"

    if any(
        x in lower
        for x in [
            "goal",
            "want to become",
        ]
    ):
        return "goal"

    if any(
        x in lower
        for x in [
            "project",
            "building",
            "tyler ai",
        ]
    ):
        return "project"

    if any(
        x in lower
        for x in [
            "job",
            "career",
            "work",
        ]
    ):
        return "career"

    return "general"


# =========================================================
# TAVILY
# =========================================================

def web_search(query):
    if not TAVILY_API_KEY:
        raise RuntimeError(
            "TAVILY_API_KEY is not configured"
        )

    response = requests.post(
        "https://api.tavily.com/search",

        headers={
            "Authorization":
                f"Bearer {TAVILY_API_KEY}",

            "Content-Type":
                "application/json",
        },

        json={
            "query":
                query,

            "search_depth":
                "basic",

            "include_answer":
                True,

            "max_results":
                4,
        },

        timeout=60,
    )

    try:
        result = response.json()

    except Exception:
        raise RuntimeError(
            f"Tavily returned "
            f"{response.status_code}: "
            f"{response.text[:500]}"
        )

    if not response.ok:
        raise RuntimeError(
            str(result)
        )

    sources = []

    for item in result.get(
        "results",
        []
    )[:4]:

        sources.append(
            {
                "title":
                    item.get(
                        "title",
                        ""
                    ),

                "url":
                    item.get(
                        "url",
                        ""
                    ),

                "content":
                    normalize_text(
                        item.get(
                            "content",
                            ""
                        )
                    )[:400],
            }
        )

    return {
        "answer":
            normalize_text(
                result.get(
                    "answer",
                    ""
                )
            )[:1100],

        "sources":
            sources,
    }


def compact_research(research):
    pieces = []

    answer = research.get(
        "answer",
        ""
    )

    if answer:
        pieces.append(
            "SEARCH SUMMARY:\n"
            + answer
        )

    for index, source in enumerate(
        research.get(
            "sources",
            []
        ),
        start=1
    ):

        pieces.append(
            f"\nSOURCE {index}\n"
            f"Title: {source.get('title', '')}\n"
            f"Info: {source.get('content', '')}"
        )

    return "\n".join(
        pieces
    )[:3300]


# =========================================================
# N8N
# =========================================================

def send_to_n8n(payload):
    if not N8N_WEBHOOK_URL:
        raise RuntimeError(
            "N8N_WEBHOOK_URL is not configured"
        )

    response = requests.post(
        N8N_WEBHOOK_URL,
        json=payload,
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"n8n returned "
            f"{response.status_code}: "
            f"{response.text[:500]}"
        )

    return response.text


def send_email(
    body,
    subject="Tyler AI Results"
):
    if not TYLER_DEFAULT_EMAIL:
        raise RuntimeError(
            "TYLER_DEFAULT_EMAIL is not configured"
        )

    result = send_to_n8n(
        {
            "action":
                "email",

            "data": {
                "to":
                    TYLER_DEFAULT_EMAIL,

                "subject":
                    subject,

                "message":
                    body,
            },
        }
    )

    return {
        "sent":
            True,

        "to":
            TYLER_DEFAULT_EMAIL,

        "subject":
            subject,

        "n8n_response":
            result[:250],
    }


# =========================================================
# LOCAL INTENT HELPERS
# =========================================================

def needs_memory(message):
    lower = message.lower()

    terms = [
        "what you remember",
        "what you know about me",
        "based on what you know",
        "my goals",
        "my goal",
        "my preferences",
        "my preference",
        "my favorite",
        "for me",
        "best fit for me",
    ]

    return any(
        term in lower
        for term in terms
    )


def needs_research(message):
    lower = message.lower()

    terms = [
        "research",
        "latest",
        "current",
        "today",
        "recent",
        "news",
        "look up",
        "search",
        "best current",
        "right now",
        "available now",
    ]

    return any(
        term in lower
        for term in terms
    )


# =========================================================
# LOCAL FALLBACK DECIDER
# =========================================================

def fallback_next_action(
    message,
    used_tools,
    email_allowed,
    memory_allowed,
    has_final_reply,
):
    if (
        needs_memory(message)
        and "read_memory"
        not in used_tools
    ):
        return {
            "tool":
                "read_memory",

            "instruction":
                "Read relevant saved user context.",

            "why":
                "User-specific context may improve the answer.",

            "decision_source":
                "local-fallback",
        }

    if (
        needs_research(message)
        and "research_web"
        not in used_tools
    ):
        return {
            "tool":
                "research_web",

            "instruction":
                message,

            "why":
                "The request needs current information.",

            "decision_source":
                "local-fallback",
        }

    if (
        not has_final_reply
        and "reason"
        not in used_tools
    ):
        return {
            "tool":
                "reason",

            "instruction":
                "Produce the final answer using gathered information.",

            "why":
                "Enough information is available to reason.",

            "decision_source":
                "local-fallback",
        }

    if (
        memory_allowed
        and has_final_reply
        and "save_memory"
        not in used_tools
    ):
        return {
            "tool":
                "save_memory",

            "instruction":
                "Save the final durable recommendation.",

            "why":
                "The user explicitly requested memory storage.",

            "decision_source":
                "local-fallback",
        }

    if (
        email_allowed
        and has_final_reply
        and "send_email"
        not in used_tools
    ):
        return {
            "tool":
                "send_email",

            "instruction":
                "Email the completed answer.",

            "why":
                "The user explicitly requested email.",

            "decision_source":
                "local-fallback",
        }

    return {
        "tool":
            "finish",

        "instruction":
            "Finish the task.",

        "why":
            "The request is complete.",

        "decision_source":
            "local-fallback",
    }


# =========================================================
# STRICT AUTONOMOUS NEXT-ACTION DECIDER
# =========================================================

def decide_next_action(
    message,
    used_tools,
    email_allowed,
    memory_allowed,
    has_memory,
    has_research,
    has_final_reply,
    memory_done,
    email_done,
):
    available = [
        "read_memory",
        "research_web",
        "reason",
        "finish",
    ]

    if memory_allowed:
        available.append(
            "save_memory"
        )

    if email_allowed:
        available.append(
            "send_email"
        )

    status = {
        "tools_already_used":
            used_tools,

        "memory_available":
            has_memory,

        "research_available":
            has_research,

        "final_answer_available":
            has_final_reply,

        "memory_write_complete":
            memory_done,

        "email_complete":
            email_done,

        "email_authorized":
            email_allowed,

        "memory_write_authorized":
            memory_allowed,
    }

    prompt = f"""
USER REQUEST:
{message}

CURRENT STATUS:
{json.dumps(status)}

AVAILABLE TOOLS:
{", ".join(available)}

Choose exactly ONE next action.

Rules:
- Never repeat a tool already used.
- If user-specific history matters and memory has not been read, choose read_memory.
- If current information matters and research has not been done, choose research_web.
- Choose reason after enough information has been collected.
- Do not save memory before a final answer exists.
- Do not send email before a final answer exists.
- save_memory is allowed only when memory_write_authorized is true.
- send_email is allowed only when email_authorized is true.
- Choose finish only when all explicitly requested actions are complete.
"""

    try:
        raw = call_groq(
            system_prompt=(
                "You are Tyler AI's autonomous "
                "next-action controller."
            ),

            user_prompt=
                prompt,

            max_tokens=
                120,

            temperature=
                0.0,

            response_format=
                AGENT_DECISION_SCHEMA,
        )

        decision = json.loads(
            raw
        )

        tool = decision.get(
            "tool",
            ""
        )

        if tool not in available:
            raise RuntimeError(
                f"Invalid tool selected: {tool}"
            )

        if (
            tool != "finish"
            and tool in used_tools
        ):
            raise RuntimeError(
                f"Repeated tool selected: {tool}"
            )

        if (
            tool == "save_memory"
            and not memory_allowed
        ):
            raise RuntimeError(
                "Unauthorized memory write"
            )

        if (
            tool == "send_email"
            and not email_allowed
        ):
            raise RuntimeError(
                "Unauthorized email"
            )

        if (
            tool in [
                "save_memory",
                "send_email",
            ]
            and not has_final_reply
        ):
            raise RuntimeError(
                "Action requires a final answer first"
            )

        return {
            "tool":
                tool,

            "instruction":
                decision.get(
                    "instruction",
                    ""
                ),

            "why":
                decision.get(
                    "why",
                    ""
                ),

            "decision_source":
                "groq-strict-schema",
        }

    except Exception as e:
        fallback = fallback_next_action(
            message,
            used_tools,
            email_allowed,
            memory_allowed,
            has_final_reply,
        )

        fallback[
            "decision_error"
        ] = str(e)[:300]

        return fallback


# =========================================================
# REASONING
# =========================================================

def reasoning_step(
    message,
    memory_text,
    research_text,
):
    prompt = f"""
USER REQUEST:
{message}

SAVED USER CONTEXT:
{memory_text[:1600] if memory_text else "None"}

LIVE RESEARCH:
{research_text[:3500] if research_text else "None"}

Answer the user's request.

Requirements:
- Use user context only when relevant.
- Use current research when available.
- If comparing choices, clearly identify the strongest choice.
- Explain the most important reasons.
- Do not claim an email or memory save happened yet.
- Keep the response useful and readable.
- End with exactly one line in this format when you make a recommendation:

RECOMMENDATION: <one concise sentence describing the final recommendation and why>

If the task does not involve a recommendation or decision, end with:

RECOMMENDATION: None
"""

    result = call_groq(
        system_prompt=(
            "You are Tyler AI, a practical "
            "personal autonomous assistant."
        ),

        user_prompt=
            prompt,

        max_tokens=
            700,

        temperature=
            0.2,
    )

    result = str(
        result
    ).strip()

    if not result:
        raise RuntimeError(
            "Empty reasoning response"
        )

    return result


# =========================================================
# FALLBACK ANSWER
# =========================================================

def build_fallback_answer(
    memory_text,
    research,
):
    pieces = []

    if research:
        answer = normalize_text(
            research.get(
                "answer",
                ""
            )
        )

        if answer:
            pieces.append(
                answer
            )

        if not answer:
            for source in research.get(
                "sources",
                []
            )[:3]:

                content = normalize_text(
                    source.get(
                        "content",
                        ""
                    )
                )

                if content:
                    pieces.append(
                        content
                    )

    if not pieces and memory_text:
        pieces.append(
            "Relevant saved context: "
            + memory_text
        )

    if not pieces:
        pieces.append(
            "I received the request, but I could "
            "not generate a complete response."
        )

    return (
        "\n\n".join(pieces)[:3200]
        + "\n\nRECOMMENDATION: None"
    )


# =========================================================
# CLEAN DECISION MEMORY
# =========================================================

def extract_recommendation(
    final_reply
):
    if not final_reply:
        return None

    match = re.search(
        r"(?im)^\s*RECOMMENDATION:\s*(.+?)\s*$",
        final_reply
    )

    if match:
        recommendation = normalize_text(
            match.group(1)
        )

        if (
            recommendation
            and recommendation.lower()
            not in [
                "none",
                "n/a",
                "not applicable",
            ]
        ):
            return recommendation[:350]

    # fallback if model did not follow ending format
    sentences = re.split(
        r"(?<=[.!?])\s+",
        normalize_text(
            final_reply
        )
    )

    trigger_terms = [
        "recommend",
        "best fit",
        "best choice",
        "top choice",
        "winner",
        "my pick",
        "i would choose",
    ]

    for sentence in sentences:
        lower = sentence.lower()

        if any(
            trigger in lower
            for trigger in trigger_terms
        ):
            clean = normalize_text(
                sentence
            )

            if "|" not in clean:
                return clean[:350]

    return None


def build_clean_memory(
    final_reply
):
    recommendation = extract_recommendation(
        final_reply
    )

    if not recommendation:
        return None

    return (
        "Tyler AI recommendation: "
        + recommendation
    )[:400]


# =========================================================
# AUTONOMOUS AGENT LOOP
# =========================================================

def run_agent(message):
    email_allowed = user_allows_email(
        message
    )

    memory_allowed = user_allows_memory_write(
        message
    )

    used_tools = []
    actions = []

    memory_text = ""
    research = None
    research_text = ""

    final_reply = ""

    memory_result = None
    email_result = None

    sources = []

    decision_calls = 0
    reasoning_calls = 0


    for action_number in range(
        1,
        MAX_AGENT_ACTIONS + 1
    ):

        decision = decide_next_action(
            message=
                message,

            used_tools=
                used_tools,

            email_allowed=
                email_allowed,

            memory_allowed=
                memory_allowed,

            has_memory=
                bool(memory_text),

            has_research=
                bool(research),

            has_final_reply=
                bool(final_reply),

            memory_done=
                memory_result is not None,

            email_done=
                email_result is not None,
        )

        if (
            decision.get(
                "decision_source"
            )
            == "groq-strict-schema"
        ):
            decision_calls += 1

        tool = decision[
            "tool"
        ]


        # =================================================
        # FINISH
        # =================================================

        if tool == "finish":

            actions.append(
                {
                    "action":
                        action_number,

                    "tool":
                        "finish",

                    "decision":
                        decision,
                }
            )

            break


        # =================================================
        # DUPLICATE PROTECTION
        # =================================================

        if tool in used_tools:

            actions.append(
                {
                    "action":
                        action_number,

                    "tool":
                        tool,

                    "skipped":
                        True,

                    "reason":
                        "Duplicate tool prevented.",

                    "decision":
                        decision,
                }
            )

            break


        used_tools.append(
            tool
        )


        # =================================================
        # READ MEMORY
        # =================================================

        if tool == "read_memory":

            try:
                memory_text = (
                    compact_memory_context(
                        8
                    )
                )

                result = (
                    memory_text
                    or
                    "No saved memory was found."
                )

            except Exception as e:
                result = (
                    f"Memory read failed: {e}"
                )

            actions.append(
                {
                    "action":
                        action_number,

                    "tool":
                        tool,

                    "decision":
                        decision,

                    "result":
                        result,
                }
            )


        # =================================================
        # RESEARCH WEB
        # =================================================

        elif tool == "research_web":

            try:
                research = web_search(
                    decision.get(
                        "instruction",
                        ""
                    )
                    or message
                )

                research_text = compact_research(
                    research
                )

                sources.extend(
                    research.get(
                        "sources",
                        []
                    )
                )

                result = research_text

            except Exception as e:
                research = None
                research_text = ""

                result = (
                    f"Research failed: {e}"
                )

            actions.append(
                {
                    "action":
                        action_number,

                    "tool":
                        tool,

                    "decision":
                        decision,

                    "result":
                        result,
                }
            )


        # =================================================
        # REASON
        # =================================================

        elif tool == "reason":

            try:
                reasoning_calls += 1

                final_reply = reasoning_step(
                    message,
                    memory_text,
                    research_text,
                )

                fallback_used = False
                reason_error = None

            except Exception as e:
                final_reply = (
                    build_fallback_answer(
                        memory_text,
                        research,
                    )
                )

                fallback_used = True
                reason_error = str(e)[:300]

            action_record = {
                "action":
                    action_number,

                "tool":
                    tool,

                "decision":
                    decision,

                "result":
                    final_reply,

                "fallback_used":
                    fallback_used,
            }

            if reason_error:
                action_record[
                    "reason_error"
                ] = reason_error

            actions.append(
                action_record
            )


        # =================================================
        # SAVE MEMORY
        # =================================================

        elif tool == "save_memory":

            if not memory_allowed:

                result = {
                    "saved":
                        False,

                    "reason":
                        "Memory writing was not authorized."
                }

            elif memory_result is not None:

                result = {
                    "saved":
                        False,

                    "reason":
                        "Memory write already attempted."
                }

            else:
                candidate = build_clean_memory(
                    final_reply
                )

                if not candidate:

                    result = {
                        "saved":
                            False,

                        "reason":
                            "No clear recommendation "
                            "was available to save."
                    }

                elif looks_sensitive(
                    candidate
                ):

                    result = {
                        "saved":
                            False,

                        "reason":
                            "Sensitive information was not stored."
                    }

                elif memory_exists(
                    candidate
                ):

                    result = {
                        "saved":
                            False,

                        "reason":
                            "Memory already exists.",

                        "memory":
                            candidate,
                    }

                else:

                    try:
                        database_result = save_memory(
                            candidate,
                            "decision",
                            8
                        )

                        result = {
                            "saved":
                                True,

                            "memory":
                                candidate,

                            "category":
                                "decision",

                            "importance":
                                8,

                            "database_result":
                                database_result,
                        }

                    except Exception as e:

                        result = {
                            "saved":
                                False,

                            "reason":
                                str(e),
                        }

            memory_result = result

            actions.append(
                {
                    "action":
                        action_number,

                    "tool":
                        tool,

                    "decision":
                        decision,

                    "result":
                        result,
                }
            )


        # =================================================
        # SEND EMAIL
        # =================================================

        elif tool == "send_email":

            if not email_allowed:

                result = {
                    "sent":
                        False,

                    "reason":
                        "Email was not authorized."
                }

            elif email_result is not None:

                result = {
                    "sent":
                        False,

                    "reason":
                        "Email already attempted."
                }

            else:

                try:
                    result = send_email(
                        final_reply,
                        "Tyler AI Results"
                    )

                except Exception as e:

                    result = {
                        "sent":
                            False,

                        "error":
                            str(e),
                    }

            email_result = result

            actions.append(
                {
                    "action":
                        action_number,

                    "tool":
                        tool,

                    "decision":
                        decision,

                    "result":
                        result,
                }
            )


    # =====================================================
    # GUARANTEE A FINAL ANSWER
    # =====================================================

    if not final_reply:

        try:
            reasoning_calls += 1

            final_reply = reasoning_step(
                message,
                memory_text,
                research_text,
            )

        except Exception:
            final_reply = build_fallback_answer(
                memory_text,
                research,
            )


    # =====================================================
    # GUARANTEE EXPLICITLY AUTHORIZED ACTIONS
    #
    # If the 5-action limit prevents the controller from
    # reaching save/email, perform each explicitly requested
    # action once after reasoning.
    # =====================================================

    if (
        memory_allowed
        and memory_result is None
    ):

        candidate = build_clean_memory(
            final_reply
        )

        if not candidate:

            memory_result = {
                "saved":
                    False,

                "reason":
                    "No clear recommendation "
                    "was available to save."
            }

        elif looks_sensitive(
            candidate
        ):

            memory_result = {
                "saved":
                    False,

                "reason":
                    "Sensitive information was not stored."
            }

        elif memory_exists(
            candidate
        ):

            memory_result = {
                "saved":
                    False,

                "reason":
                    "Memory already exists.",

                "memory":
                    candidate,
            }

        else:

            try:
                db_result = save_memory(
                    candidate,
                    "decision",
                    8
                )

                memory_result = {
                    "saved":
                        True,

                    "memory":
                        candidate,

                    "category":
                        "decision",

                    "importance":
                        8,

                    "database_result":
                        db_result,
                }

            except Exception as e:

                memory_result = {
                    "saved":
                        False,

                    "reason":
                        str(e),
                }


    if (
        email_allowed
        and email_result is None
    ):

        try:
            email_result = send_email(
                final_reply,
                "Tyler AI Results"
            )

        except Exception as e:

            email_result = {
                "sent":
                    False,

                "error":
                    str(e),
            }


    return {
        "reply":
            final_reply,

        "actions":
            actions,

        "used_tools":
            used_tools,

        "memory_result":
            memory_result,

        "email_result":
            email_result,

        "sources":
            sources,

        "decision_calls":
            decision_calls,

        "reasoning_calls":
            reasoning_calls,

        "total_groq_calls":
            decision_calls
            + reasoning_calls,

        "max_actions":
            MAX_AGENT_ACTIONS,

        "email_authorized":
            email_allowed,

        "memory_write_authorized":
            memory_allowed,
    }


# =========================================================
# HOME
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify(
        {
            "name":
                "Tyler AI",

            "status":
                "online",

            "version":
                "2.2.1-strict-agent",

            "mode":
                "autonomous-next-action",

            "decision_format":
                "groq-strict-json-schema",

            "secured":
                bool(
                    TYLER_API_KEY
                ),

            "groq_connected":
                bool(
                    GROQ_API_KEY
                ),

            "tavily_connected":
                bool(
                    TAVILY_API_KEY
                ),

            "n8n_connected":
                bool(
                    N8N_WEBHOOK_URL
                ),

            "memory_connected":
                bool(
                    SUPABASE_URL
                    and SUPABASE_KEY
                ),

            "max_actions":
                MAX_AGENT_ACTIONS,

            "tools": [
                "read_memory",
                "research_web",
                "reason",
                "save_memory",
                "send_email",
            ],
        }
    )


# =========================================================
# HEALTH
# =========================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify(
        {
            "status":
                "healthy",

            "version":
                "2.2.1-strict-agent",
        }
    )


# =========================================================
# MEMORIES
# =========================================================

@app.route(
    "/memories",
    methods=["GET"]
)
def memories_route():

    if not authorized():

        return jsonify(
            {
                "success":
                    False,

                "error":
                    "Unauthorized",
            }
        ), 401

    try:
        items = get_memories(
            50
        )

        return jsonify(
            {
                "success":
                    True,

                "count":
                    len(items),

                "memories":
                    items,
            }
        )

    except Exception as e:

        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(e),
            }
        ), 500


# =========================================================
# CHAT
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    if not authorized():

        return jsonify(
            {
                "success":
                    False,

                "error":
                    "Unauthorized",
            }
        ), 401


    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    message = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    if not message:

        return jsonify(
            {
                "success":
                    False,

                "error":
                    "Missing message",
            }
        ), 400


    # =====================================================
    # DIRECT MEMORY FAST PATH
    # =====================================================

    if explicit_memory_request(
        message
    ):

        try:
            memory = clean_explicit_memory(
                message
            )

            if not memory:
                raise RuntimeError(
                    "No memory text found."
                )

            if looks_sensitive(
                memory
            ):

                return jsonify(
                    {
                        "success":
                            False,

                        "type":
                            "memory",

                        "error":
                            "Sensitive information "
                            "will not be stored.",
                    }
                ), 400

            if memory_exists(
                memory
            ):

                return jsonify(
                    {
                        "success":
                            True,

                        "type":
                            "memory",

                        "saved":
                            False,

                        "reason":
                            "Memory already exists.",

                        "groq_calls":
                            0,
                    }
                )

            category = guess_memory_category(
                memory
            )

            saved = save_memory(
                memory,
                category,
                7
            )

            return jsonify(
                {
                    "success":
                        True,

                    "type":
                        "memory",

                    "saved":
                        True,

                    "memory":
                        memory,

                    "category":
                        category,

                    "groq_calls":
                        0,

                    "database_result":
                        saved,
                }
            )

        except Exception as e:

            return jsonify(
                {
                    "success":
                        False,

                    "type":
                        "memory",

                    "error":
                        str(e),
                }
            ), 500


    # =====================================================
    # AUTONOMOUS AGENT
    # =====================================================

    try:
        execution = run_agent(
            message
        )

    except Exception as e:

        return jsonify(
            {
                "success":
                    False,

                "type":
                    "autonomous_agent",

                "version":
                    "2.2.1-strict-agent",

                "error":
                    str(e),
            }
        ), 500


    return jsonify(
        {
            "success":
                True,

            "type":
                "autonomous_agent",

            "version":
                "2.2.1-strict-agent",

            "reply":
                execution[
                    "reply"
                ],

            "actions":
                execution[
                    "actions"
                ],

            "used_tools":
                execution[
                    "used_tools"
                ],

            "memory_result":
                execution[
                    "memory_result"
                ],

            "email_result":
                execution[
                    "email_result"
                ],

            "sources":
                execution[
                    "sources"
                ],

            "decision_calls":
                execution[
                    "decision_calls"
                ],

            "reasoning_calls":
                execution[
                    "reasoning_calls"
                ],

            "total_groq_calls":
                execution[
                    "total_groq_calls"
                ],

            "max_actions":
                execution[
                    "max_actions"
                ],

            "permissions": {
                "email":
                    execution[
                        "email_authorized"
                    ],

                "memory_write":
                    execution[
                        "memory_write_authorized"
                    ],
            },
        }
    )


# =========================================================
# WEBHOOK
# =========================================================

@app.route(
    "/webhook",
    methods=["POST"]
)
def webhook():

    if not authorized():

        return jsonify(
            {
                "success":
                    False,

                "error":
                    "Unauthorized",
            }
        ), 401


    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    if not data.get(
        "action"
    ):

        return jsonify(
            {
                "success":
                    False,

                "error":
                    "Missing action",
            }
        ), 400


    try:
        result = send_to_n8n(
            data
        )

        return jsonify(
            {
                "success":
                    True,

                "n8n_response":
                    result[:500],
            }
        )

    except Exception as e:

        return jsonify(
            {
                "success":
                    False,

                "error":
                    str(e),
            }
        ), 500


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        )
