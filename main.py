import os
import discord
from discord.ext import commands
from groq import Groq

# -----------------------------
# TOKENS
# -----------------------------

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# PRO USERS
# -----------------------------

pro_users = [
    123456789012345678
]

def is_pro(user_id):
    return user_id in pro_users


# -----------------------------
# MEMORY SYSTEM
# -----------------------------

user_memory = {}

SYSTEM_PROMPT = """
You are Thinksy.

Personality:
- calm
- intelligent
- strategic
- futuristic
- helpful

You explain ideas clearly and logically.
You remember previous messages in conversation.
Never mention AI models or APIs.
"""


# -----------------------------
# AI RESPONSE FUNCTION
# -----------------------------

async def ai_reply(channel, user_id, prompt, pro=False):

    if user_id not in user_memory:
        user_memory[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    user_memory[user_id].append({
        "role": "user",
        "content": prompt
    })

    memory_limit = 40 if pro else 15

    if len(user_memory[user_id]) > memory_limit:
        user_memory[user_id] = user_memory[user_id][-memory_limit:]

    model = "llama-3.1-70b-versatile" if pro else "llama-3.1-8b-instant"

    try:

        async with channel.typing():

            response = client.chat.completions.create(
                model=model,
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
# BOT READY
# -----------------------------

@bot.event
async def on_ready():
    print(f"Thinksy is online as {bot.user}")


# -----------------------------
# BASIC AI
# -----------------------------

@bot.command()
async def ai(ctx, *, question):

    await ai_reply(
        ctx.channel,
        ctx.author.id,
        question,
        pro=is_pro(ctx.author.id)
    )


# -----------------------------
# EXPLAIN COMMAND
# -----------------------------

@bot.command()
async def explain(ctx, *, topic):

    await ai_reply(
        ctx.channel,
        ctx.author.id,
        f"Explain this clearly: {topic}",
        pro=is_pro(ctx.author.id)
    )


# -----------------------------
# SUMMARIZE
# -----------------------------

@bot.command()
async def summarize(ctx, *, text):

    await ai_reply(
        ctx.channel,
        ctx.author.id,
        f"Summarize this text: {text}",
        pro=is_pro(ctx.author.id)
    )


# -----------------------------
# BRAINSTORM
# -----------------------------

@bot.command()
async def brainstorm(ctx, *, idea):

    await ai_reply(
        ctx.channel,
        ctx.author.id,
        f"Brainstorm creative ideas about: {idea}",
        pro=is_pro(ctx.author.id)
    )


# -----------------------------
# RESEARCH (PRO)
# -----------------------------

@bot.command()
async def research(ctx, *, topic):

    if not is_pro(ctx.author.id):
        await ctx.send("💎 Research is a Thinksy Pro feature.")
        return

    await ai_reply(
        ctx.channel,
        ctx.author.id,
        f"Provide a deep research explanation on: {topic}",
        pro=True
    )


# -----------------------------
# CODE GENERATOR (PRO)
# -----------------------------

@bot.command()
async def code(ctx, *, prompt):

    if not is_pro(ctx.author.id):
        await ctx.send("💎 Coding tools are Thinksy Pro features.")
        return

    await ai_reply(
        ctx.channel,
        ctx.author.id,
        f"Write code for: {prompt}",
        pro=True
    )


# -----------------------------
# FUN COMMANDS
# -----------------------------

@bot.command()
async def joke(ctx):

    await ai_reply(
        ctx.channel,
        ctx.author.id,
        "Tell me a funny joke.",
        pro=is_pro(ctx.author.id)
    )


@bot.command()
async def riddle(ctx):

    await ai_reply(
        ctx.channel,
        ctx.author.id,
        "Give me a clever riddle.",
        pro=is_pro(ctx.author.id)
    )


@bot.command()
async def fact(ctx):

    await ai_reply(
        ctx.channel,
        ctx.author.id,
        "Tell me an interesting fact.",
        pro=is_pro(ctx.author.id)
    )


# -----------------------------
# RESET MEMORY
# -----------------------------

@bot.command()
async def reset(ctx):

    user_id = ctx.author.id

    if user_id in user_memory:
        del user_memory[user_id]

    await ctx.send("🧠 Your Thinksy memory was reset.")


# -----------------------------
# HELP MENU
# -----------------------------

@bot.command()
async def helpai(ctx):

    await ctx.send(
        """
🤖 **Thinksy Commands**

AI:
!ai question
!explain topic
!summarize text
!brainstorm idea

Fun:
!joke
!riddle
!fact

Pro:
!research topic
!code prompt

Utility:
!reset
"""
    )


# -----------------------------
# DM CHAT (PRO ONLY)
# -----------------------------

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):

        if not is_pro(message.author.id):
            await message.channel.send(
                "💎 DM chatting is available in Thinksy Pro."
            )
            return

        await ai_reply(
            message.channel,
            message.author.id,
            message.content,
            pro=True
        )

    await bot.process_commands(message)


# -----------------------------
# RUN BOT
# -----------------------------

bot.run(DISCORD_TOKEN)
