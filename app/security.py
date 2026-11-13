import hashlib, hmac, json, os, time
from urllib.parse import parse_qsl

def verify_init_data(init_data: str, bot_token: str, max_age=86400):
    if not init_data or not bot_token:
        raise ValueError("Telegram authentication data missing")
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received = values.pop("hash", None)
    if not received:
        raise ValueError("Invalid Telegram data")
    pairs = [f"{k}={v}" for k,v in sorted(values.items())]
    data_check = "\n".join(pairs)
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received):
        raise ValueError("Telegram authentication failed")
    auth_date = int(values.get("auth_date","0"))
    if auth_date <= 0 or time.time()-auth_date > max_age:
        raise ValueError("Telegram session expired")
    user = json.loads(values.get("user","{}"))
    if not user.get("id"):
        raise ValueError("Telegram user not found")
    return user
