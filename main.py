import os, json, time, asyncio, discord, requests
from datetime import timedelta
from collections import defaultdict
from discord.ext import commands
from groq import Groq
from duckduckgo_search import DDGS

# ========= CONFIG =========
TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OWNER_ID = 123456789012345678

groq = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========= STORAGE =========
def load(n,d): return json.load(open(n)) if os.path.exists(n) else d
def save(n,d): json.dump(d, open(n,"w"))

memory = load("memory.json", {})
notes = load("notes.json", {})
tasks = load("tasks.json", {})
config = load("config.json", {
    "tiers": {},
    "ai_channels": {},
    "ai_banned": []
})

# ========= TIERS =========
def tier(uid): return config["tiers"].get(str(uid),"lite")

COOLDOWN = {"lite":6,"go":4,"plus":3,"pro":2}
LIMITS = {"lite":(8,15),"go":(12,15),"plus":(16,15),"pro":(25,15)}

# ========= MODERATION =========
activity=defaultdict(list)
last_msg={}
warn=defaultdict(int)

async def punish(msg):
    uid=msg.author.id
    activity[uid]=[]
    warn[uid]=0

    if msg.guild:
        try:
            await msg.author.timeout(discord.utils.utcnow()+timedelta(seconds=600))
            await msg.channel.send(f"{msg.author.mention} timed out (spam)")
        except: pass
    else:
        config["ai_banned"].append(uid)
        save("config.json",config)
        await msg.channel.send("Blocked for spam.")
    return True

async def moderate(msg):
    uid=msg.author.id
    t=tier(uid)
    limit,per=LIMITS[t]
    now=time.time()

    activity[uid].append(now)
    activity[uid]=[x for x in activity[uid] if now-x<per]

    if len(activity[uid])>limit: return await punish(msg)

    if last_msg.get(uid)==msg.content: warn[uid]+=1
    else: warn[uid]=0

    last_msg[uid]=msg.content
    if warn[uid]>=5: return await punish(msg)

    return False

# ========= AI =========
ai_cd={}

async def ai_call(msgs, t):
    model = "openai/gpt-oss-120b" if t in ["plus","pro"] else "openai/gpt-oss-20b"
    try:
        return groq.chat.completions.create(model=model,messages=msgs).choices[0].message.content
    except:
        r=requests.post("https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization":f"Bearer {OPENROUTER_API_KEY}"},
        json={"model":model,"messages":msgs})
        return r.json()["choices"][0]["message"]["content"]

async def ai_reply(ch, uid, text):
    if uid in config["ai_banned"]:
        return await ch.send("You are banned.")

    t=tier(uid)

    if time.time()-ai_cd.get(uid,0)<COOLDOWN[t]:
        return await ch.send("Slow down.")

    ai_cd[uid]=time.time()
    uid=str(uid)

    if uid not in memory:
        memory[uid]=[{"role":"system","content":"You are Thinksy AI."}]

    memory[uid].append({"role":"user","content":text})
    memory[uid]=memory[uid][-30:]

    async with ch.typing():
        reply=await ai_call(memory[uid],t)

    memory[uid].append({"role":"assistant","content":reply})
    save("memory.json",memory)

    await ch.send(reply[:2000])

# ========= EVENTS =========
@bot.event
async def on_ready():
    print("Thinksy V6 Ready")

@bot.event
async def on_message(msg):
    if msg.author.bot: return

    if await moderate(msg): return

    if msg.guild:
        gid=str(msg.guild.id)
        if gid in config["ai_channels"]:
            if msg.channel.id==config["ai_channels"][gid]:
                await ai_reply(msg.channel,msg.author.id,msg.content)

    if isinstance(msg.channel,discord.DMChannel):
        if tier(msg.author.id)!="lite":
            await ai_reply(msg.channel,msg.author.id,msg.content)
        else:
            await msg.channel.send("Upgrade for DM access.")

    await bot.process_commands(msg)

# ========= CORE =========
@bot.command()
async def ai(ctx,*,q): await ai_reply(ctx.channel,ctx.author.id,q)

@bot.command()
async def setup(ctx):
    config["ai_channels"][str(ctx.guild.id)]=ctx.channel.id
    save("config.json",config)
    await ctx.send("AI channel set.")

# ========= USEFUL FEATURES =========
@bot.command()
async def summarize(ctx,*,text):
    await ai_reply(ctx.channel,ctx.author.id,f"Summarize clearly:\n{text}")

@bot.command()
async def research(ctx,*,q):
    await ai_reply(ctx.channel,ctx.author.id,f"Do deep research and structure answer:\n{q}")

@bot.command()
async def scan(ctx,*,text):
    await ai_reply(ctx.channel,ctx.author.id,f"Check scam or risk:\n{text}")

@bot.command()
async def analyze(ctx,*,url):
    await ai_reply(ctx.channel,ctx.author.id,f"Explain content of this link simply:\n{url}")

# ========= MEMORY =========
@bot.command()
async def remember(ctx,*,info):
    uid=str(ctx.author.id)
    notes.setdefault(uid,[]).append(info)
    save("notes.json",notes)
    await ctx.send("Saved.")

@bot.command()
async def recall(ctx):
    await ctx.send("\n".join(notes.get(str(ctx.author.id),["Nothing saved"])))

# ========= TASKS =========
@bot.command()
async def task(ctx,*,t):
    uid=str(ctx.author.id)
    tasks.setdefault(uid,[]).append(t)
    save("tasks.json",tasks)
    await ctx.send("Task added.")

@bot.command()
async def tasks(ctx):
    await ctx.send("\n".join(tasks.get(str(ctx.author.id),["No tasks"])))

@bot.command()
async def done(ctx,index:int):
    uid=str(ctx.author.id)
    try:
        tasks[uid].pop(index-1)
        save("tasks.json",tasks)
        await ctx.send("Task done.")
    except:
        await ctx.send("Invalid index.")

# ========= FOCUS =========
@bot.command()
async def focus(ctx,time_min:int):
    await ctx.send(f"Focus started for {time_min} minutes.")
    await asyncio.sleep(time_min*60)
    await ctx.send(f"{ctx.author.mention} Focus session ended.")

# ========= ADMIN =========
@bot.command()
async def settier(ctx,user:discord.Member,t):
    if ctx.author.id!=OWNER_ID: return
    config["tiers"][str(user.id)]=t
    save("config.json",config)
    await ctx.send("Tier updated.")

# ========= RUN =========
bot.run(TOKEN)
