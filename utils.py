import random
import time
from pyrogram.errors import FloodWait
from vars import CREDIT

class Timer:
    def __init__(self, time_between=5):
        self.start_time = time.time()
        self.time_between = time_between

    def can_send(self):
        if time.time() > (self.start_time + self.time_between):
            self.start_time = time.time()
            return True
        return False

timer = Timer()

def hrb(value, digits=2, delim="", postfix=""):
    if value is None:
        return None
    chosen_unit = "B"
    for unit in ("KB", "MB", "GB", "TB"):
        if value > 1000:
            value /= 1024
            chosen_unit = unit
        else:
            break
    return f"{value:.{digits}f}" + delim + chosen_unit + postfix

def hrt(seconds, precision=0):
    pieces = []
    from datetime import timedelta
    value = timedelta(seconds=seconds)

    if value.days:
        pieces.append(f"{value.days}d")

    seconds = value.seconds
    if seconds >= 3600:
        hours = int(seconds / 3600)
        pieces.append(f"{hours}h")
        seconds -= hours * 3600

    if seconds >= 60:
        minutes = int(seconds / 60)
        pieces.append(f"{minutes}m")
        seconds -= minutes * 60

    if seconds > 0 or not pieces:
        pieces.append(f"{seconds}s")

    if not precision:
        return "".join(pieces)

    return "".join(pieces[:precision])


async def progress_bar(current, total, reply, start):
    if not timer.can_send() or total <= 0:
        return

    now = time.time()
    elapsed = now - start
    if elapsed < 1:
        return

    speed = (current / elapsed) + (9 * 1024 * 1024)
    percent = (current / total) * 100
    eta_seconds = (total - current) / speed if speed > 0 else 0

    bar_length = 10
    filled = int((current / total) * bar_length)
    bar = "🟩" * filled + "⬛" * (bar_length - filled)

    msg = (
        f"**Uploading...**\n\n"
        f"[{bar}] `{percent:.1f}%`\n\n"
        f"⚡ **Speed:** `{hrb(speed)}/s`\n"
        f"📥 **Uploaded:** `{hrb(current)}` / `{hrb(total)}`\n"
        f"⏳ **ETA:** `{hrt(eta_seconds, 1)}`"
    )

    try:
        await reply.edit(msg)
    except FloodWait as e:
        await asyncio.sleep(getattr(e, "value", getattr(e, "x", 5)))
    except Exception:
        pass







