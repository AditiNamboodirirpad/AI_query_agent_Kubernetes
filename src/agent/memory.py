# Stores conversation history per session so the agent remembers previous questions
import threading
from collections import defaultdict
from langchain_core.messages import AIMessage, HumanMessage

_store = defaultdict(list)
_lock = threading.Lock()  # needed if multiple requests come in at the same time
MAX_MESSAGES = 20  # keep the last 10 question/answer pairs


def get_history(session_id):
    with _lock:
        return list(_store[session_id])


def add_exchange(session_id, user_question, ai_answer):
    with _lock:
        _store[session_id].append(HumanMessage(content=user_question))
        _store[session_id].append(AIMessage(content=ai_answer))
        # Trim old messages so memory doesn't grow forever
        _store[session_id] = _store[session_id][-MAX_MESSAGES:]


def clear_session(session_id):
    with _lock:
        _store.pop(session_id, None)


def list_sessions():
    with _lock:
        return list(_store.keys())
