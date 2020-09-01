import os
import random
from collections import defaultdict

from hoshino import Service, priv, util
from hoshino.typing import *
from hoshino.util import DailyNumberLimiter, concat_pic, pic2b64
from hoshino.modules.priconne.memberdata import Commic_DB

from .. import chara
from .gacha import Gacha

try:
    import ujson as json
except:
    import json

_j_limit = 93300    #每日钻石上限
_r_limit = 1        #白嫖次数上限
_rf_limit = 3       #日偷钻人数上限

gacha_jewel_data = os.path.abspath('hoshino/modules/priconne/data/gacha_jewel_data.json')
gacha_rst_data   = os.path.abspath('hoshino/modules/priconne/data/gacha_rst_data.json')
gacha_rstf_data  = os.path.abspath('hoshino/modules/priconne/data/gacha_rstf_data.json')

jewel_limit = DailyNumberLimiter(_j_limit, gacha_jewel_data)
rst_limit = DailyNumberLimiter(_r_limit, gacha_rst_data)
rstf_limit = DailyNumberLimiter(_rf_limit, gacha_rstf_data)

dbfile = os.path.abspath('hoshino/modules/priconne/data/signindata')
cdb = Commic_DB(dbfile)

sv_help = f'''
模拟扭蛋
[@bot来发十连] 扭蛋单抽模拟
[@bot来发单抽] 扭蛋十连模拟
[@bot来一井] 4w5钻！
[帮助抽卡] 获取详细使用说明
'''.strip()

sv_help_detail = f'''
※扭蛋模拟器※
每人每天默认可用{_j_limit}钻石，凌晨5点重置钻石数量
[@bot来发十连] 扭蛋单抽模拟
[@bot来发单抽] 扭蛋十连模拟
[@bot来一井] 4w5钻！
[查看卡池] 查看卡池up&出率
[切换卡池] 切换模拟卡池
[氪金 金币数量] 为自己充值钻石（1金币=10钻石，不填写数量默认4500金币，『无需』at自己）【每日可白嫖{_r_limit}次】
[氪金 金币数量@xxx] 『群管理员』为指定群员充值钻石，可@多人【『不可』at自己】
[偷钻@xxx] 偷取指定群员的钻石，可@多人【每日可对{_rf_limit}人使用】
'''

sv = Service('gacha', help_=sv_help, bundle='pcr娱乐')

POOL = ('MIX', 'JP', 'TW', 'BL')
DEFAULT_POOL = POOL[0]

_pool_config_file = os.path.expanduser('~/.hoshino/group_pool_config.json')
_group_pool = {}
try:
    with open(_pool_config_file, encoding='utf8') as f:
        _group_pool = json.load(f)
except FileNotFoundError as e:
    sv.logger.warning('group_pool_config.json not found, will create when needed.')
_group_pool = defaultdict(lambda: DEFAULT_POOL, _group_pool)


@sv.on_fullmatch(('帮助抽卡', '帮助 抽卡', '抽卡帮助', '帮助gacha'))
async def gacha_help(bot, ev):
    await bot.send(ev, sv_help_detail, at_sender=True)


def dump_pool_config():
    with open(_pool_config_file, 'w', encoding='utf8') as f:
        json.dump(_group_pool, f, ensure_ascii=False)


gacha_10_aliases = ('抽十连', '十连', '十连！', '十连抽', '来个十连', '来发十连', '来次十连', '抽个十连', '抽发十连', '抽次十连', '十连扭蛋', '扭蛋十连',
                    '10连', '10连！', '10连抽', '来个10连', '来发10连', '来次10连', '抽个10连', '抽发10连', '抽次10连', '10连扭蛋', '扭蛋10连',
                    '十連', '十連！', '十連抽', '來個十連', '來發十連', '來次十連', '抽個十連', '抽發十連', '抽次十連', '十連轉蛋', '轉蛋十連',
                    '10連', '10連！', '10連抽', '來個10連', '來發10連', '來次10連', '抽個10連', '抽發10連', '抽次10連', '10連轉蛋', '轉蛋10連')
gacha_1_aliases = ('单抽', '单抽！', '来发单抽', '来个单抽', '来次单抽', '扭蛋单抽', '单抽扭蛋',
                   '單抽', '單抽！', '來發單抽', '來個單抽', '來次單抽', '轉蛋單抽', '單抽轉蛋')
gacha_300_aliases = ('抽一井', '来一井', '来发井', '抽发井', '天井扭蛋', '扭蛋天井', '天井轉蛋', '轉蛋天井')

@sv.on_fullmatch(('卡池资讯', '查看卡池', '看看卡池', '康康卡池', '卡池資訊', '看看up', '看看UP'))
async def gacha_info(bot, ev: CQEvent):
    gid = str(ev.group_id)
    gacha = Gacha(_group_pool[gid])
    up_chara = gacha.up
    up_chara = map(lambda x: str(chara.fromname(x, star=3).icon.cqcode) + x, up_chara)
    up_chara = '\n'.join(up_chara)
    await bot.send(ev, f"本期卡池主打的角色：\n{up_chara}\nUP角色合计={(gacha.up_prob/10):.1f}%\n3★出率={(gacha.s3_prob)/10:.1f}%")


POOL_NAME_TIP = '请选择以下卡池\n> 切换卡池jp\n> 切换卡池tw\n> 切换卡池b\n> 切换卡池mix'
@sv.on_prefix(('切换卡池', '选择卡池', '切換卡池', '選擇卡池'))
async def set_pool(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '只有群管理才能切换卡池', at_sender=True)
    name = util.normalize_str(ev.message.extract_plain_text())
    if not name:
        await bot.finish(ev, POOL_NAME_TIP, at_sender=True)
    elif name in ('国', '国服', 'cn'):
        await bot.finish(ev, '请选择以下卡池\n> 选择卡池 b服\n> 选择卡池 台服')
    elif name in ('b', 'b服', 'bl', 'bilibili'):
        name = 'BL'
    elif name in ('台', '台服', 'tw', 'sonet'):
        name = 'TW'
    elif name in ('日', '日服', 'jp', 'cy', 'cygames'):
        name = 'JP'
    elif name in ('混', '混合', 'mix'):
        name = 'MIX'
    else:
        await bot.finish(ev, f'未知服务器地区 {POOL_NAME_TIP}', at_sender=True)
    gid = str(ev.group_id)
    _group_pool[gid] = name
    dump_pool_config()
    await bot.send(ev, f'卡池已切换为{name}池', at_sender=True)
    await gacha_info(bot, ev)


JEWEL_EXCEED_NOTICE1 = '您今天的钻石已经用完啦，欢迎明早5点后再来！\n（也可使用[氪金]指令兑换钻石，或者[偷钻]←_←）'
JEWEL_EXCEED_NOTICE2 = '要不抽个便宜点的？或者明早5点后再来吧！\n（也可使用[氪金]指令兑换钻石，或者[偷钻]←_←）'
async def check_jewel_num(bot, ev: CQEvent, num):
    #没钻了
    if not jewel_limit.check(ev.user_id):
        await bot.finish(ev, JEWEL_EXCEED_NOTICE1, at_sender=True)
    #还有钻
    else:
        remain = jewel_limit.get_num(ev.user_id)
        #钻不够
        if remain < num:
            await bot.finish(ev, f"您今天只剩{remain}钻石啦，{JEWEL_EXCEED_NOTICE2}", at_sender=True)


@sv.on_prefix(gacha_1_aliases, only_to_me=True)
async def gacha_1(bot, ev: CQEvent):

    await check_jewel_num(bot, ev, 150)
    jewel_limit.increase(ev.user_id, 150)

    gid = str(ev.group_id)
    gacha = Gacha(_group_pool[gid])
    chara, hiishi = gacha.gacha_one(gacha.up_prob, gacha.s3_prob, gacha.s2_prob)
    #silence_time = hiishi * 60

    res = f'{chara.icon.cqcode} {chara.name} {"★"*chara.star}'
    
    await bot.send(ev, f'本次抽卡消耗150钻石，您今天还剩{jewel_limit.get_num(ev.user_id)}钻石！', at_sender=True)
    await bot.send(ev, f'素敵な仲間が増えますよ！\n{res}', at_sender=True)


@sv.on_prefix(gacha_10_aliases, only_to_me=True)
async def gacha_10(bot, ev: CQEvent):
    SUPER_LUCKY_LINE = 170

    await check_jewel_num(bot, ev, 1500)
    jewel_limit.increase(ev.user_id, 1500)

    gid = str(ev.group_id)
    gacha = Gacha(_group_pool[gid])
    result, hiishi = gacha.gacha_ten()
    #silence_time = hiishi * 6 if hiishi < SUPER_LUCKY_LINE else hiishi * 60

    res1 = chara.gen_team_pic(result[:5], star_slot_verbose=False)
    res2 = chara.gen_team_pic(result[5:], star_slot_verbose=False)
    res = concat_pic([res1, res2])
    res = pic2b64(res)
    res = MessageSegment.image(res)
    result = [f'{c.name}{"★"*c.star}' for c in result]
    res1 = ' '.join(result[0:5])
    res2 = ' '.join(result[5:])
    res = f'{res}\n{res1}\n{res2}'
    # 纯文字版
    # result = [f'{c.name}{"★"*c.star}' for c in result]
    # res1 = ' '.join(result[0:5])
    # res2 = ' '.join(result[5:])
    # res = f'{res1}\n{res2}'

    await bot.send(ev, f'本次抽卡消耗1500钻石，您今天还剩{jewel_limit.get_num(ev.user_id)}钻石！', at_sender=True)
    if hiishi >= SUPER_LUCKY_LINE:
        await bot.send(ev, '恭喜海豹！おめでとうございます！')
    await bot.send(ev, f'素敵な仲間が増えますよ！\n{res}\n', at_sender=True)


@sv.on_prefix(gacha_300_aliases, only_to_me=True)
async def gacha_300(bot, ev: CQEvent):
    
    await check_jewel_num(bot, ev, 45000)
    jewel_limit.increase(ev.user_id, 45000)

    gid = str(ev.group_id)
    gacha = Gacha(_group_pool[gid])
    result = gacha.gacha_tenjou()
    up = len(result['up'])
    s3 = len(result['s3'])
    s2 = len(result['s2'])
    s1 = len(result['s1'])

    res = [*(result['up']), *(result['s3'])]
    random.shuffle(res)
    lenth = len(res)
    if lenth <= 0:
        res = "竟...竟然没有3★？！"
    else:
        step = 4
        pics = []
        for i in range(0, lenth, step):
            j = min(lenth, i + step)
            pics.append(chara.gen_team_pic(res[i:j], star_slot_verbose=False))
        res = concat_pic(pics)
        res = pic2b64(res)
        res = MessageSegment.image(res)

    msg = [
        f"\n素敵な仲間が増えますよ！ {res}",
        f"★★★×{up+s3} ★★×{s2} ★×{s1}",
        f"获得记忆碎片×{100*up}与女神秘石×{50*(up+s3) + 10*s2 + s1}！\n第{result['first_up_pos']}抽首次获得up角色" if up else f"获得女神秘石{50*(up+s3) + 10*s2 + s1}个！"
    ]

    if up == 0 and s3 == 0:
        msg.append("太惨了，咱们还是退款删游吧...")
    elif up == 0 and s3 > 7:
        msg.append("up呢？我的up呢？")
    elif up == 0 and s3 <= 3:
        msg.append("这位酋长，梦幻包考虑一下？")
    elif up == 0:
        msg.append("据说天井的概率只有12.16%")
    elif up <= 2:
        if result['first_up_pos'] < 50:
            msg.append("你的喜悦我收到了，滚去喂鲨鱼吧！")
        elif result['first_up_pos'] < 100:
            msg.append("已经可以了，您已经很欧了")
        elif result['first_up_pos'] > 290:
            msg.append("标 准 结 局")
        elif result['first_up_pos'] > 250:
            msg.append("补井还是不补井，这是一个问题...")
        else:
            msg.append("期望之内，亚洲水平")
    elif up == 3:
        msg.append("抽井母五一气呵成！多出30等专武～")
    elif up >= 4:
        msg.append("记忆碎片一大堆！您是托吧？")

    await bot.send(ev, f'本次抽卡消耗45000钻石，您今天还剩{jewel_limit.get_num(ev.user_id)}钻石！', at_sender=True)
    await bot.send(ev, '\n'.join(msg), at_sender=True)
    #silence_time = (100*up + 50*(up+s3) + 10*s2 + s1) * 1


@sv.on_prefix('氪金')
async def kakin(bot, ev: CQEvent):
    recharge = ev.message.extract_plain_text().strip()  #取出金币参数
    if len(recharge) == 0:
        recharge = 4500 #默认充值4500金币，即45000钻石
    elif int(recharge) == 0:
        await bot.send(ev, "？\n小伙子，我觉得你有问题")
        return
    else:
        recharge = int(recharge)
    
#    if ev.user_id not in bot.config.SUPERUSERS:
    if not priv.check_priv(ev, priv.ADMIN):
    #群成员
        uid = ev['user_id']
        #白嫖次数没有了
        if not rst_limit.check(uid):
            if cdb.read(uid, '金币') < recharge:
                await bot.send(ev, "您的金币不够啦～您可以通过[签到]获得金币，优先签到和连续签到都会带来额外金币收益哦！", at_sender=True)
            else:
                cdb.write(uid, cdb.read(uid, '金币') - recharge, '金币')
                jewel_limit.set_num(uid, jewel_limit.get_num(uid) + (recharge*10))
                await bot.send(ev, f"花凛桑已为这位骑士君充值完毕！这是您的小票：\n本次花费：{recharge}金币\n金币余额：{cdb.read(uid, '金币')}金币\n本次充值：{recharge*10}钻石\n钻石余额：{jewel_limit.get_num(uid)}钻石\n谢谢惠顾～", at_sender=True)
            return
        #还可以白嫖
        if recharge > 4500: #白嫖数额过多
            await bot.send(ev, f"数额太大啦！每日白嫖数额最大为4500金币！", at_sender=True)
        else:
            rst_limit.increase(uid)
            jewel_limit.set_num(uid, jewel_limit.get_num(uid) + (recharge*10))
            await bot.send(ev, f"花凛桑已为这位骑士君充值完毕！这是您的小票：\n本次花费：0金币\n金币余额：{cdb.read(uid, '金币')}金币\n本次充值：{recharge*10}钻石\n钻石余额：{jewel_limit.get_num(uid)}钻石\n本次免单哦，谢谢惠顾～", at_sender=True)
            return
    
    #管理员
    count = 0
    uid = ev['user_id']
        #at了自己
    for m in ev.message:
        if m.type == 'at' and int(m.data['qq']) == uid:
            await bot.send(ev, f"不可以at自己哦~如果想为自己充值请使用[氪金 金币数量]吧！（每日可白嫖{_r_limit}次，不填写数量默认4500金币）", at_sender=True)
            return
        #正常使用
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            jewel_limit.set_num(uid, jewel_limit.get_num(uid) + (recharge*10))
            count += 1
        #为别人充值
    if count:
        await bot.send(ev, f"花凛桑已为{count}位骑士君充值{recharge*10}钻石！本次免单哦，谢谢惠顾～")
        #为自己充值
    else:
        uid = ev['user_id']
            #白嫖次数没有了
        if not rst_limit.check(uid):
            if cdb.read(uid, '金币') < recharge:
                await bot.send(ev, "您的金币不够啦～您可以通过[签到]获得金币，优先签到和连续签到都会带来额外金币收益哦！", at_sender=True)
            else:
                cdb.write(uid, cdb.read(uid, '金币') - recharge, '金币')
                jewel_limit.set_num(uid, jewel_limit.get_num(uid) + (recharge*10))
                await bot.send(ev, f"花凛桑已为这位骑士君充值完毕！这是您的小票：\n本次花费：{recharge}金币\n金币余额：{cdb.read(uid, '金币')}金币\n本次充值：{recharge*10}钻石\n钻石余额：{jewel_limit.get_num(uid)}钻石\n谢谢惠顾～", at_sender=True)
            return
            #还可以白嫖
        if recharge > 4500: #白嫖数额过多
            await bot.send(ev, f"数额太大啦！每日白嫖数额最大为4500金币！", at_sender=True)
        else:
            rst_limit.increase(uid)
            jewel_limit.set_num(uid, jewel_limit.get_num(uid) + (recharge*10))
            await bot.send(ev, f"花凛桑已为这位骑士君充值完毕！这是您的小票：\n本次花费：0金币\n金币余额：{cdb.read(uid, '金币')}金币\n本次充值：{recharge*10}钻石\n钻石余额：{jewel_limit.get_num(uid)}钻石\n本次免单哦，谢谢惠顾～", at_sender=True)
            return
        



@sv.on_prefix('偷钻')
async def gacha_lmt_max(bot, ev: CQEvent):
#    if not priv.check_priv(ev, priv.ADMIN):
#        await bot.send(ev, f"权限不足！", at_sender=True)
#        return
    uid = ev['user_id']
    if not rstf_limit.check(uid):         #偷钻次数没有了
        await bot.send(ev, f"您已经偷了{_rf_limit}个骑士君的钻啦，偷不动啦，明天5点后再来吧！", at_sender=True)
        return
    
    #偷钻
        #at人数检查
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            count += 1
            #at人数大于剩余偷钻次数
    if count > rstf_limit.get_num(uid):
        await bot.send(ev, f"您at的人数太多啦！\n您今天的偷钻机会还剩：{rstf_limit.get_num(uid)}人")
        return
            #at人数大于3
#    elif count > 3:
#        await bot.send(ev, "您太贪心啦！一次最多只能对三个人使用哦~")
#        return
        #偷钻
    count = 0
    steal_sum = 0
    steal_msg = ''
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            steal = 0
            uid = int(m.data['qq'])
#            jewel_limit.check(uid)      #刷新钻石数量
            if random.random() < 0.80:  #成功概率80%
                steal = jewel_limit.get_num(uid)
                steal = random.randint(int(steal/3), steal)    #偷钻随机数 
            steal_sum += steal
            nicname = cdb.read(uid, '昵称')
            if nicname == 'NIC_NULL0':  #没有起昵称
                nicname = str(uid)
            steal_msg += f'▶从【{nicname}】偷取{steal}钻石\n'
            jewel_limit.increase(uid, steal)        #钻石减少
            count += 1
    if count:
        uid = ev['user_id']
        jewel_limit.set_num(uid, jewel_limit.get_num(uid) + steal_sum)  #给自己加钻石
        rstf_limit.increase(uid, count)    #偷钻剩余次数减少
        await bot.send(ev, f"有{count}位骑士君的钻出事了！\n“战果”汇报：\n{steal_msg}\n本次共偷得：{steal_sum}钻石\n您现在拥有：{jewel_limit.get_num(uid)}钻石")
    
    
    
    
    

