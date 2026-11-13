import os, sqlite3, time
DB = os.getenv("DATABASE_PATH", "chiken_usdt.db")

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
          balance REAL NOT NULL DEFAULT 0, eggs INTEGER NOT NULL DEFAULT 0,
          corn INTEGER NOT NULL DEFAULT 0, referrer INTEGER,
          joined_at INTEGER NOT NULL, banned INTEGER NOT NULL DEFAULT 0,
          last_mine INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS deposits(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          asset TEXT NOT NULL, amount REAL NOT NULL, tx_hash TEXT NOT NULL UNIQUE,
          status TEXT NOT NULL DEFAULT 'pending', created_at INTEGER NOT NULL,
          reviewed_at INTEGER, reviewed_by INTEGER
        );
        CREATE TABLE IF NOT EXISTS withdrawals(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          asset TEXT NOT NULL, amount REAL NOT NULL, address TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending', created_at INTEGER NOT NULL,
          reviewed_at INTEGER, reviewed_by INTEGER, tx_hash TEXT
        );
        CREATE TABLE IF NOT EXISTS referrals(
          id INTEGER PRIMARY KEY AUTOINCREMENT, referrer INTEGER NOT NULL,
          referred INTEGER NOT NULL UNIQUE, rewarded INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS purchases(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          item_type TEXT NOT NULL, item_name TEXT NOT NULL, price REAL NOT NULL,
          created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(
          id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER,
          action TEXT NOT NULL, detail TEXT, created_at INTEGER NOT NULL
        );
        """)
        defaults = {
          "min_deposit": os.getenv("MIN_DEPOSIT_USDT","3"),
          "min_withdraw": os.getenv("MIN_WITHDRAW_USDT","0.01"),
          "joining_bonus": os.getenv("JOINING_BONUS_USDT","0.01"),
          "ref_one_time": os.getenv("REFERRAL_ONE_TIME_USDT","0.02"),
          "ref_percent": os.getenv("REFERRAL_COMMISSION_PERCENT","10"),
          "egg_rate": os.getenv("EGG_USD_RATE","0.0000027"),
          "deposit_address": os.getenv("TON_DEPOSIT_ADDRESS",""),
          "maintenance": "0"
        }
        for k,v in defaults.items():
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,str(v)))

def setting(key, default=""):
    with conn() as c:
        r=c.execute("SELECT value FROM settings WHERE key=?",(key,)).fetchone()
        return r["value"] if r else default

def set_setting(key,value):
    with conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(key,str(value)))

def audit(admin, action, detail=""):
    with conn() as c:
        c.execute("INSERT INTO audit(admin_id,action,detail,created_at) VALUES(?,?,?,?)",(admin,action,detail,int(time.time())))
