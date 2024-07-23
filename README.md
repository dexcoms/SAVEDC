Request : 
- VPS or Raspberry Pi on Ubuntu
- Telegram bot
- @BotFather


Sutup
Download https://github.com/dexcoms/SAVEDC/blob/main/bot.py

replace

RPC_URL = 'http://localhost:9091/transmission/rpc/'


USERNAME = 'your_username'


PASSWORD = 'your_password'

and 


def main():

    """เริ่มบอทและจัดการข้อความ."""
    TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'  # ใช้ Token ใหม่ของบอทที่คุณได้รับ
    application = Application.builder().token(TOKEN).build()
Create and generated token from @BotFather

Run


python3 /root/bot.py

make bot start anytime on Service

sudo nano /etc/systemd/system/telegram-bot.service

[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
User=pi
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/bot.py
Restart=always
RestartSec=10
Environment="PATH=/usr/bin"

[Install]
WantedBy=multi-user.target

Ctrl+X , Y
