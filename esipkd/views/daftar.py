from email.utils import parseaddr
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )

from ..models import DBSession,User

from ..models.isipkd import(
      Wilayah, Jabatan, Unit, Rekening, SubjekPajak, Pajak
      )
      
def email_validator(node, value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        raise colander.Invalid(node, 'Invalid email format')

      
STATUS = (
    (1, 'Aktif'),
    (0, 'Inaktif'),
    )    
@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
SUMMARIES = (
    (1, 'Header'),
    (0, 'Detail'),
    )   
    
@colander.deferred
def deferred_summary(node, kw):
    values = kw.get('daftar_summary', [])
    return widget.SelectWidget(values=values)

def daftar_wilayah():
    rows = DBSession.query(Wilayah.id, Wilayah.nama).all()
    r=[]
    d = (0,'Pilih Wilayah')
    r.append(d)
    for row in rows:
        d = (row.id, row.nama)
        r.append(d)
    return r
    
@colander.deferred
def deferred_wilayah(node, kw):
    values = kw.get('daftar_wilayah',[])
    return widget.SelectWidget(values=values)

def daftar_jabatan():
    rows = DBSession.query(Jabatan.id, Jabatan.nama).all()
    r=[]
    d = (0,'Pilih Jabatan')
    r.append(d)
    for row in rows:
        d = (row.id, row.nama)
        r.append(d)
    return r
    
@colander.deferred
def deferred_jabatan(node, kw):
    values = kw.get('daftar_jabatan',[])
    return widget.SelectWidget(values=values)

def daftar_unit():
    rows = DBSession.query(Unit).filter_by(level_id=3).all()
    r=[]
    d = (0,'Pilih SKPD')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+':'+row.nama)
        r.append(d)
    return r
    
@colander.deferred
def deferred_unit(node, kw):
    values = kw.get('daftar_unit',[])
    return widget.SelectWidget(values=values)

def daftar_rekening():
    rows = DBSession.query(Rekening).filter_by(is_summary=0).all()
    r=[]
    d = (0,'Pilih REKENING')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+':'+row.nama)
        r.append(d)
    return r
    
@colander.deferred
def deferred_rekening(node, kw):
    values = kw.get('daftar_rekening',[])
    return widget.SelectWidget(values=values)


def daftar_user():
    rows = DBSession.query(User).all()
    r=[]
    d = (0,'Pilih USER')
    r.append(d)
    for row in rows:
        d = (row.id, row.email+':'+row.user_name)
        r.append(d)
    return r
    
@colander.deferred
def deferred_user(node, kw):
    values = kw.get('daftar_user',[])
    return widget.SelectWidget(values=values)

def daftar_pajak():
    rows = DBSession.query(Pajak).all()
    r=[]
    d = (0,'Pilih PAJAK')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+':'+row.nama)
        r.append(d)
    return r
    
@colander.deferred
def deferred_pajak(node, kw):
    values = kw.get('daftar_pajak',[])
    return widget.SelectWidget(values=values)

    
def daftar_subjekpajak():
    rows = DBSession.query(SubjekPajak).all()
    r=[]
    d = (0,'Pilih SP')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+':'+row.nama)
        r.append(d)
    return r
    
@colander.deferred
def deferred_subjekpajak(node, kw):
    values = kw.get('daftar_subjekpajak',[])
    return widget.SelectWidget(values=values)
                        