import gevent
from gevent import monkey

monkey.patch_all()
from logging import Logger
from wxpy import *
from traceback import print_exc
import builtins
from datetime import datetime, timedelta
from typing import List

bot = Bot(cache_path=True, console_qr=1)
logger = Logger('sports')
myFriend = bot.friends()








from mysports.run import run

red, green = 2, 2


@bot.register(myFriend)
def bot_start_run(msg):
    builtins.print = wxprint(bot)
    def wxprint(my_bot):
        def func(x, **kwargs):
            logger.warning(x)
            gevent.spawn(msg.reply_msg, x)
            # return x
        return func
    
    try:
        if msg.text == '高校体育':
            msg.reply_msg("使用方法：帮肥宅跑步 账号 密码 （开始跑步后请不要打开高校体育！！！")
        elif msg.text.startswith("帮肥宅跑步"):
            msg.reply_msg("开始跑步...")
            userid = msg.text.split(' ')[1]
            passwd = msg.text.split(' ')[2]
            run(userid, passwd, rg=(red, green))

        # else:
            # msg.reply_msg('滚一边玩去')
    except Exception as e:
        print_exc(e)


def diligent_runner(hours: List[int]):
    userid = ''
    passwd = ''
    curr = datetime.now()
    tom = curr + timedelta(days=1)
    to_runs = []
    for hour in hours:
        if hour > curr.hour:
            to_runs.append(datetime(year=curr.year, month=curr.month, day=curr.day, hour=hour))
        else:
            to_runs.append(datetime(year=tom.year, month=tom.month, day=tom.day, hour=hour))
    logger.warning(to_runs)
    for tr in to_runs:
        gevent.spawn_later((tr - curr).total_seconds(), run, userid, passwd, rg=(red, green))
    gevent.spawn_later((tom - curr).total_seconds(), diligent_runner, hours)


if __name__ == '__main__':
    # diligent_runner([6, 9, 12, 15, 18, 21])
    bot.join()
