from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import requests
import os
import base64
import asyncio

# ตั้งค่าข้อมูลพื้นฐาน
RPC_URL = 'http://localhost:9091/transmission/rpc/'
USERNAME = 'your_username'
PASSWORD = 'your_password'

def get_session_id():
    """ดึง X-Transmission-Session-Id จาก Transmission."""
    try:
        response = requests.get(RPC_URL, auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        return response.headers.get('X-Transmission-Session-Id')
    except requests.HTTPError as e:
        if e.response.status_code == 409:
            # ลองอีกครั้งหลังจากการรีเฟรชเซสชัน
            return e.response.headers.get('X-Transmission-Session-Id')
        else:
            raise e

def add_torrent(torrent_file_path, session_id):
    """เพิ่ม torrent ไปยัง Transmission โดยใช้ไฟล์ .torrent."""
    headers = {'X-Transmission-Session-Id': session_id}
    with open(torrent_file_path, 'rb') as torrent_file:
        torrent_content = base64.b64encode(torrent_file.read()).decode('utf-8')

    payload = {
        'method': 'torrent-add',
        'arguments': {
            'metainfo': torrent_content
        }
    }

    response = requests.post(
        RPC_URL,
        auth=(USERNAME, PASSWORD),
        headers=headers,
        json=payload
    )

    if response.status_code == 409:  # จัดการข้อผิดพลาด 409 และลองอีกครั้ง
        session_id = response.headers.get('X-Transmission-Session-Id')
        headers['X-Transmission-Session-Id'] = session_id
        response = requests.post(
            RPC_URL,
            auth=(USERNAME, PASSWORD),
            headers=headers,
            json=payload
        )

    response.raise_for_status()
    return response.json()

def get_torrent_status(torrent_id, session_id):
    """ดึงสถานะของ torrent โดยใช้ ID."""
    headers = {'X-Transmission-Session-Id': session_id}
    payload = {
        'method': 'torrent-get',
        'arguments': {
            'ids': [torrent_id],
            'fields': ['id', 'name', 'status', 'percentDone', 'rateDownload', 'rateUpload']
        }
    }

    response = requests.post(
        RPC_URL,
        auth=(USERNAME, PASSWORD),
        headers=headers,
        json=payload
    )

    if response.status_code == 409:  # จัดการข้อผิดพลาด 409 และลองอีกครั้ง
        session_id = response.headers.get('X-Transmission-Session-Id')
        headers['X-Transmission-Session-Id'] = session_id
        response = requests.post(
            RPC_URL,
            auth=(USERNAME, PASSWORD),
            headers=headers,
            json=payload
        )

    response.raise_for_status()
    return response.json()

async def start(update: Update, context: CallbackContext):
    """ส่งข้อความต้อนรับเมื่อผู้ใช้เริ่มการสนทนา."""
    await update.message.reply_text("ส่งไฟล์ .torrent มาได้เลยครับ!")

async def handle_document(update: Update, context: CallbackContext):
    """จัดการไฟล์ที่ผู้ใช้ส่งมา."""
    document = update.message.document
    if document.mime_type != "application/x-bittorrent":
        await update.message.reply_text("กรุณาส่งไฟล์ .torrent เท่านั้น.")
        return

    file = await document.get_file()
    file_path = f'/tmp/{document.file_id}.torrent'  # กำหนดเส้นทางไฟล์ชั่วคราว

    # ดาวน์โหลดไฟล์
    file_bytearray = await file.download_as_bytearray()
    with open(file_path, 'wb') as f:
        f.write(file_bytearray)

    try:
        session_id = get_session_id()
        result = add_torrent(file_path, session_id)
        torrent_id = result.get('arguments', {}).get('torrent-added', {}).get('id')

        if torrent_id:
            # รอ 10 วินาทีเพื่อให้การดาวน์โหลดเริ่มต้น
            await asyncio.sleep(10)
            status = get_torrent_status(torrent_id, session_id)
            torrent_info = status.get('arguments', {}).get('torrents', [{}])[0]
            percent_done = torrent_info.get('percentDone', 0) * 100
            rate_download = torrent_info.get('rateDownload', 0) / 1024
            rate_upload = torrent_info.get('rateUpload', 0) / 1024
            message = (f"Torrent added successfully.\n"
                       f"Name: {torrent_info.get('name', 'Unknown')}\n"
                       f"Status: {torrent_info.get('status', 'Unknown')}\n"
                       f"Progress: {percent_done:.2f}%\n"
                       f"Download Rate: {rate_download:.2f} KB/s\n"
                       f"Upload Rate: {rate_upload:.2f} KB/s")
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("ไม่พบ ID ของ torrent หลังจากเพิ่ม.")
    except requests.RequestException as e:
        await update.message.reply_text(f"Request error: {e}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        os.remove(file_path)  # ลบไฟล์หลังจากการอัพโหลดเสร็จสิ้น

def main():
    """เริ่มบอทและจัดการข้อความ."""
    TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'  # ใช้ Token ใหม่ของบอทที่คุณได้รับ
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    application.run_polling()

if __name__ == '__main__':
    main()
