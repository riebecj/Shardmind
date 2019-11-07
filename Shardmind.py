#!/usr/bin/env python3
from Daemon import daemon

import asyncio
import discord
import requests

from datetime import datetime
import logging.config
import re
import sys
import os

LOGGER = logging.getLogger('Shardmind.Main')
loop = asyncio.get_event_loop()


class QRNG(object):
    def __init__(self):
        self.endpoint = 'https://qrng.anu.edu.au/API/jsonI.php?length={quantity}&type=uint16'

    def get_data(self, quantity):
        response = requests.get(self.endpoint.format(quantity=quantity))
        if not response.ok:
            LOGGER.error(response.status_code, response.json())
        else:
            return response.json()['data']


class Bot(object):
    def __init__(self):
        # token for Discord API (VERY SECRET)
        self.token = self.read_token()
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

    def read_token(self):
        token_file = 'token.txt'

        if not os.path.isfile(token_file):
            raise FileNotFoundError('Cannot find token file')

        with open('token.txt', 'rt') as tf:
            token = tf.readline()

        return token


    def set_commands(self):
        """Set the bot command to the function"""
        self.commands = {
            '!help': self._help,
            '!stats': self._stats,
            '!info': self._info,
            '!rNdX': self._roll
        }

    def roll_calculator(self, number, die):
        return int(number / 65536 * die + 1)

    async def start(self):
        """Login"""
        await self.client.login(self.token)

        try:
            await self.client.connect()
        except discord.ClientException as e:
            LOGGER.error(e)

    async def stop(self):
        """Exit"""
        LOGGER.info('Exiting...')
        await self.client.logout()

    async def on_message(self, message):
        """Handle messages as commands"""
        roll_pattern = re.compile("([!])([r])([1-9]\d*)([d])([1-9]\d*)")

        if message.author == self.client.user:  # do not respond to itself
            LOGGER.info(f'Caught message written by self: {message.content}')
            return

        # handle standard commands
        if message.content.startswith(self.prefix):
            LOGGER.info(f'Parsing message: {message.content}')
            for command, func in self.commands.items():
                if command in message.content:
                    LOGGER.info(f'Executing command: {command}')
                    await func(message)
                    return

            if roll_pattern.match(message.content) is not None:
                LOGGER.info('Matched Dice Roll Regex')
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
        """Rolls N number of X-sided dice. Can use 'kl' to keep lowest or 'kh' to keep highest.
        Example: !r2d20kl rolls [12, 10] -> a 10 is rolled due to 'kl'"""
        keep_low = keep_high = False
        die_roll = message.content.split('!r')[-1]

        if die_roll.endswith('kl'):
            keep_low = True
        elif die_roll.endswith('kh'):
            keep_high = True

        quantity, die = die_roll.split('d')

        if int(quantity) > 100:
            await message.channel.send(f"Whoa! {quantity} is too much! I don't have that many dice!")
            return

        LOGGER.info(f'Rolling {die} sided die {quantity} times...')
        quantity = int(quantity)
        die = int(''.join([i for i in die if i.isdigit()]))

        result = QRNG().get_data(quantity)
        rolls = [self.roll_calculator(i, die) for i in result]
        LOGGER.info(f'Rolled {rolls}')

        if keep_high or keep_low:
            selected = max(rolls) if keep_high else min(rolls)
            await message.channel.send(f"Out of {rolls}, {message.author.display_name} rolled a {selected}!")
            return

        await message.channel.send(f"{message.author.display_name} rolled a "
                                   f"{' + '.join([str(i) for i in rolls])} = **{sum(rolls)}**")


def main():
    bot = Bot()
    try:
        asyncio.ensure_future(bot.start())
        loop.run_forever()

        loop.close()
    except discord.errors.HTTPException as e:
        print(e)
        sys.exit(2)
    except discord.errors.LoginFailure as e:
        print(e)
        sys.exit(2)


class Daemonize(daemon):
    def run(self):
        main()


if __name__ == '__main__':
    # daemon = Daemonize(pidfile=os.getcwd())
    # if len(sys.argv) == 2:
    #     if 'start' == sys.argv[1]:
    #         daemon.start()
    #     elif 'stop' == sys.argv[1]:
    #         daemon.stop()
    #     elif 'restart' == sys.argv[1]:
    #         daemon.restart()
    #     else:
    #         print("Unknown command")
    #         sys.exit(2)
    #     sys.exit(0)
    # else:
    #     print("usage: %s start|stop|restart" % sys.argv[0])
    #     sys.exit(0)
    main()
