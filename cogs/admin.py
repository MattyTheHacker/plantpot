# admin.py
# contains various administrator commands

import discord
import os
import json
import asyncio
import time

from discord.ext import commands, tasks
from aiosqlite import connect
from cogs import checkers, leaderboard
from cogs.inventory import Inventory
from dotenv import load_dotenv


class Admin(commands.Cog):

    version = '0.1'

    def __init__(self, bot):
        self.bot = bot

        self.setup.start()

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

    @setup.before_loop
    async def before_setup(self):
        await self.bot.wait_until_ready()

    async def executesql(self, statement, data=()):
        db = await connect('database.db')
        cursor = await db.execute(statement, data)
        await db.commit()
        rows = await cursor.fetchall()
        await cursor.close()
        await db.close()
        return list(rows)

    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def load(self, ctx, *, module: str):
        """Loads a module."""
        try:
            self.bot.load_extension(f'cogs.{module}')
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(f'{module} reloaded')

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def unload(self, *, module: str):
        """Unloads a module."""
        try:
            self.bot.unload_extension(f'cogs.{module}')
        except Exception as e:
            await self.bot.say('\N{PISTOL}')
            await self.bot.say('{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx, *, module: str):
        try:
            self.bot.unload_extension(f'cogs.{module}')
            self.bot.load_extension(f'cogs.{module}')
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(f'{module} reloaded')

    @commands.command(name="refresh", hidden=True)
    @checkers.is_owner()
    async def refresh(self, ctx):
        tempstr = ''
        for f in os.listdir('./cogs/'):
            if f.endswith('.py') and not f.startswith('__'):
                try:
                    self.bot.unload_extension(f'cogs.{f[:-3]}')
                    self.bot.load_extension(f'cogs.{f[:-3]}')
                except Exception as e:
                    tempstr += '{}: {}\n'.format(type(e).__name__, e)
                else:
                    tempstr += f'{f} reloaded\n'
        embed = discord.Embed()
        embed.title = 'refresh results'
        embed.description = tempstr
        await ctx.send(embed=embed)

    @commands.command(name='kill', help='wrong lever!', hidden=True)
    @commands.is_owner()
    async def kill(self, ctx):
        await ctx.send('shutting down plant')
        await ctx.bot.logout()

    @commands.command(name='teleports', hidden=True)
    @checkers.is_plant_owner()
    async def teleports(self, ctx, user: discord.Member, points: int, url,  *, name):
        await leaderboard.AnimeLeaderboard.addpoint(self, user.id, ctx.guild.id, url, name, points)
        await ctx.send('*teleports behind you* nothing personal kid')

    @commands.command(name='tp', hidden=True)
    @checkers.is_plant_owner()
    async def tp(self, ctx, user: discord.Member, quantity: int, *, name):
        if name.lower() in ['batch']:
            items = await self.executesql("SELECT image_id, event_id FROM images WHERE text LIKE '%stripe' AND event_id = ?", (1,))
            for stripe in items:
                await Inventory.additem(self, user.id, ctx.guild.id, stripe[1], stripe[0], quantity)
            await ctx.send('*teleports behind you* nothing personal kid')
            return
        item = await self.executesql('SELECT image_id, event_id FROM images WHERE lower(text) = ?', (name.lower(),))
        if len(item):
            await Inventory.additem(self, user.id, ctx.guild.id, item[0][1], item[0][0], quantity)
            await ctx.send('*teleports behind you* nothing personal kid')
        else:
            await ctx.send('Item not found')

    @commands.command(name='remove', hidden=True)
    @checkers.is_plant_owner()
    async def remove(self, ctx, user: discord.Member, points: int, *, name):
        with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'r') as file:
            d = json.loads(file.read())
        removed = False
        for u in d['users']:
            if u['userid'] == user.id:
                for image in u['images']:
                    if image['name'].lower() == name.lower():
                        u['images'].remove(image)
                        u['points'] -= points
                        removed = True
        if removed:
            with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'w') as file:
                json.dump(d, file)
            await ctx.send(f'Removed {name} from {user.mention}\'s inventory')
        else:
            await ctx.send(f"Couldn't find {name} in {user.mention}'s inventory")

    @commands.command(name='gift', hidden=True)
    @checkers.is_plant_owner()
    async def gifting(self, ctx, user: discord.Member, *, name):
        await leaderboard.Leaderboard.addpoint(self, user.id, ctx.guild.id, name, 0)

    @commands.command(name='blacklist', hidden=True)
    @checkers.is_plant_owner()
    async def blacklist(self, ctx, user: discord.Member):
        with open(f'cogs/userblacklist.json', 'r') as file:
            d = json.loads(file.read())
        if d['id'].count(user.id):
            return await ctx.send('this user is already blacklisted')
        else:
            d['id'].append(user.id)
            await ctx.send(f'{user.mention} has been blacklisted')
        with open(f'cogs/userblacklist.json', 'w') as file:
            json.dump(d, file)

    @commands.command(name='whitelist', hidden=True)
    @checkers.is_plant_owner()
    async def whitelist(self, ctx, user: discord.Member):
        with open(f'cogs/userblacklist.json', 'r') as file:
            d = json.loads(file.read())
        if d['id'].count(user.id):
            d['id'].remove(user.id)
            await ctx.send(f'{user.mention} has been removed from the blacklist')
        else:
            return await ctx.send('user was not on the blacklist')
        with open(f'cogs/userblacklist.json', 'w') as file:
            json.dump(d, file)

    @commands.command(name='logchannel', hidden=True)
    @commands.is_owner()
    async def logchannel(self, ctx, channelid, limit=None):
        channel = await self.bot.fetch_channel(channelid)
        logstr = ''
        async for message in channel.history(limit=limit, oldest_first=True):
            logstr += f'{message.author.id} {message.author.display_name} Sent at: {str(message.created_at)}\n{message.content}\n\n'
        with open(f'{channelid}log.txt', 'w+') as f:
            f.write(logstr)
        with open('channellog.txt', 'a+') as f:
            f.write(
                f'logged {channel.guild.name}\'s {channel.name} channel, id: {channel.id} at: {time.time()}')
        await ctx.send('Channel logged')


class die:
    def __init__(self, bot):
        self.bot = bot
        self.setup.start()

    async def executesql(self, statement, data=()):
        db = await connect('database.db')
        cursor = await db.execute(statement, data)
        await db.commit()
        rows = await cursor.fetchall()
        await cursor.close()
        await db.close()
        return list(rows)

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

    @setup.before_loop
    async def before_setup(self):
        await self.bot.wait_until_ready()

    async def give(self, ctx, user: discord.Member, name):
        with open('cogs/badges.json', 'r') as file:
            d = json.loads(file.read())
        if not await self.checkuser(user.id, d):
            await self.adduser(user.id, d)
        if await self.checkbadge(user.id, name, d):
            return await ctx.send(f'{user.display_name} already has that badge')
        temp = d['badges'].get(name)
        for u in d['users']:
            if u['userid'] == user.id:
                u['badges'].append({name: temp})
                await ctx.send(f'{user.display_name} has just received {name} {temp}')

        with open('cogs/badges.json', 'w') as file:
            json.dump(d, file)

    async def checkuser(self, uid, d):
        for user in d['users']:
            if user['userid'] == uid:
                return True
        else:
            return False

    async def adduser(self, uid, d):
        d['users'].append({'userid': uid,
                           'badges': []})
        print(d)
        return d

    async def checkbadge(self, uid, name, data):
        for user in data['users']:
            if user['userid'] == uid:
                for badge in user['badges']:
                    for n in badge:
                        if n == name:
                            return True
                return False
        return False


def setup(bot):
    bot.add_cog(Admin(bot))
