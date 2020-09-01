#encoding=utf-8
import os
import shelve

#数据库操作
class Commic_DB():
    cdb_init = {'累计': 0, '连续': 0, '昨日': 0, '今日': 0, '金币': 0, '积分': 0, '昵称': 'NIC_NULL0', '时间': 'NULL'}

    def __init__(self, dbfile):
        filepath = os.path.dirname(dbfile)  #文件目录
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        
        self.dbfile = dbfile
        pass
    
    def check(self, uid):#检查是否有这个uid
        uid = str(uid)
        d = shelve.open(self.dbfile)
        if uid in d:
            d.close()
            return True
        else:
            d.close()
            return False
    
    def read(self, uid, item=None):#读取数据
        uid = str(uid)
        if not self.check(uid): #不存在该uid
            if item is None:
                cStr = self.cdb_init
            else:
                cStr = self.cdb_init[item]
            return cStr
        else:                   #存在该uid
            d = shelve.open(self.dbfile)
            if item is None:
                cStr = d[uid]
            else:
                cStr = d[uid][item]
            d.close()
            return cStr

    def write(self, uid, data, item=None):#写入数据
        uid = str(uid)
        d = shelve.open(self.dbfile, writeback=True)
        if item is None:
            d[uid] = data
        else:
            d[uid][item] = data
        d.close()
        pass

    def delet(self, uid, item=None):#删除指定数据
        uid = str(uid)
        if self.check(uid): #存在该uid
            d = shelve.open(self.dbfile, writeback=True)
            if item is None:
                del d[uid]
            else:
                if item in d[uid]:
                    del d[uid][item]
            d.close()
            pass

    def listall(self):#列出全部数据
        d = shelve.open(self.dbfile)
        cStr = ''
        for i in d:
            cStr += '\n' + i + ': ' + str(d[i])
            pass
        d.close()
        return cStr

    def deletall(self):#删除全部数据
        d = shelve.open(self.dbfile, writeback=True)
        for i in d:
            del d[i]
        d.close()
        pass
    
    def copydata(self, item1, item2, uid=None):#项目间复制数据item1<-item2
        d = shelve.open(self.dbfile, writeback=True)
        if uid is None:
            for i in d:
                d[i][item1] = d[i][item2]
        else:
            if self.check(uid): #存在该uid
                uid = str(uid)
                d[uid][item1] = d[uid][item2]
        d.close()
        pass
    
    def formatdata(self, data, item):#格式化一项数据
        d = shelve.open(self.dbfile, writeback=True)
        for i in d:
            d[i][item] = data
        d.close()
        pass





