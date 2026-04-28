import time
import logging
from dataclasses import dataclass, field
from typing import List
from app.config import settings

logger = logging.getLogger(__name__)
Message = dict

@dataclass
class Session:
    session_id: str
    messages: List[Message] = field(default_factory=list)
    last_access: float = field(default_factory=time.time)

    def touch(self):
        self.last_access = time.time()

    def is_expired(self, ttl: int) -> bool:
        return (time.time() - self.last_access) > ttl

class SessionManager:
    def __init__(self):
        self._sessions = {}
        self._max_history = settings.MAX_HISTORY_MESSAGES
        self._ttl = settings.SESSION_TTL_SECONDS

    def get_history(self, session_id: str) -> List[Message]:
        self._evict_expired()
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id)
            return []
        session = self._sessions[session_id]
        if session.is_expired(self._ttl):
            del self._sessions[session_id]
            self._sessions[session_id] = Session(session_id=session_id)
            return []
        session.touch()
        return list(session.messages)

    def add_turn(self, session_id: str, user_msg: str, assistant_msg: str) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id=session_id)
        session = self._sessions[session_id]
        session.messages.append({"role": "user", "content": user_msg})
        session.messages.append({"role": "assistant", "content": assistant_msg})
        session.touch()
        if len(session.messages) > self._max_history * 2:
            session.messages = session.messages[-(self._max_history * 2):]

    def _evict_expired(self):
        expired = [sid for sid, s in self._sessions.items() if s.is_expired(self._ttl)]
        for sid in expired:
            del self._sessions[sid]

    @property
    def active_sessions(self) -> int:
        self._evict_expired()
        return len(self._sessions)
