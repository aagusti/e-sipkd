import sys
import re
from email.utils import parseaddr
from sqlalchemy import not_, func
from datetime import datetime
from time import gmtime, strftime
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
from esipkd.views.base_view import BaseViews

from pyjasper import (JasperGenerator)
from pyjasper import (JasperGeneratorWithSubreport)
import xml.etree.ElementTree as ET
from pyramid.path import AssetResolver

from ..models import (
    DBSession,
    UserResourcePermission,
    Resource,
    User,
    Group,
    )
from ..models.isipkd import *

"""import sys
import unittest
import os.path
import uuid

from osipkd.tools import row2dict, xls_reader

from datetime import datetime
#from sqlalchemy import not_, func
from sqlalchemy import *
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession, User, Group, Route, GroupRoutePermission
from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews

from pyjasper import (JasperGenerator)
from pyjasper import (JasperGeneratorWithSubreport)
import xml.etree.ElementTree as ET
from pyramid.path import AssetResolver

from osipkd.models.base_model import *
from osipkd.models.pemda_model import *
from osipkd.models.apbd import * 
from osipkd.models.apbd_anggaran import * 
"""

def get_rpath(filename):
    a = AssetResolver('esipkd')
    resolver = a.resolve(''.join(['reports/',filename]))
    return resolver.abspath()
    
angka = {1:'satu',2:'dua',3:'tiga',4:'empat',5:'lima',6:'enam',7:'tujuh',\
         8:'delapan',9:'sembilan'}
b = ' puluh '
c = ' ratus '
d = ' ribu '
e = ' juta '
f = ' milyar '
g = ' triliun '
def Terbilang(x):   
    y = str(x)         
    n = len(y)        
    if n <= 3 :        
        if n == 1 :   
            if y == '0' :   
                return ''   
            else :         
                return angka[int(y)]   
        elif n == 2 :
            if y[0] == '1' :                
                if y[1] == '1' :
                    return 'sebelas'
                elif y[0] == '0':
                    x = y[1]
                    return Terbilang(x)
                elif y[1] == '0' :
                    return 'sepuluh'
                else :
                    return angka[int(y[1])] + ' belas'
            elif y[0] == '0' :
                x = y[1]
                return Terbilang(x)
            else :
                x = y[1]
                return angka[int(y[0])] + b + Terbilang(x)
        else :
            if y[0] == '1' :
                x = y[1:]
                return 'seratus ' + Terbilang(x)
            elif y[0] == '0' : 
                x = y[1:]
                return Terbilang(x)
            else :
                x = y[1:]
                return angka[int(y[0])] + c + Terbilang(x)
    elif 3< n <=6 :
        p = y[-3:]
        q = y[:-3]
        if q == '1' :
            return 'seribu' + Terbilang(p)
        elif q == '000' :
            return Terbilang(p)
        else:
            return Terbilang(q) + d + Terbilang(p)
    elif 6 < n <= 9 :
        r = y[-6:]
        s = y[:-6]
        return Terbilang(s) + e + Terbilang(r)
    elif 9 < n <= 12 :
        t = y[-9:]
        u = y[:-9]
        return Terbilang(u) + f + Terbilang(t)
    else:
        v = y[-12:]
        w = y[:-12]
        return Terbilang(w) + g + Terbilang(v)

class ViewLaporan(BaseViews):
    def __init__(self, context, request):
        global logo
        BaseViews.__init__(self, context, request)
        logo = self.request.static_url('esipkd:static/img/logo.png')
      
        """BaseViews.__init__(self, context, request)
        self.app = 'anggaran'

        row = DBSession.query(Tahun.status_apbd).filter(Tahun.tahun==self.tahun).first()
        self.session['status_apbd'] = row and row[0] or 0


        self.status_apbd =  'status_apbd' in self.session and self.session['status_apbd'] or 0        
        #self.status_apbd_nm =  status_apbd[str(self.status_apbd)]        
        
        self.all_unit =  'all_unit' in self.session and self.session['all_unit'] or 0        
        self.unit_id  = 'unit_id' in self.session and self.session['unit_id'] or 0
        self.unit_kd  = 'unit_kd' in self.session and self.session['unit_kd'] or "X.XX.XX"
        self.unit_nm  = 'unit_nm' in self.session and self.session['unit_nm'] or "Pilih Unit"
        self.keg_id  = 'keg_id' in self.session and self.session['keg_id'] or 0
        
        self.datas['status_apbd'] = self.status_apbd 
        #self.datas['status_apbd_nm'] = self.status_apbd_nm
        self.datas['all_unit'] = self.all_unit
        self.datas['unit_kd'] = self.unit_kd
        self.datas['unit_nm'] = self.unit_nm
        self.datas['unit_id'] = self.unit_id

        self.cust_nm = 'cust_nm' in self.session and self.session['cust_nm'] or 'PEMERINTAH KABUPATEN TANGERANG'
        customer = self.cust_nm
        logo = self.request.static_url('osipkd:static/img/logo.png')
        """
    @view_config(route_name="reports_act")
    def reports_act(self):
        req    = self.request
        params = req.params
        url_dict = req.matchdict
        id = 'id' in params and params['id'] and int(params['id']) or 0

        ###################### USER
        if url_dict['act']=='r001' :
            query = DBSession.query(User.user_name.label('username'), User.email, User.status, User.last_login_date.label('last_login'), User.registered_date).\
                    order_by(User.user_name).all()
            generator = r001Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### GROUP
        elif url_dict['act']=='r002' :
            query = DBSession.query(Group.group_name.label('kode'), Group.description.label('nama')).order_by(Group.group_name).all()
            generator = r002Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### SKPD/UNIT
        elif url_dict['act']=='r003' :
            query = DBSession.query(Unit.kode, Unit.nama, Unit.level_id, Unit.is_summary).order_by(Unit.kode).all()
            generator = r003Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### JABATAN
        elif url_dict['act']=='r004' :
            query = DBSession.query(Jabatan.kode, Jabatan.nama, Jabatan.status).order_by(Jabatan.kode).all()
            generator = r004Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)   
            return response
        ###################### PEGAWAI
        elif url_dict['act']=='r005' :
            query = DBSession.query(Pegawai.kode, Pegawai.nama).order_by(Pegawai.kode).all()
            generator = r005Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### REKENING
        elif url_dict['act']=='r006' :
            query = DBSession.query(Rekening.kode, Rekening.nama, Rekening.level_id, Rekening.is_summary).order_by(Rekening.kode).all()
            generator = r006Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### PAJAK DAN TARIF
        elif url_dict['act']=='r007' :
            query = DBSession.query(Pajak.kode, Pajak.nama, Rekening.nama.label('rek_nm'), Pajak.tahun, Pajak.tarif
                ).filter(Pajak.rekening_id==Rekening.id
                ).order_by(Pajak.kode).all()
            generator = r007Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### WILAYAH
        elif url_dict['act']=='r008' :
            query = DBSession.query(Wilayah.kode, Wilayah.nama, Wilayah.level_id).order_by(Wilayah.kode).all()
            generator = r008Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### SUBJEK PAJAK
        elif url_dict['act']=='r009' :
            query = DBSession.query(SubjekPajak.kode, SubjekPajak.nama, SubjekPajak.alamat_1, SubjekPajak.alamat_2, SubjekPajak.status).order_by(SubjekPajak.kode).all()
            generator = r009Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### OBJEK PAJAK
        elif url_dict['act']=='r010' :
            query = DBSession.query(ObjekPajak).join(SubjekPajak).join(Pajak).join(Wilayah).order_by(SubjekPajak.kode).all()
            generator = r010Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### ARINVOICE
        elif url_dict['act']=='r100' :
            #u = req.user.id
            query = DBSession.query(ARInvoice
               ).filter(ARInvoice.id==id
               ).order_by(ARInvoice.kode).all()
            generator = r100Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
             
        ###################### ARSSPD
        elif url_dict['act']=='r200' :
            query = DBSession.query(ARSspd).join(ARInvoice).order_by(ARSspd.id).all()
            generator = r200Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ###################### ARSTS
        elif url_dict['act']=='r300' :
            query = DBSession.query(ARSts.id, ARSts.kode, ARSts.nama, ARSts.tgl_sts, 
              Unit.kode.label('unit_kd'), Unit.nama.label('unit_nm'),
              Rekening.kode.label('rek_kd'), Rekening.nama.label('rek_nm'), 
              ARStsItem.jumlah
              ).filter(ARSts.unit_id==Unit.id, ARSts.id==ARStsItem.sts_id, ARStsItem.rekening_id==Rekening.id, ARSts.id==id).order_by(Rekening.kode).all()
            generator = r300Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ###################### E-SAMSAT
        elif url_dict['act']=='esamsat' :
            query = self.request.params
            generator = r400Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ###################### E-PAP
        elif url_dict['act']=='epap' :
            query = self.request.params
            generator = r500Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        else:
            return HTTPNotFound() #TODO: Warning Hak Akses 
            
#User
class r001Generator(JasperGenerator):
    def __init__(self):
        super(r001Generator, self).__init__()
        self.reportname = get_rpath('R0001.jrxml')
        self.xpath = '/webr/user'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'user')
            ET.SubElement(xml_greeting, "username").text = row.username
            ET.SubElement(xml_greeting, "email").text = row.email
            ET.SubElement(xml_greeting, "status").text = unicode(row.status)
            ET.SubElement(xml_greeting, "last_login").text = unicode(row.last_login)
            ET.SubElement(xml_greeting, "registered_date").text = unicode(row.registered_date)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#Grup
class r002Generator(JasperGenerator):
    def __init__(self):
        super(r002Generator, self).__init__()
        self.reportname = get_rpath('R0002.jrxml')
        self.xpath = '/webr/grup'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'grup')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#Unit
class r003Generator(JasperGenerator):
    def __init__(self):
        super(r003Generator, self).__init__()
        self.reportname = get_rpath('R0003.jrxml')
        self.xpath = '/webr/unit'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'unit')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "is_summary").text = unicode(row.is_summary)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#Jabatan
class r004Generator(JasperGenerator):
    def __init__(self):
        super(r004Generator, self).__init__()
        self.reportname = get_rpath('R0004.jrxml')
        self.xpath = '/webr/jabatan'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'jabatan')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "status").text = unicode(row.status)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#Pegawai
class r005Generator(JasperGenerator):
    def __init__(self):
        super(r005Generator, self).__init__()
        self.reportname = get_rpath('R0005.jrxml')
        self.xpath = '/webr/pegawai'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'pegawai')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#Rekening
class r006Generator(JasperGenerator):
    def __init__(self):
        super(r006Generator, self).__init__()
        self.reportname = get_rpath('R0006.jrxml')
        self.xpath = '/webr/rekening'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'rekening')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "is_summary").text = unicode(row.is_summary)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#Pajak dan Tarif
class r007Generator(JasperGenerator):
    def __init__(self):
        super(r007Generator, self).__init__()
        self.reportname = get_rpath('R0007.jrxml')
        self.xpath = '/webr/pajak'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'pajak')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "tahun").text = unicode(row.tahun)
            ET.SubElement(xml_greeting, "tarif").text = unicode(row.tarif)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#Wilayah
class r008Generator(JasperGenerator):
    def __init__(self):
        super(r008Generator, self).__init__()
        self.reportname = get_rpath('R0008.jrxml')
        self.xpath = '/webr/wilayah'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'wilayah')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "level_id").text = unicode(row.level_id)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#SubjekPajak
class r009Generator(JasperGenerator):
    def __init__(self):
        super(r009Generator, self).__init__()
        self.reportname = get_rpath('R0009.jrxml')
        self.xpath = '/webr/subjekpajak'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'subjekpajak')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "alamat_1").text = row.alamat_1
            ET.SubElement(xml_greeting, "alamat_2").text = row.alamat_2
            ET.SubElement(xml_greeting, "status").text = unicode(row.status)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#ObjekPajak
class r010Generator(JasperGenerator):
    def __init__(self):
        super(r010Generator, self).__init__()
        self.reportname = get_rpath('R0010.jrxml')
        self.xpath = '/webr/op'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'op')
            ET.SubElement(xml_greeting, "kode").text = row.subjekpajaks.kode
            ET.SubElement(xml_greeting, "no").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "rekening").text = row.pajaks.kode
            ET.SubElement(xml_greeting, "wilayah").text = row.wilayahs.nama
            ET.SubElement(xml_greeting, "status").text = unicode(row.status)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#ARINVOICE
class r100Generator(JasperGenerator):
    def __init__(self):
        super(r100Generator, self).__init__()
        self.reportname = get_rpath('epayment.jrxml')
        self.xpath = '/webr/epayment'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'epayment')
            ET.SubElement(xml_greeting, "kd_bayar").text = row.kode
            ET.SubElement(xml_greeting, "wp_nama").text = row.wp_nama
            ET.SubElement(xml_greeting, "op_nama").text = row.op_nama
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kode
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nama
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kode
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nama
            ET.SubElement(xml_greeting, "periode1").text = unicode(row.periode_1)
            ET.SubElement(xml_greeting, "periode2").text = unicode(row.periode_2)
            ET.SubElement(xml_greeting, "tgl_tetap").text = unicode(row.tgl_tetap)
            ET.SubElement(xml_greeting, "tgl_jt_tempo").text = unicode(row.jatuh_tempo)
            ET.SubElement(xml_greeting, "dasar").text = unicode(row.dasar)
            ET.SubElement(xml_greeting, "tarif").text = unicode(row.tarif)
            ET.SubElement(xml_greeting, "pokok").text = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#ARSSPD
class r200Generator(JasperGenerator):
    def __init__(self):
        super(r200Generator, self).__init__()
        self.reportname = get_rpath('R2000.jrxml')
        self.xpath = '/webr/arsspd'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'arsspd')
            ET.SubElement(xml_greeting, "id").text = unicode(row.id)
            ET.SubElement(xml_greeting, "kode").text = row.arinvoices.kode
            ET.SubElement(xml_greeting, "wp_kode").text = row.arinvoices.wp_kode
            ET.SubElement(xml_greeting, "wp_nama").text = row.arinvoices.wp_nama
            ET.SubElement(xml_greeting, "op_kode").text = row.arinvoices.op_kode
            ET.SubElement(xml_greeting, "op_nama").text = row.arinvoices.op_nama
            ET.SubElement(xml_greeting, "rek_nama").text = row.arinvoices.rek_nama
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.bayar)
            ET.SubElement(xml_greeting, "tgl_bayar").text = unicode(row.tgl_bayar)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root
#ARSTS
class r300Generator(JasperGenerator):
    def __init__(self):
        super(r300Generator, self).__init__()
        self.reportname = get_rpath('R3000.jrxml')
        self.xpath = '/webr/arsts'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'arsts')
            ET.SubElement(xml_greeting, "id").text = unicode(row.id)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "tgl_sts").text = unicode(row.tgl_sts)
            ET.SubElement(xml_greeting, "unit_kd").text = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = row.unit_nm
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text = logo
        return self.root

#E-SAMSAT
class r400Generator(JasperGenerator):
    def __init__(self):
        super(r400Generator, self).__init__()
        self.reportname = get_rpath('esamsat.jrxml')
        self.xpath = '/webr/esamsat'
        self.root = ET.Element('webr') 

    def generate_xml(self, row):
        #for row in tobegreeted:
        xml_greeting  =  ET.SubElement(self.root, 'esamsat')
        ET.SubElement(xml_greeting, "logo").text = logo
        ET.SubElement(xml_greeting, "customer").text = 'AAAA'
        ET.SubElement(xml_greeting, "kd_bayar").text = row['kd_bayar']
        ET.SubElement(xml_greeting, "no_rangka").text = row['no_rangka1']
        ET.SubElement(xml_greeting, "no_polisi").text = row['no_polisi']
        ET.SubElement(xml_greeting, "no_identitas").text = row['no_ktp1']
        ET.SubElement(xml_greeting, "nm_pemilik").text = row['nm_pemilik']
        ET.SubElement(xml_greeting, "warna").text = row['warna_tnkb']
        ET.SubElement(xml_greeting, "merk").text = row['nm_merek_kb']
        ET.SubElement(xml_greeting, "model").text = row['nm_model_kb']
        ET.SubElement(xml_greeting, "tahun").text = row['th_buatan']
        ET.SubElement(xml_greeting, "tgl_pjk_lama").text = row['tg_akhir_pjklm']
        ET.SubElement(xml_greeting, "tgl_pjk_baru").text = row['tg_akhir_pjkbr']
        ET.SubElement(xml_greeting, "pokok_bbn").text = row['bbn_pok']
        ET.SubElement(xml_greeting, "denda_bbn").text = row['bbn_den']
        ET.SubElement(xml_greeting, "pokok_swdkllj").text = row['swd_pok']
        ET.SubElement(xml_greeting, "denda_swdkllj").text = row['swd_den']
        ET.SubElement(xml_greeting, "adm_stnk").text = row['adm_stnk']
        ET.SubElement(xml_greeting, "adm_tnkb").text = row['adm_tnkb']
        ET.SubElement(xml_greeting, "jumlah").text = row['jumlah']
        ET.SubElement(xml_greeting, "status_byr").text = row['kd_status']
        ET.SubElement(xml_greeting, "keterangan").text = row['ket']
        return self.root

#E-PAP
class r500Generator(JasperGenerator):
    def __init__(self):
        super(r500Generator, self).__init__()
        self.reportname = get_rpath('epap.jrxml')
        self.xpath = '/webr/epap'
        self.root = ET.Element('webr') 

    def generate_xml(self, row):
        #for row in tobegreeted:
        xml_greeting  =  ET.SubElement(self.root, 'epap')
        ET.SubElement(xml_greeting, "logo").text = logo
        ET.SubElement(xml_greeting, "kd_bayar").text = row['kd_bayar']
        ET.SubElement(xml_greeting, "npwpd").text = row['npwpd']
        ET.SubElement(xml_greeting, "nm_perus").text = row['nm_perus']
        ET.SubElement(xml_greeting, "al_perus").text = row['al_perus']
        ET.SubElement(xml_greeting, "vol_air").text = row['vol_air']
        ET.SubElement(xml_greeting, "npa").text = row['npa']
        ET.SubElement(xml_greeting, "m_pjk_thn").text = row['m_pjk_thn']
        ET.SubElement(xml_greeting, "m_pjk_bln").text = row['m_pjk_bln']
        ET.SubElement(xml_greeting, "bea_pok_pjk").text = row['bea_pok_pjk']
        ET.SubElement(xml_greeting, "bea_den_pjk").text = row['bea_den_pjk']
        ET.SubElement(xml_greeting, "tgl_tetap").text = row['tgl_tetap']
        ET.SubElement(xml_greeting, "tgl_jt_tempo").text = row['tgl_jt_tempo']
        ET.SubElement(xml_greeting, "keterangan").text = row['keterangan']
        return self.root
