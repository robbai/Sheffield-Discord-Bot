#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A cog to get confessions from the public facebook page.

https://www.facebook.com/sheffessions
"""
import traceback
import re

import orator
from discord.ext import commands, tasks
from facebook_scraper import get_posts
import utils as ut

from models import Sheffession

SHEFFESSIONS_PAGE = 'sheffessions'

SHEFFESSION_ID_REGEX = re.compile(r"#Sheffession\d+")


class SheffessionsCog(commands.Cog, name="Sheffessions"):
    """Create a class that extends Cog to make our functionality in."""

    def __init__(self, bot):
        """Save our bot argument that is passed in to the class."""
        self.bot = bot

        self.post_daemon.start()

    @commands.group(
        name="sheffession")
    async def sheffession(self, ctx):
        if ctx.invoked_subcommand is None:
            print("post id")

    @sheffession.command(
        name="latest",
        help="Gets information about the lastest sheffession.")
    @commands.has_role("Member")
    async def latest(self, ctx):
        """
        Create a simple ping pong command.

        This command adds some help text and also required that the user
        have the Member role, this is case-sensitive.
        """
        await ctx.send("Latest Post")

    @sheffession.command(
        name="random",
        help="Gets information about a random sheffession.")
    @commands.has_role("Member")
    async def random(self, ctx):
        """
        Create a simple ping pong command.

        This command adds some help text and also required that the user
        have the Member role, this is case-sensitive.
        """
        await ctx.send("Random Post")

    @sheffession.command(
        name="loadall",
        help="Attempts to load all posts from the sheffessions page "
             "into the database.")
    @commands.has_role("Admin")
    async def load_all(self, ctx):
        """
        Create a simple ping pong command.

        This command adds some help text and also required that the user
        have the Member role, this is case-sensitive.
        """

        loading_message = await ctx.send("Loading Sheffessions")

        for index, post in enumerate(get_posts(SHEFFESSIONS_PAGE, pages=1000)):
            if not (index % 5):
                await loading_message.edit(
                    content=loading_message.content + ".")

            if not (index % 15):
                await loading_message.edit(content="Loading Sheffessions")

            sheffession = Sheffession()

            if post['post_text'] is None:
                continue

            match = SHEFFESSION_ID_REGEX.match(post['post_text'])

            if match:
                sheffession.id = post['post_text'] \
                    [match.start(0) + 12: match.end(0)]
            else:
                continue

            sheffession.post_text = post['post_text']
            sheffession.post_url = post['post_url']
            sheffession.post_date = post['time']
            sheffession.image_url = post['image']
            sheffession.video_url = post['video']

            try:
                sheffession.save()
            except orator.exceptions.query.QueryException:
                pass

        await loading_message.delete()
        await ctx.send("Loaded all sheffessions")

    @tasks.loop(seconds=60.0)
    async def post_daemon(self):
        """
        Task loop that update response counts
        and ends polls that need to be ended
        """

        # try-except can be replaced with a coroutine
        # wrapped with discord.ext.tasks.Loop.error on release of 1.4
        try:
            print("hi")
        except Exception:
            traceback.print_exc()


def setup(bot):
    """
    Add the cog we have made to our bot.

    This function is necessary for every cog file, multiple classes in the
    same file all need adding and each file must have their own setup function.
    """
    bot.add_cog(SheffessionsCog(bot))
