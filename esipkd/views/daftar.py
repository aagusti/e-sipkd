from email.utils import parseaddr
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )

from ..models import DBSession,User, Group, Route
from ..models.isipkd import Param
from ..models.isipkd import(
      Wilayah, Jabatan, Unit, Rekening, SubjekPajak, Pajak, ObjekPajak
      )

#############################    
## Untuk perhitungan bunga ##
#############################      
def hitung_bunga(pokok, jatuh_tempo):
    row = DBSession.query(Param.denda).first()
    if row:
        persen_denda = row.denda
    else:
        return 0
    kini = date.today()
    denda = bln_tunggakan = 0
    jatuh_tempo = jatuh_tempo
    x = (kini.year - jatuh_tempo.year) * 12
    y = kini.month - jatuh_tempo.month
    bln_tunggakan = x + y + 1
    if kini.day <= jatuh_tempo.day:
        bln_tunggakan -= 1
    if bln_tunggakan < 1:
        bln_tunggakan = 0
    if bln_tunggakan > 24:
        bln_tunggakan = 24
    denda = bln_tunggakan * persen_denda / 100 * pokok
    return denda

###################################    
## Untuk validasi struktur email ##
###################################    
def email_validator(node, value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        raise colander.Invalid(node, 'Invalid email format')
    
############################    
## Untuk pemilihan Status ##
############################
@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (1, 'Aktif'),
    (0, 'Inaktif'),
    )     
 
#############################    
## Untuk pemilihan Summary ##
############################# 
@colander.deferred
def deferred_summary(node, kw):
    values = kw.get('daftar_summary', [])
    return widget.SelectWidget(values=values)

SUMMARIES = (
    (1, 'Header'),
    (0, 'Detail'),
    )  
    
#############################    
## Untuk pemilihan Wilayah ##
#############################
@colander.deferred
def deferred_wilayah(node, kw):
    values = kw.get('daftar_wilayah',[])
    return widget.SelectWidget(values=values)

def daftar_wilayah():
    rows = DBSession.query(Wilayah.id, 
                           Wilayah.kode, 
                           Wilayah.nama
                   ).filter_by(level_id=2
                   ).all()
    r=[]
    d = (0,'Pilih Wilayah')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+' : '+row.nama)
        r.append(d)
    return r

###############################    
## Untuk pemilihan Wilayah 1 ##
###############################	
@colander.deferred
def deferred_wilayah1(node, kw):
    values = kw.get('daftar_wilayah1',[])
    return widget.SelectWidget(values=values)

def daftar_wilayah1():
    rows = DBSession.query(Wilayah.id, 
                           Wilayah.kode, 
                           Wilayah.nama
                   ).filter_by(level_id=1
                   ).all()
    r=[]
    d = (0,'Pilih Wilayah')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+' : '+row.nama)
        r.append(d)
    return r

#############################    
## Untuk pemilihan Jabatan ##
#############################
@colander.deferred
def deferred_jabatan(node, kw):
    values = kw.get('daftar_jabatan',[])
    return widget.SelectWidget(values=values)

def daftar_jabatan():
    rows = DBSession.query(Jabatan.id, 
                           Jabatan.nama
                   ).filter(Jabatan.status==1
                   ).all()
    r=[]
    d = (0,'Pilih Jabatan')
    r.append(d)
    for row in rows:
        d = (row.id, row.nama)
        r.append(d)
    return r
    
####################################    
## Untuk pemilihan Unit Kerja/OPD ##
####################################    
@colander.deferred
def deferred_unit(node, kw):
    values = kw.get('daftar_unit',[])
    return widget.SelectWidget(values=values)

def daftar_unit():
    #rows = DBSession.query(Unit).filter_by(level_id=4).all()
    rows = DBSession.query(Unit
                   ).filter(Unit.level_id.in_([3,4])
                   ).all()
    r=[]
    d = (0,'Pilih OPD')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+' : '+row.nama)
        r.append(d)
    return r
    
##############################    
## Untuk pemilihan Rekening ##
##############################
@colander.deferred
def deferred_rekening(node, kw):
    values = kw.get('daftar_rekening',[])
    return widget.SelectWidget(values=values)

def daftar_rekening():
    rows = DBSession.query(Rekening
                   ).filter_by(is_summary=0
                   ).all()
    r=[]
    d = (0,'Pilih Rekening')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+' : '+row.nama)
        r.append(d)
    return r
    
@colander.deferred
def deferred_rekening1(node, kw):
    values = kw.get('daftar_rekening1',[])
    return widget.SelectWidget(values=values)

def daftar_rekening1():
    #rows = DBSession.query(Rekening).filter_by(is_summary=0).all()
    rows = DBSession.query(Rekening
                   ).filter(Rekening.level_id.in_([5,6,7,8,9])
                   ).all()
    r=[]
    d = (0,'Pilih Rekening')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+' : '+row.nama)
        r.append(d)
    return r

###########################    
## Untuk pemilihan Pajak ##
###########################
@colander.deferred
def deferred_pajak(node, kw):
    values = kw.get('daftar_pajak',[])
    return widget.SelectWidget(values=values)
    
def daftar_pajak():
    rows = DBSession.query(Pajak
                   ).filter(Pajak.status==1
                   ).all()
    r=[]
    d = (0,'Pilih Rekening')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+' : '+row.nama)
        r.append(d)
    return r
    
############################    
## Untuk pemilihan Subjek ##
############################
@colander.deferred
def deferred_subjekpajak(node, kw):
    values = kw.get('daftar_subjekpajak',[])
    return widget.SelectWidget(values=values)
    
def daftar_subjekpajak():
    rows = DBSession.query(SubjekPajak
                   ).filter(SubjekPajak.status==1
                   ).all()
    r=[]
    d = (0,'Pilih Penyetor')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+' : '+row.nama)
        r.append(d)
    return r

###########################
## Untuk pemilihan Objek ##
###########################   
@colander.deferred
def deferred_objekpajak(node, kw):
    values = kw.get('daftar_objekpajak',[])
    return widget.SelectWidget(values=values)

def daftar_objekpajak():
    rows = DBSession.query(ObjekPajak
                   ).filter(ObjekPajak.status==1
                   ).all()
    r=[]
    d = (0,'Pilih Objek')
    r.append(d)
    for row in rows:
        d = (row.id, row.kode+' : '+row.nama)
        r.append(d)
    return r

##########################    
## Untuk pemilihan User ##
##########################      
@colander.deferred
def deferred_user(node, kw):
    values = kw.get('daftar_user',[])
    return widget.SelectWidget(values=values)
                            
def daftar_user():
    rows = DBSession.query(User
                   ).all()
    r=[]
    d = (0,'Pilih User')
    r.append(d)
    for row in rows:
        d = (row.id, row.user_name+' : '+row.email)
        r.append(d)
    return r
  
###########################    
## Untuk pemilihan Group ##
###########################      
@colander.deferred
def deferred_group(node, kw):
    values = kw.get('daftar_group',[])
    return widget.SelectWidget(values=values)
                            
def daftar_group():
    rows = DBSession.query(Group
                   ).all()
    r=[]
    d = (0,'Pilih Group')
    r.append(d)
    for row in rows:
        d = (row.id, row.group_name)
        r.append(d)
    return r
    
###########################
## Untuk pemilihan Route ##
###########################       
@colander.deferred
def deferred_route(node, kw):
    values = kw.get('daftar_route',[])
    return widget.SelectWidget(values=values)
                            
def daftar_route():
    rows = DBSession.query(Route
                   ).order_by(Route.kode
                   ).all()
    r=[]
    d = (0,'Pilih Route')
    r.append(d)
    for row in rows:
        d = (row.id, row.nama)
        r.append(d)
    return r

######################################    
## Kumpulan Headofkode & Headofname ##
######################################   
auto_unit_nm_sptpd = widget.AutocompleteInputWidget(
        size=60,
        values = '/skpd/hon_sptpd/act',
        min_length=1)   
        
auto_unit_nm2 = widget.AutocompleteInputWidget(
        size=60,
        values = '/skpd/hon_tbp/act',
        min_length=1)  
        
auto_unit_nm = widget.AutocompleteInputWidget(
        size=60,
        values = '/skpd/hon/act',
        min_length=1)
            
auto_unit_kode = widget.AutocompleteInputWidget(
        size=60,
        values = '/skpd/hoc/act',
        min_length=1)
                
auto_wp_nm = widget.AutocompleteInputWidget(
        size=60,
        values = '/wp/hon/act',
        min_length=1)
        
auto_wp_nm1 = widget.AutocompleteInputWidget(
        size=60,
        values = '/wp/hon1/act',
        min_length=1)
auto_wp_nm3 = widget.AutocompleteInputWidget(
        size=60,
        values = '/wp/hon2/act',
        min_length=1)
auto_wp_nm4 = widget.AutocompleteInputWidget(
        size=60,
        values = '/wp/hon3/act',
        min_length=1)
auto_wp_nm2 = widget.AutocompleteInputWidget(
        size=60,
        values = '/wp/ho_objek/act',
        min_length=1)

auto_op_nm = widget.AutocompleteInputWidget(
        size=60,
        values = '/op/hon/act',
        min_length=1)
        
auto_group_nm = widget.AutocompleteInputWidget(
        size=60,
        values = '/group/hon/act',
        min_length=1)

auto_route_nm = widget.AutocompleteInputWidget(
        size=60,
        values = '/group/hon/act',
        min_length=1)

auto_user_nm = widget.AutocompleteInputWidget(
        size=60,
        values = '/user/hon/act',
        min_length=1)

auto_wilayah_nm = widget.AutocompleteInputWidget(
        size=60,
        values = '/wilayah/hon/act',
        min_length=1)

auto_rekening_nm = widget.AutocompleteInputWidget(
        size=60,
        values = '/rekening/hon/act',
        min_length=1)

auto_pajak_nm = widget.AutocompleteInputWidget(
        size=60,
        values = '/pajak/hon/act',
        min_length=1)

