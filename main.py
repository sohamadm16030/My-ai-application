import os
import json
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from groq import Groq
from duckduckgo_search import DDGS

# =========================
# CONFIG
# =========================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

OWNER_ID = 123456789012345678

client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# =========================
# DATA FILES
# =========================

MEMORY_FILE = "memory.json"
SERVER_BRAIN_FILE = "server_brain.json"
TASK_FILE = "tasks.json"
CONFIG_FILE = "config.json"

def load_file(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def save_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

user_memory = load_file(MEMORY_FILE, {})
server_brain = load_file(SERVER_BRAIN_FILE, {})
tasks = load_file(TASK_FILE, {})
config = load_file(CONFIG_FILE, {
    "pro_users": [],
    "ai_channels": {},
    "internet_mode": {},
    "user_modes": {}
})

# =========================
# AI SYSTEM
# =========================

BASE_PROMPT = """
You are Thinksy.
You are intelligent, calm, and futuristic.
Explain clearly and help users effectively.
"""

def build_system_prompt(user_id):

    mode = config["user_modes"].get(str(user_id), "normal")

    if mode == "scientist":
        return BASE_PROMPT + "\nRespond like a scientist with logical explanations."

    if mode == "philosopher":
        return BASE_PROMPT + "\nRespond thoughtfully like a philosopher."

    if mode == "hacker":
        return BASE_PROMPT + "\nRespond like a technical hacker expert."

    return BASE_PROMPT

async def ai_reply(channel, user_id, text):

    uid = str(user_id)

    if uid not in user_memory:
        user_memory[uid] = [{"role":"system","content":build_system_prompt(user_id)}]

    # INTERNET MODE
    if config["internet_mode"].get(uid):
        try:
            results=[]
            with DDGS() as ddgs:
                for r in ddgs.text(text, max_results=3):
                    results.append(r["body"])
            info="\n".join(results)
            text=f"Use this info:\n{info}\n\nQuestion:{text}"
        except:
            pass

    user_memory[uid].append({"role":"user","content":text})

    pro = user_id in config["pro_users"]

    limit = 40 if pro else 15

    if len(user_memory[uid]) > limit:
        user_memory[uid] = user_memory[uid][-limit:]

    model = "llama-3.3-70b-versatile" if pro else "llama3-8b-8192"

    try:
        async with channel.typing():
            response = client.chat.completions.create(
                model=model,
                messages=user_memory[uid]
            )

        answer = response.choices[0].message.content

        user_memory[uid].append({"role":"assistant","content":answer})

        save_file(MEMORY_FILE, user_memory)

        if len(answer) > 2000:
            answer = answer[:1990]

        await channel.send(answer)

    except Exception as e:
        print(e)
        await channel.send("AI error.")

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    await tree.sync()
    print("Thinksy v3 ready")

# =========================
# SETUP AI CHANNEL
# =========================

@bot.command()
async def setup(ctx):

    config["ai_channels"][str(ctx.guild.id)] = ctx.channel.id
    save_file(CONFIG_FILE, config)

    await ctx.send("AI chat channel set.")

@tree.command(name="setup")
async def setup_slash(interaction:discord.Interaction):

    config["ai_channels"][str(interaction.guild.id)] = interaction.channel.id
    save_file(CONFIG_FILE, config)

    await interaction.response.send_message("AI channel set.")

# =========================
# BASIC AI
# =========================

@bot.command()
async def ai(ctx,*,question):
    await ai_reply(ctx.channel, ctx.author.id, question)

# =========================
# THREAD AI
# =========================

@bot.command()
async def threadai(ctx):

    thread = await ctx.channel.create_thread(
        name=f"Thinksy-{ctx.author.name}",
        type=discord.ChannelType.public_thread
    )

    await thread.send(f"{ctx.author.mention} your AI thread is ready.")

# =========================
# MODE SYSTEM
# =========================

@bot.command()
async def mode(ctx, mode):

    config["user_modes"][str(ctx.author.id)] = mode
    save_file(CONFIG_FILE, config)

    await ctx.send(f"Mode set to {mode}")

# =========================
# INTERNET MODE
# =========================

@bot.command()
async def internet(ctx, state):

    uid = str(ctx.author.id)

    if state.lower() == "on":
        config["internet_mode"][uid] = True
        await ctx.send("Internet research ON")

    else:
        config["internet_mode"][uid] = False
        await ctx.send("Internet research OFF")

    save_file(CONFIG_FILE, config)

# =========================
# SERVER BRAIN
# =========================

@bot.command()
async def teach(ctx, key, *, value):

    gid=str(ctx.guild.id)

    if gid not in server_brain:
        server_brain[gid]={}

    server_brain[gid][key]=value

    save_file(SERVER_BRAIN_FILE, server_brain)

    await ctx.send("Stored in Thinksy brain.")

@bot.command()
async def ask(ctx, key):

    gid=str(ctx.guild.id)

    if gid in server_brain and key in server_brain[gid]:
        await ctx.send(server_brain[gid][key])
    else:
        await ctx.send("I don't know that.")

# =========================
# REMINDER
# =========================

@bot.command()
async def remind(ctx,time,*,msg):

    unit=time[-1]
    amount=int(time[:-1])

    if unit=="m":
        seconds=amount*60
    elif unit=="h":
        seconds=amount*3600
    else:
        seconds=amount

    await ctx.send("Reminder set.")

    await asyncio.sleep(seconds)

    await ctx.send(f"{ctx.author.mention} reminder: {msg}")

# =========================
# TASK SYSTEM
# =========================

@bot.command()
async def task(ctx,*,text):

    uid=str(ctx.author.id)

    if uid not in tasks:
        tasks[uid]=[]

    tasks[uid].append(text)

    save_file(TASK_FILE, tasks)

    await ctx.send("Task saved.")

@bot.command()
async def tasklist(ctx):

    uid=str(ctx.author.id)

    if uid not in tasks or not tasks[uid]:
        await ctx.send("No tasks.")
        return

    msg="\n".join(tasks[uid])

    await ctx.send(msg)

# =========================
# SERVER STATS
# =========================

@bot.command()
async def serverstats(ctx):

    g=ctx.guild

    embed=discord.Embed(title="Server Stats")

    embed.add_field(name="Members",value=g.member_count)
    embed.add_field(name="Channels",value=len(g.channels))
    embed.add_field(name="Roles",value=len(g.roles))

    await ctx.send(embed=embed)

# =========================
# SECURITY SCAN
# =========================

@bot.command()
async def scan(ctx,*,text):

    prompt=f"""
Check if this message or link may be a scam or dangerous.

{text}

Explain risk level.
"""

    await ai_reply(ctx.channel, ctx.author.id, prompt)

# =========================
# RESET MEMORY
# =========================

@bot.command()
async def reset(ctx):

    uid=str(ctx.author.id)

    if uid in user_memory:
        del user_memory[uid]

    save_file(MEMORY_FILE, user_memory)

    await ctx.send("Memory cleared.")

# =========================
# OWNER PRO COMMAND
# =========================

@tree.command(name="addpro")
async def addpro(interaction:discord.Interaction,user:discord.Member):

    if interaction.user.id!=OWNER_ID:
        await interaction.response.send_message("Not allowed",ephemeral=True)
        return

    config["pro_users"].append(user.id)
    save_file(CONFIG_FILE, config)

    await interaction.response.send_message(f"{user.name} is now Pro.")

# =========================
# MESSAGE LISTENER
# =========================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.guild:

        gid=str(message.guild.id)

        if gid in config["ai_channels"]:

            if message.channel.id == config["ai_channels"][gid]:

                if message.content.startswith("!msg"):
                    return

                await ai_reply(
                    message.channel,
                    message.author.id,
                    message.content
                )

    # PRO DM CHAT
    if isinstance(message.channel, discord.DMChannel):

        if message.author.id not in config["pro_users"]:
            await message.channel.send("DM chat is Pro only.")
            return

        await ai_reply(
            message.channel,
            message.author.id,
            message.content
        )

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
