import discord
from discord.ext import commands
import re
import random
import asyncio
import json
import os

with open("credentials.txt", "r") as f:
    q = f.read().splitlines()

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

The currency for interacting with GameBot is monies. Monies can be earned from gambling, being paid by another user, stealing from another user, working, or begging.

-# This bot is made by [ethan](https://ethan-codes.com)
""")


client.run(q[0])