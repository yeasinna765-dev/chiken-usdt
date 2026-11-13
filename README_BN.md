# CHIKEN USDT — TON Network

এটি FastAPI + SQLite + Telegram Bot + Telegram Mini App-এর একটি runnable starter project।

## ১) যা আছে
- Telegram Mini App authentication: Telegram `initData` HMAC যাচাই
- Admin ID: `7419171743`
- Hen shop ও Corn shop
- Server-side balance, egg conversion ও mining accrual
- TON Network asset selection: USDT_TON / GRAM_TON
- Deposit request + unique transaction hash protection
- Withdrawal request; reject করলে balance ফেরত
- Admin pending deposit/withdrawal approval
- Admin settings: deposit address, minimum deposit, maintenance
- SQLite database

## ২) যা এখনো production-এ চালুর আগে করতে হবে
- TON blockchain-এ USDT Jetton transaction auto-verification এই starter-এ নেই। Deposit প্রথমে pending থাকবে; Admin explorer-এ যাচাই করে approve করবেন।
- Withdrawal approve করলে এটি payout সম্পন্ন করে না; Admin নিজে TON wallet থেকে পাঠিয়ে “Mark Paid” করবেন। Production payout-এর জন্য নিরাপদ hot-wallet service/TON API ও key management আলাদা করে যোগ করতে হবে।
- GRAM token-এর সঠিক Jetton master address, decimals ও বাস্তব exchange rate Admin/Developer-কে নিশ্চিত করতে হবে। এই starter-এ GRAM deposit request-ও manual review।
- Referral registration/payout workflow UI-তে placeholder; referral abuse protection এবং full ledger পরের production phase-এ যোগ করতে হবে।
- Mining economics, corn consumption ও egg conversion rate ব্যবসায়িকভাবে যাচাই করুন। কোনো আয়ের নিশ্চয়তা নয়।

## ৩) ইনস্টল
Python 3.11+ লাগবে।

```bash
python -m venv venv
# Windows:
venv\\Scripts\\activate
# Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

`.env` ফাইলে:
- `BOT_TOKEN` = BotFather থেকে পাওয়া bot token
- `WEBAPP_URL` = আপনার HTTPS Mini App URL
- `TON_DEPOSIT_ADDRESS` = আপনার নিজের TON wallet address
- `TON_USDT_JETTON_MASTER` = TON network-এর official USDT Jetton master address
- `ADMIN_IDS=7419171743`

## ৪) চালু
দুটি terminal-এ চালান:

Terminal 1:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Terminal 2:
```bash
python bot.py
```

Telegram Mini App অবশ্যই HTTPS domain-এ host করতে হবে। BotFather-এ Web App/Menu Button URL সেট করুন।

## ৫) গুরুত্বপূর্ণ নিরাপত্তা
- `.env` কখনো GitHub-এ public করবেন না।
- Wallet seed phrase/private key কখনো server বা developer-কে দেবেন না।
- Admin approval-এর আগে TON transaction explorer-এ amount, destination, asset Jetton master, confirmations ও transaction hash মিলিয়ে নিন।
- Production deployment-এর আগে HTTPS, backups, rate limiting, CSRF/origin policy, audit monitoring, database migration, and independent security review যোগ করুন।
