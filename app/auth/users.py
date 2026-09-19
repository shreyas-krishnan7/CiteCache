"""
User accounts in MongoDB. One collection, `users`:

    {_id, username (unique, lowercase), password_hash (bcrypt), created_at}
"""
from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

import bcrypt
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError

from app.config import settings


class UsernameTaken(Exception):
    pass


class AuthStoreUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def users_collection():
    if not settings.mongodb_uri:
        raise AuthStoreUnavailable("MONGODB_URI is not set in .env -- sign-up and login need MongoDB.")
    collection = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)[settings.mongodb_db]["users"]
    collection.create_index([("username", ASCENDING)], unique=True)
    return collection


def _public(user: dict) -> dict:
    return {"id": str(user["_id"]), "username": user["username"]}


def create_user(username: str, password: str) -> dict:
    doc = {
        "username": username,
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = users_collection().insert_one(doc)
    except DuplicateKeyError:
        raise UsernameTaken(username)
    doc["_id"] = result.inserted_id
    return _public(doc)


# Checked against when the username doesn't exist, so a login attempt takes
# the same time whether or not the account exists (no username probing).
_DUMMY_HASH = bcrypt.hashpw(b"citecache-timing-equaliser", bcrypt.gensalt())


def authenticate(username: str, password: str) -> dict | None:
    user = users_collection().find_one({"username": username})
    stored = user["password_hash"].encode() if user else _DUMMY_HASH
    valid = bcrypt.checkpw(password.encode(), stored)
    return _public(user) if user and valid else None
