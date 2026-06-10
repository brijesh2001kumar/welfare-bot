# utils/session.py

class UserSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = "idle"
        self.lang = "en"
        self.eligibility_answers = {}
        self.eligibility_step = 0
        self.eligible_schemes = []
        self.chat_history = []  # format: [{"role": "user", "content": "..."}]

    def add_message(self, role: str, content: str):
        self.chat_history.append({"role": role, "content": content})


class SessionStore:
    def __init__(self):
        self._store = {}

    def get_or_create(self, session_id: str) -> UserSession:
        if session_id not in self._store:
            self._store[session_id] = UserSession(session_id)
        return self._store[session_id]

    def reset(self, session_id: str):
        if session_id in self._store:
            self._store[session_id] = UserSession(session_id)


session_store = SessionStore()