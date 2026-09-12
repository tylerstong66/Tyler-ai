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
# BASIC HELPERS
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


    return (
        result["choices"][0]
        ["message"]["content"]
        .strip()
    )


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

    target = (
        str(text)
        .strip()
        .lower()
    )


    try:

        memories = get_memories(
            50
        )

    except Exception:

        return False


    for item in memories:

        existing = (
            str(
                item.get(
                    "memories",
                    ""
                )
            )
            .strip()
            .lower()
        )

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

        text = str(
            item.get(
                "memories",
                ""
            )
        )[:300]

        category = item.get(
            "category",
            "general"
        )

        lines.append(
            f"- [{category}] {text}"
        )


    return "\n".join(lines)[:2000]


# =========================================================
# MEMORY SAFETY
# =========================================================

def looks_sensitive(text):

    lower = text.lower()

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
# EXPLICIT MEMORY
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
        lower.startswith(x)
        for x in starts
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
                    str(
                        item.get(
                            "content",
                            ""
                        )
                    )[:500],
            }
        )


    return {
        "answer":
            str(
                result.get(
                    "answer",
                    ""
                )
            )[:1200],

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

            f"Title: "
            f"{source.get('title', '')}\n"

            f"URL: "
            f"{source.get('url', '')}\n"

            f"Info: "
            f"{source.get('content', '')}"
        )


    return "\n".join(pieces)[:4500]


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
            result[:300],
    }


# =========================================================
# LOCAL ROUTER
# =========================================================

def fallback_route(message):

    lower = message.lower()

    steps = []


    memory_terms = [
        "what you remember",
        "what you know about me",
        "based on what you know",
        "my preference",
        "my preferences",
        "my goal",
        "my goals",
        "my favorite",
    ]


    research_terms = [
        "research",
        "latest",
        "current",
        "today",
        "news",
        "look up",
        "search",
        "recent",
        "right now",
        "best current",
    ]


    save_terms = [
        "save that recommendation",
        "save the recommendation",
        "save this recommendation",
        "remember which",
        "remember the recommendation",
        "remember my choice",
        "save it to memory",
        "save to memory",
    ]


    email_terms = [
        "email me",
        "send me an email",
        "email the result",
        "email the results",
        "send the result",
        "send the results",
    ]


    if any(
        term in lower
        for term in memory_terms
    ):

        steps.append(
            {
                "tool":
                    "read_memory",

                "instruction":
                    "Read relevant user preferences, goals, and project information."
            }
        )


    if any(
        term in lower
        for term in research_terms
    ):

        steps.append(
            {
                "tool":
                    "research_web",

                "instruction":
                    message
            }
        )


    steps.append(
        {
            "tool":
                "reason",

            "instruction":
                "Complete the user's request using all available results."
        }
    )


    if any(
        term in lower
        for term in save_terms
    ):

        steps.append(
            {
                "tool":
                    "save_memory",

                "instruction":
                    "Save the final recommendation or decision."
            }
        )


    if any(
        term in lower
        for term in email_terms
    ):

        steps.append(
            {
                "tool":
                    "send_email",

                "instruction":
                    "Email the completed result."
            }
        )


    return {
        "goal":
            message[:250],

        "steps":
            steps[:6],

        "router":
            "fallback-local",
    }


# =========================================================
# GROQ ROUTER
# =========================================================

def tool_router(message):

    prompt = f"""
User request:

{message}

Choose the smallest ordered list of tools needed.

Available tools:

read_memory
research_web
reason
save_memory
send_email

Return ONLY a JSON object in this exact shape:

{{
  "goal": "short goal",
  "steps": [
    {{
      "tool": "read_memory",
      "instruction": "instruction"
    }}
  ]
}}

Rules:

Maximum 6 steps.

Use read_memory when previous preferences,
goals, projects, or decisions matter.

Use research_web when current information matters.

Use reason when analysis, comparison,
ranking, synthesis, or a final answer is needed.

Use save_memory only when the user explicitly asks
to remember or save a durable result.

Use send_email only when the user asks for email.

Never store passwords, API keys,
tokens, secrets, or banking credentials.
"""


    raw = call_groq(

        system_prompt=(
            "You are Tyler AI's tool router. "
            "Output JSON only."
        ),

        user_prompt=
            prompt,

        max_tokens=
            350,

        temperature=
            0.0,
    )


    parsed = parse_json_object(
        raw
    )


    if not parsed:

        return fallback_route(
            message
        )


    allowed_tools = {
        "read_memory",
        "research_web",
        "reason",
        "save_memory",
        "send_email",
    }


    clean_steps = []


    for step in parsed.get(
        "steps",
        []
    )[:6]:

        if not isinstance(
            step,
            dict
        ):
            continue


        tool = str(
            step.get(
                "tool",
                ""
            )
        ).strip()


        instruction = str(
            step.get(
                "instruction",
                message
            )
        ).strip()


        if tool not in allowed_tools:
            continue


        clean_steps.append(
            {
                "tool":
                    tool,

                "instruction":
                    instruction or message,
            }
        )


    if not clean_steps:

        return fallback_route(
            message
        )


    return {
        "goal":
            str(
                parsed.get(
                    "goal",
                    message
                )
            )[:250],

        "steps":
            clean_steps,

        "router":
            "groq-v2.1.1",
    }


# =========================================================
# REASONING
# =========================================================

def reasoning_step(
    original_request,
    instruction,
    working_context
):

    prompt = f"""
ORIGINAL USER REQUEST:

{original_request}


CURRENT TASK:

{instruction}


AVAILABLE MEMORY AND TOOL RESULTS:

{working_context[:6500] if working_context else "None"}


Create the best useful final answer.

Rules:

Use the research and memory above when relevant.

If comparing products or options,
clearly choose a winner.

Do not claim something was emailed or saved
unless that action actually happened.

Be concise but useful.
"""


    return call_groq(

        system_prompt=(
            "You are Tyler AI, a capable personal "
            "autonomous assistant."
        ),

        user_prompt=
            prompt,

        max_tokens=
            800,

        temperature=
            0.2,
    )


# =========================================================
# MEMORY FROM FINAL ANSWER
# =========================================================

def build_recommendation_memory(
    final_reply,
    original_request
):

    if not final_reply:
        return None


    text = final_reply.strip()


    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


    useful = []


    for line in lines:

        lower = line.lower()

        if any(
            word in lower
            for word in [
                "recommend",
                "best",
                "winner",
                "choice",
                "pick",
            ]
        ):

            useful.append(line)


    if useful:

        memory = " ".join(
            useful[:3]
        )

    else:

        memory = text[:550]


    memory = re.sub(
        r"\s+",
        " ",
        memory
    ).strip()


    if len(memory) > 600:

        memory = memory[:600]


    if memory:

        return (
            "Tyler AI recommendation: "
            + memory
        )


    return None


# =========================================================
# CHAIN EXECUTOR
# =========================================================

def execute_chain(
    message,
    route
):

    results = []

    working_context = ""

    final_reply = ""

    email_result = None

    memory_result = None

    sources = []

    groq_calls = 0


    for index, step in enumerate(
        route["steps"],
        start=1
    ):

        tool = step["tool"]

        instruction = step["instruction"]


        # -------------------------------------------------
        # READ MEMORY
        # -------------------------------------------------

        if tool == "read_memory":

            try:

                memory_text = (
                    compact_memory_context(
                        8
                    )
                )

                result_value = (
                    memory_text
                    or "No relevant saved memory found."
                )

            except Exception as e:

                result_value = (
                    f"Memory read failed: {e}"
                )


            results.append(
                {
                    "step":
                        index,

                    "tool":
                        tool,

                    "result":
                        result_value,
                }
            )


            working_context += (

                f"\n\nSTEP {index} MEMORY:\n"

                f"{result_value}"
            )


        # -------------------------------------------------
        # RESEARCH WEB
        # -------------------------------------------------

        elif tool == "research_web":

            try:

                research = web_search(
                    instruction
                )

                compact = compact_research(
                    research
                )

                sources.extend(
                    research.get(
                        "sources",
                        []
                    )
                )


                results.append(
                    {
                        "step":
                            index,

                        "tool":
                            tool,

                        "result":
                            compact,

                        "sources":
                            research.get(
                                "sources",
                                []
                            ),
                    }
                )


                working_context += (

                    f"\n\nSTEP {index} RESEARCH:\n"

                    f"{compact}"
                )


            except Exception as e:

                error_text = (
                    f"Research failed: {e}"
                )

                results.append(
                    {
                        "step":
                            index,

                        "tool":
                            tool,

                        "result":
                            error_text,
                    }
                )

                working_context += (

                    f"\n\nSTEP {index} RESEARCH ERROR:\n"

                    f"{error_text}"
                )


        # -------------------------------------------------
        # REASON
        # -------------------------------------------------

        elif tool == "reason":

            try:

                final_reply = reasoning_step(
                    message,
                    instruction,
                    working_context
                )

                groq_calls += 1


            except Exception as e:

                if working_context.strip():

                    final_reply = (
                        "I completed the available tool steps, "
                        "but the reasoning model was temporarily "
                        "unavailable.\n\n"
                        + working_context[-4500:]
                    )

                else:

                    final_reply = (
                        "The reasoning model was temporarily "
                        f"unavailable: {e}"
                    )


            results.append(
                {
                    "step":
                        index,

                    "tool":
                        tool,

                    "result":
                        final_reply,
                }
            )


            working_context += (

                f"\n\nSTEP {index} REASONING:\n"

                f"{final_reply}"
            )


        # -------------------------------------------------
        # SAVE MEMORY
        # -------------------------------------------------

        elif tool == "save_memory":

            candidate = (
                build_recommendation_memory(
                    final_reply,
                    message
                )
            )


            if not candidate:

                memory_result = {
                    "saved":
                        False,

                    "reason":
                        "There was no final result to save."
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

                    database_result = save_memory(
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
                            database_result,
                    }


                except Exception as e:

                    memory_result = {
                        "saved":
                            False,

                        "reason":
                            str(e),
                    }


            results.append(
                {
                    "step":
                        index,

                    "tool":
                        tool,

                    "result":
                        memory_result,
                }
            )


        # -------------------------------------------------
        # SEND EMAIL
        # -------------------------------------------------

        elif tool == "send_email":

            body = (
                final_reply
                or working_context
                or message
            )


            try:

                email_result = send_email(
                    body,
                    "Tyler AI Results"
                )


            except Exception as e:

                email_result = {
                    "sent":
                        False,

                    "error":
                        str(e),
                }


            results.append(
                {
                    "step":
                        index,

                    "tool":
                        tool,

                    "result":
                        email_result,
                }
            )


    # =====================================================
    # FINAL ANSWER IF ROUTER DID NOT ADD REASON
    # =====================================================

    if not final_reply:

        try:

            final_reply = reasoning_step(
                message,
                "Answer the user's request.",
                working_context
            )

            groq_calls += 1


        except Exception as e:

            if working_context:

                final_reply = working_context[-4500:]

            else:

                final_reply = (
                    f"Unable to complete reasoning: {e}"
                )


    return {
        "reply":
            final_reply,

        "results":
            results,

        "email_result":
            email_result,

        "memory_result":
            memory_result,

        "sources":
            sources,

        "execution_groq_calls":
            groq_calls,
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
                "2.1.1-resilient-chain",

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
                "2.1.1-resilient-chain",
        }
    )


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
    # DIRECT MEMORY SAVE
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


            category = (
                guess_memory_category(
                    memory
                )
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
    # ROUTE
    # =====================================================

    router_calls = 0


    try:

        route = tool_router(
            message
        )

        router_calls = 1


    except Exception as e:

        print(
            "Router error, using local fallback:",
            str(e)
        )

        route = fallback_route(
            message
        )


    # =====================================================
    # EXECUTE
    # =====================================================

    try:

        execution = execute_chain(
            message,
            route
        )


    except Exception as e:

        return jsonify(
            {
                "success":
                    False,

                "type":
                    "chain_execution",

                "version":
                    "2.1.1-resilient-chain",

                "route":
                    route,

                "error":
                    str(e),

                "router_calls":
                    router_calls,
            }
        ), 500


    return jsonify(
        {
            "success":
                True,

            "type":
                "chain_execution",

            "version":
                "2.1.1-resilient-chain",

            "goal":
                route.get(
                    "goal",
                    message
                ),

            "route":
                route,

            "execution":
                execution[
                    "results"
                ],

            "reply":
                execution[
                    "reply"
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

            "router_calls":
                router_calls,

            "execution_groq_calls":
                execution[
                    "execution_groq_calls"
                ],

            "total_groq_calls":
                router_calls
                + execution[
                    "execution_groq_calls"
                ],
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
