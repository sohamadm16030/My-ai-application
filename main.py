import os
import discord
import threading
import time
import requests
from discord.ext import commands
from discord import app_commands
from groq import Groq
from keep_alive import keep_alive

# -----------------------------
# KEEP ALIVE SERVER
# -----------------------------

keep_alive()

# -----------------------------
# SELF PING (HELPS REPLIT STAY ACTIVE)
# -----------------------------

REPL_URL = os.getenv("REPL_URL")

def self_ping():
    while True:
        try:
            if REPL_URL:
                requests.get(REPL_URL)
        except:
            pass
        time.sleep(240)

threading.Thread(target=self_ping).start()

# -----------------------------
# TOKENS
# -----------------------------

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# BOT SETUP
# -----------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# PRO USERS
# -----------------------------

pro_users = [
    1456136074282930251,
    1060181057514778704,
    1190610939515502732
]

def is_pro(user_id):
    return user_id in pro_users

# -----------------------------
# AI CHANNEL STORAGE
# -----------------------------

ai_channels = {}

# -----------------------------
# MEMORY SYSTEM
# -----------------------------

user_memory = {}

SYSTEM_PROMPT = """
You are Thinksy, an intelligent AI assistant.

Personality:
- smart
- friendly
- logical
- explains clearly
- remembers conversations

Never mention AI models or Groq.
Act like an independent AI assistant.
Your creator is Blaze but only mention if asked.
"""

# -----------------------------
# BOT READY
# -----------------------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Thinksy AI is online as {bot.user}")

# -----------------------------
# AI RESPONSE
# -----------------------------

async def ai_reply(channel, user_id, text, pro=False):

    if user_id not in user_memory:
        user_memory[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    user_memory[user_id].append({
        "role": "user",
        "content": text
    })

    memory_limit = 40 if pro else 15

    if len(user_memory[user_id]) > memory_limit:
        user_memory[user_id] = user_memory[user_id][-memory_limit:]

    try:

        async with channel.typing():

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=user_memory[user_id]
            )

        answer = response.choices[0].message.content

        user_memory[user_id].append({
            "role": "assistant",
            "content": answer
        })

        if len(answer) > 2000:
            answer = answer[:1990] + "..."

        await channel.send(answer)

    except Exception as e:
        print("AI ERROR:", e)
        await channel.send("⚠️ AI error occurred.")

# -----------------------------
# COMMANDS
# -----------------------------

@bot.command()
async def ai(ctx, *, question):
    await ai_reply(ctx.channel, ctx.author.id, question, pro=is_pro(ctx.author.id))

@bot.command()
async def reset(ctx):

    if ctx.author.id in user_memory:
        del user_memory[ctx.author.id]

    await ctx.send("Your AI memory has been reset.")

@bot.command()
async def code(ctx, *, prompt):

    if not is_pro(ctx.author.id):
        await ctx.send(" This command is only for Thinksy Pro users.")
        return

    await ai_reply(ctx.channel, ctx.author.id, f"Write code for: {prompt}", pro=True)

@bot.command()
async def research(ctx, *, topic):

    if not is_pro(ctx.author.id):
        await ctx.send(" This command is only for Thinksy Pro users.")
        return

    await ai_reply(ctx.channel, ctx.author.id, f"Research deeply: {topic}", pro=True)

@bot.command()
async def joke(ctx):
    await ai_reply(ctx.channel, ctx.author.id, "Tell me a funny joke that will make us laugh", pro=is_pro(ctx.author.id))

# -----------------------------
# SLASH COMMAND
# -----------------------------

@bot.tree.command(name="setup", description="Set Thinksy auto chat channel")
@app_commands.describe(channel="Select AI chat channel")

async def set_ai_channel(interaction: discord.Interaction, channel: discord.TextChannel):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "⚠️ Only administrators can use this command.",
            ephemeral=True
        )
        return

    ai_channels[interaction.guild.id] = channel.id

    await interaction.response.send_message(
        f"AI chat channel set to {channel.mention}"
    )

# -----------------------------
# MESSAGE HANDLER
# -----------------------------

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    # PRO DM CHAT

    if isinstance(message.channel, discord.DMChannel):

        if not is_pro(message.author.id):
            await message.channel.send("DM chatting is Thinksy Pro only.")
            return

        await ai_reply(message.channel, message.author.id, message.content, pro=True)
        return

    # AUTO AI CHANNEL

    if message.guild:

        guild_id = message.guild.id

        if guild_id in ai_channels:

            if message.channel.id == ai_channels[guild_id]:

                await ai_reply(
                    message.channel,
                    message.author.id,
                    message.content,
                    pro=is_pro(message.author.id)
                )
                return

    await bot.process_commands(message)

# -----------------------------
# RUN BOT
# -----------------------------

bot.run(DISCORD_TOKEN)
