import os, time, math
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.db import init_db, conn, setting, set_setting, audit
from app.security import verify_init_data

BOT_TOKEN=os.getenv("BOT_TOKEN","")
ADMIN_IDS={int(x) for x in os.getenv("ADMIN_IDS","7419171743").split(",") if x.strip().isdigit()}
app=FastAPI(title="CHIKEN USDT TON")
app.mount("/static",StaticFiles(directory="app/static"),name="static")

HENS=[
 {"id":1,"name":"Baby Put","price":0.5,"eggs_day":11111,"income_day":0.03},
 {"id":2,"name":"Jun Put","price":2,"eggs_day":62963,"income_day":0.17},
 {"id":3,"name":"Take Put","price":3,"eggs_day":96296,"income_day":0.26},
 {"id":4,"name":"Silkie Put","price":5,"eggs_day":166667,"income_day":0.45},
 {"id":5,"name":"Rhode Island Put","price":12,"eggs_day":377778,"income_day":1.02},
 {"id":6,"name":"Plymouth Rock Put","price":25,"eggs_day":814815,"income_day":2.20},
]
CORN=[{"id":1,"name":"Corn Bag","price":0.15,"corn":50000},
      {"id":2,"name":"Corn Sack","price":0.5,"corn":250000},
      {"id":3,"name":"Corn Silo","price":1.5,"corn":480000}]

@app.on_event("startup")
def startup(): init_db()

def current_user(authorization):
    if not authorization or not authorization.startswith("tma "):
        raise HTTPException(401,"Telegram login required")
    try: u=verify_init_data(authorization[4:],BOT_TOKEN)
    except Exception as e: raise HTTPException(401,str(e))
    uid=int(u["id"])
    with conn() as c:
        row=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
        if not row:
            ref=None
            # start_param is not trusted from initData user; referral is handled by /api/register
            c.execute("INSERT INTO users(id,username,first_name,joined_at,last_mine) VALUES(?,?,?,?,?)",
                      (uid,u.get("username",""),u.get("first_name",""),int(time.time()),int(time.time())))
            bonus=float(setting("joining_bonus","0.01"))
            c.execute("UPDATE users SET balance=balance+? WHERE id=?",(bonus,uid))
            row=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
        if row["banned"]: raise HTTPException(403,"Account restricted")
        return dict(row)

def admin_check(user):
    if user["id"] not in ADMIN_IDS: raise HTTPException(403,"Admin only")

@app.get("/")
def home(): return FileResponse("app/static/index.html")

@app.get("/api/me")
def me(authorization:str|None=Header(default=None)):
    u=current_user(authorization)
    now=int(time.time())
    with conn() as c:
        r=c.execute("SELECT COALESCE(SUM(eggs_day),0) total FROM purchases WHERE user_id=? AND item_type='hen'",(u["id"],)).fetchone()
        eggs_day=int(r["total"])
        elapsed=max(0,min(now-u["last_mine"],86400))
        earned=int(eggs_day*elapsed/86400)
        # Mining is calculated server-side; corn is consumed only while corn remains.
        if earned and u["corn"]>0:
            earned=min(earned,u["corn"]*1000)
            c.execute("UPDATE users SET eggs=eggs+?, corn=MAX(0,corn-?), last_mine=? WHERE id=?",
                      (earned, math.ceil(earned/1000),now,u["id"]))
        else:
            c.execute("UPDATE users SET last_mine=? WHERE id=?",(now,u["id"]))
        u=dict(c.execute("SELECT * FROM users WHERE id=?",(u["id"],)).fetchone())
    return {"id":u["id"],"username":u["username"],"balance":u["balance"],"eggs":u["eggs"],"corn":u["corn"],
            "hens":HENS,"corn_shop":CORN,"eggs_per_day":eggs_day,"admin":u["id"] in ADMIN_IDS,
            "deposit_address":setting("deposit_address"),"min_deposit":float(setting("min_deposit","3")),
            "min_withdraw":float(setting("min_withdraw","0.01")),"maintenance":setting("maintenance","0")=="1"}

class DepositIn(BaseModel):
    asset:str
    amount:float=Field(gt=0)
    tx_hash:str=Field(min_length=10,max_length=180)

@app.post("/api/deposit")
def deposit(body:DepositIn,authorization:str|None=Header(default=None)):
    u=current_user(authorization)
    if body.asset not in ("USDT_TON","GRAM_TON"): raise HTTPException(400,"Only TON network assets are supported")
    if body.amount<float(setting("min_deposit","3")): raise HTTPException(400,"Below minimum deposit")
    with conn() as c:
        try:
            c.execute("INSERT INTO deposits(user_id,asset,amount,tx_hash,created_at) VALUES(?,?,?,?,?)",
                      (u["id"],body.asset,body.amount,body.tx_hash.strip(),int(time.time())))
        except Exception: raise HTTPException(409,"This transaction hash has already been submitted")
    return {"ok":True,"message":"Deposit submitted for admin review"}

class WithdrawIn(BaseModel):
    asset:str
    amount:float=Field(gt=0)
    address:str=Field(min_length=20,max_length=160)

@app.post("/api/withdraw")
def withdraw(body:WithdrawIn,authorization:str|None=Header(default=None)):
    u=current_user(authorization)
    if body.asset not in ("USDT_TON","GRAM_TON"): raise HTTPException(400,"Only TON network assets are supported")
    if body.amount<float(setting("min_withdraw","0.01")): raise HTTPException(400,"Below minimum withdrawal")
    with conn() as c:
        bal=c.execute("SELECT balance FROM users WHERE id=?",(u["id"],)).fetchone()["balance"]
        if body.amount>bal: raise HTTPException(400,"Insufficient balance")
        c.execute("UPDATE users SET balance=balance-? WHERE id=?",(body.amount,u["id"]))
        c.execute("INSERT INTO withdrawals(user_id,asset,amount,address,created_at) VALUES(?,?,?,?,?)",
                  (u["id"],body.asset,body.amount,body.address.strip(),int(time.time())))
    return {"ok":True,"message":"Withdrawal request submitted"}

class BuyIn(BaseModel):
    item_type:str
    item_id:int

@app.post("/api/buy")
def buy(body:BuyIn,authorization:str|None=Header(default=None)):
    u=current_user(authorization)
    items=HENS if body.item_type=="hen" else CORN if body.item_type=="corn" else []
    item=next((x for x in items if x["id"]==body.item_id),None)
    if not item: raise HTTPException(404,"Item not found")
    with conn() as c:
        bal=c.execute("SELECT balance FROM users WHERE id=?",(u["id"],)).fetchone()["balance"]
        if bal<item["price"]: raise HTTPException(400,"Insufficient balance")
        c.execute("UPDATE users SET balance=balance-? WHERE id=?",(item["price"],u["id"]))
        if body.item_type=="corn": c.execute("UPDATE users SET corn=corn+? WHERE id=?",(item["corn"],u["id"]))
        c.execute("INSERT INTO purchases(user_id,item_type,item_name,price,created_at) VALUES(?,?,?,?,?)",
                  (u["id"],body.item_type,item["name"],item["price"],int(time.time())))
    return {"ok":True}

@app.post("/api/convert-eggs")
def convert(authorization:str|None=Header(default=None)):
    u=current_user(authorization); rate=float(setting("egg_rate","0.0000027"))
    with conn() as c:
        r=c.execute("SELECT eggs FROM users WHERE id=?",(u["id"],)).fetchone()
        if r["eggs"]<=0: raise HTTPException(400,"No eggs to convert")
        amount=r["eggs"]*rate
        c.execute("UPDATE users SET eggs=0,balance=balance+? WHERE id=?",(amount,u["id"]))
    return {"ok":True,"amount":amount}

@app.get("/api/history")
def history(authorization:str|None=Header(default=None)):
    u=current_user(authorization)
    with conn() as c:
        d=[dict(x) for x in c.execute("SELECT asset,amount,tx_hash,status,created_at FROM deposits WHERE user_id=? ORDER BY id DESC LIMIT 30",(u["id"],))]
        w=[dict(x) for x in c.execute("SELECT asset,amount,address,status,created_at,tx_hash FROM withdrawals WHERE user_id=? ORDER BY id DESC LIMIT 30",(u["id"],))]
    return {"deposits":d,"withdrawals":w}

@app.get("/api/admin/overview")
def admin_overview(authorization:str|None=Header(default=None)):
    u=current_user(authorization); admin_check(u)
    with conn() as c:
        users=c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
        deposits=[dict(x) for x in c.execute("SELECT * FROM deposits WHERE status='pending' ORDER BY id")]
        withdrawals=[dict(x) for x in c.execute("SELECT * FROM withdrawals WHERE status='pending' ORDER BY id")]
        settings={x["key"]:x["value"] for x in c.execute("SELECT * FROM settings")}
    return {"users":users,"deposits":deposits,"withdrawals":withdrawals,"settings":settings}

class ReviewIn(BaseModel):
    kind:str
    request_id:int
    action:str
    tx_hash:str|None=None

@app.post("/api/admin/review")
def review(body:ReviewIn,authorization:str|None=Header(default=None)):
    u=current_user(authorization); admin_check(u)
    if body.kind not in ("deposit","withdrawal") or body.action not in ("approve","reject"):
        raise HTTPException(400,"Invalid review action")
    table="deposits" if body.kind=="deposit" else "withdrawals"
    with conn() as c:
        r=c.execute(f"SELECT * FROM {table} WHERE id=?",(body.request_id,)).fetchone()
        if not r or r["status"]!="pending": raise HTTPException(404,"Pending request not found")
        status="approved" if body.action=="approve" else "rejected"
        c.execute(f"UPDATE {table} SET status=?,reviewed_at=?,reviewed_by=?"+(",tx_hash=?" if body.kind=="withdrawal" else "")+" WHERE id=?",
                  ((status,int(time.time()),u["id"],body.tx_hash,body.request_id) if body.kind=="withdrawal" else (status,int(time.time()),u["id"],body.request_id)))
        if body.kind=="deposit" and body.action=="approve":
            c.execute("UPDATE users SET balance=balance+? WHERE id=?",(r["amount"],r["user_id"]))
        if body.kind=="withdrawal" and body.action=="reject":
            c.execute("UPDATE users SET balance=balance+? WHERE id=?",(r["amount"],r["user_id"]))
        audit(u["id"],f"{body.kind}_{status}",f"request={body.request_id}")
    return {"ok":True}

class SettingIn(BaseModel):
    key:str
    value:str

@app.post("/api/admin/setting")
def admin_setting(body:SettingIn,authorization:str|None=Header(default=None)):
    u=current_user(authorization); admin_check(u)
    allowed={"min_deposit","min_withdraw","joining_bonus","ref_one_time","ref_percent","egg_rate","deposit_address","maintenance"}
    if body.key not in allowed: raise HTTPException(400,"Setting not allowed")
    set_setting(body.key,body.value); audit(u["id"],"setting_changed",body.key)
    return {"ok":True}
