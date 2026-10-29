
# Python 3.11+
# File: raidbot.py

import os
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

# Full requested command directory (150 entries).
COMMAND_NAMES = """
nuke banall kickall massban masskick roledelete channeldelete
categorydelete webhookspam massdm servername servericon vanityclaim
everyoneping hereping roleping spam spamall channelspam dmspam raidmode
lockdown unlock purge purgeall prune prunemembers rolecreate channelcreate
categorycreate massrole striproles adminall ownersteal inviteabuse inviteflood
webhookcreate webhookdelete emojiabuse stickerabuse reactionspam threadspam
forumspam stagehijack voicekick voicemove voicespam deafenall muteall
unmuteall undeafenall massmove channelrename categoryrename rolerename
nickall nickspam statusspam presenceflood activityspam embedspam filespam
stickerspam emojispam gifspam imageflood linkflood invitelinkspam massinvite
raidinvite botadd botflood tokengrab selfbot clone serverclone backup restore
wipe fullwipe softbanall hardbanall unbanall banwave kickwave rolewave
channelwave categorywave webhookwave dmwave pingwave mentionwave everyonewave
herewave rolewaveping spamwave flood floodall textflood voiceflood memberflood
joinflood leaveflood rejoinspam altflood proxyflood ratelimitbypass antirate
cooldowndisable permissionsteal adminsteal modsteal overwritesteal
channelpermsteal rolepermsteal hierarchybreak toppos bottompos rolepos
channelpos categorypos massoverwrite clearoverwrites denyall allowall
viewchanneldeny sendmessagedeny connectdeny speakdeny streamdeny reactdeny
attachdeny embeddeny historydeny managechanneldeny manageroledeny
banmembersdeny kickmembersdeny mentionalldeny externalemojideny
externalstickerdeny useappdeny requesttospeakdeny createinvitedeny
changenicknameall forcednick resetnicks massdeafen massmute fullraid
""".split()

PAGE_SIZE = 25


@bot.event
async def on_ready():
    print(f"Online as {bot.user} | {len(bot.guilds)} guilds")
    print(f"Command directory: {len(COMMAND_NAMES)} entries")


@bot.command(name="cmds", aliases=["commands", "helpme"])
async def cmds(ctx, page: int = 1):
    """Show the command directory. Usage: !cmds [page]"""
    total_pages = (len(COMMAND_NAMES) + PAGE_SIZE - 1) // PAGE_SIZE

    if not 1 <= page <= total_pages:
        await ctx.reply(
            f"Choose a page from 1 to {total_pages}.",
            mention_author=False,
        )
        return

    start = (page - 1) * PAGE_SIZE
    entries = COMMAND_NAMES[start:start + PAGE_SIZE]

    embed = discord.Embed(
        title="Discord Bot | Commands",
        description=(
            "Working commands are available to use. "
            "Raid-only entries are listed for reference and are disabled."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name=f"Commands {start + 1}-{start + len(entries)}",
        value="\n".join(
            f"`!{name}`"
            + (" — available" if name in bot.all_commands
               else " — disabled / not implemented")
            for name in entries
        ),
        inline=False,
    )
    embed.set_footer(
        text=f"Page {page}/{total_pages} | Use !cmds {min(page + 1, total_pages)} for the next page"
    )
    await ctx.reply(embed=embed, mention_author=False)


@bot.command()
async def ping(ctx):
    """Check whether the bot is responding."""
    ms = round(bot.latency * 1000)
    await ctx.reply(f"Pong! Latency: {ms} ms", mention_author=False)


@bot.command()
@commands.has_guild_permissions(manage_messages=True)
@commands.bot_has_guild_permissions(manage_messages=True)
async def purge(ctx, amount: int = 10):
    """Delete up to 100 recent messages. Usage: !purge 20"""
    if not 1 <= amount <= 100:
        await ctx.reply("Choose an amount between 1 and 100.")
        return

    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(
        f"Deleted {max(0, len(deleted) - 1)} messages.",
        delete_after=5,
    )


@bot.command()
@commands.has_guild_permissions(manage_channels=True)
@commands.bot_has_guild_permissions(manage_channels=True)
async def lockdown(ctx):
    """Prevent regular members from sending messages in this channel."""
    channel = ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite,
        reason=f"Channel lockdown by {ctx.author}",
    )
    await ctx.send("This channel is now locked.")


@bot.command()
@commands.has_guild_permissions(manage_channels=True)
@commands.bot_has_guild_permissions(manage_channels=True)
async def unlock(ctx):
    """Restore the default role's send-message setting."""
    channel = ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = None
    await channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite,
        reason=f"Channel unlocked by {ctx.author}",
    )
    await ctx.send("The channel's default send-message setting was restored.")


@bot.command()
@commands.has_guild_permissions(manage_channels=True)
@commands.bot_has_guild_permissions(manage_channels=True)
async def channelcreate(ctx, *, name: str):
    """Create one text channel. Usage: !channelcreate announcements"""
    name = name.strip().replace(" ", "-")[:100]
    if not name:
        await ctx.reply("Provide a channel name.")
        return

    channel = await ctx.guild.create_text_channel(
        name,
        reason=f"Requested by {ctx.author}",
    )
    await ctx.reply(f"Created channel: {channel.mention}")


@bot.command()
@commands.has_guild_permissions(manage_roles=True)
@commands.bot_has_guild_permissions(manage_roles=True)
async def rolecreate(ctx, *, name: str):
    """Create one role. Usage: !rolecreate Event Member"""
    name = name.strip()[:100]
    if not name:
        await ctx.reply("Provide a role name.")
        return

    role = await ctx.guild.create_role(
        name=name,
        reason=f"Requested by {ctx.author}",
    )
    await ctx.reply(f"Created role: {role.mention}")


@bot.command()
@commands.has_guild_permissions(manage_guild=True)
async def servername(ctx, *, name: str):
    """Change the server name."""
    name = name.strip()[:100]
    if not name:
        await ctx.reply("Provide a server name.")
        return

    await ctx.guild.edit(
        name=name,
        reason=f"Requested by {ctx.author}",
    )
    await ctx.reply(f"Server name changed to **{name}**.")


@bot.command()
@commands.has_guild_permissions(manage_nicknames=True)
@commands.bot_has_guild_permissions(manage_nicknames=True)
async def resetnicks(ctx, member: discord.Member):
    """Reset one member's nickname. Usage: !resetnicks @member"""
    await member.edit(
        nick=None,
        reason=f"Requested by {ctx.author}",
    )
    await ctx.reply(f"Reset the nickname for {member.mention}.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(
            "You don't have permission to use that command.",
            mention_author=False,
        )
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.reply(
            "The bot needs additional server permissions.",
            mention_author=False,
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(
            f"Missing argument: `{error.param.name}`.",
            mention_author=False,
        )
    elif isinstance(error, commands.BadArgument):
        await ctx.reply(
            "Invalid argument. Check the command usage.",
            mention_author=False,
        )
    else:
        print(f"Command error: {type(error).__name__}: {error}")
        await ctx.reply(
            "The command failed. Check the Render logs.",
            mention_author=False,
        )


bot.run(TOKEN)
