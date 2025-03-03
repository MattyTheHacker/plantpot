# imageposting.py
# cog with all image posting capabilities
# BASICALLY ANCIENT THIS CODE WAS WRITTEN BEFORE COBOL WAS USED TO PROP UP THE WORLD'S FINANCES

import discord
import random
from re import fullmatch
import time
import json
import asyncio
from cogs import leaderboard, serversettings, profile, checkers, flowers

from discord.ext import commands


class Imageposting(commands.Cog):
    version = '0.1'

    def __init__(self, bot):
        self.bot = bot
        self.spam = False
        self.store = 'randomImages'
        self.emoji = '\U0001F338'

    @commands.group(help='please use .image help for more help', hidden=True)
    async def image(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('please specify a command, type ``.image help`` for more help')
            return

    @image.command(name='help', help='full help for image commands')
    async def help(self, ctx, command):
        commandhelp = {"post": "`.image post [description]` will post an image, if you give the description of one, it will post that image",
                       "add": "`.image add [image-url] [description]` will add a given image url in the format `https://i.imgur.com/{url-code}.[jpg/png/gif]` with a given description",
                       "all": "`.image all` will post all images"}
        helpstr = commandhelp.get(command)
        if helpstr is None:
            await ctx.send('please enter a valid command, type `.image help` for a command list')
        else:
            embed = discord.Embed()
            embed.title = f'".image {command}" help'
            embed.description = helpstr
            await ctx.send(embed=embed)

    @image.command(name='post', help='posts a random image, mostly debugging')
    async def post(self, ctx, *, desc=None):
        with open(f'cogs/{self.store}.json', 'r') as file:
            d = json.loads(file.read())

        if desc is None:
            image = {'desc': 'AniSoc 2021'}
            while image['desc'] == 'AniSoc 2021':
                image = random.choice(d['images'])
        else:
            for i in d['images']:
                if i['desc'] == desc:
                    image = i
                    break
            if image is None:
                await ctx.send(f'i\'m sorry but i couldn\'t find {desc}')
                return
        embed = discord.Embed()
        embed.set_image(url=image['url'])
        return [await ctx.send(embed=embed), image['desc']]

    @image.command(name='setstore', help='sets default store', hidden=True)
    async def setstore(self, ctx, store):
        self.store = store

    @image.command(name='add', help='adds a new image to postable images, ".image add [imgur link] [description]"')
    @checkers.is_plant_owner()
    async def add(self, ctx, link, *, desc):
        if fullmatch('^https://i\.imgur\.com/.*(\.jpg|\.jpeg|\.png|\.gif)$', link) is None:
            return await ctx.send('please link images in the form ```https://i.imgur.com/{url-code}.[jpg/png/gif]```')

        with open(f'cogs/{self.store}.json', 'r') as file:
            d = json.loads(file.read())
        images = d['images']
        for image in images:
            if image['url'] == link:
                return await ctx.send('this image is already added!')
        images.append({"url": link,
                       "desc": desc})

        temp = {"images": images}
        with open(f'cogs/{self.store}.json', 'w') as file:
            json.dump(temp, file)
            await ctx.send('image added')

    @image.command(name='remove', help='removes images', hidden=True)
    @commands.is_owner()
    async def remove(self, ctx, link):
        with open(f'cogs/{self.store}.json', 'r') as file:
            d = json.loads(file.read())
        for image in range(len(d['images'])):
            if d['images'][image]['url'] == link:
                d['images'].pop(image)
                return await ctx.send('removed image')
        await ctx.send('image not found!')

    # posts all images
    @image.command(name='all', help='posts all images')
    @checkers.is_guild_owner()
    async def all(self, ctx):
        with open(f'cogs/{self.store}.json', 'r') as file:
            d = json.loads(file.read())
        images = d['images']
        embed = discord.Embed()
        for image in images:
            embed.set_image(url=image['url'])
            await ctx.send(embed=embed)

    @image.command(name='rarity', help='displays different rarities, their chances, and points given')
    async def rarity(self, ctx):
        tempstr = ''
        temp = ["Legendary **(600/150)**: 0.5%",
                "Mythic **(400/100)**: 1.5%",
                "Epic **(200/50)**: 3%",
                "Plant's favourite **(100/30)**: 5%",
                "Ultra rare **(50/15)**: 12.5%",
                "Rare **(20/8)**: 17.5%",
                "Uncommon **(10/4)**: 25%",
                "Common **(1/1)**: 35%"]
        for r in temp:
            tempstr += r + '\n'
        embed = discord.Embed()
        embed.title = "Flower rarities"
        embed.description = tempstr
        await ctx.send(embed=embed)

    # starts posting images as over a function of time
    @image.command(name='event', help='starts an image collecting event')
    @checkers.is_guild_owner()
    @commands.max_concurrency(2, commands.BucketType.guild)
    async def event(self, ctx, season: str = None):
        if season == "spring":
            return await flowers.Flower.flowerevent(self, ctx)
        await ctx.message.delete()
        cd = await serversettings.ServerSettings.getcd(self, ctx)
        start = time.time()
        while True:
            await asyncio.sleep(2)
            if self.checktime(start):
                p, d = await self.post(ctx)
                await p.add_reaction(self.emoji)

                def check(r, u):
                    if str(r.emoji) == self.emoji and r.message.id == p.id and u != self.bot.user:
                        return r, u
                r, usr = await self.bot.wait_for('reaction_add', check=check)
                await leaderboard.Leaderboard.addpoint(self, usr.id, ctx.guild.id, d, 1)
                await profile.Profile.addpoint(self, usr.id, 1)
                await ctx.send(self.emoji + " " + usr.mention + '**, you just picked up ' + d + "!** " + self.emoji)
                await ctx.send('**you\'ve earned one point!**')
                await asyncio.sleep(cd)
                start = time.time()
                print('restarting countdown')

    # ugly and doesn't work
    @image.command(name='stop', help='stops the spam')
    @commands.is_owner()
    async def stop(self, ctx):
        Imageposting.event.stop()

    def checktime(self, oldtime):
        newtime = time.time()
        if random.random() > pow(0.99, newtime - oldtime):
            return True

    # ------------- Error handling ------------- #

    @help.error
    async def helperror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed()
            embed.title = 'please format this command as .image help [command]'
            embed.description = """image commands are:
            **post**: posts an image
            **add**: adds an image
            **all**: posts all images
            **event**: posts randomly on a timer
            **stop**: stops event"""

            await ctx.send(embed=embed)

    @post.error
    async def posterror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await self.help(ctx, "post")

    @add.error
    async def adderror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await self.help(ctx, "add")

    @all.error
    async def allerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await self.help(ctx, "all")

    @event.error
    async def eventerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await self.help(ctx, "event")
        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send('You\'ve reached the maximum number of times you can start an event! Please end one before trying again')


def setup(bot):
    bot.add_cog(Imageposting(bot))
