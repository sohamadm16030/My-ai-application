import os
import json
import asyncio
import discord
import requests
from discord.ext import commands
from groq import Groq
from duckduckgo_search import DDGS

# ================= CONFIG =================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OWNER_ID = 1456136074282930251

groq_client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= FILES =================

def load(name, default):
    if os.path.exists(name):
        return json.load(open(name))
    return default

def save(name, data):
    json.dump(data, open(name, "w"))

memory = load("memory.json", {})
config = load("config.json", {
    "pro_users": [],
    "ai_channels": {},
    "modes": {},
    "internet": {}
})

tasks = load("tasks.json", {})

# ================= AI CORE =================

def system_prompt(uid):
    mode = config["modes"].get(str(uid), "normal")

    base = "You are Thinksy, a smart futuristic AI. your creater and owner is Blaze and u are helpful and funny"

    if mode == "scientist":
        return base + " Explain logically."
    if mode == "hacker":
        return base + " Be technical."
    if mode == "philosopher":
        return base + " Be deep and thoughtful."

    return base

async def call_groq(messages, pro):
    model = "openai/gpt-oss-120b" if pro else "openai/gpt-oss-20b"

    return groq_client.chat.completions.create(
        model=model,
        messages=messages
    ).choices[0].message.content

async def call_openrouter(messages, pro):
    model = "openai/gpt-oss-120b" if pro else "openai/gpt-oss-20b"

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}"
        },
        json={
            "model": model,
            "messages": messages
        }
    )

    return r.json()["choices"][0]["message"]["content"]

async def ai_call(messages, pro):
    # AUTO SWITCH SYSTEM
    try:
        return await call_groq(messages, pro)
    except Exception as e:
        print("Groq failed:", e)

    try:
        return await call_openrouter(messages, pro)
    except Exception as e:
        print("OpenRouter failed:", e)

    return "AI is currently unavailable."

# ================= AI REPLY =================

async def ai_reply(channel, uid, text):

    uid = str(uid)

    if uid not in memory:
        memory[uid] = [{"role":"system","content":system_prompt(uid)}]

    # INTERNET MODE
    if config["internet"].get(uid):
        try:
            results=[]
            with DDGS() as ddgs:
                for r in ddgs.text(text, max_results=3):
                    results.append(r["body"])
            text = "Info:\n" + "\n".join(results) + "\n\nQ:" + text
        except:
            pass

    memory[uid].append({"role":"user","content":text})

    pro = int(uid) in config["pro_users"]

    if len(memory[uid]) > (40 if pro else 15):
        memory[uid] = memory[uid][-15:]

    async with channel.typing():
        reply = await ai_call(memory[uid], pro)

    memory[uid].append({"role":"assistant","content":reply})
    save("memory.json", memory)

    await channel.send(reply[:2000])

# ================= COMMANDS =================

@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def ai(ctx, *, q):
    await ai_reply(ctx.channel, ctx.author.id, q)

@bot.command()
async def setup(ctx):
    config["ai_channels"][str(ctx.guild.id)] = ctx.channel.id
    save("config.json", config)
    await ctx.send("AI channel set.")

@bot.command()
async def mode(ctx, m):
    config["modes"][str(ctx.author.id)] = m
    save("config.json", config)
    await ctx.send("Mode updated.")

@bot.command()
async def internet(ctx, state):
    config["internet"][str(ctx.author.id)] = state == "on"
    save("config.json", config)
    await ctx.send("Internet mode updated.")

@bot.command()
async def task(ctx, *, t):
    uid=str(ctx.author.id)
    tasks.setdefault(uid, []).append(t)
    save("tasks.json", tasks)
    await ctx.send("Task saved.")

@bot.command()
async def tasklist(ctx):
    uid=str(ctx.author.id)
    await ctx.send("\n".join(tasks.get(uid, ["No tasks"])))

@bot.command()
async def remind(ctx, time, *, msg):
    sec = int(time[:-1]) * (60 if time[-1]=="m" else 3600)
    await ctx.send("Reminder set.")
    await asyncio.sleep(sec)
    await ctx.send(f"{ctx.author.mention} {msg}")

@bot.command()
async def scan(ctx, *, text):
    await ai_reply(ctx.channel, ctx.author.id, f"Check if scam: {text}")

@bot.command()
async def threadai(ctx):
    t = await ctx.channel.create_thread(name=f"Thinksy-{ctx.author.name}")
    await t.send("Thread ready.")

# ================= LISTENER =================

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    # AI CHANNEL AUTO CHAT
    if msg.guild:
        gid=str(msg.guild.id)
        if gid in config["ai_channels"]:
            if msg.channel.id == config["ai_channels"][gid]:
                if not msg.content.startswith("!msg"):
                    await ai_reply(msg.channel, msg.author.id, msg.content)

    # DM (PRO ONLY)
    if isinstance(msg.channel, discord.DMChannel):
        if msg.author.id in config["pro_users"]:
            await ai_reply(msg.channel, msg.author.id, msg.content)
        else:
            await msg.channel.send("Pro only feature.")

    await bot.process_commands(msg)

# ================= START =================

bot.run(DISCORD_TOKEN)
