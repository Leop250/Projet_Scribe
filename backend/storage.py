from models import Recap

_store: dict[str, Recap] = {}


def save(recap: Recap) -> None:
    _store[recap.id] = recap


def get(recap_id: str) -> Recap | None:
    return _store.get(recap_id)
