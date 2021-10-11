import discord
import requests
import json
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bs4 import BeautifulSoup

CHANNEL = 685977939820544053


class CheckNewComments:
    json = "https://steamcommunity.com/comment/PublishedFile_Public/render/76561198121161119/2016264376/"
    picture = "https://steamuserimages-a.akamaihd.net/ugc/786380326254665411/35373243E8C3371C02D2D65DF36E2E3CF5ACDB46/"

    def __init__(self, bot):
        self.bot = bot
        with open('lastpost', 'r') as f:
            self.lastpost = eval(f.read())
        self.start = self.lastpost['start']
        self.pagesize = self.lastpost['pagesize']

    async def check_page(self):
        req = requests.get(self.json)
        req.raise_for_status()
        comments = json.loads(req.text)
        self.pagesize = comments['pagesize']
        if self.lastpost['timelastpost'] != comments['timelastpost']:
            await self.update_comments(comments)
        print('Checked')

    def next_page(self):
        self.start += self.pagesize
        req = requests.get(self.json, params={'start': self.start})
        req.raise_for_status()
        comments = json.loads(req.text)
        soup = BeautifulSoup(comments['comments_html'], 'lxml')
        return soup.find_all(class_="commentthread_comment responsive_body_text")

    async def update_comments(self, comments):
        soup = BeautifulSoup(comments['comments_html'], 'lxml')
        all_comms = soup.find_all(class_="commentthread_comment responsive_body_text")
        timestamp = time.time()
        while timestamp > comments['timelastpost']:
            comment = all_comms.pop(0)
            timestamp = int(comment.span.attrs['data-timestamp'])
            await self.new_comment(comment)
            if all_comms == list():
                all_comms = self.next_page()
                comments['start'] = comments['start'] + comments['pagesize']
        with open('lastpost', 'w') as f:
            f.write(str(comments))
        self.lastpost = comments

    async def new_comment(self, comment):
        description = comment.find(class_="commentthread_comment_text").text.strip()
        author = comment.find(class_="commentthread_comment_author").a.text.strip()
        author_url = comment.find(class_="commentthread_comment_author").a.attrs['href']
        avatar = comment.find(class_="commentthread_comment_avatar").a.img.attrs['src']
        date = comment.find(class_="commentthread_comment_timestamp").attrs['title']
        embed = discord.Embed(description=description, color=discord.Colour.dark_blue())
        embed.set_author(name=author, url=author_url, icon_url=avatar)
        # embed.set_thumbnail(url=self.picture)
        embed.set_footer(text=date)
        await self.bot.get_channel(CHANNEL).send(embed=embed)


bot = discord.Client()
scheduler = AsyncIOScheduler()


async def check_page():
    check = CheckNewComments(bot)
    await check.check_page()


with open('token', 'r') as tok:
    token = tok.read()

scheduler.add_job(check_page, 'cron', day='*')
bot.run(token)
