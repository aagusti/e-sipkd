import os
import re
import base64
from sqlalchemy import (
    Table,
    MetaData,
    )
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.sql.expression import text
from ..models import (
    Base,
    BaseModel,
    CommonModel,
    DBSession,
    User,
    )
from tools import get_fullpath


SQL_TABLE = """
SELECT c.oid, n.nspname, c.relname
  FROM pg_catalog.pg_class c
  LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relname = :table_name
    AND pg_catalog.pg_table_is_visible(c.oid)
  ORDER BY 2, 3
"""

SQL_TABLE_SCHEMA = """
SELECT c.oid, n.nspname, c.relname
  FROM pg_catalog.pg_class c
  LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relname = :table_name
    AND n.nspname = :schema
  ORDER BY 2, 3
"""

SQL_FIELDS = """
SELECT a.attname,
  pg_catalog.format_type(a.atttypid, a.atttypmod),
  (SELECT substring(pg_catalog.pg_get_expr(d.adbin, d.adrelid) for 128)
     FROM pg_catalog.pg_attrdef d
     WHERE d.adrelid = a.attrelid
       AND d.adnum = a.attnum
       AND a.atthasdef) AS substring,
  a.attnotnull, a.attnum,
  (SELECT c.collname
     FROM pg_catalog.pg_collation c, pg_catalog.pg_type t
     WHERE c.oid = a.attcollation
       AND t.oid = a.atttypid
       AND a.attcollation <> t.typcollation) AS attcollation,
  NULL AS indexdef,
  NULL AS attfdwoptions
  FROM pg_catalog.pg_attribute a
  WHERE a.attrelid = :table_id AND a.attnum > 0 AND NOT a.attisdropped
  ORDER BY a.attnum"""

def table_seq(table):
    engine = DBSession.bind
    if table.schema:
        sql = text(SQL_TABLE_SCHEMA)
        q = engine.execute(sql, schema=table.schema, table_name=table.name)
    else:
        sql = text(SQL_TABLE)
        q = engine.execute(sql, table_name=table.name)    
    r = q.fetchone()
    table_id = r.oid
    sql = text(SQL_FIELDS)
    q = engine.execute(sql, table_id=table_id)
    regex = re.compile("nextval\('(.*)'\:")
    for r in q.fetchall():
        if not r.substring:
            continue
        if r.substring.find('nextval') == -1:
            continue
        match = regex.search(r.substring)
        return match.group(1)

def set_sequence(orm):
    seq_name = table_seq(orm.__table__)
    if not seq_name:
        return
    row = DBSession.query(orm).order_by('id DESC').first()
    last_id = row and row.id or 1
    sql = "SELECT setval('%s', %d)" % (seq_name, last_id)
    engine = DBSession.bind
    engine.execute(sql)
    
def split_tablename(tablename):
    t = tablename.split('.')
    if t[1:]:
        schema = t[0]
        tablename = t[1]
    else:
        schema = None
    return schema, tablename    
        
def get_pkeys(table):
    r = []
    for c in table.constraints:
        if c.__class__ is PrimaryKeyConstraint:
            for col in c:
                r.append(col.name)
            return r
    return r

def execute(engine, sql_file):
    sql_file_ = get_fullpath(sql_file)
    f = open(sql_file_)
    sql = f.read()
    f.close()
    engine.execute(sql)
