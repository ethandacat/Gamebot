import discord
from discord.ext import commands
import re
import random
import asyncio
import time

with open("credentials.txt", "r") as f:
    q = f.read().splitlines()

i = discord.Intents.default()
i.message_content = True
client = commands.Bot(command_prefix=".", intents=i)

# Money system
m = {}

with open("monies.txt", "r") as f:
    for g in f.read().splitlines():
        if g.strip():
            user, amount = g.rsplit(" ", 1)
            m[user] = int(amount)


def save():
    with open("monies.txt", "w") as f:
        for user, amount in m.items():
            f.write(f"{user} {amount}\n")


def balance(user):
    return m.get(user, 0)


def give(user, amount):
    m[user] = balance(user) + amount
    save()


def take(user, amount):
    if amount > balance(user):
        return False
    give(user, -amount)
    return True


@client.event
async def on_ready():
    print("gaming time")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    x = re.search(
        r"\b(i['’]?\s*m|i\s+am)\s+(\w+)",
        message.content,
        re.IGNORECASE
    )

    if x:
        await message.channel.send(f"Hi, {x[2]}!")

    await client.process_commands(message)


@client.command(name="leaderboard")
async def leaderboard(ctx):
    s = sorted(m.items(), key=lambda x: x[1], reverse=True)
    await ctx.send("\n".join(f"{k}: ${v}" for k, v in s))


@client.command(name="beg")
async def beg(ctx):
    user = ctx.author.name

    if random.randint(0, 1):
        n = random.randint(0, 50)
        n = 100 if n == 37 else n
        give(user, n)

        await ctx.send(
            random.choice([
                "Go away, filthy person. Take your money. ",
                "Aww, you're so sweet! Have some money! "
            ]) + f"I'll give you ${n}."
        )
    else:
        await ctx.send("Nobody gave you anything. Skill issue.")


@client.command(name="coinflip")
async def coinflip(ctx, amount: int):
    user = ctx.author.name

    if amount < 1:
        await ctx.send("Bet at least 1 monies.")
        return

    if amount > balance(user):
        await ctx.send("You don't have that much money!")
        return

    if random.choice([True, False]):
        give(user, amount)
        await ctx.send(f"You won {amount} monies!")
    else:
        take(user, amount)
        await ctx.send("Womp womp, you lost.")


@client.command(name="work")
async def work(ctx):
    give(ctx.author.name, 10)
    await ctx.send("You worked an hour for $10.")


@client.command(name="steal")
async def steal(ctx, user: str):
    thief = ctx.author.name

    if user == thief:
        await ctx.send("You can't steal from yourself.")
        return

    if balance(user) <= 0:
        await ctx.send("This person is broke!")
        return

    r = random.randint(1, 3)

    if r == 1:
        await ctx.send("You got scared and didn't make it in time.")

    elif r == 2:
        fine = round(balance(thief) / 2)
        give(user, fine)
        take(thief, fine)
        await ctx.send(f"{user} spotted you! You paid {fine} monies.")

    else:
        amount = round(balance(user) / 2)
        take(user, amount)
        give(thief, amount)
        await ctx.send(f"You stole {amount} monies!")


@client.command(name="pay")
async def pay(ctx, user: str, amount: int):
    sender = ctx.author.name

    if amount < 1:
        await ctx.send("Pay at least 1 monies.")
        return

    if user == sender:
        await ctx.send("You can't pay yourself.")
        return

    if not take(sender, amount):
        await ctx.send("You don't have that much money!")
        return

    give(user, amount)
    await ctx.send(f"Sent {user} {amount} monies!")

@client.command("slots")
async def slots(ctx, bet: int):
    user = ctx.author.name
    if not take(user, bet):
        await ctx.send("You don't have that much money!")
        return
    symbols = ["🍒","🍋","🍊","🍇","🍉","🔔","⭐","💎","7️⃣","💰","🪙","👑","🍀","🐱","🐟","🌈","🧨","💀","🦈"]
    # Slot spinning
    # ⠀ SYMBOL ⠀
    upls = [random.choice(symbols), random.choice(symbols), random.choice(symbols)]
    midls = [random.choice(symbols), random.choice(symbols), random.choice(symbols)]
    msgup = await ctx.send("⠀ "+" ⠀⠀ ".join(upls)+" ⠀")
    msg = await ctx.send(" ".join(midls))
    msgdown = await ctx.send("⠀ "+" ⠀⠀ ".join([random.choice(symbols), random.choice(symbols), random.choice(symbols)])+" ⠀")
    for i in range(5):
        new_upls = [random.choice(symbols) for _ in range(3)]
        await asyncio.gather(
            msgdown.edit(content="⠀ " + " ⠀⠀ ".join(midls) + " ⠀"),
            msg.edit(content=" ".join(upls)),
            msgup.edit(content="⠀ " + " ⠀⠀ ".join(new_upls) + " ⠀")
        )
        midls = upls
        upls = new_upls
        await asyncio.sleep(0.5)
    # Calculating results
    multipliers = {
        "7️⃣": 300,
        "💎": 200, "💰": 200, "👑": 200,
        "🔔": 150, "⭐": 150, "🍀": 150, "🌈": 150, "🪙": 150, "🦈": 150,
        "🍒": 70, "🍋": 70, "🍊": 70, "🍇": 70, "🍉": 70,
        "🐱": 70, "🐟": 70, "🧨": 70, "💀": 70,
    }
    # 3 of a kind
    ret = 0
    if midls[0] == midls[1] and midls[1] == midls[2]:
        ret = bet * multipliers[midls[0]]
    elif midls[0] == midls[1] or midls[0] == midls[2] or midls[1] == midls[2]:
        ret = bet * 3
    if ret == 0:
        await ctx.send("Aww, better luck next time. You didn't win anything.")
    else:
        await ctx.send(f"You won {ret} monies!")
        give(user, ret)
        
client.run(q[0])
