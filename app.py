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
# GENERAL HELPERS
# =========================================================

def clamp(value, low, high):
    try:
        value = int(value)
    except Exception:
        value = low

    return max(
        low,
        min(high, value)
    )


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
        result = json.loads(text)

        if isinstance(result, dict):
            return result

    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        try:
            result = json.loads(
                text[start:end + 1]
            )

            if isinstance(result, dict):
                return result

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
    temperature=0.2
):
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured"
        )

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",

        headers={
            "Authorization":
                f"Bearer {GROQ_API_KEY}",

            "Content-Type":
                "application/json",
        },

        json={
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
        },

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

        if isinstance(
            error,
            dict
        ):
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


def compact_memory_context(
    limit=8
):
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
        )[:250]

        category = item.get(
            "category",
            "general"
        )

        lines.append(
            f"- [{category}] {text}"
        )

    return "\n".join(
        lines
    )[:1500]


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
# USER PERMISSIONS
# =========================================================

def user_allows_email(message):
    lower = message.lower()

    phrases = [
        "email me",
        "email the result",
        "email the results",
        "send me an email",
        "send the result to my email",
        "send the results to my email",
        "send it to my email",
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
# DIRECT MEMORY SAVE
# =========================================================

def explicit_memory_request(
    message
):
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
        lower.startswith(
            item
        )
        for item in starts
    )


def clean_explicit_memory(
    message
):
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


def guess_memory_category(
    text
):
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
            )[:1000],

        "sources":
            sources,
    }


def compact_research(
    research
):
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
            f"{source.get('title', '')}\n"
            f"{source.get('content', '')}"
        )

    return "\n".join(
        pieces
    )[:3000]


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
            "TYLER_DEFAULT_EMAIL "
            "is not configured"
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
# FALLBACK ROUTING LOGIC
# =========================================================

def needs_memory(
    message
):
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


def needs_research(
    message
):
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


def fallback_next_action(
    message,
    used_tools,
    email_allowed,
    memory_allowed,
    final_reply
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
                "Read relevant saved user context."
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
                message
        }

    if (
        "reason"
        not in used_tools
    ):
        return {
            "tool":
                "reason",

            "instruction":
                "Answer the request using all available information."
        }

    if (
        memory_allowed
        and final_reply
        and "save_memory"
        not in used_tools
    ):
        return {
            "tool":
                "save_memory",

            "instruction":
                "Save the useful final decision or recommendation."
        }

    if (
        email_allowed
        and final_reply
        and "send_email"
        not in used_tools
    ):
        return {
            "tool":
                "send_email",

            "instruction":
                "Email the final answer."
        }

    return {
        "tool":
            "finish",

        "instruction":
            "Finish the task."
    }


# =========================================================
# AUTONOMOUS NEXT-ACTION DECISION
# =========================================================

def decide_next_action(
    message,
    used_tools,
    state_summary,
    email_allowed,
    memory_allowed
):
    available_tools = [
        "read_memory",
        "research_web",
        "reason",
        "finish",
    ]

    if memory_allowed:
        available_tools.append(
            "save_memory"
        )

    if email_allowed:
        available_tools.append(
            "send_email"
        )

    prompt = f"""
USER REQUEST:
{message}

TOOLS ALREADY USED:
{", ".join(used_tools) if used_tools else "none"}

CURRENT STATE:
{state_summary[:2200] if state_summary else "No tool results yet."}

AVAILABLE NEXT ACTIONS:
{", ".join(available_tools)}

Choose ONE next action.

Return ONLY JSON:

{{
  "tool": "one available action",
  "instruction": "short specific instruction",
  "why": "very short reason"
}}

Rules:

- Choose only ONE action.
- Never choose a tool already used.
- Use read_memory if user history or preferences matter.
- Use research_web if live/current information matters.
- Use reason when enough information exists to answer or decide.
- Use save_memory only if it is available.
- Use send_email only if it is available.
- Choose finish when the request has been completed.
- Do not repeat tools.
"""

    try:
        raw = call_groq(
            system_prompt=(
                "You control Tyler AI one action at a time. "
                "Return compact JSON only."
            ),

            user_prompt=
                prompt,

            max_tokens=
                180,

            temperature=
                0.0,
        )

        parsed = parse_json_object(
            raw
        )

        if not parsed:
            raise RuntimeError(
                "No valid decision JSON"
            )

        tool = str(
            parsed.get(
                "tool",
                ""
            )
        ).strip()

        instruction = str(
            parsed.get(
                "instruction",
                message
            )
        ).strip()

        if tool not in available_tools:
            raise RuntimeError(
                "Invalid tool selected"
            )

        if (
            tool != "finish"
            and tool in used_tools
        ):
            raise RuntimeError(
                "Duplicate tool selected"
            )

        return {
            "tool":
                tool,

            "instruction":
                instruction or message,

            "why":
                str(
                    parsed.get(
                        "why",
                        ""
                    )
                )[:200],

            "decision_source":
                "groq",
        }

    except Exception as e:
        fallback = fallback_next_action(
            message,
            used_tools,
            email_allowed,
            memory_allowed,
            final_reply=(
                "reason"
                in used_tools
            )
        )

        fallback[
            "decision_source"
        ] = "local-fallback"

        fallback[
            "decision_error"
        ] = str(e)[:250]

        return fallback


# =========================================================
# REASONING
# =========================================================

def reasoning_step(
    message,
    state_summary
):
    prompt = f"""
USER REQUEST:

{message}

INFORMATION GATHERED:

{state_summary[:5000] if state_summary else "No additional information."}

Give the user the best final answer.

Rules:

- Use saved memory when relevant.
- Use live research when available.
- If comparing choices, pick a clear winner.
- Explain the main reason for your choice.
- Do not say something was emailed or saved unless it already happened.
- Return normal prose.
- Never return an empty answer.
"""

    result = call_groq(
        system_prompt=(
            "You are Tyler AI, a practical personal autonomous assistant."
        ),

        user_prompt=
            prompt,

        max_tokens=
            750,

        temperature=
            0.2,
    )

    result = result.strip()

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
    research
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
        return (
            "I received the request, but I could not "
            "generate a complete response this time."
        )

    return "\n\n".join(
        pieces
    )[:3500]


# =========================================================
# CLEAN MEMORY CREATION
# =========================================================

def build_concise_memory(
    final_reply
):
    text = normalize_text(
        final_reply
    )

    if not text:
        return None

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    preferred = []

    trigger_phrases = [
        "recommend",
        "best fit",
        "best choice",
        "top choice",
        "winner",
        "my pick",
        "i would choose",
        "choose",
    ]

    for sentence in sentences:
        lower = sentence.lower()

        if any(
            trigger in lower
            for trigger in trigger_phrases
        ):
            preferred.append(
                sentence
            )

    if preferred:
        memory = " ".join(
            preferred[:2]
        )

    else:
        memory = " ".join(
            sentences[:2]
        )

    memory = normalize_text(
        memory
    )[:400]

    if not memory:
        return None

    return (
        "Tyler AI decision: "
        + memory
    )


# =========================================================
# AUTONOMOUS LOOP
# =========================================================

def run_agent(
    message
):
    email_allowed = user_allows_email(
        message
    )

    memory_allowed = user_allows_memory_write(
        message
    )

    used_tools = []

    actions = []

    state_parts = []

    latest_memory = ""

    latest_research = None

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

        state_summary = "\n\n".join(
            state_parts
        )[-5500:]

        decision = decide_next_action(
            message,
            used_tools,
            state_summary,
            email_allowed,
            memory_allowed,
        )

        if decision.get(
            "decision_source"
        ) == "groq":
            decision_calls += 1

        tool = decision[
            "tool"
        ]

        instruction = decision.get(
            "instruction",
            message
        )

        # -------------------------------------------------
        # FINISH
        # -------------------------------------------------

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


        # -------------------------------------------------
        # DUPLICATE SAFETY
        # -------------------------------------------------

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
                }
            )

            break

        used_tools.append(
            tool
        )


        # -------------------------------------------------
        # READ MEMORY
        # -------------------------------------------------

        if tool == "read_memory":

            try:
                latest_memory = (
                    compact_memory_context(
                        8
                    )
                )

                result = (
                    latest_memory
                    or
                    "No saved memory was found."
                )

            except Exception as e:
                result = (
                    f"Memory read failed: {e}"
                )

            state_parts.append(
                "MEMORY:\n"
                + result
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


        # -------------------------------------------------
        # WEB RESEARCH
        # -------------------------------------------------

        elif tool == "research_web":

            try:
                latest_research = web_search(
                    instruction
                )

                research_text = compact_research(
                    latest_research
                )

                sources.extend(
                    latest_research.get(
                        "sources",
                        []
                    )
                )

                result = research_text

            except Exception as e:
                result = (
                    f"Research failed: {e}"
                )

            state_parts.append(
                "RESEARCH:\n"
                + result
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


        # -------------------------------------------------
        # REASON
        # -------------------------------------------------

        elif tool == "reason":

            state_summary = "\n\n".join(
                state_parts
            )[-5000:]

            try:
                reasoning_calls += 1

                final_reply = reasoning_step(
                    message,
                    state_summary
                )

                fallback_used = False

            except Exception as e:
                final_reply = build_fallback_answer(
                    latest_memory,
                    latest_research
                )

                fallback_used = True

                reason_error = str(
                    e
                )[:300]

            state_parts.append(
                "FINAL REASONING:\n"
                + final_reply
            )

            action_data = {
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

            if fallback_used:
                action_data[
                    "reason_error"
                ] = reason_error

            actions.append(
                action_data
            )


        # -------------------------------------------------
        # SAVE MEMORY
        # -------------------------------------------------

        elif tool == "save_memory":

            if not memory_allowed:
                result = {
                    "saved":
                        False,

                    "reason":
                        "User did not authorize memory writing."
                }

            elif memory_result is not None:
                result = {
                    "saved":
                        False,

                    "reason":
                        "Memory write already attempted."
                }

            else:
                candidate = build_concise_memory(
                    final_reply
                )

                if not candidate:
                    result = {
                        "saved":
                            False,

                        "reason":
                            "No useful final result was available."
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


        # -------------------------------------------------
        # EMAIL
        # -------------------------------------------------

        elif tool == "send_email":

            if not email_allowed:
                result = {
                    "sent":
                        False,

                    "reason":
                        "User did not authorize email."
                }

            elif email_result is not None:
                result = {
                    "sent":
                        False,

                    "reason":
                        "Email already attempted."
                }

            else:
                body = (
                    final_reply.strip()
                    if final_reply
                    else build_fallback_answer(
                        latest_memory,
                        latest_research
                    )
                )

                try:
                    result = send_email(
                        body,
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
    # GUARANTEE FINAL ANSWER
    # =====================================================

    if not final_reply:
        state_summary = "\n\n".join(
            state_parts
        )[-5000:]

        try:
            reasoning_calls += 1

            final_reply = reasoning_step(
                message,
                state_summary
            )

        except Exception:
            final_reply = build_fallback_answer(
                latest_memory,
                latest_research
            )


    # =====================================================
    # REQUIRED USER-AUTHORIZED ACTIONS
    #
    # If the loop hits its action limit before reaching
    # email/save, complete those explicit user requests
    # exactly once after reasoning.
    # =====================================================

    if (
        memory_allowed
        and memory_result is None
    ):
        candidate = build_concise_memory(
            final_reply
        )

        if not candidate:
            memory_result = {
                "saved":
                    False,

                "reason":
                    "No useful result was available."
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
                "2.2-autonomous-loop",

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

            "mode":
                "autonomous-next-action",

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
                "2.2-autonomous-loop",
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
                    "2.2-autonomous-loop",

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
                "2.2-autonomous-loop",

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
