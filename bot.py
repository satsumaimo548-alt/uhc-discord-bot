import discord
from discord.ext import commands, tasks
import requests
import os
import asyncio

# ======================
# 環境変数
# ======================

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
HYPIXEL_API_KEY = os.environ["HYPIXEL_API_KEY"]

# ======================
# 設定
# ======================

GUILD_ID = 1401111226133516299
SOLO_CHANNEL_ID = 1455567694706376705
TEAM_CHANNEL_ID = 1455567665585455197

UPDATE_SECONDS = 360  # 6分（安全）

# ======================
# Bot設定（重要）
# ======================

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# Hypixel API
# ======================

def get_uhc_counts():
    url = "https://api.hypixel.net/v2/counts"
    headers = {"API-Key": HYPIXEL_API_KEY}

    r = requests.get(url, headers=headers, timeout=10)
    data = r.json()

    if not data.get("success"):
        print("Hypixel API Error:", data)
        return 0, 0

    modes = data["games"]["UHC"]["modes"]

    solo = modes.get("SOLO", 0)
    teams = modes.get("TEAMS", 0)

    if isinstance(solo, dict):
        solo = solo.get("players", 0)
    if isinstance(teams, dict):
        teams = teams.get("players", 0)

    return solo, teams

# ======================
# 定期更新
# ======================

@tasks.loop(seconds=UPDATE_SECONDS)
async def update_channels():
    try:
        solo, teams = get_uhc_counts()

        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            print("Guildが見つかりません")
            return

        solo_ch = guild.get_channel(SOLO_CHANNEL_ID)
        team_ch = guild.get_channel(TEAM_CHANNEL_ID)

        if solo_ch:
            name = f"🧍 UHC Solo｜{solo}"
            if solo_ch.name != name:
                await solo_ch.edit(name=name)

        if team_ch:
            name = f"👥 UHC Teams｜{teams}"
            if team_ch.name != name:
                await team_ch.edit(name=name)

        print(f"更新完了｜Solo {solo}｜Teams {teams}")

    except Exception as e:
        print("更新失敗:", e)

# ======================
# 起動時
# ======================

@bot.event
async def on_ready():
    print(f"ログイン成功: {bot.user}")
    if not update_channels.is_running():
        update_channels.start()

# ======================
# 安全起動（429対策）
# ======================

async def main():
    while True:
        try:
            await bot.start(DISCORD_TOKEN)
        except discord.HTTPException as e:
            if e.status == 429:
                print("429 Rate Limit → 60秒待機")
                await asyncio.sleep(60)
            else:
                raise
        except Exception as e:
            print("致命的エラー:", e)
            await asyncio.sleep(30)

asyncio.run(main())
