import informixdb
from ..tools import get_settings

class EngInformix(object):
    def __init__(self):
        self.conn = None
        self.database = None
        self.user = None
        self.password = None
        settings = get_settings()
        url = settings['otherdb.url']
        self.dbtype, url = url.split('://')
        user_pass, url = url.split('@')
        self.user, self.password = user_pass.split(':')
        self.server, self.database = url.split('/')
    def connect(self):
       
        self.conn = informixdb.connect(self.database, user=self.user, password=self.password)
        return self.conn
    
    def execute(self, sql):
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor(rowformat=informixdb.ROW_AS_OBJECT)
        cursor.execute(sql)
        self.conn.commit()
        return 
        
    def fetchone(self, sql):
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor(rowformat=informixdb.ROW_AS_OBJECT)
        cursor.execute(sql)
        row = cursor.fetchone()
        return row
    def query_obj(self, sql):
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor(rowformat=informixdb.ROW_AS_OBJECT)
        cursor.execute(sql)
        return cursor.fetchall()
        
    def query_dict(sql):
        if not self.conn:
            self.connect()
        cursor = self.conn.cursor(rowformat=informixdb.ROW_AS_DICT)
        cursor.execute(sql)
        return cursor.fetchall()
    