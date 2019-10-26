from datetime import datetime
import logging.config
import asyncio
import discord
import re
import quantumrandom as qr


log = logging.getLogger('Shardmind.Main')
loop = asyncio.get_event_loop()


class Bot(object):
    def __init__(self):
        # token for Discord API (VERY SECRET)
        self.token = 'NjM3NzE1NTI5ODg4Njk0MzAy.XbSM_g.jMA8AwSQk36j-QNev79adeuDlu0'
        # prefix for all commands to bot
        self.prefix = '!'
        # specific channel lock. Won't reply or post to any other public channel
        self.client = discord.Client(loop=loop)
        # dictionary for commands
        self.commands = dict()
        # adds the event handler for messages
        self.client.event(self.on_message)
        # get bot start time
        self._start_time = datetime.now()
        # set the bot commands
        self.set_commands()

    def set_commands(self):
        """Set the bot command to the function"""
        self.commands = {
            '!help': self._help,
            '!stats': self._stats,
            '!info': self._info
        }

    async def start(self):
        """Login"""
        await self.client.login(self.token)

        try:
            await self.client.connect()
        except discord.ClientException:
            raise

    async def stop(self):
        """Exit"""
        await self.client.logout()

    async def on_message(self, message):
        """Handle messages as commands"""
        roll_pattern = re.compile("([!])([r])([1-9]\d*)([d])([1-9]\d*)")
        if message.author == self.client.user:  # do not respond to itself
            return

        # handle standard commands
        if message.content.startswith(self.prefix):
            for command, func in self.commands.items():
                if command in message.content:
                    await func(message)
                    return

            if roll_pattern.match(message.content) is not None:
                await self._roll(message)
            else:
                await message.channel.send(f'Invalid Command: {message.content}')

    async def _help(self, message):
        """Print the help message"""
        msg = 'Available commands:\n'
        for command, func in self.commands.items():
            msg += '`%s' % command
            msg += (' : %s`\n' % func.__doc__) if func.__doc__ else '`\n'

        await message.channel.send(msg)

    async def _info(self, message):
        """Print your id"""
        await message.channel.send("{0.display_name}, Your id: `{0.id}`".format(message.author))

    async def _stats(self, message):
        """Show the bot's general stats"""
        users = -1
        for s in self.client.guilds:
            users += len(s.members)
        msg = 'General informations:\n'
        msg += '`Uptime            : {} Seconds`\n'.format((datetime.now() - self._start_time).total_seconds())
        msg += '`Users in touch    : {} Users in {} servers`\n'.format(users, len(self.client.guilds))
        await message.channel.send(msg)

    async def _roll(self, message):
        die_roll = message.content.split('!r')[-1]
        quantity, die = die_roll.split('d')
        for i in range(1, int(quantity) + 1):
            result = int(qr.get_data()[0] / 65536 * int(die) + 1)
            if result == 20:
                await message.channel.send(f"**{message.author.display_name}'s Roll {i}: {result}**")
            else:
                await message.channel.send(f"{message.author.display_name}'s Roll {i}: {result}")


if __name__ == '__main__':
    bot = Bot()

    asyncio.ensure_future(bot.start())
    loop.run_forever()

    loop.close()
