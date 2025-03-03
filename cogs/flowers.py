# flowers.py
# spring 2021 code
# VERY OLD, TO BE REPLACED WITH EVENTS.PY

import os
import json
import asyncio
import random
import time
import discord

from cogs import imageposting, leaderboard, profile, checkers
from discord.ext import commands


class Flower(commands.Cog):
    version = '0.1'

    def __init__(self, bot):
        self.bot = bot
        self.emoji = '\U0001F338'

    @commands.command(name='flowerevent', hidden=True)
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def flowerevent(self, ctx):
        await ctx.message.delete()
        cd = 60
        start = time.time()
        c = checkers.SpamChecker()
        while True:
            await asyncio.sleep(5)
            if imageposting.Imageposting.checktime(self, start):
                r = random.random()
                if r <= 0.0001:
                    p = 1500
                    x = 0
                elif r <= 0.005:
                    p = 600
                    x = 1
                elif r <= 0.02:
                    p = 400
                    x = 2
                elif r <= 0.05:
                    p = 200
                    x = 3
                elif r <= 0.1:
                    p = 100
                    x = 4
                elif r <= 0.225:
                    p = 50
                    x = 5
                elif r <= 0.425:
                    p = 20
                    x = 6
                elif r <= 0.7:
                    p = 10
                    x = 7
                else:
                    p = 1
                    x = 8
                temp = await Flower.getflower(self, ctx, x)
                image = list(temp.items())[0]
                rarities = {0: "ultra super amazing", 1: "legendary", 2: "mythic", 3: "epic",
                            4: "plant's favourite", 5: "ultra rare", 6: "rare", 7: "uncommon", 8: "common"}
                embed = discord.Embed()
                embed.title = (image[0])
                embed.set_image(url=image[1])
                post = await ctx.send(embed=embed)
                await post.add_reaction(self.emoji)
                while True:
                    def check(r, u):
                        if str(r.emoji) == self.emoji and r.message.id == post.id and u != self.bot.user:
                            return r, u

                    try:
                        r, usr = await self.bot.wait_for('reaction_add', check=check, timeout=14400)
                    except asyncio.TimeoutError:
                        return await ctx.send('Event timed out due to inactivity, please ask a user with `manage server` permissions to restart the event using `.image event spring`')
                    if await c.checkuser(ctx, usr.id):
                        await ctx.send(f'hold up {usr.mention}, you\'ve collected a flower too recently, please wait a second to give other users a chance!')
                        await r.remove(usr)
                    else:
                        break
                coll = False
                if await leaderboard.Leaderboard.checkimage(self, usr.id, ctx.guild.id, image[0]):
                    coll = True
                    if x == 0:
                        p = 500
                    elif x == 1:
                        p = 150
                    elif x == 2:
                        p = 100
                    elif x == 3:
                        p = 50
                    elif x == 4:
                        p = 30
                    elif x == 5:
                        p = 15
                    elif x == 6:
                        p = 8
                    elif x == 7:
                        p = 4
                    else:
                        p = 1
                await leaderboard.Leaderboard.addpoint(self, usr.id, ctx.guild.id, image[0], p)
                await profile.Profile.addpoint(self, usr.id, p)
                r = rarities[x]
                if x == 1 or x == 2 or x == 6 or x == 8:
                    await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up a {r} flower!** {self.emoji}')
                elif x == 4:
                    await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up one of {r} flowers!** {self.emoji}')
                else:
                    await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up an {r} flower!** {self.emoji}')
                if p == 1:
                    await ctx.send('**you\'ve earned 1 point!**')
                else:
                    if coll:
                        await ctx.send(f'**as you\'ve collected this before, you\'ve earned {p} points**')
                    else:
                        await ctx.send(f'**you\'ve earned {p} points!**')
                await asyncio.sleep(cd)
                await c.unloadusers(ctx)
                print('restarting countdown')
                start = time.time()

    async def getflower(self, ctx, rarity):
        with open(f'cogs/flowers.json', 'r') as file:
            d = json.loads(file.read())
        if rarity == 0:
            return {"me!!": "https://i.imgur.com/I9SPukW.jpg"}
        elif rarity == 1:
            temp = d['Legendary']
            return random.choice(temp)
        elif rarity == 2:
            temp = d['Mythic']
            return random.choice(temp)
        elif rarity == 3:
            temp = d['Epic']
            return random.choice(temp)
        elif rarity == 4:
            temp = d["Plant's Favourites"]
            return random.choice(temp)
        elif rarity == 5:
            temp = d['Ultra Rare']
            return random.choice(temp)
        elif rarity == 6:
            temp = d['Rare']
            return random.choice(temp)
        elif rarity == 7:
            temp = d['Uncommon']
            return random.choice(temp)
        elif rarity == 8:
            temp = d['Common']
            return random.choice(temp)


def setup(bot):
    bot.add_cog(Flower(bot))
