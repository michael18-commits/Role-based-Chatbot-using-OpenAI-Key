# Role-based Chatbot (Streamlit + OpenAI)

A simple role-based chatbot you can deploy on **Streamlit Cloud** from **GitHub**.

## ✨ Features
- Role presets (Mentor / Critic / Coder) with editable system prompts
- Per-role chat history
- Uses **OpenAI API Key** via `st.secrets` (never hard-code your key)

## 🗂 Structure
```
.
├─ app.py
├─ requirements.txt
└─ .streamlit/
   └─ secrets.toml   # (optional for local dev only; on Streamlit set in dashboard)
```

## 🚀 Local Run
1) Create `.streamlit/secrets.toml` (for local use only):
```toml
OPENAI_API_KEY = "sk-your_key_here"
```

2) Install & run:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Deploy to Streamlit Cloud (via GitHub)
1) Push this folder to a new GitHub repo (e.g., `rolebot-streamlit`).
2) On https://share.streamlit.io/ create a new app:
   - Repo: your `rolebot-streamlit`
   - Branch: `main` (or the branch you pushed)
   - Main file path: `app.py`
3) In the Streamlit app's **Settings → Secrets**, add:
```
OPENAI_API_KEY = "sk-your_key_here"
```
4) Deploy. Enjoy!

## 🧠 Notes
- The API key is **only** read from `st.secrets["OPENAI_API_KEY"]`.
- For simplicity we use Chat Completions API with `gpt-5-chat`.
- You can add more roles or change schemas.
