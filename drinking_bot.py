import discord
from discord.ext import commands
import asyncio
from random import randint, shuffle, sample
import sys

SUITS = ['Spades', 'Clubs', 'Hearts', 'Diamonds']
CARDS = ['Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']

def GetCard(id):
    suit = SUITS[int(id / 13)]
    n = CARDS[id % 13]
    return f"The {n} of {suit}."

def GetDeck(count = 1):
    deck = []
    for _ in range(count):
        for i in range(52):
            deck.append(GetCard(i))
    shuffle(deck)
    return deck   

def GetDrinkCountForPlayer(player, hand, card_list, drink_count):
    try:
        if player in ['pyramid', 'pyramid_n', 'cards']:
            return ""
        name = bot.get_user(player).name
        some_hidden = False
        drinks = 0
        for card, revealed in hand:
            card_val = CARDS.index(card.split(' ')[1])
            drinks += drink_count * card_list.count(card_val)
            some_hidden |= not revealed
        s = f"{name}: {drinks}"
        if some_hidden:
            s += ' (you really should flip all your cards, silly)'
        return s
    except Exception as e:
        return f"{player} ??? {e}\n"       

bot = commands.Bot(command_prefix = '£')

db = {}

# Log that the bot logs in successfully
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

# Only respond to dm messages which weren't from the bot
@bot.event
async def on_message(msg):
    if msg.author != bot.user and '-bots' in msg.channel.name:
        await bot.process_commands(msg)

@bot.command(name='deal')
async def DealCmd(ctx):
    try:
        channel = ctx.message.channel.id
        author = ctx.message.author.id
        if channel not in db.keys():
            db[channel] = {'cards' : GetDeck()}
        if author in db[channel].keys():
            await ctx.send("You already have a hand, if you want to start again then please use the command !restart")
            return
        if len(db[channel]['cards']) < 4:
            db[channel]['cards'] += GetDeck()
        db[channel][author] = []
        for _ in range(4):
            idx = randint(0, len(db[channel]['cards']) - 1)
            card = db[channel]['cards'][idx]
            db[channel][author].append((card, False)) # card, not yet visible
            del db[channel]['cards'][idx]
        await ctx.send(f"Dealt {ctx.message.author.name} 4 cards")
    except Exception as e:
        await ctx.send("Something went wrong, please try again")
        if author == 210062164118077440:
            await ctx.send(e)

@bot.command(name='make', help='Makes the pyramid')
async def MakeCmd(ctx):
    try:
        channel = ctx.message.channel.id
        if channel not in db.keys() or len(list(db[channel].keys())) < 2:
            await ctx.send("You should probably deal some hands first! (use the £deal command)")
            return
        if len(db[channel]['cards']) < 21:
            db[channel]['cards'] += GetDeck() 
        db[channel]['pyramid_n'] = 6
        db[channel]['pyramid'] = []
        for _ in range(21):
            idx = randint(0, len(db[channel]['cards']) -1)
            card = db[channel]['cards'][idx]
            db[channel]['pyramid'].append((card, False)) # card, not yet visible
            del db[channel]['cards'][idx]
        await ctx.send("6 row pyramid constructed!")
    except Exception as e:
        await ctx.send("Something went wrong, please try again")
        if ctx.message.author.id == 210062164118077440:
            print(db[channel])
            await ctx.send(e)


@bot.command(name='restart')
async def RestartCmd(ctx):
    try:
        channel = ctx.message.channel.id
        if channel in db.keys():
            del db[channel]      
        await ctx.send("Cleared the cards off the table! You'll want to £deal some new hands and £make a new pyramid!")
    except Exception:
        await ctx.send("Something went wrong, please try again")

@bot.command(name='flip')
async def flipCmd(ctx):
    try:
        if 'pyramid' in ctx.message.content:
            await FlipRow(ctx)
            return
        if len(ctx.message.content.strip()) == 5:
            await FlipMe(ctx)
            return
        await ctx.send("Did you mean `£flip` or `£flip pyramid`?")
    except Exception as e:
        await ctx.send("Something went wrong, please try again")
        if ctx.message.author.id == 210062164118077440:
            await ctx.send(e)

@bot.command(name='row')
async def FlipRow(ctx):
    try:
        channel = ctx.message.channel.id
        if channel not in db.keys():
            await ctx.send("You should deal some hands first! (use the £deal command)")
            return
        if 'pyramid' not in db[channel].keys():
            await ctx.send("You should deal some hands first! (Use the £make command)")
            return
        i = db[channel]['pyramid_n']
        drink_count = (7-i)
        who = 'Take' if i % 2 == 1 else 'Hand out' 
        drinks = 'drinks' if drink_count != 1 else 'drink'
        s = f"```{who} {drink_count} {drinks} for each matching card:\n"
        idx = 0
        card_list = []
        while i != 0:
            if db[channel]['pyramid'][idx][1]:
                idx += 1
                continue
            card = db[channel]['pyramid'][idx][0]
            card_list.append(CARDS.index(card.split(' ')[1]))
            s += f"{card}\n"
            db[channel]['pyramid'][idx] = (card, True)
            idx += 1
            i -= 1
        for player, hand in db[channel].items():
            s += GetDrinkCountForPlayer(player, hand, card_list, drink_count)

        s += "```"
        await ctx.send(s)
        db[channel]['pyramid_n'] -= 1
    except Exception as e:
        await ctx.send("Something went wrong, please try again")
        if ctx.message.author.id == 210062164118077440:
            await ctx.send(e)

@bot.command(name='card')
async def FlipMe(ctx):
    try:
        channel = ctx.message.channel.id
        author = ctx.message.author.id
        if channel not in db.keys() or author not in db[channel].keys():
            await ctx.send("You should deal yourself a hand first! (use the £deal command)")
            return
        i = 0
        for card, flipped in db[channel][author]:
            if not flipped:
                await ctx.send(f"```{ctx.message.author.name} drew {card}```")
                db[channel][author][i] = (card, True)
                return
            i += 1
        await ctx.send(f"Seems you've flipped all your cards, {ctx.message.author.name}")
    except Exception as e:
        await ctx.send("Something went wrong, please try again")
        if ctx.message.author.id == 210062164118077440:
            await ctx.send(e)

@bot.command(name='hand')
async def HandCmd(ctx):
    try:
        channel = ctx.message.channel.id
        author = ctx.message.author.id
        if channel not in db.keys():
            await ctx.send("There's no game in this channel, start one with £deal")
            return
        if author not in db[channel].keys():
            await ctx.send("You do not have a hand, deal yourself in with £deal")
            return
        s = f"```\nYour hand, {ctx.message.author.name}:\n"
        for card, flipped in db[channel][author]:
            if not flipped:
                s += "???\n"
            else:
                s += f"{card}\n"
        s += "```"
        await ctx.send(s)
    except Exception as e:
        await ctx.send("Something went wrong, please try again")
        if ctx.message.author.id == 210062164118077440:
            await ctx.send(e)
tokenFile = open(sys.argv[1], "r")
token = tokenFile.read().strip()

bot.run(token)