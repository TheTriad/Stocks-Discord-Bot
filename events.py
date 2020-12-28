import discord, os, operator
from discord.ext import commands, tasks
from ledger import Ledger
from stocks import (
    YahooFinance,
    PolygonRest,
)
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from config import TOKEN

ledger = Ledger('data.json')
stocks = PolygonRest()
intents = discord.Intents.default()
intents.members = True
command_prefix = "!"
bot = commands.Bot(command_prefix=command_prefix, intents=intents)
bot.remove_command('help')
embed_color = 0x00ff00

def rnd(f):
    return round(f, 2)

def sdate():
    return str(datetime.now())[:19]

def add_embed(title=None, description=None, fields=None, inline=False, ctx=None, author=None, image=None, color=embed_color):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
    )
    if fields != None:
        for name, value in fields:
            embed.add_field(
                name=name,
                value=value,
                inline=inline,
            )
    if author != None:
        embed.set_author(name=author.name, icon_url=author.avatar_url)
    if image != None:
        embed.set_image(url=image)
    return embed

@bot.command()
async def help(ctx):
    fields = [
        ('!add', 'Sign up for StocksBot'),
        ('!buy (type) (symbol) (amount)', 'To purchase shares'),
        ('!sell (type) (symbol) (amount)', 'To sell shares'),
        ('!liquidate', 'To liquidate all assets'),
        ('!portfolio (id)', 'To view all your assets'),
        ('!stock (symbol)', 'To view the stock trend of a specific company'),
        ('!lookup (symbol)', 'To get the information of a specific company'),
    ]
    embed = add_embed('Help', description='Descriptions for all the commmands', fields=fields)
    await ctx.send(embed=embed)

@bot.command()
async def echo(ctx, *, content:str):
    print(ctx.author)
    await ctx.send(content)

@bot.command()
async def add(ctx):
    id = ctx.author.id
    name = ctx.author.name
    if (ledger.contains(id)):
        embed = add_embed('StocksBot', 'Error: Already registered with StocksBot!', color=0xFF0000, author=ctx.author)
    else:
        ledger.add_user(id, name)
        embed = add_embed('StocksBot', 'You have been added to StocksBot!', author=ctx.author)
    await ctx.send(embed=embed)

@bot.command()
async def buy(ctx, type:str, symbol:str, amount:str):
    symbol = symbol.upper()
    id = str(ctx.author.id)
    name = ctx.author.name
    try:
        price = stocks.latest_price(symbol)
        if price == None:
            raise
    except:
        await ctx.send(f'{ctx.author.mention} "{symbol}" couldn\'t be found')
        return
    if amount == 'all':
        qty = None
    elif type == 'cash':
        qty = int(amount)/price
    elif type == 'qty':
        qty = int(amount)
    else:
        await ctx.send(f'Invalid Command {ctx.author.mention}')

    pqty = ledger.enter_position(str(id), 'long', symbol, price, qty)
    if pqty == False:
        embed = add_embed('Error in Transaction', f'{ctx.author.mention} error processing transaction! (Maybe Oversold)', author=ctx.author)
        await ctx.send(embed=embed)
    else:
        fields = [
            ('Share Price', f'$ {rnd(price)}'),
            ('Quantity', f'{rnd(pqty)} shares'),
            ('Worth', f'${rnd(pqty * price)}')
        ]
        embed = add_embed(f'Bought {symbol}', f'Transaction at {sdate()}', fields=fields, author=ctx.author, inline=True)
        await ctx.send(embed=embed)

@bot.command()
async def sell(ctx, type:str, symbol:str, amount:str):
    symbol = symbol.upper()
    id = str(ctx.author.id)
    name = ctx.author.name
    price = stocks.latest_price(symbol)
    try:
        price = stocks.latest_price(symbol)
        if price == None:
            raise
    except:
        await ctx.send(f'{ctx.author.mention} "{symbol}" couldn\'t be found')
        return
    if amount == 'all':
        qty = None
    elif type == 'cash':
        qty = int(amount)/price
    elif type == 'qty':
        qty = int(amount)
    else:
        await ctx.send(f'Invalid Command {ctx.author.mention}')

    pqty = ledger.exit_position(id, 'sell', symbol, price, qty)
    if pqty == False:
        embed = add_embed('Error in Transaction', f'{ctx.author.mention} error processing transaction! (Maybe Oversold)', author=ctx.author)
        await ctx.send(embed=embed)
    else:
        fields = [
            ('Share Price', f'$ {rnd(price)}'),
            ('Quantity', f'{rnd(pqty)} shares'),
            ('Worth', f'${rnd(pqty * price)}')
        ]
        embed = add_embed(f'Sold {symbol}', f'Transaction at {sdate()}', fields=fields, author=ctx.author, inline=True)
        await ctx.send(embed=embed)


@bot.command()
async def stock(ctx, symbol:str):
    symbol = symbol.upper()
    price = stocks.latest_price(symbol)
    open, high, low = stocks.get_stats(symbol)
    trend = rnd(price-open)
    trend_perc = rnd((price-open)/open*100)
    if trend > 0:
        trend = f'+${trend}'
        trend_perc = f'+{trend_perc}%'
    else:
        trend = f'-${trend}'
        trend_perc = f'-{trend_perc}%'
    fields = [
        ('Current Price', f'${price}'),
        ('Open Price', f'${open}'),
        ('High Price', f'${high}'),
        ('Low Price', f'${low}'),
        ('Trend Today', trend),
        ('Trend Today %', trend_perc),
    ]
    o, h, l, c = stocks.get_aggregate(symbol)
    layout = go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        width=1200,
        height=800,
        xaxis=go.layout.XAxis(
            showticklabels=False
        ),
        yaxis=go.layout.YAxis(
            color="white"
        )
    )
    fig = go.Figure(data=[go.Candlestick(open=o, high=h, low=l, close=c)], layout=layout)
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.write_image("images/" + symbol + ".png")
    file = discord.File("images/" + symbol + ".png", filename='image.png')
    embed = add_embed(title=symbol, description=f'Stats as of ({sdate()})', fields=fields, author=ctx.author, inline=True, image='attachment://image.png')
    await ctx.send(file=file, embed=embed)
    os.remove('images/' + symbol + '.png')

@bot.command()
async def liquidate(ctx):
    id = str(ctx.author.id)
    stocklist = ledger.liquidate(id)
    for symbol, qty in stocklist:
        price = stocks.latest_price(symbol)
        fields = []
        embed = add_embed(f'Sold {symbol}', f'{rnd(qty)} Shares (${rnd(qty * price)})', author=ctx.author)
        await ctx.send(embed=embed)

    embed = add_embed(f'Portfolio Liquidated', author=ctx.author)
    await ctx.send(embed=embed)


@bot.command()
async def leaderboard(ctx):
    ports, i, fields = ledger.get_all_owned(), 1, []
    worths = {}
    for id in ports:
        worth = ledger.get_balance(id)
        for sym, qty in ports[id]:
            worth += qty * stocks.latest_price(sym)
        worths[id] = worth
    sorted_worths = sorted(worths.items(), key=operator.itemgetter(1))
    sorted_worths.reverse()
    for id, bal in sorted_worths:
        if i > 10: break
        fields.append((f'{i}: {ctx.guild.get_member(int(id)).name}', f'Net Worth: ${bal}'))
        i += 1
    embed = add_embed(title='Leaderboard', fields=fields, author=ctx.author)
    await ctx.send(embed=embed)

@bot.command()
async def portfolio(ctx):
    after = ctx.message.content.lower().split("portfolio")[1]
    if (len(ctx.message.mentions) > 0):
        author = ctx.message.mentions[0]
    elif (len(after) > 2 and ctx.guild.get_member(int(after.split(' ')[1])) != None):
        author = ctx.guild.get_member(int(after.split(' ')[1]))
    else:
        author = ctx.author
    id = str(author.id)
    port = ledger.portfolio(id)
    fields = []
    cash_balance = ledger.get_balance(id)
    total_worth = cash_balance
    for sym, qty, ptype, price in port:
        current_price = stocks.latest_price(sym)
        if ptype == 'long':
            profit = rnd((current_price-price)*qty)
            profit_perc = rnd((current_price-price)/price*100)
            total_worth += current_price * qty
        else:
            total_worth += qty * (2 * price - current_price)
            profit = rnd((price-current_price)*qty)
            profit_perc = rnd((price-current_price)/price*100)
        value = f'''
            Shares: {rnd(qty)}
            Position: {ptype}
            Worth: ${rnd(current_price*qty)}‎‎‎‎‎‎‎‎‏‏‎‎‏‏‎‏‏‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎
            Profit: {profit}$
            Profit %: {profit_perc}%‏‏‎

        '''
        fields.append((f'{sym}', value))
    total_stats = f'''
        Net Worth: ${rnd(total_worth)}
        Cash Balance: ${rnd(cash_balance)}
        Total Profit:
        ${rnd(total_worth - 10e3)} | {rnd((total_worth - 10e3)/10e3 * 100)}%
    '''
    embed = add_embed(f'Portfolio', total_stats, fields=fields, inline=True, author=author)
    await ctx.send(embed=embed)


@bot.command()
async def lookup(ctx):
    query = ctx.message.content.lower().split("lookup")[1][1:]
    symbol = stocks.lookup(query)
    data = stocks.get_info(symbol)
    if data == False:
        embed = add_embed(f'Couldn\'t find information for "{query}"', 'Make sure symbol exists!')
        await ctx.send(embed=embed)
        return
    fields = [
        ('Symbol', data['symbol']),
        ('Maket Cap', f'${data["marketcap"]}'),
        ('Employees', data['employees']),
        ('Sector', data['sector']),
        ('Industry', data['industry']),
        ('Website', data['url'])
    ]
    embed = add_embed(data['name'], 'Basic Infomation', fields=fields, image=data['logo'], inline=True)
    await ctx.send(embed=embed)


bot.run(TOKEN)
