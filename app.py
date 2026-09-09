import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==================================================
# ENVIRONMENT VARIABLES
# ==================================================

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
TYLER_API_KEY = os.environ.get("TYLER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
TYLER_DEFAULT_EMAIL = os.environ.get("TYLER_DEFAULT_EMAIL")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


# ==================================================
# SECURITY
# ==================================================

def authorized():
    provided_key = request.headers.get("X-Tyler-Key")

    return bool(
        TYLER_API_KEY
        and provided_key
        and provided_key == TYLER_API_KEY
    )


# ==================================================
# GROQ
# ==================================================

def call_groq(messages, temperature=0.3):

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-oss-20b",
            "temperature": temperature,
            "messages": messages
        },
        timeout=90
    )

    result = response.json()

    if not response.ok:
        raise RuntimeError(str(result))

    return result["choices"][0]["message"]["content"].strip()


# ==================================================
# SUPABASE
# ==================================================

def supabase_headers():

    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_KEY is not configured")

    return {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }


def save_memory(memory_text, category="general", importance=5):

    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not configured")

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers={
            **supabase_headers(),
            "Prefer": "return=representation"
        },
        json={
            "memories": memory_text,
            "category": category,
            "importance": importance
        },
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase save failed: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


def update_memory(
    memory_id,
    memory_text,
    category="general",
    importance=5
):

    response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers={
            **supabase_headers(),
            "Prefer": "return=representation"
        },
        params={
            "id": f"eq.{memory_id}"
        },
        json={
            "memories": memory_text,
            "category": category,
            "importance": importance
        },
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase update failed: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


def get_memories(limit=50):

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/memories",
        headers=supabase_headers(),
        params={
            "select":
                "id,created_at,memories,category,importance",
            "order":
                "importance.desc,created_at.desc",
            "limit":
                limit
        },
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            f"Supabase read failed: "
            f"{response.status_code} {response.text}"
        )

    return response.json()


def memory_context(limit=12):

    memories = get_memories(limit)

    if not memories:
        return "No saved long-term memories yet."

    lines = []

    for item in memories:

        lines.append(
            f"- ID {item.get('id')} "
            f"[{item.get('category', 'general')}] "
            f"{item.get('memories', '')} "
            f"(importance {item.get('importance', 5)})"
        )

    return "\n".join(lines)


# ==================================================
# EXPLICIT MEMORY
# ==================================================

def wants_to_remember(message):

    text = message.lower()

    triggers = [
        "remember that",
        "remember this",
        "save this",
        "save that",
        "add this to memory",
        "store this",
        "don't forget"
    ]

    return any(
        trigger in text
        for trigger in triggers
    )


def extract_memory(user_message):

    prompt = f"""
The user explicitly asked Tyler AI to remember something.

User message:
{user_message}

Extract the durable useful information.

Return ONLY valid JSON:

{{
  "memory": "concise durable memory",
  "category": "preference, project, person, task, goal, career, or general",
  "importance": 5
}}

Importance must be 1 through 10.

Never store:
- passwords
- API keys
- authentication tokens
- credit card numbers
- banking credentials
- security secrets
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content":
                    "You extract safe, useful long-term memories."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    try:

        result = json.loads(raw)

        importance = int(
            result.get("importance", 5)
        )

        importance = max(
            1,
            min(10, importance)
        )

        return {
            "memory":
                result.get("memory", user_message),
            "category":
                result.get("category", "general"),
            "importance":
                importance
        }

    except Exception:

        return {
            "memory": user_message,
            "category": "general",
            "importance": 5
        }


# ==================================================
# AUTOMATIC MEMORY
# ==================================================

def analyze_for_automatic_memory(user_message):

    prompt = f"""
Determine whether this message contains durable
information worth saving in Tyler AI long-term memory.

MESSAGE:
{user_message}

Good memory candidates include:
- stable preferences
- long-term goals
- important projects
- career direction
- recurring workflows
- durable decisions
- ongoing plans

Do NOT save:
- casual questions
- temporary requests
- news/search requests
- email instructions
- passwords
- API keys
- tokens
- banking credentials
- authentication information
- private secrets

Return ONLY JSON.

No memory:

{{
  "save": false
}}

Save memory:

{{
  "save": true,
  "memory": "concise durable fact",
  "category": "preference, project, person, task, goal, career, or general",
  "importance": 5
}}
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content":
                    "You are Tyler AI's selective memory manager."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    try:

        result = json.loads(raw)

        if not result.get("save"):
            return None

        memory_text = str(
            result.get("memory", "")
        ).strip()

        if not memory_text:
            return None

        importance = int(
            result.get("importance", 5)
        )

        importance = max(
            1,
            min(10, importance)
        )

        return {
            "memory":
                memory_text,
            "category":
                result.get("category", "general"),
            "importance":
                importance
        }

    except Exception:
        return None


# ==================================================
# MEMORY CREATE / UPDATE / SKIP
# ==================================================

def decide_memory_action(candidate):

    existing = get_memories(50)

    if not existing:

        return {
            "action": "create",
            **candidate
        }

    existing_text = ""

    for item in existing:

        existing_text += f"""
ID: {item.get("id")}
CATEGORY: {item.get("category")}
IMPORTANCE: {item.get("importance")}
MEMORY: {item.get("memories")}
"""

    prompt = f"""
NEW CANDIDATE MEMORY:

Memory:
{candidate["memory"]}

Category:
{candidate["category"]}

Importance:
{candidate["importance"]}

EXISTING MEMORIES:

{existing_text}

Choose one:

CREATE
Use if this is genuinely new information.

UPDATE
Use if an existing memory covers the same subject
and the new information improves or changes it.

SKIP
Use if the information is already adequately stored.

Return ONLY JSON.

CREATE:

{{
  "action": "create",
  "memory": "final memory",
  "category": "category",
  "importance": 5
}}

UPDATE:

{{
  "action": "update",
  "id": 2,
  "memory": "merged final memory",
  "category": "category",
  "importance": 5
}}

SKIP:

{{
  "action": "skip",
  "reason": "already covered"
}}

Never overwrite an unrelated memory.
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content":
                    "You safely manage and deduplicate AI memory."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    try:

        result = json.loads(raw)

        action = result.get(
            "action",
            "create"
        )

        if action == "skip":

            return {
                "action": "skip",
                "reason":
                    result.get(
                        "reason",
                        "already covered"
                    )
            }

        if action == "update":

            memory_id = result.get("id")

            valid_ids = {
                item.get("id")
                for item in existing
            }

            if memory_id not in valid_ids:

                return {
                    "action": "create",
                    **candidate
                }

            importance = int(
                result.get(
                    "importance",
                    candidate["importance"]
                )
            )

            importance = max(
                1,
                min(10, importance)
            )

            return {
                "action": "update",
                "id": memory_id,
                "memory":
                    result.get(
                        "memory",
                        candidate["memory"]
                    ),
                "category":
                    result.get(
                        "category",
                        candidate["category"]
                    ),
                "importance":
                    importance
            }

        importance = int(
            result.get(
                "importance",
                candidate["importance"]
            )
        )

        importance = max(
            1,
            min(10, importance)
        )

        return {
            "action": "create",
            "memory":
                result.get(
                    "memory",
                    candidate["memory"]
                ),
            "category":
                result.get(
                    "category",
                    candidate["category"]
                ),
            "importance":
                importance
        }

    except Exception:

        return {
            "action": "create",
            **candidate
        }


def process_memory_candidate(candidate):

    decision = decide_memory_action(
        candidate
    )

    if decision["action"] == "skip":

        return {
            "saved": False,
            "action": "skip",
            "reason":
                decision.get(
                    "reason",
                    "already covered"
                )
        }

    if decision["action"] == "update":

        update_memory(
            decision["id"],
            decision["memory"],
            decision["category"],
            decision["importance"]
        )

        return {
            "saved": True,
            "action": "update",
            "id":
                decision["id"],
            "memory":
                decision["memory"],
            "category":
                decision["category"],
            "importance":
                decision["importance"]
        }

    save_memory(
        decision["memory"],
        decision["category"],
        decision["importance"]
    )

    return {
        "saved": True,
        "action": "create",
        "memory":
            decision["memory"],
        "category":
            decision["category"],
        "importance":
            decision["importance"]
    }


def maybe_save_automatic_memory(user_message):

    try:

        candidate = analyze_for_automatic_memory(
            user_message
        )

        if not candidate:
            return None

        return process_memory_candidate(
            candidate
        )

    except Exception as e:

        print(
            "Automatic memory error:",
            str(e)
        )

        return None


# ==================================================
# TAVILY SEARCH
# ==================================================

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
                "application/json"
        },
        json={
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 5
        },
        timeout=60
    )

    result = response.json()

    if not response.ok:
        raise RuntimeError(str(result))

    sources = []

    for item in result.get(
        "results",
        []
    ):

        sources.append({
            "title":
                item.get("title"),
            "url":
                item.get("url"),
            "content":
                item.get("content")
        })

    return {
        "answer":
            result.get("answer", ""),
        "sources":
            sources
    }


def summarize_research(
    user_request,
    research
):

    source_text = ""

    for index, source in enumerate(
        research["sources"],
        start=1
    ):

        source_text += f"""
SOURCE {index}

TITLE:
{source.get("title")}

URL:
{source.get("url")}

CONTENT:
{source.get("content")}
"""

    prompt = f"""
USER GOAL:

{user_request}

LIVE SEARCH RESULT:

{research["answer"]}

SOURCES:

{source_text}

Produce a useful research result.

Rules:
- Use the supplied sources.
- Do not invent information.
- Explain uncertainty where appropriate.
- Include useful URLs when relevant.
"""

    return call_groq(
        [
            {
                "role": "system",
                "content":
                    "You are Tyler AI's research analyst."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )


# ==================================================
# N8N / EMAIL
# ==================================================

def send_to_n8n(payload):

    if not N8N_WEBHOOK_URL:

        return {
            "success": False,
            "error":
                "N8N_WEBHOOK_URL is not configured"
        }, 500

    try:

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=60
        )

        return {
            "success":
                response.ok,
            "status_code":
                response.status_code,
            "n8n_response":
                response.text
        }, response.status_code

    except requests.RequestException as e:

        return {
            "success": False,
            "error": str(e)
        }, 502


def create_email(subject_goal, content):

    prompt = f"""
Create an email from the following material.

GOAL:
{subject_goal}

CONTENT:
{content}

Return ONLY valid JSON:

{{
  "subject": "short useful subject",
  "message": "complete email body"
}}
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content":
                    "You create concise professional emails."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    try:

        result = json.loads(raw)

        return {
            "subject":
                result.get(
                    "subject",
                    "Message from Tyler AI"
                ),
            "message":
                result.get(
                    "message",
                    content
                )
        }

    except Exception:

        return {
            "subject":
                "Message from Tyler AI",
            "message":
                content
        }


def send_email(subject_goal, content):

    if not TYLER_DEFAULT_EMAIL:

        raise RuntimeError(
            "TYLER_DEFAULT_EMAIL is not configured"
        )

    email = create_email(
        subject_goal,
        content
    )

    payload = {
        "action": "email",
        "data": {
            "to":
                TYLER_DEFAULT_EMAIL,
            "subject":
                email["subject"],
            "message":
                email["message"]
        }
    }

    result, status_code = send_to_n8n(
        payload
    )

    if not result.get("success"):

        raise RuntimeError(
            f"Email action failed: {result}"
        )

    return {
        "sent": True,
        "to":
            TYLER_DEFAULT_EMAIL,
        "subject":
            email["subject"]
    }


# ==================================================
# TYLER PLANNER
# ==================================================

def create_plan(user_message, memories):

    prompt = f"""
You are the planning system for Tyler AI.

USER REQUEST:

{user_message}

RELEVANT LONG-TERM MEMORY:

{memories}

Tyler currently has these executable tools:

1. research_web
   Searches the live internet.

2. reason
   Analyzes, compares, ranks, summarizes, or decides
   using available information.

3. send_email
   Sends an email to the user's configured address.

Your job is to create the smallest useful plan required
to satisfy the user's request.

Return ONLY valid JSON.

Format:

{{
  "goal": "short description of the user's goal",
  "steps": [
    {{
      "tool": "research_web",
      "instruction": "specific instruction"
    }},
    {{
      "tool": "reason",
      "instruction": "specific analysis to perform"
    }},
    {{
      "tool": "send_email",
      "instruction": "what should be emailed"
    }}
  ]
}}

Rules:

- Use only the listed tools.
- Do not invent tools.
- Do not add email unless the user asked to email something.
- Use research_web when current internet information is needed.
- Use reason for analysis, rankings, synthesis, comparisons,
  recommendations, or normal conversational responses.
- A simple question may need only one reason step.
- A complex request may require multiple steps.
- Maximum 6 steps.
"""

    raw = call_groq(
        [
            {
                "role": "system",
                "content":
                    "You are Tyler AI Planner. "
                    "Create executable, minimal plans."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    try:

        plan = json.loads(raw)

        steps = plan.get(
            "steps",
            []
        )

        allowed_tools = {
            "research_web",
            "reason",
            "send_email"
        }

        cleaned_steps = []

        for step in steps[:6]:

            tool = step.get("tool")

            if tool not in allowed_tools:
                continue

            cleaned_steps.append({
                "tool":
                    tool,
                "instruction":
                    str(
                        step.get(
                            "instruction",
                            ""
                        )
                    )
            })

        if not cleaned_steps:

            cleaned_steps = [
                {
                    "tool": "reason",
                    "instruction":
                        user_message
                }
            ]

        return {
            "goal":
                plan.get(
                    "goal",
                    user_message
                ),
            "steps":
                cleaned_steps
        }

    except Exception:

        return {
            "goal":
                user_message,
            "steps": [
                {
                    "tool": "reason",
                    "instruction":
                        user_message
                }
            ]
        }


# ==================================================
# REASONING TOOL
# ==================================================

def reasoning_step(
    user_message,
    instruction,
    memory_text,
    working_context
):

    prompt = f"""
ORIGINAL USER REQUEST:

{user_message}

CURRENT STEP:

{instruction}

LONG-TERM MEMORY:

{memory_text}

RESULTS FROM PREVIOUS STEPS:

{working_context}

Perform the requested reasoning step.

Be practical and concrete.
Do not claim you performed external actions.
"""

    return call_groq(
        [
            {
                "role": "system",
                "content":
                    "You are Tyler AI's reasoning engine."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.25
    )


# ==================================================
# PLAN EXECUTOR
# ==================================================

def execute_plan(
    user_message,
    plan,
    memory_text
):

    results = []

    working_context = ""

    for number, step in enumerate(
        plan["steps"],
        start=1
    ):

        tool = step["tool"]

        instruction = step["instruction"]

        # ------------------------------------------
        # WEB RESEARCH
        # ------------------------------------------

        if tool == "research_web":

            research = web_search(
                instruction
            )

            research_summary = summarize_research(
                instruction,
                research
            )

            step_result = {
                "step":
                    number,
                "tool":
                    tool,
                "instruction":
                    instruction,
                "result":
                    research_summary,
                "sources":
                    research["sources"]
            }

            results.append(
                step_result
            )

            working_context += f"""

STEP {number} RESEARCH RESULT:

{research_summary}
"""

        # ------------------------------------------
        # REASON
        # ------------------------------------------

        elif tool == "reason":

            reasoning = reasoning_step(
                user_message,
                instruction,
                memory_text,
                working_context
            )

            step_result = {
                "step":
                    number,
                "tool":
                    tool,
                "instruction":
                    instruction,
                "result":
                    reasoning
            }

            results.append(
                step_result
            )

            working_context += f"""

STEP {number} REASONING RESULT:

{reasoning}
"""

        # ------------------------------------------
        # EMAIL
        # ------------------------------------------

        elif tool == "send_email":

            if not working_context.strip():

                content = user_message

            else:

                content = working_context

            email_result = send_email(
                instruction,
                content
            )

            step_result = {
                "step":
                    number,
                "tool":
                    tool,
                "instruction":
                    instruction,
                "result":
                    email_result
            }

            results.append(
                step_result
            )

            working_context += f"""

STEP {number} EMAIL RESULT:

Email sent to {email_result["to"]}
Subject: {email_result["subject"]}
"""

    return {
        "results":
            results,
        "working_context":
            working_context
    }


# ==================================================
# FINAL RESPONSE
# ==================================================

def create_final_response(
    user_message,
    plan,
    execution
):

    prompt = f"""
USER REQUEST:

{user_message}

PLAN:

{json.dumps(plan, indent=2)}

EXECUTION RESULTS:

{execution["working_context"]}

Give the user the final answer.

Rules:

- Clearly answer the original request.
- Mention completed external actions only if they
  actually appear in the execution results.
- If research was performed, summarize the useful findings.
- If email was sent, say that it was sent.
- Do not expose internal planning prompts.
- Be concise but useful.
"""

    return call_groq(
        [
            {
                "role": "system",
                "content":
                    "You are Tyler AI. "
                    "Report the outcome of completed work."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.25
    )


# ==================================================
# HOME
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "name":
            "Tyler AI",

        "status":
            "online",

        "groq_connected":
            bool(GROQ_API_KEY),

        "tavily_connected":
            bool(TAVILY_API_KEY),

        "n8n_connected":
            bool(N8N_WEBHOOK_URL),

        "memory_connected":
            bool(
                SUPABASE_URL
                and SUPABASE_KEY
            ),

        "planner_enabled":
            True,

        "secured":
            bool(TYLER_API_KEY),

        "tools": [
            "planner",
            "reason",
            "web_research",
            "email",
            "long_term_memory",
            "automatic_memory",
            "memory_merge_update"
        ]
    })


# ==================================================
# HEALTH
# ==================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "healthy"
    })


# ==================================================
# MEMORIES
# ==================================================

@app.route("/memories", methods=["GET"])
def memories_route():

    if not authorized():

        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    try:

        memories = get_memories(50)

        return jsonify({
            "success": True,
            "count":
                len(memories),
            "memories":
                memories
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================================================
# CHAT
# ==================================================

@app.route("/chat", methods=["POST"])
def chat():

    if not authorized():

        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    user_message = data.get(
        "message"
    )

    if not user_message:

        return jsonify({
            "success": False,
            "error": "Missing message"
        }), 400


    # ----------------------------------------------
    # EXPLICIT MEMORY
    # ----------------------------------------------

    if wants_to_remember(
        user_message
    ):

        try:

            candidate = extract_memory(
                user_message
            )

            memory_result = (
                process_memory_candidate(
                    candidate
                )
            )

            return jsonify({
                "success": True,
                "type": "memory",
                "memory_result":
                    memory_result
            })

        except Exception as e:

            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ----------------------------------------------
    # AUTOMATIC MEMORY
    # ----------------------------------------------

    automatic_memory = (
        maybe_save_automatic_memory(
            user_message
        )
    )


    # ----------------------------------------------
    # GET MEMORY CONTEXT
    # ----------------------------------------------

    try:

        memory_text = memory_context(
            12
        )

    except Exception:

        memory_text = (
            "Long-term memory temporarily unavailable."
        )


    # ----------------------------------------------
    # CREATE PLAN
    # ----------------------------------------------

    try:

        plan = create_plan(
            user_message,
            memory_text
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "error":
                f"Planner failed: {str(e)}"
        }), 500


    # ----------------------------------------------
    # EXECUTE PLAN
    # ----------------------------------------------

    try:

        execution = execute_plan(
            user_message,
            plan,
            memory_text
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "plan":
                plan,
            "error":
                f"Plan execution failed: {str(e)}"
        }), 500


    # ----------------------------------------------
    # FINAL RESPONSE
    # ----------------------------------------------

    try:

        final_reply = create_final_response(
            user_message,
            plan,
            execution
        )

    except Exception:

        final_reply = (
            execution["working_context"]
        )


    return jsonify({
        "success":
            True,

        "type":
            "planned_execution",

        "goal":
            plan["goal"],

        "plan":
            plan["steps"],

        "execution":
            execution["results"],

        "reply":
            final_reply,

        "automatic_memory":
            automatic_memory
    })


# ==================================================
# DIRECT N8N WEBHOOK
# ==================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    if not authorized():

        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    if not data.get("action"):

        return jsonify({
            "success": False,
            "error": "Missing action"
        }), 400

    result, status_code = send_to_n8n(
        data
    )

    return jsonify(
        result
    ), status_code


# ==================================================
# START SERVER
# ==================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
        )
