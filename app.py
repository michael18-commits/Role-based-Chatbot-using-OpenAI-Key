# app.py  — Role-based Chatbot (Streamlit + OpenAI)
import sys
import streamlit as st
from typing import List, Dict

# Some environments default to ASCII. Make stdout UTF-8 to avoid encoding errors.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------- Page config ----------------
st.set_page_config(page_title="Role-based Chatbot", layout="centered")

# ---------------- Roles ----------------
DEFAULT_ROLES: Dict[str, Dict[str, str]] = {
    "mentor": {
        "name": "Mentor",
        "system": (
            "You are a warm, practical career mentor. "
            "Give short, actionable advice with numbered steps and one example."
        ),
        "guardrails": (
            "- Be concise (under 180 words).\n"
            "- No medical/financial/legal advice beyond high-level tips."
        ),
    },
    "critic": {
        "name": "Critic",
        "system": (
            "You are a constructive film and writing critic. "
            "Point out 3 strengths and 3 concrete improvements with references to craft."
        ),
        "guardrails": "- No insults.\n- Use theory terms sparingly.",
    },
    "coder": {
        "name": "Coder",
        "system": (
            "You are a senior full-stack engineer. "
            "Return code-first answers with runnable snippets."
        ),
        "guardrails": "- Prefer Node/TS or Python.\n- Include command lines when needed.",
    },
}

# ---------------- Session state ----------------
if "roles" not in st.session_state:
    st.session_state.roles = DEFAULT_ROLES.copy()

if "history_by_role" not in st.session_state:
    st.session_state.history_by_role = {k: [] for k in st.session_state.roles.keys()}

# ---------------- Sidebar: role + prompts ----------------
st.sidebar.title("Settings")
role_key = st.sidebar.selectbox(
    "Choose a role",
    options=list(st.session_state.roles.keys()),
    format_func=lambda k: f"{st.session_state.roles[k]['name']} ({k})",
)

with st.sidebar.expander("Edit role prompts"):
    name = st.text_input("Display name", value=st.session_state.roles[role_key]["name"])
    system = st.text_area("System prompt", value=st.session_state.roles[role_key]["system"], height=140)
    guard = st.text_area("Guardrails", value=st.session_state.roles[role_key]["guardrails"], height=120)
    if st.button("Save role"):
        st.session_state.roles[role_key]["name"] = name
        st.session_state.roles[role_key]["system"] = system
        st.session_state.roles[role_key]["guardrails"] = guard
        st.success("Role updated.")

if st.sidebar.button("Clear history for this role"):
    st.session_state.history_by_role[role_key] = []
    st.sidebar.success("History cleared.")

# ---------------- Model picker ----------------
st.sidebar.markdown("### Model")
AVAILABLE_MODELS = [
    "gpt-4o-mini",  # safe default
    "gpt-4o",
]
model = st.sidebar.selectbox("Choose a model", options=AVAILABLE_MODELS, index=0)
temperature = st.sidebar.slider("Temperature", 0.0, 1.2, 0.7, 0.1)

# ---------------- API key + client ----------------
st.sidebar.subheader("OpenAI API Key")
api_key_input = st.sidebar.text_input(
    "Enter your OpenAI API Key",
    type="password",
    placeholder="sk-...",
    help="Create and copy your key from https://platform.openai.com/account/api-keys",
)

OPENAI_API_KEY = api_key_input.strip() if api_key_input else st.secrets.get("OPENAI_API_KEY", None)

from openai import OpenAI
client = None
if not OPENAI_API_KEY:
    st.warning("Please enter your OpenAI API Key on the left sidebar.")
else:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        st.sidebar.info("API Key loaded successfully.")
    except Exception as e:
        st.sidebar.error(f"Failed to initialize OpenAI client: {e}")

# ---------------- UI header ----------------
st.title("Role-based Chatbot")
st.caption("Streamlit + OpenAI · per-role prompts and history")

# ---------------- History rendering ----------------
history: List[Dict[str, str]] = st.session_state.history_by_role.get(role_key, [])
for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- Helper ----------------
def build_messages(role_def: Dict[str, str], past: List[Dict[str, str]], user_message: str):
    sys_content = "\n\n".join([
        f"ROLE: {role_def['name']}",
        role_def["system"],
        f"POLICY:\n{role_def['guardrails']}",
        "ALWAYS: If the user asks for unsafe or restricted content, refuse and suggest safe alternatives."
    ])
    messages = [{"role": "system", "content": sys_content}]
    messages.extend(past)
    messages.append({"role": "user", "content": user_message})
    return messages

# ---------------- Chat input ----------------
user_input = st.chat_input(f"Talk to {st.session_state.roles[role_key]['name']}...")

if user_input:
    # Append user message
    history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build messages
    role_def = st.session_state.roles[role_key]
    messages = build_messages(role_def, history[:-1], user_input)

    # If client is not ready
    if client is None:
        reply = "No API client available. Please enter a valid OpenAI API Key in the sidebar."
    else:
        # Call OpenAI with fallback when model not available
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=messages,
            )
            reply = resp.choices[0].message.content or ""
        except Exception as e:
            err_msg = str(e)
            if "model_not_found" in err_msg or "does not exist" in err_msg:
                try:
                    fallback_model = "gpt-4o-mini"
                    resp = client.chat.completions.create(
                        model=fallback_model,
                        temperature=temperature,
                        messages=messages,
                    )
                    reply = resp.choices[0].message.content or ""
                    st.sidebar.warning(f"Selected model not available. Falling back to {fallback_model}.")
                except Exception as e2:
                    reply = f"Error: {e2}"
            else:
                reply = f"Error: {e}"

    # Append assistant reply
    history.append({"role": "assistant", "content": reply})
    st.session_state.history_by_role[role_key] = history

    with st.chat_message("assistant"):
        st.markdown(reply)
