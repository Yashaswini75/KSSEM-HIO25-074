# auth_csv.py
import pandas as pd
from pathlib import Path
from utils import ensure_dirs, now_iso, atomic_save_csv
import hashlib
import os
import base64

# Prefer passlib when available; if not, provide a minimal compatible
# pbkdf2_sha256 replacement so the app can run without the dependency.
try:
    from passlib.hash import pbkdf2_sha256  # type: ignore
except Exception:
    class pbkdf2_sha256:
        """Minimal drop-in replacement for passlib's pbkdf2_sha256.hash/verify.

        Format used for stored hashes:
          pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>

        This will also attempt to verify existing passlib-style hashes of the
        form: $pbkdf2-sha256$<rounds>$<salt_b64>$<checksum_b64>
        """

        @staticmethod
        def hash(password: str, rounds: int = 29000) -> str:
            salt = os.urandom(16)
            dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, rounds)
            return f"pbkdf2_sha256${rounds}${base64.b64encode(salt).decode('ascii')}${base64.b64encode(dk).decode('ascii')}"

        @staticmethod
        def verify(password: str, stored: str) -> bool:
            if stored is None:
                return False
            # Our custom format: pbkdf2_sha256$rounds$salt_b64$hash_b64
            try:
                if stored.startswith('pbkdf2_sha256$'):
                    parts = stored.split('$')
                    _, rounds_s, salt_b64, hash_b64 = parts
                    rounds = int(rounds_s)
                    salt = base64.b64decode(salt_b64)
                    expected = base64.b64decode(hash_b64)
                    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, rounds)
                    return hashlib.compare_digest(dk, expected)

                # Try to parse passlib's $pbkdf2-sha256$ rounds $salt $checksum format
                if stored.startswith('$pbkdf2-sha256$'):
                    parts = stored.split('$')
                    # ['', 'pbkdf2-sha256', '<rounds>', '<salt_b64>', '<checksum_b64>']
                    if len(parts) >= 5:
                        rounds = int(parts[2])
                        salt_b64 = parts[3]
                        checksum_b64 = parts[4]
                        salt = base64.b64decode(salt_b64)
                        expected = base64.b64decode(checksum_b64)
                        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, rounds)
                        return hashlib.compare_digest(dk, expected)
            except Exception:
                return False
            return False

ensure_dirs()
USERS_CSV = Path("data") / "users.csv"

def _load_users():
    if USERS_CSV.exists():
        return pd.read_csv(USERS_CSV)
    return pd.DataFrame(columns=["id","email","password_hash","full_name","phone","created_at","profile_completed"])

def register(email, password, full_name="", phone=""):
    users = _load_users()
    if (users['email'] == email).any():
        return False, "Email already registered"
    new_id = int(users['id'].max()) + 1 if len(users) > 0 else 1
    pw_hash = pbkdf2_sha256.hash(password)
    row = {"id": new_id, "email": email, "password_hash": pw_hash, "full_name": full_name, "phone": phone, "created_at": now_iso(), "profile_completed": False}
    users = pd.concat([users, pd.DataFrame([row])], ignore_index=True)

    atomic_save_csv(users, USERS_CSV)
    return True, "Registered"

def login(email, password):
    users = _load_users()
    match = users[users['email'] == email]
    if match.empty:
        return False, "Email not found"
    pw_hash = match.iloc[0]['password_hash']
    if pbkdf2_sha256.verify(password, pw_hash):
        return True, dict(match.iloc[0])
    return False, "Wrong password"

def get_user_by_id(uid):
    users = _load_users()
    match = users[users['id'] == int(uid)]
    return dict(match.iloc[0]) if not match.empty else None

def update_user_profile(uid, updates:dict):
    users = _load_users()
    idx = users[users['id'] == int(uid)].index
    if len(idx) == 0:
        return False
    for k, v in updates.items():
        users.at[idx[0], k] = v
    atomic_save_csv(users, USERS_CSV)
    return True
