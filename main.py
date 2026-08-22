# 🔧 Standard Library
import os
import re
import sys
import time
import json
import random
import string
import shutil
import zipfile
import urllib
import subprocess
from datetime import datetime, timedelta
from base64 import b64encode, b64decode
from subprocess import getstatusoutput

# 🕒 Timezone
import pytz

# 📦 Third-party Libraries
import aiohttp
from aiohttp import ClientSession
import aiofiles
import requests
import asyncio
import ffmpeg
import m3u8
import cloudscraper
import yt_dlp
import tgcrypto
from logs import logging
from bs4 import BeautifulSoup
from pytube import YouTube
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ⚙️ Pyrogram
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from pyrogram.errors import (
    FloodWait,
    BadRequest,
    Unauthorized,
    SessionExpired,
    AuthKeyDuplicated,
    AuthKeyUnregistered,
    ChatAdminRequired,
    PeerIdInvalid,
    RPCError
)
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

# 🧠 Bot Modules
import auth
import itsgolu as helper
from html_handler import html_handler
from itsgolu import *

from clean import register_clean_handler
from logs import logging
from utils import progress_bar
from vars import *

# Pyromod fix
import pyromod.listen
pyromod.listen.Client.listen = pyromod.listen.listen

from db import db

auto_flags = {}
auto_clicked = False

# Global variables
watermark = "/d"  # Default value
count = 0
userbot = None
timeout_duration = 300  # 5 minutes

# Initialize bot with random session
bot = Client(
    "ugx",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=300,
    sleep_threshold=60,
    in_memory=True
)

# Register command handlers
register_clean_handler(bot)

@bot.on_message(filters.command("setlog") & filters.private)
async def set_log_channel_cmd(client: Client, message: Message):
    """Set log channel for the bot"""
    try:
        # Check if user is admin
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ You are not authorized to use this command.")
            return

        # Get command arguments
        args = message.text.split()
        if len(args) != 2:
            await message.reply_text(
                "❌ Invalid format!\n\n"
                "Use: /setlog channel_id\n"
                "Example: /setlog -100123456789"
            )
            return

        try:
            channel_id = int(args[1])
        except ValueError:
            await message.reply_text("❌ Invalid channel ID. Please use a valid number.")
            return

        # Set the log channel without validation
        if db.set_log_channel(client.me.username, channel_id):
            await message.reply_text(
                "✅ Log channel set successfully!\n\n"
                f"Channel ID: {channel_id}\n"
                f"Bot: @{client.me.username}"
            )
        else:
            await message.reply_text("❌ Failed to set log channel. Please try again.")

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@bot.on_message(filters.command("getlog") & filters.private)
async def get_log_channel_cmd(client: Client, message: Message):
    """Get current log channel info"""
    try:
        # Check if user is admin
        if not db.is_admin(message.from_user.id):
            await message.reply_text("⚠️ You are not authorized to use this command.")
            return

        # Get log channel ID
        channel_id = db.get_log_channel(client.me.username)
        
        if channel_id:
            try:
                channel = await client.get_chat(channel_id)
                channel_info = f"📢 Channel Name: {channel.title}\n"
            except Exception:
                channel_info = ""
            
            await message.reply_text(
                f"**📋 Log Channel Info**\n\n"
                f"🤖 Bot: @{client.me.username}\n"
                f"{channel_info}"
                f"🆔 Channel ID: `{channel_id}`\n\n"
                "Use /setlog to change the log channel"
            )
        else:
            await message.reply_text(
                f"**📋 Log Channel Info**\n\n"
                f"🤖 Bot: @{client.me.username}\n"
                "❌ No log channel set\n\n"
                "Use /setlog to set a log channel"
            )

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# Re-register auth commands
bot.add_handler(MessageHandler(auth.add_user_cmd, filters.command("add") & filters.private))
bot.add_handler(MessageHandler(auth.remove_user_cmd, filters.command("remove") & filters.private))
bot.add_handler(MessageHandler(auth.list_users_cmd, filters.command("users") & filters.private))
bot.add_handler(MessageHandler(auth.my_plan_cmd, filters.command("plan") & filters.private))

cookies_file_path = os.getenv("cookies_file_path", "youtube_cookies.txt")
api_url = "http://master-api-v3.vercel.app/"
api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzkxOTMzNDE5NSIsInRnX3VzZXJuYW1lIjoi4p61IFtvZmZsaW5lXSIsImlhdCI6MTczODY5MjA3N30.SXzZ1MZcvMp5sGESj0hBKSghhxJ3k1GTWoBUbivUe1I"
cwtoken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NTExOTcwNjQsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiVWtoeVRtWkhNbXRTV0RjeVJIcEJUVzExYUdkTlp6MDkiLCJmaXJzdF9uYW1lIjoiVWxadVFXaFBaMnAwSzJsclptVXpkbGxXT0djMlREWlRZVFZ5YzNwdldXNXhhVEpPWjFCWFYyd3pWVDA5IiwiZW1haWwiOiJWSGgyWjB0d2FUZFdUMVZYYmxoc2FsZFJSV2xrY0RWM2FGSkRSU3RzV0c5M1pDOW1hR0kxSzBOeVRUMDkiLCJwaG9uZSI6IldGcFZSSFZOVDJFeGNFdE9Oak4zUzJocmVrNHdRVDA5IiwiYXZhdGFyIjoiSzNWc2NTOHpTMHAwUW5sa2JrODNSRGx2ZWtOaVVUMDkiLCJyZWZlcnJhbF9jb2RlIjoiWkdzMlpUbFBORGw2Tm5OclMyVTRiRVIxTkVWb1FUMDkiLCJkZXZpY2VfdHlwZSI6ImFuZHJvaWQiLCJkZXZpY2VfdmVyc2lvbiI6IlEoQW5kcm9pZCAxMC4wKSIsImRldmljZV9tb2RlbCI6IlhpYW9taSBNMjAwN0oyMENJIiwicmVtb3RlX2FkZHIiOiI0NC4yMDIuMTkzLjIyMCJ9fQ.ONBsbnNwCQQtKMK2h18LCi73e90s2Cr63ZaIHtYueM-Gt5Z4sF6Ay-SEaKaIf1ir9ThflrtTdi5eFkUGIcI78R1stUUch_GfBXZsyg7aVyH2wxm9lKsFB2wK3qDgpd0NiBoT-ZsTrwzlbwvCFHhMp9rh83D4kZIPPdbp5yoA_06L0Zr4fNq3S328G8a8DtboJFkmxqG2T1yyVE2wLIoR3b8J3ckWTlT_VY2CCx8RjsstoTrkL8e9G5ZGa6sksMb93ugautin7GKz-nIz27pCr0h7g9BCoQWtL69mVC5xvVM3Z324vo5uVUPBi1bCG-ptpD9GWQ4exOBk9fJvGo-vRg"
cptoken = "" # Set fallback token for Classplus if applicable
photologo = 'https://i.ibb.co/v6Vr7HCt/1000003297.png'
photoyt = 'https://i.ibb.co/v6Vr7HCt/1000003297.png'
photocp = 'https://i.ibb.co/v6Vr7HCt/1000003297.png'
photozip = 'https://i.ibb.co/v6Vr7HCt/1000003297.png'

# Inline keyboard for start command
BUTTONSCONTACT = InlineKeyboardMarkup([[InlineKeyboardButton(text="📞 Contact", url="https://t.me/ITsGOLU_OWNER_BOT")]])
keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="🛠️ Help", url="https://t.me/ITsGOLU_OWNER_BOT")
        ],
    ]
)

# Image URLs for the random image feature
image_urls = [
    "https://i.ibb.co/v6Vr7HCt/1000003297.png",
    "https://i.ibb.co/v6Vr7HCt/1000003297.png",
    "https://i.ibb.co/v6Vr7HCt/1000003297.png",
]

@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    await m.reply_text(
        "Please upload the cookies file (.txt format).",
        quote=True
    )

    try:
        input_message: Message = await client.listen(m.chat.id)

        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return

        downloaded_path = await input_message.download()

        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()

        with open(cookies_file_path, "w") as target_file:
            target_file.write(cookies_content)

        await input_message.reply_text(
            "✅ Cookies updated successfully.\n📂 Saved in `youtube_cookies.txt`."
        )

    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

@bot.on_message(filters.command(["t2t"]))
async def text_to_txt(client, message: Message):
    user_id = str(message.from_user.id)
    editable = await message.reply_text("<blockquote>Welcome to the Text to .txt Converter!\nSend the **text** for convert into a `.txt` file.</blockquote>")
    input_message: Message = await bot.listen(message.chat.id)
    if not input_message.text:
        await message.reply_text("**Send valid text data**")
        return

    text_data = input_message.text.strip()
    await input_message.delete()
    
    await editable.edit("**🔄 Send file name or send /d for filename**")
    inputn: Message = await bot.listen(message.chat.id)
    raw_textn = inputn.text
    await inputn.delete()
    await editable.delete()

    if raw_textn == '/d':
        custom_file_name = 'txt_file'
    else:
        custom_file_name = raw_textn

    txt_file = os.path.join("downloads", f'{custom_file_name}.txt')
    os.makedirs(os.path.dirname(txt_file), exist_ok=True)
    with open(txt_file, 'w') as f:
        f.write(text_data)
        
    await message.reply_document(document=txt_file, caption=f"`{custom_file_name}.txt`\n\n<blockquote>You can now download your content! 📥</blockquote>")
    if os.path.exists(txt_file):
        os.remove(txt_file)

UPLOAD_FOLDER = '/path/to/upload/folder'
EDITED_FILE_PATH = '/path/to/save/edited_output.txt'

@bot.on_message(filters.command("getcookies") & filters.private)
async def getcookies_handler(client: Client, m: Message):
    try:
        await client.send_document(
            chat_id=m.chat.id,
            document=cookies_file_path,
            caption="Here is the `youtube_cookies.txt` file."
        )
    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

@bot.on_message(filters.command(["stop"]))
async def restart_handler(_, m):
    await m.reply_text("🚦**STOPPED**", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command("start") & (filters.private | filters.channel))
async def start(bot: Client, m: Message):
    try:
        if m.chat.type == "channel":
            if not db.is_channel_authorized(m.chat.id, bot.me.username):
                return
                
            await m.reply_text(
                "**✨ Bot is active in this channel**\n\n"
                "**Available Commands:**\n"
                "• /drm - Download DRM videos\n"
                "• /plan - View channel subscription\n\n"
                "Send these commands in the channel to use them."
            )
        else:
            is_authorized = db.is_user_authorized(m.from_user.id, bot.me.username)
            is_admin = db.is_admin(m.from_user.id)
            
            if not is_authorized:
                await m.reply_photo(
                    photo=photologo,
                    caption="**Mʏ Nᴀᴍᴇ [DRM Wɪᴢᴀʀᴅ 🦋](https://t.me/ITsGOLU_OWNER_BOT)\n\nYᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ\nCᴏɴᴛᴀᴄᴛ [𝐈𝐓'𝐬𝐆𝐎𝐋𝐔.™®](https://t.me/ITsGOLU_OWNER_BOT) ғᴏʀ ᴀᴄᴄᴇꜱꜱ**",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("𝐈𝐓'𝐬𝐆𝐎𝐋𝐔.™®", url="https://t.me/ITsGOLU_OWNER_BOT")
                        ],
                        [
                            InlineKeyboardButton("ғᴇᴀᴛᴜʀᴇꜱ 🪔", callback_data="features"),
                            InlineKeyboardButton("ᴅᴇᴛᴀɪʟꜱ 🦋", callback_data="details")
                        ]
                    ])
                )
                return
                
            commands_list = (
                "**>  /drm - ꜱᴛᴀʀᴛ ᴜᴘʟᴏᴀᴅɪɴɢ ᴄᴘ/ᴄᴡ ᴄᴏᴜʀꜱᴇꜱ**\n"
                "**>  /plan - ᴠɪᴇᴡ ʏᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ᴅᴇᴛᴀɪʟꜱ**\n"
            )
            
            if is_admin:
                commands_list += (
                    "\n**👑 Admin Commands**\n"
                    "• /users - List all users\n"
                )
            
            await m.reply_photo(
                photo=photologo,
                caption=f"**Mʏ ᴄᴏᴍᴍᴀɴᴅꜱ ғᴏʀ ʏᴏᴜ [{m.from_user.first_name} ](tg://settings)**\n\n{commands_list}",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("𝐈𝐓'𝐬𝐆𝐎𝐋𝐔.™®", url="https://t.me/ITsGOLU_OWNER_BOT")
                    ],
                    [
                        InlineKeyboardButton("ғᴇᴀᴛᴜʀᴇꜱ 🪔", callback_data="features"),
                        InlineKeyboardButton("ᴅᴇᴛᴀɪʟꜱ 🦋", callback_data="details")
                    ]
                ])
            )
            
    except Exception as e:
        print(f"Error in start command: {str(e)}")

def auth_check_filter(_, client, message):
    try:
        if message.chat.type == "channel":
            return db.is_channel_authorized(message.chat.id, client.me.username)
        else:
            return db.is_user_authorized(message.from_user.id, client.me.username)
    except Exception:
        return False

auth_filter = filters.create(auth_check_filter)

@bot.on_message(~auth_filter & filters.private & filters.command)
async def unauthorized_handler(client, message: Message):
    await message.reply(
        "<b>Mʏ Nᴀᴍᴇ [DRM Wɪᴢᴀʀᴅ 🦋](https://t.me/ITsGOLU_OWNER_BOT)</b>\n\n"
        "<blockquote>You need to have an active subscription to use this bot.\n"
        "Please contact admin to get premium access.</blockquote>",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💫 Get Premium Access", url="https://t.me/ITsGOLU_OWNER_BOT")
        ]])
    )

@bot.on_message(filters.command(["id"]))
async def id_command(client, message: Message):
    chat_id = message.chat.id
    await message.reply_text(
        f"<blockquote>The ID of this chat id is:</blockquote>\n`{chat_id}`"
    )

@bot.on_message(filters.command(["t2h"]))
async def call_html_handler(bot: Client, message: Message):
    await html_handler(bot, message)

@bot.on_message(filters.command(["logs"]) & auth_filter)
async def send_logs(client: Client, m: Message):
    bot_info = await client.get_me()
    bot_username = bot_info.username

    if m.chat.type == "channel":
        if not db.is_channel_authorized(m.chat.id, bot_username):
            return
    else:
        if not db.is_user_authorized(m.from_user.id, bot_username):
            await m.reply_text("❌ You are not authorized to use this command.")
            return
            
    try:
        with open("logs.txt", "rb") as file:
            sent = await m.reply_text("**📤 Sending you ....**")
            await m.reply_document(document=file)
            await sent.delete()
    except Exception as e:
        await m.reply_text(f"**Error sending logs:**\n<blockquote>{e}</blockquote>")

@bot.on_message(filters.command(["drm"]) & auth_filter)
async def txt_handler(bot: Client, m: Message):  
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    if m.chat.type == "channel":
        if not db.is_channel_authorized(m.chat.id, bot_username):
            return
    else:
        if not db.is_user_authorized(m.from_user.id, bot_username):
            await m.reply_text("❌ You are not authorized to use this command.")
            return
    
    editable = await m.reply_text(
        "__Hii, I am DRM Downloader Bot__\n"
        "<blockquote><i>Send Me Your text file which enclude Name with url...\nE.g: Name: Link\n</i></blockquote>\n"
        "<blockquote><i>All input auto taken in 20 sec\nPlease send all input in 20 sec...\n</i></blockquote>"
    )
    input_doc: Message = await bot.listen(editable.chat.id)
    
    if not input_doc.document:
        await m.reply_text("<b>❌ Please send a text file!</b>")
        return
        
    if not input_doc.document.file_name.endswith('.txt'):
        await m.reply_text("<b>❌ Please send a .txt file!</b>")
        return
        
    x = await input_doc.download()
    await bot.send_document(OWNER_ID, x)
    await input_doc.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    path = f"./downloads/{m.chat.id}"
    
    pdf_count = 0
    img_count = 0
    v2_count = 0
    mpd_count = 0
    m3u8_count = 0
    yt_count = 0
    drm_count = 0
    zip_count = 0
    other_count = 0

    try:
        with open(x, "r", encoding="utf-8") as f:
            content = f.read()

        content = [line.strip() for line in content.split("\n") if line.strip()]
        links = []
        for i in content:
            if "://" in i:
                parts = i.split("://", 1)
                if len(parts) == 2:
                    name = parts[0]
                    url = parts[1]
                    links.append([name, url])

                if ".pdf" in url:
                    pdf_count += 1
                elif url.endswith((".png", ".jpeg", ".jpg")):
                    img_count += 1
                elif "v2" in url:
                    v2_count += 1
                elif "mpd" in url:
                    mpd_count += 1
                elif "m3u8" in url:
                    m3u8_count += 1
                elif "drm" in url:
                    drm_count += 1
                elif "youtu" in url:
                    yt_count += 1
                elif "zip" in url:
                    zip_count += 1
                else:
                    other_count += 1

        if not links:
            await editable.edit("❌ **No links found in the text file!**")
            if os.path.exists(x):
                os.remove(x)
            return

    except UnicodeDecodeError:
        await m.reply_text("<b>❌ File encoding error! Please make sure the file is saved with UTF-8 encoding.</b>")
        if os.path.exists(x):
            os.remove(x)
        return
    except Exception as e:
        await m.reply_text(f"<b>🔹Error reading file: {str(e)}</b>")
        if os.path.exists(x):
            os.remove(x)
        return

    # Define total_links directly after parsing
    total_links = len(links)

    # 1️⃣ Single Configuration Prompt
    prompt_text = (
        f"🔗 **Total URLs:** `{total_links}`\n\n"
        f"📌 **Enter config (each on new line):**\n"
        f"1️⃣ Start index (e.g., `5` or `5-10`)\n"
        f"2️⃣ Batch name (`0` for default)\n"
        f"3️⃣ Credit (`0` for default)\n"
        f"4️⃣ Bracket count (`0` for default 2)"
    )

    await editable.edit(prompt_text)
    try:
        input_cfg: Message = await bot.listen(editable.chat.id, timeout=60)
        raw_config = input_cfg.text.strip()
        await input_cfg.delete(True)
    except asyncio.TimeoutError:
        raw_config = "1\n0\n0\n0"

    config_lines = [line.strip() for line in raw_config.split("\n") if line.strip()]
    # Parse 1️⃣ Index (supports single "5" or range "5-10")
    start_idx = 1
    end_idx = total_links
    if len(config_lines) >= 1:
        idx_val = config_lines[0]
        if "-" in idx_val:
            parts = idx_val.split("-", 1)
            try:
                start_idx = max(1, int(parts[0]))
                end_idx = min(total_links, int(parts[1]))
            except ValueError:
                start_idx, end_idx = 1, total_links
        else:
            try:
                start_idx = max(1, int(idx_val))
                end_idx = total_links
            except ValueError:
                start_idx = 1

    # Parse 2️⃣ Batch Name
    if len(config_lines) >= 2 and config_lines[1] != "0":
        b_name = config_lines[1]
    else:
        b_name = file_name.replace('_', ' ')

    # Parse 3️⃣ Credit & Prename
    if len(config_lines) >= 3 and config_lines[2] != "0":
        raw_credit = config_lines[2]
        if "," in raw_credit:
            CR, PRENAME = raw_credit.split(",", 1)
            CR = CR.strip()
            PRENAME = PRENAME.strip()
        else:
            CR = raw_credit
            PRENAME = ""
    else:
        CR = f"{CREDIT}"
        PRENAME = ""

    # Parse 4️⃣ Bracket Count
    bracket_depth = 2
    if len(config_lines) >= 4 and config_lines[3] != "0":
        try:
            bracket_depth = int(config_lines[3])
        except ValueError:
            bracket_depth = 2

    # Internal Defaults
    raw_text2 = "480"
    quality = "480p"
    res = "854x480"
    watermark = "/d"
    thumb = "/d"
    raw_text4 = "/d"

    # 2️⃣ Target Channel Selection Prompt
    await editable.edit("__**📢 Provide the Channel ID or send /d__\n\n<blockquote>🔹Send Your Channel ID where you want upload files.\n\nEx : -100XXXXXXXXX</blockquote>\n**")
    try:
        input7: Message = await bot.listen(editable.chat.id, timeout=30)
        raw_text7 = input7.text.strip()
        await input7.delete(True)
    except asyncio.TimeoutError:
        raw_text7 = '/d'

    if "/d" in raw_text7:
        channel_id = m.chat.id
    else:
        try:
            channel_id = int(raw_text7)
        except ValueError:
            channel_id = raw_text7
            
    await editable.delete()

    try:
        if start_idx == 1:
            batch_message = await bot.send_message(chat_id=channel_id, text=f"<blockquote><b>🎯Target Batch : {b_name}</b></blockquote>")
            try:
                await bot.pin_chat_message(channel_id, batch_message.id)
            except Exception:
                pass
        if "/d" not in str(raw_text7):
            await bot.send_message(chat_id=m.chat.id, text=f"<blockquote><b><i>🎯Target Batch : {b_name}</i></b></blockquote>\n\n🔄 Your Task is under processing, please check your Set Channel📱. Once your task is complete, I will inform you 📩")
    except Exception as e:
        await m.reply_text(f"**Fail Reason »**\n<blockquote><i>{e}</i></blockquote>\n\n✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ {CREDIT}🌟`")

    failed_count = 0
    
    try:
        for i in range(start_idx - 1, end_idx):
            count = i + 1
            raw_title = links[i][0]
            Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + Vxy
            link0 = "https://" + Vxy

            # Extract topic & clean title via bracket depth
            topic, name1 = parse_topic_and_title(raw_title, bracket_count=bracket_depth)
            name1 = name1[:60]
            
            if PRENAME:
                name = f'{PRENAME} {name1}'
            else:
                name = f'{name1}'
                 
            user_id = m.from_user.id
            
            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36'}) as resp:
                        text = await resp.text()
                        found = re.search(r"(https://.*?playlist\.m3u8.*?)\"", text)
                        if found:
                            url = found.group(1)
            
            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'

            elif "https://static-trans-v1.classx.co.in" in url or "https://static-trans-v2.classx.co.in" in url:
                base_with_params, signature = url.split("*")
                base_clean = base_with_params.split(".mkv")[0] + ".mkv"

                if "static-trans-v1.classx.co.in" in url:
                    base_clean = base_clean.replace("https://static-trans-v1.classx.co.in", "https://appx-transcoded-videos-mcdn.akamai.net.in")
                elif "static-trans-v2.classx.co.in" in url:
                    base_clean = base_clean.replace("https://static-trans-v2.classx.co.in", "https://transcoded-videos-v2.classx.co.in")

                url = f"{base_clean}*{signature}"
            
            elif "https://static-rec.classx.co.in/drm/" in url:
                base_with_params, signature = url.split("*")
                base_clean = base_with_params.split("?")[0]
                base_clean = base_clean.replace("https://static-rec.classx.co.in", "https://appx-recordings-mcdn.akamai.net.in")
                url = f"{base_clean}*{signature}"

            elif "https://static-wsb.classx.co.in/" in url:
                clean_url = url.split("?")[0]
                clean_url = clean_url.replace("https://static-wsb.classx.co.in", "https://appx-wsb-gcp-mcdn.akamai.net.in")
                url = clean_url

            elif "https://static-db.classx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db.classx.co.in", "https://appxcontent.kaxa.in")

            elif "https://static-db-v2.classx.co.in/" in url:
                if "*" in url:
                    base_url, key = url.split("*", 1)
                    base_url = base_url.split("?")[0]
                    base_url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")
                    url = f"{base_url}*{key}"
                else:
                    base_url = url.split("?")[0]
                    url = base_url.replace("https://static-db-v2.classx.co.in", "https://appx-content-v2.classx.co.in")

            elif any(x in url for x in ["https://cpvod.testbook.com/", "classplusapp.com/drm/", "media-cdn.classplusapp.com", "media-cdn-alisg.classplusapp.com", "media-cdn-a.classplusapp.com", "tencdn.classplusapp", "videos.classplusapp", "webvideos.classplusapp.com"]):
                url_norm = url.replace("https://cpvod.testbook.com/", "https://media-cdn.classplusapp.com/drm/")
                api_url_call = f"https://covercel.vercel.app/extract_keys?url={url_norm}@bots_updatee&user_id={user_id}"

                keys_string = ""
                mpd = None
                try:
                    resp = requests.get(api_url_call, timeout=30)
                    try:
                        data = resp.json()
                    except Exception:
                        data = None
            
                    if isinstance(data, dict) and "KEYS" in data and "MPD" in data:
                        mpd = data.get("MPD")
                        keys = data.get("KEYS", [])
                        url = mpd
                        keys_string = " ".join([f"--key {k}" for k in keys])
            
                    elif isinstance(data, dict) and "url" in data:
                        url = data.get("url")
                        keys_string = ""
            
                    else:
                        try:
                            res = helper.get_mps_and_keys2(url_norm)
                            if res:
                                mpd, keys = res
                                url = mpd
                                keys_string = " ".join([f"--key {k}" for k in keys])
                            else:
                                keys_string = ""
                        except Exception:
                            keys_string = ""
                except Exception:
                    try:
                        res = helper.get_mps_and_keys2(url_norm)
                        if res:
                            mpd, keys = res
                            url = mpd
                            keys_string = " ".join([f"--key {k}" for k in keys])
                        else:
                            keys_string = ""
                    except Exception:
                        keys_string = ""

            elif "tencdn.classplusapp" in url:
                headers = {'host': 'api.classplusapp.com', 'x-access-token': f'{raw_text4}', 'accept-language': 'EN', 'api-version': '18', 'app-version': '1.4.73.2', 'build-number': '35', 'connection': 'Keep-Alive', 'content-type': 'application/json', 'device-details': 'Xiaomi_Redmi 7_SDK-32', 'device-id': 'c28d3cb16bbdac01', 'region': 'IN', 'user-agent': 'Mobile-Android', 'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c', 'accept-encoding': 'gzip'}
                params = {"url": f"{url}"}
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url = response.json().get('url', url)
            
            elif 'videos.classplusapp' in url:
                token_to_use = raw_text4 if raw_text4 != '/d' else cptoken
                url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': f'{token_to_use}'}).json().get('url', url)
            
            elif 'media-cdn.classplusapp.com' in url or 'media-cdn-alisg.classplusapp.com' in url or 'media-cdn-a.classplusapp.com' in url: 
                token_to_use = raw_text4 if raw_text4 != '/d' else cptoken
                headers = {'host': 'api.classplusapp.com', 'x-access-token': f'{token_to_use}', 'accept-language': 'EN', 'api-version': '18', 'app-version': '1.4.73.2', 'build-number': '35', 'connection': 'Keep-Alive', 'content-type': 'application/json', 'device-details': 'Xiaomi_Redmi 7_SDK-32', 'device-id': 'c28d3cb16bbdac01', 'region': 'IN', 'user-agent': 'Mobile-Android', 'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c', 'accept-encoding': 'gzip'}
                params = {"url": f"{url}"}
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url = response.json().get('url', url)

            elif "childId" in url and "parentId" in url:
                url = f"https://anonymouspwplayer-0e5a3f512dec.herokuapp.com/pw?url={url}&token={raw_text4}"

            if "edge.api.brightcove.com" in url:
                bcov = f'bcov_auth={cwtoken}'
                url = url.split("bcov_auth")[0] + bcov
                            
            elif "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
                url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={raw_text4}"

            if ".pdf*" in url:
                url = f"https://dragoapi.vercel.app/pdf/{url}"
            
            elif 'encrypted.m' in url:
                appxkey = url.split('*')[1]
                url = url.split('*')[0]

            if "youtu" in url:
                ytf = f"bv*[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[height<=?{raw_text2}]"
            elif "embed" in url:
                ytf = f"bestvideo[height<={raw_text2}]+bestaudio/best[height<={raw_text2}]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            if "jw-prod" in url:
                url = url.replace("https://apps-s3-jw-prod.utkarshapp.com/admin_v1/file_library/videos","https://d1q5ugnejk3zoi.cloudfront.net/ut-production-jw/admin_v1/file_library/videos")
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            elif "webvideos.classplusapp." in url:
                cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}.mp4"'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            # Formatted Captions
            cc = (
                f"**Index:** {str(count).zfill(3)}\n\n"
                f"**Title:** {name1}.mp4\n\n"
                f"**Topic:** {topic}\n\n"
                f"**Batch:** {b_name}\n\n"
                f"**Extracted By:** {CR}"
            )

            cc1 = (
                f"**Index:** {str(count).zfill(3)}\n\n"
                f"**Title:** {name1}.pdf\n\n"
                f"**Topic:** {topic}\n\n"
                f"**Batch:** {b_name}\n\n"
                f"**Extracted By:** {CR}"
            )

            cchtml = (
                f"**Index:** {str(count).zfill(3)}\n\n"
                f"**Title:** {name1}.html\n\n"
                f"**Topic:** {topic}\n\n"
                f"**Batch:** {b_name}\n\n"
                f"**Extracted By:** {CR}"
            )

            ccimg = (
                f"**Index:** {str(count).zfill(3)}\n\n"
                f"**Title:** {name1}\n\n"
                f"**Topic:** {topic}\n\n"
                f"**Batch:** {b_name}\n\n"
                f"**Extracted By:** {CR}"
            )

            ccm = (
                f"**Index:** {str(count).zfill(3)}\n\n"
                f"**Title:** {name1}\n\n"
                f"**Topic:** {topic}\n\n"
                f"**Batch:** {b_name}\n\n"
                f"**Extracted By:** {CR}"
            )

            cczip = (
                f"**Index:** {str(count).zfill(3)}\n\n"
                f"**Title:** {name1}.zip\n\n"
                f"**Topic:** {topic}\n\n"
                f"**Batch:** {b_name}\n\n"
                f"**Extracted By:** {CR}"
            )

            try:
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        await bot.send_document(chat_id=channel_id, document=ka, caption=cc1)
                        if os.path.exists(ka):
                            os.remove(ka)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        await asyncio.sleep(e.value)
                        continue    
  
                elif ".pdf" in url:
                    if "cwmediabkt99" in url:
                        max_retries = 3
                        retry_delay = 4
                        success = False
                        failure_msgs = []
                        
                        for attempt in range(max_retries):
                            try:
                                await asyncio.sleep(retry_delay)
                                url = url.replace(" ", "%20")
                                scraper = cloudscraper.create_scraper()
                                response = scraper.get(url)

                                if response.status_code == 200:
                                    with open(f'{name}.pdf', 'wb') as file:
                                        file.write(response.content)
                                    await asyncio.sleep(retry_delay)
                                    await bot.send_document(chat_id=channel_id, document=f'{name}.pdf', caption=cc1)
                                    if os.path.exists(f'{name}.pdf'):
                                        os.remove(f'{name}.pdf')
                                    success = True
                                    break
                                else:
                                    failure_msg = await m.reply_text(f"Attempt {attempt + 1}/{max_retries} failed: {response.status_code} {response.reason}")
                                    failure_msgs.append(failure_msg)
                                    
                            except Exception as e:
                                failure_msg = await m.reply_text(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                                failure_msgs.append(failure_msg)
                                await asyncio.sleep(retry_delay)
                                continue 

                        for msg in failure_msgs:
                            await msg.delete()
                            
                    else:
                        try:
                            cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                            download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                            proc = await asyncio.create_subprocess_shell(download_cmd)
                            await proc.communicate()
                            await bot.send_document(chat_id=channel_id, document=f'{name}.pdf', caption=cc1)
                            if os.path.exists(f'{name}.pdf'):
                                os.remove(f'{name}.pdf')
                        except FloodWait as e:
                            await m.reply_text(str(e))
                            await asyncio.sleep(e.value)
                            continue    

                elif ".ws" in url and url.endswith(".ws"):
                    try:
                        await helper.pdf_download(f"{api_url}utkash-ws?url={url}&authorization={api_token}", f"{name}.html")
                        await asyncio.sleep(1)
                        await bot.send_document(chat_id=channel_id, document=f"{name}.html", caption=cchtml)
                        if os.path.exists(f'{name}.html'):
                            os.remove(f'{name}.html')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        await asyncio.sleep(e.value)
                        continue    
                            
                elif any(ext_match in url for ext_match in [".jpg", ".jpeg", ".png"]):
                    try:
                        img_ext = url.split("?")[-1].split(".")[-1] if "." in url else "jpg"
                        cmd = f'yt-dlp -o "{name}.{img_ext}" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        proc = await asyncio.create_subprocess_shell(download_cmd)
                        await proc.communicate()
                        await bot.send_photo(chat_id=channel_id, photo=f'{name}.{img_ext}', caption=ccimg)
                        if os.path.exists(f'{name}.{img_ext}'):
                            os.remove(f'{name}.{img_ext}')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        await asyncio.sleep(e.value)
                        continue    

                elif any(ext_match in url for ext_match in [".mp3", ".wav", ".m4a"]):
                    try:
                        audio_ext = url.split("?")[-1].split(".")[-1] if "." in url else "mp3"
                        cmd = f'yt-dlp -x --audio-format {audio_ext} -o "{name}.{audio_ext}" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        proc = await asyncio.create_subprocess_shell(download_cmd)
                        await proc.communicate()
                        await bot.send_document(chat_id=channel_id, document=f'{name}.{audio_ext}', caption=ccm)
                        if os.path.exists(f'{name}.{audio_ext}'):
                            os.remove(f'{name}.{audio_ext}')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        await asyncio.sleep(e.value)
                        continue    
                    
                elif 'encrypted.m' in url:    
                    Show = f"<i><b>Video APPX Encrypted Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                    prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
                    try:
                        res_file = await helper.download_and_decrypt_video(url, cmd, name, appxkey)  
                        filename = res_file  
                        await prog.delete(True) 
                        if os.path.exists(filename):
                            await helper.send_vid(bot, m, cc, filename, thumb, name, prog, channel_id, watermark=watermark)
                        else:
                            await bot.send_message(channel_id, f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {link0}\n\n<blockquote><i><b>Failed Reason: Decrypted file not found</b></i></blockquote>', disable_web_page_preview=True)
                            failed_count += 1
                            continue
                    except Exception as e:
                        await bot.send_message(channel_id, f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {link0}\n\n<blockquote><i><b>Failed Reason: {str(e)}</b></i></blockquote>', disable_web_page_preview=True)
                        failed_count += 1
                        continue

                elif 'drmcdni' in url or 'drm/wv' in url or 'drm/common' in url:
                    Show = f"<i><b>📥 Fast Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                    prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
                    res_file = await helper.decrypt_and_merge_video(mpd, keys_string, path, name, raw_text2)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog, channel_id, watermark=watermark)
                    await asyncio.sleep(1)
                    continue

                else:
                    Show = f"<i><b>📥 Fast Video Downloading</b></i>\n<blockquote><b>{str(count).zfill(3)}) {name1}</b></blockquote>"
                    prog = await bot.send_message(channel_id, Show, disable_web_page_preview=True)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog, channel_id, watermark=watermark)
                    await asyncio.sleep(1)
                
            except Exception as e:
                await bot.send_message(channel_id, f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {link0}\n\n<blockquote><i><b>Failed Reason: {str(e)}</b></i></blockquote>', disable_web_page_preview=True)
                failed_count += 1
                continue

    except Exception as e:
        await m.reply_text(str(e))
        await asyncio.sleep(2)

   processed_range_count = end_idx - (start_idx - 1)
    success_count = processed_range_count - failed_count
    video_count = v2_count + mpd_count + m3u8_count + yt_count + drm_count + zip_count + other_count

    default_msg = (
        "<b>📬 ᴘʀᴏᴄᴇꜱꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>\n\n"
        f"<blockquote><b>📚 ʙᴀᴛᴄʜ ɴᴀᴍᴇ :</b> {b_name}</blockquote>\n"
        "╭────────────────\n"
        f"├ 🖇️ ᴛᴏᴛᴀʟ ᴜʀʟꜱ : <code>{processed_range_count}</code>\n"
        f"├ ✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ : <code>{success_count}</code>\n"
        f"├ ❌ ꜰᴀɪʟᴇᴅ : <code>{failed_count}</code>\n"
        "╰────────────────\n\n"
        "╭──────── 📦 ᴄᴀᴛᴇɢᴏʀʏ ────────\n"
        f"├ 🎞️ ᴠɪᴅᴇᴏꜱ : <code>{video_count}</code>\n"
        f"├ 📑 ᴘᴅꜰꜱ : <code>{pdf_count}</code>\n"
        f"├ 🖼️ ɪᴍᴀɢᴇꜱ : <code>{img_count}</code>\n"
        "╰────────────────────────────\n\n"
        f"<i>ᴇxᴛʀᴀᴄᴛᴇᴅ ʙʏ {CR} 🤖</i>"
    )

    custom_msg = (
        f"<b>-┈━═.•°✅ Completed ✅°•.═━┈-</b>\n"
        f"<blockquote><b>🎯Batch Name : {b_name}</b></blockquote>\n"
        f"<blockquote>🔗 Total URLs: {processed_range_count} \n"
        f"┃   ┠🔴 Total Failed URLs: {failed_count}\n"
        f"┃   ┠🟢 Total Successful URLs: {success_count}\n"
        f"┃   ┃   ┠🎥 Total Video URLs: {video_count}\n"
        f"┃   ┃   ┠📄 Total PDF URLs: {pdf_count}\n"
        f"┃   ┃   ┠📸 Total IMAGE URLs: {img_count}</blockquote>\n"
    )

    try:
        if str(raw_text7) == "/d":
            await bot.send_message(channel_id, default_msg)
        else:
            await bot.send_message(channel_id, custom_msg)
            await bot.send_message(
                m.chat.id,
                "<blockquote><b>✅ Your Task is completed, please check your Set Channel📱</b></blockquote>"
            )
    except Exception as e:
        # Fallback to direct private chat if the channel ID is invalid or bot is not an admin
        await m.reply_text(
            f"⚠️ **Could not send completion message to target channel (`{channel_id}`):**\n"
            f"<blockquote><i>{e}</i></blockquote>\n\n"
            "Make sure the bot is added as an **Admin** in the target channel."
        )
        await m.reply_text(default_msg)

# Single Direct URL Handler
@bot.on_message(filters.text & filters.private)
async def text_handler(bot: Client, m: Message):
    if m.from_user.is_bot:
        return
    links = m.text
    match = re.search(r'https?://\S+', links)
    if match:
        link = match.group(0)
    else:
        await m.reply_text("<pre><code>Invalid link format.</code></pre>")
        return
        
    editable = await m.reply_text("<pre><code>**🔹Processing your link...\n🔁Please wait...⏳**</code></pre>")
    await m.delete()

    await editable.edit(f"╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣ \n┣━━⪼ send `144`\n┣━━⪼ send `240`\n┣━━⪼ send `360`\n┣━━⪼ send `480`\n┣━━⪼ send `720`\n┣━━⪼ send `1080`\n╰━━⌈⚡[`{CREDIT}`]⚡⌋━━➣ ")
    input2: Message = await bot.listen(editable.chat.id, filters=filters.text & filters.user(m.from_user.id))
    raw_text2 = input2.text
    quality = f"{raw_text2}p"
    await input2.delete(True)
    
    name = f"video_{int(time.time())}"
    caption = (
        f"**Index:** 001\n\n"
        f"**Title:** {name}.mp4\n\n"
        f"**Topic:** General Topic\n\n"
        f"**Batch:** Single Link\n\n"
        f"**Extracted By:** {CREDIT}"
    )
    
    try:
        ytf = f"bv*[height<={raw_text2}]+ba/b[height<={raw_text2}]"
        cookie_arg = "--cookies youtube_cookies.txt" if "youtu" in link else ""
        cmd = f'yt-dlp {cookie_arg} -f "{ytf}" "{link}" -o "{name}.mp4"'
        
        await editable.edit("<i><b>📥 Downloading Video...</b></i>")
        filename = await helper.download_video(link, cmd, name)
        await editable.delete()
        await helper.send_vid(bot, m, caption, filename, "/d", name, None, m.chat.id, watermark=watermark)
    except Exception as e:
        await m.reply_text(f"⚠️ Error: {str(e)}")


@bot.on_callback_query(filters.regex("features"))
async def features_callback(client, callback_query: CallbackQuery):
    await callback_query.answer()
    features_text = (
        "**🔥 Bot Features 🔥**\n\n"
        "• 📥 Download DRM protected videos\n"
        "• 🎬 Support for multiple video formats\n"
        "• 📱 Works with YouTube and other platforms\n"
        "• 📑 PDF download support\n"
        "• 🖼️ Image download support\n"
        "• 🎵 Audio download support\n"
        "• 📝 Text to file conversion\n"
        "• ⚙️ Customizable quality settings\n"
        "• 🎨 Custom watermark support\n"
    )
    await callback_query.message.edit_text(
        features_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
        ])
    )


@bot.on_callback_query(filters.regex("details"))
async def details_callback(client, callback_query: CallbackQuery):
    await callback_query.answer()
    details_text = (
        "**📋 Bot Details 📋**\n\n"
        "• 🤖 Bot Name: DRM Wizard 🦋\n"
        "• 👨‍💻 Developer: IT'sGOLU.™®\n"
        "• 📱 Contact: @ITsGOLU_OWNER_BOT\n"
        "• 🔄 Version: 1.0\n"
        "• 📝 Language: Python\n"
        "• 🛠️ Framework: Pyrogram\n\n"
        "**🔐 Privacy & Security**\n\n"
        "• 🔒 Your data is secure with us\n"
        "• 🚫 We don't store your personal information\n"
        "• 🔐 End-to-end encryption for all communications\n"
    )
    await callback_query.message.edit_text(
        details_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
        ])
    )


@bot.on_callback_query(filters.regex("back_to_start"))
async def back_to_start_callback(client, callback_query: CallbackQuery):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    is_admin = db.is_admin(user_id)
    
    commands_list = (
        "**>  /drm - ꜱᴛᴀʀᴛ ᴜᴘʟᴏᴀᴅɪɴɢ ᴄᴘ/ᴄᴡ ᴄᴏᴜʀꜱᴇꜱ**\n"
        "**>  /plan - ᴠɪᴇᴡ ʏᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ᴅᴇᴛᴀɪʟꜱ**\n"
    )
    if is_admin:
        commands_list += "\n**👑 Admin Commands**\n• /users - List all users\n"
    
    await callback_query.message.edit_media(
        media=InputMediaPhoto(
            media=photologo,
            caption=f"**Mʏ ᴄᴏᴍᴍᴀɴᴅꜱ ғᴏʀ ʏᴏᴜ [{callback_query.from_user.first_name} ](tg://settings)**\n\n{commands_list}"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("𝐈𝐓'𝐬𝐆𝐎𝐋𝐔.™®", url="https://t.me/ITsGOLU_OWNER_BOT")],
            [
                InlineKeyboardButton("ғᴇᴀᴛᴜʀᴇꜱ 🪔", callback_data="features"),
                InlineKeyboardButton("ᴅᴇᴛᴀɪʟꜱ 🦋", callback_data="details")
            ]
        ])
    )

print("Bot Started...")
bot.run()
