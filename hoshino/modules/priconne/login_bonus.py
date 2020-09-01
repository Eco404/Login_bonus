import time
import datetime
import pytz
import random
import os
from math import log
from hoshino import Service, R, priv
from hoshino.typing import CQEvent
from hoshino.modules.priconne.memberdata import Commic_DB
from datetime import datetime, timedelta

sv_help = f'''
[签到] 给主さま盖章章
[签到查询] 查看自己的签到情况和金币数量
'''.strip()

sv = Service('pcr-login-bonus', bundle='pcr娱乐', help_=sv_help)

dbfile = os.path.abspath('hoshino/modules/priconne/data/signindata')
cdb = Commic_DB(dbfile)

login_presents = [
    '扫荡券×5',  '家具币×1000', '普通EXP药水×5',  '宝石×50',  '玛那×3000',
    '扫荡券×10', '家具币×1500', '普通EXP药水×15', '宝石×80',  '白金扭蛋券×1',
    '扫荡券×15', '家具币×2000', '上等精炼石×3',   '宝石×100', '白金扭蛋券×1',
]
todo_list = [
    '找伊绪老师请教问题',
    '给宫子买布丁',
    '和真琴寻找伤害优衣的人',
    '找雪哥探讨女装的奥秘',
    '跟吉塔一起登上骑空艇',
    '和霞一起调查伤害优衣的人',
    '和佩可小姐一起吃午饭',
    '找小小甜心玩过家家',
    '帮碧寻找新朋友',
    '陪茜里一起练习',
    '和真步去真步王国',
    '找镜华补习数学',
    '陪胡桃排练话剧',
    '和初音一起午睡',
    '成为露娜的朋友',
    '帮铃莓打扫咲恋育幼院',
    '和静流姐姐一起做巧克力',
    '去伊丽莎白农场给小栞栞送书',
    '观看慈乐之音的演出',
    '来一发十连',
    '井一发当期的限定池',
    '给妈妈买一束康乃馨',
    '去竞技场背刺',
    '来氪一单',
    '努力工作，尽早报答妈妈的养育之恩',
    '成为魔法少女',
    '搓一把日麻'
]

class Prionne_Limiter():
    tz = pytz.timezone('Asia/Shanghai')

    def __init__(self):
        if not cdb.check('total'):               #检查总计数据是否存在
            cdb.write('total', cdb.cdb_init)     #创建总计数据
            cdb.write('total', datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[:-3], '时间')
            
        if cdb.read('total', '时间')[0:10] != datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[0:10]:
            #日期不是同一天（如维护的时候过0点了）
            cdb.copydata('昨日', '今日')
            cdb.formatdata(0, '今日')       #将今日数据清零
            cdb.write('total', datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[:-3], '时间')#更新时间
        pass
    
    def check(self, uid) -> bool:
        return bool(cdb.read(uid, '今日') == 0)
        
clm = Prionne_Limiter()


@sv.scheduled_job('cron', hour='0', minute='0')
async def signin_fresh_date():
    if not cdb.check('total'):               #检查总计数据是否存在
        cdb.write('total', cdb.cdb_init)         #创建总计数据
    cdb.copydata('昨日', '今日')
    cdb.formatdata(0, '今日')       #将今日数据清零
    cdb.write('total', datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[:-3], '时间')#更新时间


@sv.on_fullmatch(('妈', '妈?', '妈妈', '妈!', '妈！', '妈妈！'), only_to_me=True)
@sv.on_fullmatch(('签到', '盖章'))
async def signin_okodokai(bot, ev: CQEvent):
    uid = ev.user_id
    if not cdb.check('total'):               #检查总计数据是否存在
        cdb.write('total', cdb.cdb_init)         #创建总计数据
        cdb.write('total', datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[:-3], '时间')
    if not cdb.check(uid):                 #数据库里没有这个人
        cdb.write(uid, cdb.cdb_init)           #创建个人数据
    #已经签过了
    if not clm.check(uid):
        await bot.send(ev, '主さま今天已经签过到了，明天0点后再来签到吧~', at_sender=True)
        return
    #签到
    item = '今日'
    cdb.write('total', cdb.read('total', item) + 1, item)       #统计今日+1
    cdb.write(uid, cdb.read(uid, item) + 1, item)               #个人今日+1
    item = '累计'
    cdb.write('total', cdb.read('total', item) + 1, item)       #统计累计+1
    cdb.write(uid, cdb.read(uid, item) + 1, item)               #个人累计+1
    item = '时间'                                               #签到时间记录
    cdb.write(uid, datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[:-3], item)
    item = '连续'
    if cdb.read(uid, '昨日') == 0:                              #昨天断签了
        cdb.write(uid, 1, item)                                 #重新累加
    else:
        cdb.write(uid, cdb.read(uid, item) + 1, item)           #个人连续+1
    #首签
    firstsign_msg = ''
    if cdb.read('total', '今日') == 1:
        cdb.write('total', uid, '连续')
        cdb.write('total', cdb.read(uid, '时间'), '时间')
        cReport1 = f"恭喜您夺得今天的首签！\n"
        if cdb.read(uid, '昵称') == 'NIC_NULL0':
            cReport1 += "您今天可以使用[昵称设定 昵称]指令给自己起一个昵称！\n"
        else:
            cReport1 += "您今天可以使用[昵称设定 昵称]指令更改自己的昵称！\n"
        firstsign_add = random.randint(2000, 4500)
        firstsign_msg = f'今日首签赠礼：金币×{firstsign_add}\n'
        cdb.write(uid, cdb.read(uid, '金币') + firstsign_add, '金币')   #计入个人金币总数
    #非首签
    else:
        #首签的昵称
        if cdb.read(cdb.read('total', '连续'), '昵称') == 'NIC_NULL0':
            first_sign_nicname = cdb.read('total', '连续')
        else:
            first_sign_nicname = cdb.read(cdb.read('total', '连续'), '昵称')
        cReport1 = f"今天的首签由【{first_sign_nicname}】夺得。\n"
        #时间计算
        time_first_sign = datetime.strptime(cdb.read('total', '时间'), "%Y-%m-%d %H:%M:%S:%f")
        time_you_sign = datetime.strptime(cdb.read(uid, '时间'), "%Y-%m-%d %H:%M:%S:%f")
        time_delta_tsec = (time_you_sign-time_first_sign).seconds           #计算时间差（累计秒）
        time_delta_hour = int(time_delta_tsec / 3600)                       #小时部分
        time_delta_min = int(time_delta_tsec % 3600 / 60)                   #分钟部分
        time_delta_sec = int(time_delta_tsec % 3600 % 60)                   #秒部分
        time_delta_mis = int((time_you_sign-time_first_sign).microseconds/1000)  #毫秒部分
        #提示计时信息
        if time_delta_hour > 0: #超过一小时不提示计时信息
            cReport1 += f"您是今天第{cdb.read('total', '今日')}位签到的骑士君！\n"
        elif time_delta_min > 0:
            cReport1 += f"您比他慢了{time_delta_min}分{time_delta_sec}秒{time_delta_mis}毫秒！\n您是今天第{cdb.read('total', '今日')}位签到的骑士君！\n"
        elif time_delta_sec > 0:
            cReport1 += f"您比他慢了{time_delta_sec}秒{time_delta_mis}毫秒！\n您是今天第{cdb.read('total', '今日')}位签到的骑士君！\n"
        else:
            cReport1 += f"您比他慢了{time_delta_mis}毫秒！\n您是今天第{cdb.read('total', '今日')}位签到的骑士君！\n"
    #连续签到提示
    cReport2 = ""
    if cdb.read(uid, '连续') > 1:
        cReport2 = f"您已连续签到{cdb.read(uid, '连续')}次。\n"
    #金币计算
    earlier_add = int(2000 * (1/cdb.read('total', '今日')))       #签到顺序加成-反比例函数
    continu_add = log(cdb.read(uid, '连续'), 30)                  #连续签到加成-对数函数
    gold_coin = random.randint(earlier_add + int(1000 * continu_add), earlier_add + 500 + int(1500 * continu_add)) #获得金币
    cdb.write(uid, cdb.read(uid, '金币') + gold_coin, '金币')     #计入个人金币总数
    #初次签到
    if cdb.read(uid, '累计') == 1:
        firstsign_msg += '初次签到赠礼：金币×4500\n'
        cdb.write(uid, cdb.read(uid, '金币') + 4500, '金币')      #计入个人金币总数
    #随机事件
    todo = random.choice(todo_list)
    
    await bot.send(ev, f"\n欢迎回来，主さま\n{cReport1}{cReport2}{R.img('priconne/kokoro_stamp.png').cqcode}\n恭喜获得金币×{gold_coin}\n{firstsign_msg}您的金币总数为：{cdb.read(uid, '金币')}\n主さま今天要{todo}吗？", at_sender=True)


@sv.on_prefix('昵称设定')
async def set_nicname(bot, ev):
    uid = ev.user_id
    msg = ev.message.extract_plain_text()
    if cdb.read('total', '连续') == uid:  #是今天的首签
        if len(msg) < 2 or len(msg) > 20:
            await bot.send(ev, '昵称长度需要在2-20个字之间哦~', at_sender=True)
        else:
            cdb.write(uid, msg, '昵称')
            await bot.send(ev, f'已将您的昵称更改为【{msg}】', at_sender=True)
    else:
        await bot.send(ev, '只有夺得首签才可以修改昵称哦~', at_sender=True)


@sv.on_prefix('签到统计')
async def signin_report(bot, ev):
    if not priv.check_priv(ev, priv.SUPERUSER):
        return
    await bot.send(ev, f"签到统计数据：\n累计签到：{cdb.read('total', '累计')}次\n今日签到：{cdb.read('total', '今日')}人\n昨日签到：{cdb.read('total', '昨日')}人\n时间记录：{cdb.read('total', '时间')}")

@sv.on_prefix('签到查询')
async def signin_info(bot, ev):
    uid = ev.user_id
    if not cdb.check(uid):     #数据库里没有这个人
        await bot.send(ev, "未查询到您的签到信息！", at_sender=True)
        return
    if cdb.read(uid, '今日') == 0:
        todat_signin = '未'
    else:
        todat_signin = '已'
    if cdb.read(uid, '昨日') == 0:
        yesterdat_signin = '未'
    else:
        yesterdat_signin = '已'
    await bot.send(ev, f"\n您的签到信息如下：\n累计签到：{cdb.read(uid, '累计')}次\n连续签到：{cdb.read(uid, '连续')}次\n今日{todat_signin}签到，昨日{yesterdat_signin}签到\n金币总数：{cdb.read(uid, '金币')}\n最新签到时间：{cdb.read(uid, '时间')}", at_sender=True)
    

@sv.on_prefix('金币充值')
@sv.on_prefix('充值金币')
async def kakin(bot, ev: CQEvent):
    recharge = ev.message.extract_plain_text().strip()  #取出金币参数
    if len(recharge) == 0:
        return
    elif int(recharge) == 0:
        return
    else:
        recharge = int(recharge)
    
    if priv.check_priv(ev, priv.SUPERUSER):
    #超级管理员
        count = 0
        for m in ev.message:
            if m.type == 'at' and m.data['qq'] != 'all':
                uid = int(m.data['qq'])
                cdb.write(uid, cdb.read(uid, '金币') + recharge, '金币')
                count += 1
        if count:   #为别人充值
            await bot.send(ev, f"已为{count}位骑士君充值{recharge}金币！")





