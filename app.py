import streamlit as st
from openai import OpenAI
from typing import List, Dict

st.set_page_config(page_title="Role-based Chatbot", page_icon="🤖", layout="centered")

# ---------- Roles ----------
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
            "You are a constructive film & writing critic. "
            "Point out 3 strengths and 3 concrete improvements with references to craft."
        ),
        "guardrails": (
            "- No insults.\n- Cite film theory terms sparingly."
        ),
    },
    "coder": {
        "name": "Coder",
        "system": (
            "You are a senior full-stack engineer. "
            "Return code-first answers with runnable snippets."
        ),
        "guardrails": (
            "- Prefer Node/TS or Python.\n- Include command lines when needed."
        ),
    },
}

# ---------- Session State ----------
if "roles" not in st.session_state:
    st.session_state.roles = DEFAULT_ROLES.copy()

if "history_by_role" not in st.session_state:
    st.session_state.history_by_role = {key: [] for key in st.session_state.roles.keys()}

# ---------- Sidebar ----------
st.sidebar.title("⚙️ Settings")
role_key = st.sidebar.selectbox(
    "Choose a role",
    options=list(st.session_state.roles.keys()),
    format_func=lambda k: f"{st.session_state.roles[k]['name']} ({k})",
)

with st.sidebar.expander("Edit role prompts"):
    name = st.text_input("Display name", value=st.session_state.roles[role_key]["name"])
    system = st.text_area("System prompt", value=st.session_state.roles[role_key]["system"], height=140)
    guard = st.text_area("Guardrails", value=st.session_state.roles[role_key]["guardrails"], height=120)
    if st.button("Save role", use_container_width=True):
        st.session_state.roles[role_key]["name"] = name
        st.session_state.roles[role_key]["system"] = system
        st.session_state.roles[role_key]["guardrails"] = guard
        st.success("Role updated.")

if st.sidebar.button("Clear history for this role"):
    st.session_state.history_by_role[role_key] = []
    st.sidebar.success("History cleared.")

model = st.sidebar.text_input("Model", value="gpt-5-chat")
temperature = st.sidebar.slider("Temperature", 0.0, 1.2, 0.7, 0.1)

# ---------- API Key ----------
st.sidebar.subheader("🔑 OpenAI API Key")

api_key_input = st.sidebar.text_input(
    "Enter your OpenAI API Key",
    type="password",
    placeholder="sk-...",
    help="You can create and copy your API key from https://platform.openai.com/account/api-keys"
)

# If user does not input a key, try to load from Streamlit Secrets
OPENAI_API_KEY = api_key_input.strip() if api_key_input else st.secrets.get("OPENAI_API_KEY", None)

if not OPENAI_API_KEY:
    st.warning("⚠️ Please enter your OpenAI API Key on the left sidebar.", icon="⚠️")
else:
    st.sidebar.success("✅ API Key loaded successfully!")


# ---------- Title ----------
st.title("🤖 Role-based Chatbot")
st.caption("Streamlit + OpenAI · per-role prompts and history")

# ---------- Chat UI ----------
history: List[Dict[str, str]] = st.session_state.history_by_role.get(role_key, [])

for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input(f"Talk to {st.session_state.roles[role_key]['name']}…")

def build_messages(role_def: Dict[str, str], past: List[Dict[str, str]], user_message: str):
    sys_content = "\n\n".join([
        f"ROLE: {role_def['name']}",
        role_def["system"],
        f"POLICY:\n{role_def['guardrails']}",
        "ALWAYS: If user asks for unsafe or restricted content, refuse and suggest safe alternatives."
    ])
    messages = [{"role": "system", "content": sys_content}]
    messages.extend(past)
    messages.append({"role": "user", "content": user_message})
    return messages

if user_input:
    # echo user
    history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # guard key
    if not OPENAI_API_KEY:
        with st.chat_message("assistant"):
            st.error("No API key configured. Set OPENAI_API_KEY in Streamlit Secrets.")
    else:
        client = OpenAI(api_key=OPENAI_API_KEY)
        role_def = st.session_state.roles[role_key]
        messages = build_messages(role_def, history[:-1], user_input)

        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=messages,
            )
            reply = resp.choices[0].message.content or ""
        except Exception as e:
            reply = f"Error: {e}"

        history.append({"role": "assistant", "content": reply})
        st.session_state.history_by_role[role_key] = history

        with st.chat_message("assistant"):
            st.markdown(reply)
