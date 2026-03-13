import os
import discord
import json
from discord.ext import commands
from discord import app_commands
from groq import Groq
from duckduckgo_search import DDGS

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

OWNER_ID = 123456789012345678

client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# -----------------------
# DATA
# -----------------------

pro_users = [OWNER_ID]
ai_channels = {}

memory_file = "memory.json"

if os.path.exists(memory_file):
    with open(memory_file) as f:
        user_memory = json.load(f)
else:
    user_memory = {}

SYSTEM_PROMPT = """
You are Thinksy.

Personality:
calm, intelligent, strategic, futuristic.

Explain clearly and logically.
"""

def save_memory():
    with open(memory_file,"w") as f:
        json.dump(user_memory,f)

# -----------------------
# AI RESPONSE
# -----------------------

async def ai_reply(channel,user_id,text,pro=False):

    uid=str(user_id)

    if uid not in user_memory:
        user_memory[uid]=[{"role":"system","content":SYSTEM_PROMPT}]

    user_memory[uid].append({"role":"user","content":text})

    limit=40 if pro else 15

    if len(user_memory[uid])>limit:
        user_memory[uid]=user_memory[uid][-limit:]

    model="llama-3.1-70b-versatile" if pro else "llama-3.1-8b-instant"

    try:

        async with channel.typing():

            response=client.chat.completions.create(
                model=model,
                messages=user_memory[uid]
            )

        answer=response.choices[0].message.content

        user_memory[uid].append({"role":"assistant","content":answer})

        save_memory()

        if len(answer)>2000:
            answer=answer[:1990]

        await channel.send(answer)

    except Exception as e:
        print(e)
        await channel.send("AI error")

# -----------------------
# READY
# -----------------------

@bot.event
async def on_ready():
    await tree.sync()
    print("Thinksy ready")

# -----------------------
# SETUP AI CHANNEL
# -----------------------

@bot.command()
async def setup(ctx):

    ai_channels[ctx.guild.id]=ctx.channel.id
    await ctx.send("AI channel configured")

@tree.command(name="setup")
async def setup_slash(interaction:discord.Interaction):

    ai_channels[interaction.guild.id]=interaction.channel.id
    await interaction.response.send_message("AI channel configured")

# -----------------------
# BASIC AI
# -----------------------

@bot.command()
async def ai(ctx,*,question):

    await ai_reply(ctx.channel,ctx.author.id,question,ctx.author.id in pro_users)

# -----------------------
# LITE COMMANDS
# -----------------------

@bot.command()
async def explain(ctx,*,topic):

    await ai_reply(ctx.channel,ctx.author.id,f"Explain clearly: {topic}",ctx.author.id in pro_users)

@bot.command()
async def summarize(ctx,*,text):

    await ai_reply(ctx.channel,ctx.author.id,f"Summarize: {text}",ctx.author.id in pro_users)

@bot.command()
async def brainstorm(ctx,*,idea):

    await ai_reply(ctx.channel,ctx.author.id,f"Brainstorm ideas: {idea}",ctx.author.id in pro_users)

@bot.command()
async def joke(ctx):
    await ai_reply(ctx.channel,ctx.author.id,"Tell a funny joke",ctx.author.id in pro_users)

@bot.command()
async def fact(ctx):
    await ai_reply(ctx.channel,ctx.author.id,"Tell an interesting fact",ctx.author.id in pro_users)

@bot.command()
async def riddle(ctx):
    await ai_reply(ctx.channel,ctx.author.id,"Give a riddle",ctx.author.id in pro_users)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong")

# -----------------------
# PRO COMMANDS
# -----------------------

def pro_check(ctx):
    return ctx.author.id in pro_users

@bot.command()
async def research(ctx,*,topic):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Deep research: {topic}",True)

@bot.command()
async def code(ctx,*,prompt):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Write code: {prompt}",True)

@bot.command()
async def reviewcode(ctx,*,code):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Review this code: {code}",True)

@bot.command()
async def debug(ctx,*,problem):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Debug this problem: {problem}",True)

@bot.command()
async def teacher(ctx,*,topic):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Teach this step by step: {topic}",True)

@bot.command()
async def deepthink(ctx,*,topic):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Deep analysis: {topic}",True)

@bot.command()
async def solve(ctx,*,problem):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Solve this problem: {problem}",True)

@bot.command()
async def studyplan(ctx,*,topic):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Create study plan for: {topic}",True)

@bot.command()
async def quiz(ctx,*,topic):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Create a quiz on: {topic}",True)

@bot.command()
async def startupidea(ctx,*,topic):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Startup idea about: {topic}",True)

@bot.command()
async def story(ctx,*,idea):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Write a story: {idea}",True)

@bot.command()
async def poem(ctx,*,idea):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Write a poem: {idea}",True)

@bot.command()
async def rap(ctx,*,topic):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Write a rap: {topic}",True)

@bot.command()
async def worldbuild(ctx,*,idea):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Create fictional world: {idea}",True)

@bot.command()
async def character(ctx,*,idea):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Create character: {idea}",True)

@bot.command()
async def compare(ctx,*,items):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Compare: {items}",True)

@bot.command()
async def timeline(ctx,*,topic):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    await ai_reply(ctx.channel,ctx.author.id,f"Timeline of: {topic}",True)

@bot.command()
async def search(ctx,*,query):

    if not pro_check(ctx):
        await ctx.send("Pro feature")
        return

    results=[]

    with DDGS() as ddgs:
        for r in ddgs.text(query,max_results=5):
            results.append(r["body"])

    info="\n".join(results)

    prompt=f"Use this info to answer:\n{info}\nQuestion:{query}"

    await ai_reply(ctx.channel,ctx.author.id,prompt,True)

# -----------------------
# RESET MEMORY
# -----------------------

@bot.command()
async def reset(ctx):

    uid=str(ctx.author.id)

    if uid in user_memory:
        del user_memory[uid]

    save_memory()

    await ctx.send("Memory reset")

# -----------------------
# HELP
# -----------------------

@bot.command()
async def helpai(ctx):

    await ctx.send("""
Lite
!ai !explain !summarize !brainstorm
!joke !fact !riddle

Pro
!research !code !reviewcode !debug
!teacher !deepthink !solve
!studyplan !quiz
!startupidea !story !poem !rap
!worldbuild !character
!compare !timeline !search
""")

# -----------------------
# OWNER COMMAND
# -----------------------

@tree.command(name="addpro")
async def addpro(interaction:discord.Interaction,user:discord.Member):

    if interaction.user.id!=OWNER_ID:
        await interaction.response.send_message("Not allowed",ephemeral=True)
        return

    pro_users.append(user.id)

    await interaction.response.send_message(f"{user.name} is now Pro")

# -----------------------
# MESSAGE LISTENER
# -----------------------

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.guild:

        channel_id=ai_channels.get(message.guild.id)

        if channel_id==message.channel.id:

            if message.content.startswith("!msg"):
                return

            await ai_reply(
                message.channel,
                message.author.id,
                message.content,
                message.author.id in pro_users
            )

    if isinstance(message.channel,discord.DMChannel):

        if message.author.id not in pro_users:
            await message.channel.send("DM chat is Pro only")
            return

        await ai_reply(message.channel,message.author.id,message.content,True)

    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)
