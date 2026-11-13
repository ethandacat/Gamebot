from operator import truediv

from itertools import combinations
from collections import Counter
import discord
from discord.ext import commands
import re
import random
import asyncio
import json
import math
import os
import pyphen

from gensim.models import KeyedVectors
import gensim.downloader as api

with open("credentials.txt", "r") as f:
    q = f.read().splitlines()

dc = pyphen.Pyphen(lang="en_US")

i = discord.Intents.default()
i.message_content = True
client = commands.Bot(command_prefix=".", intents=i, help_command=None)

# Money system
m = {}

with open("monies.txt", "r") as f:
    for g in f.read().splitlines():
        if g.strip():
            user, amount = g.rsplit(" ", 1)
            m[user] = int(amount)

print("Loading WordGuess resources...")
model = KeyedVectors.load("glove50.kv", mmap="r") if os.path.exists("glove50.kv") else None
if model is None:
    print("Caching WordGuess resources for future runs...")
    model = KeyedVectors.load_word2vec_format(api.load("glove-wiki-gigaword-50", return_path=True))
    model.save("glove50.kv")
print("Done!")

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


def place_bet(user, bet):
    """Deduct a bet. Returns an error message, or None if the bet was placed."""
    if not take(user, bet):
        return "You don't have that much money!"
    return None

inventory = {}

try:
    with open("inventory.json", "r") as f:
        inventory = json.load(f)
except FileNotFoundError:
    pass

def saveInventory():
    with open("inventory.json", "w") as f:
        json.dump(inventory, f)

def giveInventory(user, item, count=1):
    inventory.setdefault(user, {})
    inventory[user][item] = inventory[user].get(item, 0) + count
    saveInventory()

def getInventory(user):
    return inventory.get(user, {})

def removeInventory(user, item, count=1):
    if inventory.get(user, {}).get(item, 0) < count:
        return "User does not have enough items"

    inventory[user][item] -= count

    if inventory[user][item] == 0:
        del inventory[user][item]

    saveInventory()
    return None

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

    # Haiku
    w = [(i, dc.inserted(i).split("-")) for i in re.findall(r"[a-zA-Z']+", message.content)]
    
    if sum(len(p) for i, p in w) == 17:
        lines = ["", "", ""]
        limits = [5, 7, 5]
        line = count = 0
    
        for word, parts in w:
            while parts:
                remaining = limits[line] - count
                take = parts[:remaining]
    
                lines[line] += (" " if lines[line] else "") + "".join(take)
                parts = parts[remaining:]
                count += len(take)
    
                if count == limits[line] and line < 2:
                    line += 1
                    count = 0
    
        await message.channel.send("Here's a haiku!\n" + "\n".join(lines))

    if "technoblade" in message.content.lower():
        await message.channel.send("TECHNOBLADE NEVER DIES")
    
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
    err = place_bet(user, amount)
    if err:
        await ctx.send(err)
        return

    if random.choice([True, False]):
        give(user, amount * 2)  # stake back plus winnings
        await ctx.send(f"You won {amount} monies!")
    else:
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
    err = place_bet(user, bet)
    if err:
        await ctx.send(err)
        return

    symbols = ["🍒","🍋","🍊","🍇","🍉","🔔","⭐","💎","7️⃣","💰","🪙","👑","🍀","🐱","🐟","🌈","🧨","💀","🦈"]
    # Slot spinning
    # ⠀ SYMBOL ⠀
    upls = [random.choice(symbols), random.choice(symbols), random.choice(symbols)]
    midls = [random.choice(symbols), random.choice(symbols), random.choice(symbols)]
    msgup = await ctx.send("⠀ "+" ⠀⠀ ".join(upls)+" ⠀")
    msg = await ctx.send(" ".join(midls))
    msgdown = await ctx.send("⠀ "+" ⠀⠀ ".join([random.choice(symbols), random.choice(symbols), random.choice(symbols)])+" ⠀")
    for _ in range(5):
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
        give(user, ret + bet)  # stake back plus winnings
        await ctx.send(f"You won {ret} monies!")


@client.command("wordle")
async def wordle(ctx, bet: int, word: str):
    user = ctx.author.name
    word = word.lower()

    err = place_bet(user, bet)
    if err:
        await ctx.send(err)
        return

    with open("wordle.txt", "r") as f:
        worda = random.choice(f.read().split()).lower()

    used = [False] * 5     # letters in the answer already matched
    matched = [False] * 5  # letters in the guess already matched
    score = 0

    # Green: right letter, right spot
    for k in range(5):
        if k < len(word) and word[k] == worda[k]:
            score += 0.5
            used[k] = True
            matched[k] = True

    # Yellow: right letter, wrong spot
    for k in range(min(5, len(word))):
        if matched[k]:
            continue
        for j in range(5):
            if not used[j] and worda[j] == word[k]:
                score += 0.25
                used[j] = True
                break

    am = int(bet * score)
    if am > 0:
        give(user, am)
    await ctx.send(f"You won {am} monies! (Word was {worda})")


@client.command("roulette")
async def roulette(ctx, bet: int, color: str):
    user = ctx.author.name
    color = color.lower()
    if color not in ("red", "black", "green"):
        await ctx.send("Pick red, black, or green.")
        return

    err = place_bet(user, bet)
    if err:
        await ctx.send(err)
        return

    l = random.randint(0, 36)
    winnings = 0
    if l == 0:
        if color == "green":
            winnings = 20 * bet
    elif l < 19:
        if color == "red":
            winnings = 2 * bet
    else:
        if color == "black":
            winnings = 2 * bet

    if winnings == 0:
        await ctx.send(f"The wheel decided against you and landed on {[['green'], ['red', 'black']][l != 0][l > 18]}")
    else:
        give(user, winnings + bet)  # stake back plus winnings
        await ctx.send(f"You won {winnings} monies!")


@client.command(name="dice")
async def dice(ctx, bet: int, guess: int):
    user = ctx.author.name

    err = place_bet(user, bet)
    if err:
        await ctx.send(err)
        return

    a = random.randint(1, 6) + random.randint(1, 6)
    if a == guess:
        give(user, bet * 4)  # stake back plus 3x winnings
        await ctx.send(f"You won ${bet * 3}! The dice rolled {a}.")
    else:
        await ctx.send(f"Aww, you lost. The dice rolled {a}.")


@client.command(name="rps")
async def rps(ctx, bet: int, chose: str):
    user = ctx.author.name
    chose = chose.lower()
    if chose not in ["rock", "paper", "scissors"]:
        await ctx.send("Please choose rock, paper, or scissors.")
        return

    err = place_bet(user, bet)
    if err:
        await ctx.send(err)
        return

    p = random.randint(1, 3)
    if p == 1:
        d = {'paper': 'rock', 'rock': 'scissors', 'scissors': 'paper'}
        give(user, bet * 2)  # stake back plus winnings
        await ctx.send(f"You won! Your opponent did {d[chose]}")
    elif p == 2:
        give(user, bet)  # tie refunds the bet
        await ctx.send("It was a tie.")
    else:
        d = {'rock': 'paper', 'paper': 'scissors', 'scissors': 'rock'}
        await ctx.send(f"You lost. Your opponent did {d[chose]}")

@client.command(name="ftft")
async def ftft(ctx, bet: int, inp: str, guess: str):
    user = ctx.author.name
    # Opponent
    o = random.randint(0, 2) * 5
    if inp.lower() == "zero" or inp == "0":
        inp = 0
    elif inp.lower() == "five" or inp == "5":
        inp = 5
    elif inp.lower() == "ten" or inp == "10":
        inp = 10
    else:
        await ctx.send("Please enter either five or ten as the input")
        return
    if guess.lower() == "zero" or guess == "0":
        guess = 0
    elif guess.lower() == "five" or guess == "5":
        guess = 5
    elif guess.lower() == "ten" or guess == "10":
        guess = 10
    elif guess.lower() == "fifteen" or guess == "15":
        guess = 15
    elif guess.lower() == "twenty" or guess == "20":
        guess = 20
    else:
        await ctx.send("Please enter either five, ten, fifteen, or twenty as your guess.")
        return
    err = place_bet(user, bet)
    if err:
        await ctx.send(err)
        return
    if inp + o == guess:
        await ctx.send(f"You won! You have received {bet * 2} monies.")
        give(user, bet * 2)
    else:
        await ctx.send(f"You lost. Your opponent put out {o}, putting the sum at {inp + o}.")

def nim_bot(stones):
    if random.random() < 0.7:
        # Leave a multiple of 3 whenever possible
        remainder = stones % 3
        if remainder:
            return remainder

    # Make a random legal move
    return random.randint(1, min(2, stones))


class NimView(discord.ui.View):
    def __init__(self, bet, author):
        super().__init__(timeout=300)
        self.bet = bet
        self.author = author
        self.count = 15
        self.turn = 0
        self.game_over = False

    async def take(self, interaction, amount):
        if self.game_over:
            await interaction.response.send_message(
                "This game is already over!",
                ephemeral=True
            )
            return

        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your game of Nim! Type .nim [bet] to start your own.",
                ephemeral=True
            )
            return

        if self.turn != 0:
            await interaction.response.send_message(
                "It's not your turn!",
                ephemeral=True
            )
            return

        self.count -= amount

        if self.count <= 0:
            self.game_over = True
            give(self.author.name, self.bet * 2)

            for item in self.children:
                item.disabled = True

            embed = interaction.message.embeds[0]
            embed.description = (
                f"You took {amount} rocks. There are **0 rocks left**.\n"
                f"You won **${self.bet * 2} monies!**"
            )

            await interaction.response.edit_message(
                embed=embed,
                view=self
            )
            return

        bot_take = nim_bot(self.count)
        self.count -= bot_take

        if self.count <= 0:
            self.game_over = True

            for item in self.children:
                item.disabled = True

            embed = interaction.message.embeds[0]
            embed.description = (
                f"You took {amount} rocks.\n"
                f"The bot took {bot_take} rocks.\n"
                f"There are **0 rocks left**. You lost!"
            )

            await interaction.response.edit_message(
                embed=embed,
                view=self
            )
            return

        embed = interaction.message.embeds[0]
        embed.description = (
            f"You took {amount} rocks.\n"
            f"The bot took {bot_take} rocks.\n"
            f"There are **{self.count} rocks left**. "
            f"It is **your** turn."
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(label="Take one", style=discord.ButtonStyle.primary)
    async def my_button(self, interaction, button):
        await self.take(interaction, 1)

    @discord.ui.button(label="Take two", style=discord.ButtonStyle.primary)
    async def my_button2(self, interaction, button):
        await self.take(interaction, 2)


@client.command(name="nim")
async def nim(ctx, bet: int):
    user = ctx.author.name
    err = place_bet(user, bet)

    if err:
        await ctx.send(err)
        return

    embed = discord.Embed(
        title="Nim - GameBot",
        description="There are **15 rocks left**. It is your turn.",
        color=discord.Color.blurple()
    )

    await ctx.send(embed=embed, view=NimView(bet, ctx.author))


class CrashView(discord.ui.View):
    def __init__(self, user, bet):
        super().__init__(timeout=300)
        self.multiplier = 1.0
        self.user = user
        self.bet = bet
        self.game_over = False

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message(
                "This isn't your game of Crash! "
                "Type .crash [bet] to start your own.",
                ephemeral=True
            )
            return False

        if self.game_over:
            await interaction.response.send_message(
                "This game has already ended.",
                ephemeral=True
            )
            return False

        return True

    def end_game(self):
        self.game_over = True
        for item in self.children:
            item.disabled = True

    @discord.ui.button(
        label="Cash out",
        style=discord.ButtonStyle.success
    )
    async def cash_out(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        winnings = round(self.bet * self.multiplier, 2)

        give(self.user.name, winnings)
        self.end_game()

        embed = interaction.message.embeds[0]
        embed.description = (
            f"**Cashed out!**\n"
            f"Multiplier: **{self.multiplier:.1f}x**\n"
            f"You won **${winnings:.2f} monies!**"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(
        label="Next multiplier",
        style=discord.ButtonStyle.primary
    )
    async def next_mult(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        # 30% chance to crash on each click
        loss = random.randint(1, 10) > 7

        embed = interaction.message.embeds[0]

        if loss:
            self.end_game()
            embed.description = (
                f"The multiplier **CRASHED** at "
                f"**{self.multiplier:.1f}x**!\n"
                f"You lost **${self.bet} monies.**"
            )

            await interaction.response.edit_message(
                embed=embed,
                view=self
            )
            return

        self.multiplier = round(self.multiplier + 0.1, 1)

        embed.description = (
            f"The multiplier is **{self.multiplier:.1f}x**.\n"
            f"Cash out before it crashes!"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    async def on_timeout(self):
        self.end_game()


@client.command(name="crash")
async def crash(ctx, bet: int):
    err = place_bet(ctx.author.name, bet)

    if err:
        await ctx.send(err)
        return

    embed = discord.Embed(
        title="Crash - GameBot",
        description=(
            "The multiplier is **1.0x**.\n"
            "Cash out before it crashes!"
        ),
        color=discord.Color.blurple()
    )

    await ctx.send(embed=embed, view=CrashView(ctx.author, bet))

def generatecard():
    return random.choice("A 2 3 4 5 6 7 8 9 10 J Q K".split(" "))
def getsum(li):
    summ = 0
    acount = 0
    for i in li:
        if i in "J Q K".split():
            summ += 10
        elif i == "A":
            acount += 1
            summ += 11
        else:
            summ += int(i)
    while summ > 21 and acount > 0:
        summ -= 10
        acount -= 1
    return summ

class BlackjackClass(discord.ui.View):
    def __init__(self, bet, author):
        super().__init__(timeout=300)

        self.cards = [generatecard(), generatecard()]
        self.dealercards = [generatecard(), generatecard()]

        self.bet = bet
        self.author = author
        self.gameover = False

        self.natural = len(self.cards) == 2 and getsum(self.cards) == 21

        self.message = None

    def make_embed(self, description):
        return discord.Embed(
            title="Blackjack - GameBot",
            description=description,
            color=discord.Color.blurple()
        )

    def player_text(self):
        return (
            f"Your cards: {' '.join(self.cards)}\n"
            f"Sum: **{getsum(self.cards)}**"
        )

    def dealer_text(self, reveal=False):
        if reveal:
            return (
                f"Dealer's cards: {' '.join(self.dealercards)}\n"
                f"Sum: **{getsum(self.dealercards)}**"
            )

        return (
            f"Dealer's cards: {self.dealercards[0]} ?\n"
            "Sum: Unknown"
        )

    async def start(self):
        # Check for a natural Blackjack.
        if self.natural:
            self.gameover = True

            dealer_natural = getsum(self.dealercards) == 21

            if dealer_natural:
                give(self.author.name, self.bet)
                result = (
                    "Both you and the dealer have Blackjack! "
                    "It's a push. Your bet has been returned."
                )
            else:
                # 3:2 payout, including the original stake.
                give(self.author.name, self.bet * 2.5)
                result = (
                    "Natural Blackjack! You won a 3:2 payout."
                )

            self.disable_all_items()

            return self.make_embed(
                f"{self.player_text()}\n\n"
                f"{self.dealer_text(reveal=True)}\n\n"
                f"{result}"
            )

        return self.make_embed(
            f"{self.player_text()}\n\n"
            f"{self.dealer_text()}\n\n"
            "Choose Hit or Stand."
        )

    async def interaction_check(self, interaction):
        if interaction.user != self.author:
            await interaction.response.send_message(
                "This isn't your game!",
                ephemeral=True
            )
            return False

        return True

    async def finish(self, interaction, result, payout=0):
        self.gameover = True

        if payout:
            give(self.author.name, payout)

        embed = self.make_embed(
            f"{self.player_text()}\n\n"
            f"{self.dealer_text(reveal=True)}\n\n"
            f"{result}"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    async def on_timeout(self):
        self.gameover = True
        self.disable_all_items()

        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(
        label="Hit",
        style=discord.ButtonStyle.primary
    )
    async def hit(self, interaction, button):
        if self.gameover:
            await interaction.response.send_message(
                "This game is already over!",
                ephemeral=True
            )
            return

        self.cards.append(generatecard())
        player_sum = getsum(self.cards)

        if player_sum > 21:
            await self.finish(
                interaction,
                "You busted! You lost your bet."
            )
            return

        if player_sum == 21:
            # Automatically stand at 21.
            await self.play_dealer(interaction)
            return

        embed = self.make_embed(
            f"{self.player_text()}\n\n"
            f"{self.dealer_text()}\n\n"
            "Choose Hit or Stand."
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(
        label="Stand",
        style=discord.ButtonStyle.primary
    )
    async def stand(self, interaction, button):
        if self.gameover:
            await interaction.response.send_message(
                "This game is already over!",
                ephemeral=True
            )
            return

        await self.play_dealer(interaction)

    async def play_dealer(self, interaction):
        # Dealer stands on all totals of 17 or higher.
        while getsum(self.dealercards) < 17:
            self.dealercards.append(generatecard())

        player_sum = getsum(self.cards)
        dealer_sum = getsum(self.dealercards)

        if dealer_sum > 21:
            await self.finish(
                interaction,
                "The dealer busted! You won!",
                self.bet * 2
            )
        elif player_sum > dealer_sum:
            await self.finish(
                interaction,
                "You beat the dealer! You won!",
                self.bet * 2
            )
        elif player_sum < dealer_sum:
            await self.finish(
                interaction,
                "The dealer had a higher total. You lost."
            )
        else:
            await self.finish(
                interaction,
                "You and the dealer tied! Your bet was returned.",
                self.bet
            )


@client.command(name="blackjack")
async def blackjack(ctx, bet: int):
    if bet <= 0:
        await ctx.send("Your bet must be greater than zero.")
        return

    err = place_bet(ctx.author.name, -bet)
    if err:
        await ctx.send(err)
        return

    view = BlackjackClass(bet, ctx.author)
    embed = await view.start()

    view.message = await ctx.send(
        embed=embed,
        view=view
    )

@client.command(name="craps")
async def craps(ctx, bet: int, beton: str):
    user = ctx.author.name
    beton = beton.lower()
    if beton != "pass" and beton != "dontpass":
        await ctx.send("Choose a line to bet on (put 'pass' or 'dontpass')")
        return
    err = place_bet(user, bet)
    if err:
        await ctx.send(err)
        return
    # Comeout roll
    a = random.randint(1, 6) + random.randint(1, 6)
    if a == 7 or a == 11:
        if beton == "pass":
            await ctx.send(f"You won! The shooter rolled {a}.")
            give(user, bet * 2)
        else:
            await ctx.send(f"You lost, the shooter rolled a {a}.")
        return
    
    if a == 2 or a == 3:
        if beton == "dontpass":
            await ctx.send(f"You won! The shooter rolled {a}.")
            give(user, bet * 2)
        else:
            await ctx.send(f"You lost, the shooter rolled a {a}.")
        return
    
    if a == 12:
        if beton == "dontpass":
            await ctx.send("You pushed. The shooter rolled a 12.")
            give(user, bet)
        else:
            await ctx.send("You lost, the shooter rolled a 12.")
        return
    await ctx.send(f"Point is: {a}")
    # Points rolls
    b = 0
    while b != 7:
        b = random.randint(1, 6) + random.randint(1, 6)
        await ctx.send(f"The shooter rolled {b}!")
        if b == a:
            # Pass wins - Don't pass loses
            if beton == "dontpass":
                await ctx.send("The point was reached. You lost.")
                return
            else:
                await ctx.send("You won!")
                give(user, bet * 2)
                return
    # Don't pass wins
    if beton == "dontpass":
        await ctx.send("You won! The dealer rolled 7.")
        give(user, bet * 2)
    else:
        await ctx.send("You lost, the dealer rolled a 7.")

allstocks = {
    "ROBO": 100,
    "FOOD": 100,
    "BRUH": 100,
    "NVDA": 1000,
    "NPPP": 100
}

@client.command(name="stocks")
async def stocks(ctx):
    user = ctx.author.name
    # List stocks
    a = [i.split("stock")[1] for i, j in getInventory(user).items() if i.startswith("stock")]
    await ctx.send("Your stocks: \n"+"\n".join([i + " - $"+str(allstocks[i]) for i in a]))

@client.command(name="stockprice")
async def stockprice(ctx):
    # Stock price
    await ctx.send([i + ": $"+str(j) for i, j in allstocks])

@client.command(name="buystocks")
async def buystocks(ctx, ticker: str):
    user = ctx.author.name
    ticker = ticker.upper()
    if allstocks.get(ticker, 0) == 0:
        await ctx.send("This stock doesn't exist!")
        return
    if place_bet(user, allstocks[ticker]):
        await ctx.send("You don't have enough monies!")
        return
    giveInventory(user, "stock"+ticker)
    allstocks[ticker] += random.randint(1, 10)

@client.command(name="sellstocks")
async def sellstocks(ctx, ticker: str):
    user = ctx.author.name
    ticker = ticker.upper()
    if allstocks.get(ticker, 0) == 0:
        await ctx.send("This stock doesn't exist!")
        return
    if removeInventory(user, "stock"+ticker):
        await ctx.send("You don't have enough of this stock!")
        return
    allstocks[ticker] -= random.randint(1, 10)
    give(user, allstocks[ticker])

def highlowvalue(card):
    if card == "A":
        return 1
    if card in ["J", "Q", "K"]:
       return ["J", "Q", "K"] .index(card) + 11
    return int(card)

class HighLowView(discord.ui.View):
    def __init__(self, bet, author):
        self.bet = bet
        self.author = author
        self.points = 0
        self.guesses = 0
        self.gameover = False
        self.lastcard = generatecard()
    async def start(self, ctx):
        embed = discord.Embed(
            title="Higher or Lower - GameBot",
            description=f"Card: **{self.lastcard}**\nGuess **higher or lower**!\n\nGuesses: {self.guesses}/5\nPoints: {self.points}/5",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed, view=self)
    @discord.ui.button(label="Higher", style=discord.ButtonStyle.primary)
    async def higher(self, interaction: discord.Interaction, button: discord.Button):
        if self.author != interaction.user:
            await interaction.response.send_message("This isn't your game of Higher or Lower!", ephemeral = True)
            return
        if self.gameover:
            await interaction.response.send_message("This game is over!", ephemeral = True)
            return
        card = generatecard()
        self.guesses += 1
        while card == self.lastcard:
            card = generatecard()
        if highlowvalue(card) > highlowvalue(self.lastcard):
            # Point +
            self.points += 1
        embed = discord.Embed(
            title="Higher or Lower - GameBot",
            description=f"Card: **{card}**\nGuess **higher or lower**!\n\nGuesses: {self.guesses}/5\nPoints: {self.points}/5",
            color=discord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.lastcard = card
        # Check guesses over
        if self.guesses == 5:
            await interaction.response.send_message(f"You won {self.points} out of {self.guesses}! You won {round(self.bet * self.points / self.guesses * 2)} monies!")
            give(user, round(self.bet * self.points / self.guesses * 2))
            self.gameover = True

        @discord.ui.button(label="Lower", style=discord.ButtonStyle.primary)
        async def lower(self, interaction: discord.Interaction, button: discord.Button):
            if self.author != interaction.user:
                await interaction.response.send_message("This isn't your game of Higher or Lower!", ephemeral = True)
                return
            if self.gameover:
                await interaction.response.send_message("This game is over!", ephemeral = True)
                return
            card = generatecard()
            self.guesses += 1
            while card == self.lastcard:
                card = generatecard()
            if highlowvalue(card) < highlowvalue(self.lastcard):
                self.points += 1
            embed = discord.Embed(
                title="Higher or Lower - GameBot",
                description=f"Card: **{card}**\nGuess **higher or lower**!\n\nGuesses: {self.guesses}/5\nPoints: {self.points}/5",
                color=discord.Color.blurple()
            )
            await interaction.response.edit_message(embed=embed, view=self)
            # Check guesses over
            if self.guesses == 5:
                await interaction.response.send_message(f"You won {self.points} out of {self.guesses}! You won {round(self.bet * self.points / self.guesses * 2)} monies!")
                give(user, round(self.bet * self.points / self.guesses * 2))
                self.gameover = True

@client.command(name="highlow")
async def highlow(ctx, bet: int):
    user = ctx.author.name
    if place_bet(user, bet):
        await ctx.send("you don't have enough monies!")
        return
    a = HighLowView(bet, user)
    await a.start(ctx)

SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANK_NAMES = {**{i: str(i) for i in range(2, 11)}, 11: "J", 12: "Q", 13: "K", 14: "A"}
HAND_NAMES = [
    "High Card", "One Pair", "Two Pair", "Three of a Kind", "Straight",
    "Flush", "Full House", "Four of a Kind", "Straight Flush",
]

SMALL_BLIND = 1
BIG_BLIND = 2
RAISE_SIZE = 2
MAX_RAISES = 3
TIMEOUT = 300


def new_deck():
    deck = [(v, s) for s in SUITS for v in range(2, 15)]
    random.shuffle(deck)
    return deck


def fmt_cards(cards):
    return " ".join(f"{RANK_NAMES[v]}{s}" for v, s in cards)


def score5(cards):
    vals = [c[0] for c in cards]
    counts = Counter(vals)
    groups = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    ordered = [v for v, _ in groups]
    shape = [c for _, c in groups]
    uniq = sorted(set(vals), reverse=True)
    flush = len({c[1] for c in cards}) == 1
    straight_high = 0
    if len(uniq) == 5:
        if uniq[0] - uniq[4] == 4:
            straight_high = uniq[0]
        elif uniq == [14, 5, 4, 3, 2]:
            straight_high = 5

    if straight_high and flush:
        return (8, straight_high)
    if shape == [4, 1]:
        return (7, *ordered)
    if shape == [3, 2]:
        return (6, *ordered)
    if flush:
        return (5, *uniq)
    if straight_high:
        return (4, straight_high)
    if shape == [3, 1, 1]:
        return (3, *ordered)
    if shape == [2, 2, 1]:
        return (2, *ordered)
    if shape == [2, 1, 1, 1]:
        return (1, *ordered)
    return (0, *uniq)


def best_hand(cards):
    return max(score5(c) for c in combinations(cards, 5))


def hand_name(score):
    if score[0] == 8 and score[1] == 14:
        return "Royal Flush"
    return HAND_NAMES[score[0]]


class StartTexasHoldem(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=TIMEOUT)
        self.user = user
        self.started = False

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.primary)
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.user:
            await interaction.response.send_message("You cannot sign up for your own game!", ephemeral=True)
            return
        if interaction.user.bot:
            await interaction.response.send_message("Bots can't play.", ephemeral=True)
            return
        if self.started:
            await interaction.response.send_message("This game has already started!", ephemeral=True)
            return
        self.started = True
        err = place_bet(self.user.name, SMALL_BLIND)
        if err:
            self.started = False
            await interaction.response.send_message(f"The host can't post the blind: {err}", ephemeral=True)
            return
        err = place_bet(interaction.user.name, BIG_BLIND)
        if err:
            give(self.user.name, SMALL_BLIND)
            self.started = False
            await interaction.response.send_message(err, ephemeral=True)
            return
        game = TexasHoldemGame(self.user, interaction.user)
        game.message = interaction.message
        await interaction.response.edit_message(embed=game.build_embed(), view=game)
        self.stop()


class TexasHoldemGame(discord.ui.View):
    STREETS = ["Pre-Flop", "Flop", "Turn", "River"]

    def __init__(self, host, guest):
        super().__init__(timeout=TIMEOUT)
        self.players = [host, guest]
        self.deck = new_deck()
        self.hole = [[self.deck.pop(), self.deck.pop()],
                     [self.deck.pop(), self.deck.pop()]]
        self.community = []
        self.total = [SMALL_BLIND, BIG_BLIND]
        self.street_bet = [SMALL_BLIND, BIG_BLIND]
        self.street = "Pre-Flop"
        self.to_act = 0
        self.acted = set()
        self.raises = 0
        self.over = False
        self.showdown = False
        self.result_text = ""
        self.message = None
        self.lock = asyncio.Lock()
        self.last_action = (
            f"{host.name} posted {SMALL_BLIND}, {guest.name} posted {BIG_BLIND}. "
            f"Press **My Cards** to see your hand."
        )
        self._sync_buttons()

    def name(self, i):
        return self.players[i].name

    @property
    def pot(self):
        return sum(self.total)

    def to_call(self, i):
        return max(self.street_bet) - self.street_bet[i]

    def _sync_buttons(self):
        if self.over:
            for child in self.children:
                child.disabled = True
            return
        need = self.to_call(self.to_act)
        self.call_button.label = "Check" if need == 0 else f"Call {need}"
        self.raise_button.label = f"Raise +{RAISE_SIZE}"
        self.raise_button.disabled = self.raises >= MAX_RAISES

    def build_embed(self):
        title = "Game Over" if self.over else self.street
        lines = [
            f"{self.name(0)} bet: {self.total[0]}",
            f"{self.name(1)} bet: {self.total[1]}",
            f"**Total Pot: {self.pot}**",
        ]
        if self.community:
            lines += ["", f"Community cards: {fmt_cards(self.community)}"]
        if self.over and self.showdown:
            lines += [
                "",
                f"{self.name(0)} cards: {fmt_cards(self.hole[0])}",
                f"{self.name(1)} cards: {fmt_cards(self.hole[1])}",
            ]
        lines += ["", f"Last action: {self.last_action}"]
        if self.over:
            lines += ["", self.result_text]
        else:
            lines += ["", f"Action on: {self.players[self.to_act].mention}"]
        return discord.Embed(
            title=f"{title} - Texas Hold'em - GameBot",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )

    async def _update(self, interaction):
        embed = self.build_embed()
        if interaction is not None:
            await interaction.response.edit_message(embed=embed, view=self)
        elif self.message is not None:
            try:
                await self.message.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass

    async def _finish(self, interaction, winner, text, showdown=False):
        self.over = True
        self.showdown = showdown
        self.result_text = text
        if winner is None:
            give(self.name(0), self.total[0])
            give(self.name(1), self.total[1])
        else:
            give(self.name(winner), self.pot)
        self._sync_buttons()
        await self._update(interaction)
        self.stop()

    async def _next_street(self, interaction):
        idx = self.STREETS.index(self.street)
        if idx == len(self.STREETS) - 1:
            await self._do_showdown(interaction)
            return
        self.street = self.STREETS[idx + 1]
        for _ in range(3 if self.street == "Flop" else 1):
            self.community.append(self.deck.pop())
        self.street_bet = [0, 0]
        self.acted = set()
        self.raises = 0
        self.to_act = 1
        self._sync_buttons()
        await self._update(interaction)

    async def _do_showdown(self, interaction):
        s0 = best_hand(self.hole[0] + self.community)
        s1 = best_hand(self.hole[1] + self.community)
        if s0 > s1:
            winner, text = 0, f"{self.name(0)} won {self.pot} using {hand_name(s0)}!"
        elif s1 > s0:
            winner, text = 1, f"{self.name(1)} won {self.pot} using {hand_name(s1)}!"
        else:
            winner, text = None, f"Split pot! Both players have {hand_name(s0)}."
        await self._finish(interaction, winner, text, showdown=True)

    async def _guard(self, interaction):
        if self.over:
            await interaction.response.send_message("This game is over", ephemeral=True)
            return False
        if interaction.user != self.players[self.to_act]:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return False
        return True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user not in self.players:
            await interaction.response.send_message("This is not your game", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        async with self.lock:
            if self.over:
                return
            loser = self.to_act
            await self._finish(
                None, 1 - loser,
                f"{self.name(loser)} ran out of time and folded. "
                f"{self.name(1 - loser)} won {self.pot}!",
            )

    @discord.ui.button(label="Fold", style=discord.ButtonStyle.danger)
    async def fold_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self.lock:
            if not await self._guard(interaction):
                return
            i = self.to_act
            self.last_action = f"{self.name(i)} folded."
            await self._finish(
                interaction, 1 - i,
                f"{self.name(i)} folded. {self.name(1 - i)} won {self.pot} monies!",
            )

    @discord.ui.button(label="Check", style=discord.ButtonStyle.primary)
    async def call_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self.lock:
            if not await self._guard(interaction):
                return
            i = self.to_act
            need = self.to_call(i)
            if need:
                err = place_bet(self.name(i), need)
                if err:
                    await interaction.response.send_message(err, ephemeral=True)
                    return
                self.street_bet[i] += need
                self.total[i] += need
                self.last_action = f"{self.name(i)} called and added {need} monies."
            else:
                self.last_action = f"{self.name(i)} checked."
            self.acted.add(i)
            if len(self.acted) == 2 and self.street_bet[0] == self.street_bet[1]:
                await self._next_street(interaction)
            else:
                self.to_act = 1 - i
                self._sync_buttons()
                await self._update(interaction)

    @discord.ui.button(label="Raise", style=discord.ButtonStyle.success)
    async def raise_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with self.lock:
            if not await self._guard(interaction):
                return
            if self.raises >= MAX_RAISES:
                await interaction.response.send_message("Raise limit reached for this street.", ephemeral=True)
                return
            i = self.to_act
            need = self.to_call(i) + RAISE_SIZE
            err = place_bet(self.name(i), need)
            if err:
                await interaction.response.send_message(err, ephemeral=True)
                return
            self.street_bet[i] += need
            self.total[i] += need
            self.raises += 1
            self.acted = {i}
            self.last_action = f"{self.name(i)} raised and added {need} monies."
            self.to_act = 1 - i
            self._sync_buttons()
            await self._update(interaction)

    @discord.ui.button(label="My Cards", style=discord.ButtonStyle.secondary, row=1)
    async def cards_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        i = self.players.index(interaction.user)
        await interaction.response.send_message(
            f"Your cards are: {fmt_cards(self.hole[i])}", ephemeral=True
        )

@client.command(name="texasholdem")
async def texasholdem(ctx):
    user = ctx.author
    embed = discord.Embed(
        title="Waiting for Player - Texas Hold'em - GameBot",
        description="Welcome to the 2 player no limit edition of Texas Hold'em (also known as simply poker). The host is the small blind. NOTE: A raise adds 2 monies on top of the call amount, up to 3 raises per round.",
        color= discord.Color.blurple()
    )
    view = StartTexasHoldem(user)
    await ctx.send(embed = embed, view = view)

class StartConnectFour(discord.ui.View):
    def __init__(self, user, bet):
        super().__init__(timeout=300)
        self.user = user
        self.bet = bet
        self.gameover = False
    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.primary)
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.user:
            await interaction.response.send_message("You can't join your own game!", ephemeral = True)
            return
        if self.gameover:
            await interaction.response.send_message("This game has already started!", ephemeral = True)
            return
        err = place_bet(self.user.name, self.bet)
        err2 = place_bet(interaction.user.name, self.bet)
        if err or err2:
            if err:
                give(interaction.user.name, self.bet)
                await interaction.response.send_message(f"{self.user.name} doesn't have enough monies!")
            else:
                give(self.user.name, self.bet)
                await interaction.response.send_message(f"{interaction.user.name} doesn't have enough monies!")
            return
        await interaction.response.edit_message(embed=discord.Embed(
            title="Connect 4",
            description=f"""
X: {self.user.name}, O: {interaction.user.name}
```
1 2 3 4 5 6 7
. . . . . . .
. . . . . . .
. . . . . . .
. . . . . . .
. . . . . . .
. . . . . . .
```

It is {self.user.name}'s turn.
"""
        ), view=ConnectFourGame(self.user, interaction.user, self.bet))
        

class ConnectFourGame(discord.ui.View):
    def __init__(self, user, user2, bet):
        super().__init__(timeout=300)
        self.user = user
        self.user2 = user2
        self.bet = bet
        self.board = ["" for i in range(7)]
        self.turn = user
        self.gameover = False

    def _checkfour(self):
        board = [col.ljust(6, '.') for col in self.board]
        cols = len(board)
        rows = len(board[0])
    
        # right, up, up-right, down-right
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    
        for c in range(cols):
            for r in range(rows):
                piece = board[c][r]
                if piece == '.':
                    continue
                for dc, dr in directions:
                    if all(
                        0 <= c + dc * i < cols
                        and 0 <= r + dr * i < rows
                        and board[c + dc * i][r + dr * i] == piece
                        for i in range(4)
                    ):
                        return piece
        return None

    def _update(self, column, to):
        self.board[column-1] += "OX"[to]
        rows = '\n'.join(
            ' '.join(self.board[j][i] if len(self.board[j]) > i else '.' for j in range(7))
            for i in range(5, -1, -1)
        )
        y = self._checkfour()
        if y:
            if y == "O":
                finaltext = f"{self.user2.name} won!"
                give(self.user2.name, self.bet * 2)
            else:
                finaltext = f"{self.user.name} won!"
                give(self.user.name, self.bet * 2)
            self.gameover = True
        else:
            finaltext = f"It is {self.turn.name}'s turn."
        return f"""
X: {self.user.name}, O: {self.user2.name}
```
1 2 3 4 5 6 7
{rows}
```
{finaltext}
    """
        
    @discord.ui.button(label="1", style=discord.ButtonStyle.primary)
    async def column_1(self, interaction, button):
        if interaction.user != self.user and interaction.user != self.user2:
            await interaction.response.send_message("This isn't your game!", ephemeral = True)
            return
        if self.gameover:
            await interaction.response.send_message("This game is already over!", ephemeral = True)
            return
        if self.turn != interaction.user:
            await interaction.response.send_message("It's not your turn!", ephemeral = True)
            return
        if len(self.board[0]) >= 6:
            await interaction.response.send_message("This column is full!", ephemeral = True)
            return
        if self.turn == self.user:
            self.turn = self.user2
        else:
            self.turn = self.user
        await interaction.response.edit_message(embed=discord.Embed(title="Connect 4 - GameBot", description=self._update(1, (interaction.user == self.user))), view = self)

    @discord.ui.button(label="2", style=discord.ButtonStyle.primary)
    async def column_2(self, interaction, button):
        if interaction.user != self.user and interaction.user != self.user2:
            await interaction.response.send_message("This isn't your game!", ephemeral = True)
            return
        if self.gameover:
            await interaction.response.send_message("This game is already over!", ephemeral = True)
            return
        if self.turn != interaction.user:
            await interaction.response.send_message("It's not your turn!", ephemeral = True)
            return
        if len(self.board[1]) >= 6:
            await interaction.response.send_message("This column is full!", ephemeral = True)
            return
        if self.turn == self.user:
            self.turn = self.user2
        else:
            self.turn = self.user
        await interaction.response.edit_message(embed=discord.Embed(title="Connect 4 - GameBot", description=self._update(2, (interaction.user == self.user))), view = self)

    @discord.ui.button(label="3", style=discord.ButtonStyle.primary)
    async def column_3(self, interaction, button):
        if interaction.user != self.user and interaction.user != self.user2:
            await interaction.response.send_message("This isn't your game!", ephemeral = True)
            return
        if self.gameover:
            await interaction.response.send_message("This game is already over!", ephemeral = True)
            return
        if self.turn != interaction.user:
            await interaction.response.send_message("It's not your turn!", ephemeral = True)
            return
        if len(self.board[2]) >= 6:
            await interaction.response.send_message("This column is full!", ephemeral = True)
            return
        if self.turn == self.user:
            self.turn = self.user2
        else:
            self.turn = self.user
        await interaction.response.edit_message(embed=discord.Embed(title="Connect 4 - GameBot", description=self._update(3, (interaction.user == self.user))), view = self)

    @discord.ui.button(label="4", style=discord.ButtonStyle.primary)
    async def column_4(self, interaction, button):
        if interaction.user != self.user and interaction.user != self.user2:
            await interaction.response.send_message("This isn't your game!", ephemeral = True)
            return
        if self.gameover:
            await interaction.response.send_message("This game is already over!", ephemeral = True)
            return
        if self.turn != interaction.user:
            await interaction.response.send_message("It's not your turn!", ephemeral = True)
            return
        if len(self.board[3]) >= 6:
            await interaction.response.send_message("This column is full!", ephemeral = True)
            return
        if self.turn == self.user:
            self.turn = self.user2
        else:
            self.turn = self.user
        await interaction.response.edit_message(embed=discord.Embed(title="Connect 4 - GameBot", description=self._update(4, (interaction.user == self.user))), view = self)

    @discord.ui.button(label="5", style=discord.ButtonStyle.primary)
    async def column_5(self, interaction, button):
        if interaction.user != self.user and interaction.user != self.user2:
            await interaction.response.send_message("This isn't your game!", ephemeral = True)
            return
        if self.gameover:
            await interaction.response.send_message("This game is already over!", ephemeral = True)
            return
        if self.turn != interaction.user:
            await interaction.response.send_message("It's not your turn!", ephemeral = True)
            return
        if len(self.board[4]) >= 6:
            await interaction.response.send_message("This column is full!", ephemeral = True)
            return
        if self.turn == self.user:
            self.turn = self.user2
        else:
            self.turn = self.user
        await interaction.response.edit_message(embed=discord.Embed(title="Connect 4 - GameBot", description=self._update(5, (interaction.user == self.user))), view = self)

    @discord.ui.button(label="6", style=discord.ButtonStyle.primary)
    async def column_6(self, interaction, button):
        if interaction.user != self.user and interaction.user != self.user2:
            await interaction.response.send_message("This isn't your game!", ephemeral = True)
            return
        if self.gameover:
            await interaction.response.send_message("This game is already over!", ephemeral = True)
            return
        if self.turn != interaction.user:
            await interaction.response.send_message("It's not your turn!", ephemeral = True)
            return
        if len(self.board[5]) >= 6:
            await interaction.response.send_message("This column is full!", ephemeral = True)
            return
        if self.turn == self.user:
            self.turn = self.user2
        else:
            self.turn = self.user
        await interaction.response.edit_message(embed=discord.Embed(title="Connect 4 - GameBot", description=self._update(6, (interaction.user == self.user))), view = self)

    @discord.ui.button(label="7", style=discord.ButtonStyle.primary)
    async def column_7(self, interaction, button):
        if interaction.user != self.user and interaction.user != self.user2:
            await interaction.response.send_message("This isn't your game!", ephemeral = True)
            return
        if self.gameover:
            await interaction.response.send_message("This game is already over!", ephemeral = True)
            return
        if self.turn != interaction.user:
            await interaction.response.send_message("It's not your turn!", ephemeral = True)
            return
        if len(self.board[6]) >= 6:
            await interaction.response.send_message("This column is full!", ephemeral = True)
            return
        if self.turn == self.user:
            self.turn = self.user2
        else:
            self.turn = self.user
        await interaction.response.edit_message(embed=discord.Embed(title="Connect 4 - GameBot", description=self._update(7, (interaction.user == self.user))), view = self)

@client.command(name="ram")
async def ram(ctx):
    place_bet(ctx.author.name, 1000)
    await ctx.send("Thanks for investing in our RAM market! Your return is -100%.")

@client.command(name="connect4")
async def connect4(ctx, bet: int):
    user = ctx.author
    embed = discord.Embed(
        title="Waiting for Player - Connect 4 - GameBot",
        description=f"Welcome to Connect 4.\nBet: **{bet}**",
        color= discord.Color.blurple()
    )
    view = StartConnectFour(user, bet)
    await ctx.send(embed = embed, view = view)

@client.command(name="br0k3")
async def br0k3(ctx):
    await ctx.send("You're broke? Can't be me.")

def generate_word():
    with open("english_words.txt", "r") as f:
        return random.choice(f.read().split())

class wordguessModal(discord.ui.Modal):
    def __init__(self, words, target,v, bet):
        super().__init__(title="wordguess - GameBot")
        self.words = words
        print(target)
        print(words)
        self.target = target
        self.v = v
        self.bet = bet

    quese = discord.ui.TextInput(label="Word to guess", placeholder = "fire", required=True, max_length=20)
    async def on_submit(self, interaction):
        # Check if valid word
        if self.quese.value.lower() in model.key_to_index:
            # get similarity
            sim = model.similarity(self.target, self.quese.value.lower())
            wontext = ""
            if sim == 1:
                mult = 23.3 * math.exp(-(len(self.words)+1)/8)
                wontext = f"You won in {len(self.words)+1} tries, and earned {mult} times your money, earning {round(mult*self.bet)} monies!"
                give(self.v.user.name, round(mult*self.bet))
                self.v.gameover = True
            self.words.append([self.quese.value.lower(), sim])
            self.words.sort(key=lambda x: -float(x[1]))
            embed = discord.Embed(
                title="wordguess - GameBot",
                description=f"{'\n'.join([i[0]+" - "+str((float(i[1])+1)*50)+'%' for i in self.words])}\n{wontext}"
            )
            await interaction.response.edit_message(embed=embed, view=self.v)

class wordguessView(discord.ui.View):
    def __init__(self, user, bet):
        super().__init__(timeout=300)
        self.user = user
        self.word = generate_word()
        self.gameover = False
        self.guessed = []
        self.bet = bet

class ContextoView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=300)
        self.user = user
        self.word = generate_word(model)
        self.gameover = False
        self.guessed = []
    @discord.ui.button(label="Guess")
    async def guess(self, interaction, button):
        if self.gameover:
            await interaction.response.send_message("This game has ended!")
            return
        if self.user != interaction.user:
            await interaction.response.send_message("This isn't your game of wordguess!")
            return
        await interaction.response.send_modal(wordguessModal(self.guessed, self.word, self, self.bet))
        

@client.command(name="wordguess")
async def wordguess(ctx, bet: int):
    embed = discord.Embed(
        title="wordguess - GameBot",
        description="Make your first guess!"
    )
    err = place_bet(ctx.author.name, bet)
    if err:
        await ctx.send(err)
        return
    await ctx.send(embed=embed, view=wordguessView(ctx.author, bet))

class NumberguessModal(discord.ui.Modal):
    def __init__(self, v):
        super().__init__(timeout=300, title="Number Guess - GameBot")
        self.v = v
    b=discord.ui.TextInput(label="Guess", placeholder="67", required=True, max_length=20)
    async def on_submit(self, interaction):
        # Check if valid number
        if not self.b.value.isdigit():
            await interaction.response.send_message("That's not a number!", ephemeral=True)
            return
        b= int(self.b.value)
        if b < 1 or b > 100:
            await interaction.response.send_message("This number is out of bounds!", ephemeral = True)
            return
        if b == self.v.number:
            mult = round(27.3634 / 2**(self.v.guesses+1), 2)
            await interaction.response.edit_message(embed=discord.Embed(title="Number Guess - GameBot", description=f"You won in {self.v.guesses} tries! You won a {mult}x prize!"))
            give(self.v.user.name, mult*self.v.bet)
            self.v.gameover = True
            return
        if b > self.v.number:
            self.v.up = b-1
        else:
            self.v.low = b+1
        self.v.guesses += 1
        await interaction.response.edit_message(embed=discord.Embed(
            title="Number Guess - GameBot",
            description=f"Not quite, it was {['higher','lower'][b>self.v.number]}.\nRange: {self.v.low}-{self.v.up}"
        ), view=self.v)

class NumberguessView(discord.ui.View):
    def __init__(self, bet, user):
        super().__init__(timeout=300)
        self.bet = bet
        self.number = random.randint(1, 100)
        print(self.number)
        self.user = user
        self.guesses = 0 # 6-7 avg
        self.low = 1
        self.up = 100
        self.gameover = False
    @discord.ui.button(label="Guess", style=discord.ButtonStyle.primary)
    async def guess(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message("This game is not yours!", ephemeral = True)
            return
        if self.gameover:
            await interaction.response.send_message("This game is over!", ephemeral = True)
            return
        await interaction.response.send_modal(NumberguessModal(self))

@client.command(name="numberguess")
async def numberguess(ctx, bet: int):
    err = place_bet(ctx.author.name, bet)
    if err:
        await ctx.send(err)
        return
    await ctx.send(embed=discord.Embed(title="Number Guess - GameBot", description="Make your first guess!\nRange: 1-100", color=discord.Color.blurple()), view=NumberguessView(bet, ctx.author))

@client.command(name="help")
async def help(ctx):
    await ctx.send("""
**Thanks for using GameBot**!

GameBot is a bot designed for you to gamble in slots, roulette, dice, and more! Including... wordle? Here's a list of my commands!
* .help - This command
* .slots [bet] - Slot machine
* .roulette [bet] [color] - Classic European roulette, color betting only (1 green)
* .wordle [bet] [word] - Guess a 5 letter word, get monies based on how many characters you get right!
* .work - Gives you more money.
* .beg - Beg others for money.
* .pay - Pay another user money
* .steal [username] - Attempt to steal from another user.
* .coinflip [bet] - A 50-50 coinflip, duh.
* .leaderboard - Check who's got the most monies!
* .rps [bet] [input: rock/paper/scissors] - Bet on a rock paper scissors match.
* .dice [bet] [guess 2-12] - Roll two dice, win 3x if you guess the total.
* .ftft [bet] [input: zero/five/ten] [guess: zero/five/ten/fifteen/twenty] - Game of 5 10 15. [Learn more](https://www.theworldofchinese.com/2017/09/chinese-drinking-games-5-10-15/)
* .nim [bet] - Play subtraction nim
* .crash [bet] - Play crash, except it's not rigged.
* .blackjack [bet] - Play blackjack (also known as 21) without gambling your life savings.
* .craps [bet] [bet on: pass/dontpass] - Play the classic casino dice game: craps.
* .stocks - Check your stocks
* .stockprices - Check stock prices
* .buystocks [ticker] - Buy a stock
* .sellstocks [ticker] - Sell a stock
* .highlow [bet] - Play HighLow
* .texasholdem - Play Texas Hold'em
* .ram - Invest in the RAM market, lose money 100% of the time.
* .connect4 [bet] - Play Multiplayer connect 4
* .wordguess [bet] - Play wordguess (also known as Contexto)
)

The currency for interacting with GameBot is monies. Monies can be earned from gambling, being paid by another user, stealing from another user, working, or begging.

-# This bot is made by [ethan](https://ethan-codes.com)
""")


client.run(q[0])