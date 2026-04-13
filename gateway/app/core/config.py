import os

USER_API_BASE = os.getenv("USER_API_BASE")
TODO_API_BASE = os.getenv("TODO_API_BASE")

if not USER_API_BASE:
    raise RuntimeError("USER_API_BASE is not set")

if not TODO_API_BASE:
    raise RuntimeError("TODO_API_BASE is not set")
