import sys
import re
from email.utils import parseaddr
from sqlalchemy import not_, func, case, and_, or_
from sqlalchemy.sql.expression import literal_column, column
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
from ..security import group_in

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
        global logo_pemda
        BaseViews.__init__(self, context, request)
        logo = self.request.static_url('esipkd:static/img/logo.png')
        logo_pemda = self.request.static_url('esipkd:static/img/logo-pemda.png')
      
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
    # LAPORAN PENERIMAAN
    @view_config(route_name="report-sspd", renderer="templates/report/report_sspd.pt", permission="read")
    def report_sspd(self):
        params = self.request.params
        return dict()
        
    # LAPORAN
    @view_config(route_name="report", renderer="templates/report/report.pt", permission="read")
    def report(self):
        params = self.request.params
        return dict()
        
    @view_config(route_name="reports_act")
    def reports_act(self):
        global awal, akhir, tgl_awal, tgl_akhir, u, unit_kd, unit_nm, unit_al
        req       = self.request
        params    = req.params
        url_dict  = req.matchdict
        u         = req.user.id
        id        = 'id' in params and params['id'] and int(params['id']) or 0
        
        #---------------------- Laporan ----------------------------------------------#
        jenis = 'jenis' in params and params['jenis'] and str(params['jenis']) or ''
        bayar = 'bayar' in params and params['bayar'] and str(params['bayar']) or ''
        rek   = 'rek'   in params and params['rek']   and str(params['rek'])   or ''
        h2h   = 'h2h'   in params and params['h2h']   and str(params['h2h'])   or ''
        unit  = 'unit'  in params and params['unit']  and str(params['unit'])  or ''
        sptpd_id  = 'sptpd_id'  in params and params['sptpd_id']  and str(params['sptpd_id'])  or ''
        
        if group_in(req, 'bendahara'):
            unit_id = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            unit_id = '%s' % unit_id
            unit_id = int(unit_id) 
            
            unit_kd = DBSession.query(Unit.kode).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
            unit_kd = '%s' % unit_kd
            
            unit_nm = DBSession.query(Unit.nama).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
            unit_nm = '%s' % unit_nm
            
            unit_al = DBSession.query(Unit.alamat).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
            unit_al = '%s' % unit_al
        #-----------------------------------------------------------------------------#        
        
        tgl_awal  = 'tgl_awal'  in params and params['tgl_awal']  and str(params['tgl_awal'])  or 0
        tgl_akhir = 'tgl_akhir' in params and params['tgl_akhir'] and str(params['tgl_akhir']) or 0
        
        awal  = 'awal'  in params and params['awal']  and str(params['awal'])  or datetime.now().strftime('%Y-%m-%d')
        akhir = 'akhir' in params and params['akhir'] and str(params['akhir']) or datetime.now().strftime('%Y-%m-%d')
 
        ##----------------------- Query laporan -------------------------------------##
        if url_dict['act']=='Laporan_1' :
            if bayar == '1':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         ARInvoice.is_tbp==0,
                                         ARInvoice.status_bayar==0,
                                         ARInvoice.rekening_id==rek
                                ).group_by(ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                           ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama
                                ).order_by(ARInvoice.unit_kode)
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '2':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         or_(ARInvoice.status_bayar==1,
                                             ARInvoice.is_tbp==1),
                                         ARInvoice.rekening_id==rek
                                ).group_by(ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                           ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama
                                ).order_by(ARInvoice.unit_kode)
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '3':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         ARInvoice.rekening_id==rek
                                ).group_by(ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                           ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama
                                ).order_by(ARInvoice.unit_kode)
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
                    
            generator = lap1Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='Laporan_2' :
            print "--------- Status Jenis Lap  --------- ",jenis
            print "--------- Status Pembayaran --------- ",bayar
            print "--------- ID Rekening --------------- ",rek
            print "--------- Tanggal Awal -------------- ",awal
            print "--------- Tanggal Akhir ------------- ",akhir
            if bayar == '1':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.kode.label('kd'),
                                        ARInvoice.wp_nama.label('wp_nm'),
                                        ARInvoice.dasar.label('dasar'),
                                        ARInvoice.pokok.label('pokok'),
                                        ARInvoice.denda.label('denda'),
                                        ARInvoice.bunga.label('bunga'),
                                        ARInvoice.jumlah.label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         ARInvoice.is_tbp==0,
                                         ARInvoice.status_bayar==0,
                                         ARInvoice.rekening_id==rek
                                ).order_by(ARInvoice.unit_kode,
                                           ARInvoice.kode,
                                           ARInvoice.jumlah
                                )
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '2':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.kode.label('kd'),
                                        ARInvoice.wp_nama.label('wp_nm'),
                                        ARInvoice.dasar.label('dasar'),
                                        ARInvoice.pokok.label('pokok'),
                                        ARInvoice.denda.label('denda'),
                                        ARInvoice.bunga.label('bunga'),
                                        ARInvoice.jumlah.label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         or_(ARInvoice.status_bayar==1,
                                             ARInvoice.is_tbp==1),
                                         ARInvoice.rekening_id==rek
                                ).order_by(ARInvoice.unit_kode,
                                           ARInvoice.kode,
                                           ARInvoice.jumlah
                                )
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '3':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.kode.label('kd'),
                                        ARInvoice.wp_nama.label('wp_nm'),
                                        ARInvoice.dasar.label('dasar'),
                                        ARInvoice.pokok.label('pokok'),
                                        ARInvoice.denda.label('denda'),
                                        ARInvoice.bunga.label('bunga'),
                                        ARInvoice.jumlah.label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         ARInvoice.rekening_id==rek
                                ).order_by(ARInvoice.unit_kode,
                                           ARInvoice.kode,
                                           ARInvoice.jumlah
                                )
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
                    
            generator = lap2Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        
        elif url_dict['act']=='Laporan_3' :
            print "--------- Status Jenis Lap  --------- ",jenis
            print "--------- Status Pembayaran --------- ",bayar
            print "--------- ID Unit ------------------- ",unit
            print "--------- Tanggal Awal -------------- ",awal
            print "--------- Tanggal Akhir ------------- ",akhir
            if bayar == '1':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         ARInvoice.is_tbp==0,
                                         ARInvoice.status_bayar==0,
                                         ARInvoice.unit_id==unit
                                ).group_by(ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                           ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama
                                ).order_by(ARInvoice.rek_kode)
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '2':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         or_(ARInvoice.status_bayar==1,
                                             ARInvoice.is_tbp==1),
                                         ARInvoice.unit_id==unit
                                ).group_by(ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                           ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama
                                ).order_by(ARInvoice.rek_kode)
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '3':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         ARInvoice.unit_id==unit
                                ).group_by(ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                           ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama
                                ).order_by(ARInvoice.rek_kode)
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
                    
            generator = lap3Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='Laporan_4' :
            print "--------- Status Jenis Lap  --------- ",jenis
            print "--------- Status Pembayaran --------- ",bayar
            print "--------- ID Unit ------------------- ",unit
            print "--------- Tanggal Awal -------------- ",awal
            print "--------- Tanggal Akhir ------------- ",akhir
            if bayar == '1':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.kode.label('kd'),
                                        ARInvoice.wp_nama.label('wp_nm'),
                                        ARInvoice.dasar.label('dasar'),
                                        ARInvoice.pokok.label('pokok'),
                                        ARInvoice.denda.label('denda'),
                                        ARInvoice.bunga.label('bunga'),
                                        ARInvoice.jumlah.label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         ARInvoice.is_tbp==0,
                                         ARInvoice.status_bayar==0,
                                         ARInvoice.unit_id==unit
                                ).order_by(ARInvoice.rek_kode,
                                           ARInvoice.kode,
                                           ARInvoice.jumlah
                                )
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '2':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.kode.label('kd'),
                                        ARInvoice.wp_nama.label('wp_nm'),
                                        ARInvoice.dasar.label('dasar'),
                                        ARInvoice.pokok.label('pokok'),
                                        ARInvoice.denda.label('denda'),
                                        ARInvoice.bunga.label('bunga'),
                                        ARInvoice.jumlah.label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         or_(ARInvoice.status_bayar==1,
                                             ARInvoice.is_tbp==1),
                                         ARInvoice.unit_id==unit
                                ).order_by(ARInvoice.rek_kode,
                                           ARInvoice.kode,
                                           ARInvoice.jumlah
                                )
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '3':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.kode.label('kd'),
                                        ARInvoice.wp_nama.label('wp_nm'),
                                        ARInvoice.dasar.label('dasar'),
                                        ARInvoice.pokok.label('pokok'),
                                        ARInvoice.denda.label('denda'),
                                        ARInvoice.bunga.label('bunga'),
                                        ARInvoice.jumlah.label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         ARInvoice.unit_id==unit
                                ).order_by(ARInvoice.rek_kode,
                                           ARInvoice.kode,
                                           ARInvoice.jumlah
                                )
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
                    
            generator = lap4Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        
        elif url_dict['act']=='Laporan_5' :
            print "--------- Status Jenis Lap  --------- ",jenis
            print "--------- Status Pembayaran --------- ",bayar
            print "--------- ID Rekening --------------- ",rek
            print "--------- ID Unit ------------------- ",unit
            print "--------- Tanggal Awal -------------- ",awal
            print "--------- Tanggal Akhir ------------- ",akhir
            if bayar == '1':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         ARInvoice.is_tbp==0,
                                         ARInvoice.status_bayar==0
                                ).group_by(ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                           ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama
                                ).order_by(ARInvoice.unit_kode,
                                           ARInvoice.rek_kode)
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '2':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         or_(ARInvoice.status_bayar==1,
                                             ARInvoice.is_tbp==1)
                                ).group_by(ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                           ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama
                                ).order_by(ARInvoice.unit_kode,
                                           ARInvoice.rek_kode)
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '3':
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir)
                                ).group_by(ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                           ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama
                                ).order_by(ARInvoice.unit_kode,
                                           ARInvoice.rek_kode)
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
                    
            generator = lap5Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        
        elif url_dict['act']=='Laporan_6' :
            print "--------- Status Jenis Lap  --------- ",jenis
            print "--------- Status Pembayaran --------- ",bayar
            print "--------- ID Rekening --------------- ",rek
            print "--------- ID Unit ------------------- ",unit
            print "--------- Tanggal Awal -------------- ",awal
            print "--------- Tanggal Akhir ------------- ",akhir
            if bayar == '1':
                query = DBSession.query(ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         ARInvoice.is_tbp==0,
                                         ARInvoice.status_bayar==0
                                ).group_by(ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama,
                                           ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                ).order_by(ARInvoice.rek_kode,
                                           ARInvoice.unit_kode
                                )
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '2':
                query = DBSession.query(ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                         or_(ARInvoice.status_bayar==1,
                                             ARInvoice.is_tbp==1)
                                ).group_by(ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama,
                                           ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                ).order_by(ARInvoice.rek_kode,
                                           ARInvoice.unit_kode
                                )
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
            elif bayar == '3':
                query = DBSession.query(ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        func.sum(ARInvoice.dasar).label('dasar'),
                                        func.sum(ARInvoice.pokok).label('pokok'),
                                        func.sum(ARInvoice.denda).label('denda'),
                                        func.sum(ARInvoice.bunga).label('bunga'),
                                        func.sum(ARInvoice.jumlah).label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir)
                                ).group_by(ARInvoice.rekening_id,
                                           ARInvoice.rek_kode,
                                           ARInvoice.rek_nama,
                                           ARInvoice.unit_id,
                                           ARInvoice.unit_kode,
                                           ARInvoice.unit_nama,
                                ).order_by(ARInvoice.rek_kode,
                                           ARInvoice.unit_kode
                                )
                if group_in(req, 'bendahara'):
                    x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                    y = '%s' % x
                    z = int(y)     
                    print "- Unit_id --------- ",z
                    query = query.filter(ARInvoice.unit_id==z)
                    
            generator = lap6Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        
        elif url_dict['act']=='Laporan_8' :
            print "--------- Status Jenis Lap  --------- ",jenis
            print "--------- Status Pembayaran --------- ",bayar
            print "--------- ID Rekening --------------- ",rek
            print "--------- ID Unit ------------------- ",unit
            print "--------- Tanggal Awal -------------- ",awal
            print "--------- Tanggal Akhir ------------- ",akhir
            if group_in(req, 'bendahara'):
                query = DBSession.query(ARTbp.kode.label('kd'),
                                        ARTbp.wp_nama.label('wp_nm'),
                                        ARTbp.rekening_id.label('rek_id'),
                                        ARTbp.rek_kode.label('rek_kd'),
                                        ARTbp.rek_nama.label('rek_nm'),
                                        ARTbp.unit_id.label('un_id'),
                                        ARTbp.unit_kode.label('un_kd'),
                                        ARTbp.unit_nama.label('un_nm'),
                                        ARTbp.dasar.label('dasar'),
                                        ARTbp.pokok.label('pokok'),
                                        ARTbp.denda.label('denda'),
                                        ARTbp.bunga.label('bunga'),
                                        ARTbp.jumlah.label('jumlah')
                                ).filter(ARTbp.tgl_terima.between(awal,akhir)
                                ).order_by(ARTbp.kode,
                                           ARTbp.jumlah
                                )
                x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                y = '%s' % x
                z = int(y)     
                print "- Unit_id --------- ",z
                query = query.filter(ARTbp.unit_id==z)
                print "--------- Query ------------- ",query
                    
                generator = lap8benGenerator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            else:
                query = DBSession.query(ARTbp.unit_id.label('un_id'),
                                        ARTbp.unit_kode.label('un_kd'),
                                        ARTbp.unit_nama.label('un_nm'),
                                        ARTbp.rekening_id.label('rek_id'),
                                        ARTbp.rek_kode.label('rek_kd'),
                                        ARTbp.rek_nama.label('rek_nm'),
                                        ARTbp.kode.label('kd'),
                                        ARTbp.wp_nama.label('wp_nm'),
                                        ARTbp.dasar.label('dasar'),
                                        ARTbp.pokok.label('pokok'),
                                        ARTbp.denda.label('denda'),
                                        ARTbp.bunga.label('bunga'),
                                        ARTbp.jumlah.label('jumlah')
                                ).filter(ARTbp.tgl_terima.between(awal,akhir)
                                ).order_by(ARTbp.unit_kode,
                                           ARTbp.rek_kode,
                                           ARTbp.kode,
                                           ARTbp.jumlah
                                )
                generator = lap8Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
        
        elif url_dict['act']=='Laporan_9' :
            print "--------- Status Jenis Lap  --------- ",jenis
            print "--------- Status Pembayaran --------- ",bayar
            print "--------- ID Rekening --------------- ",rek
            print "--------- ID Unit ------------------- ",unit
            print "--------- Tanggal Awal -------------- ",awal
            print "--------- Tanggal Akhir ------------- ",akhir
            if group_in(req, 'bendahara'):
                query = DBSession.query(ARInvoice.kode.label('kd'),
                                        ARInvoice.wp_nama.label('wp_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.dasar.label('dasar'),
                                        ARInvoice.pokok.label('pokok'),
                                        ARInvoice.denda.label('denda'),
                                        ARInvoice.bunga.label('bunga'),
                                        ARInvoice.jumlah.label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir)
                                ).order_by(ARInvoice.kode,
                                           ARInvoice.jumlah
                                )
                x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                y = '%s' % x
                z = int(y)     
                print "- Unit_id --------- ",z
                query = query.filter(ARInvoice.unit_id==z)
                print "--------- Query ------------- ",query
                    
                generator = lap9benGenerator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            else:
                query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                        ARInvoice.unit_kode.label('un_kd'),
                                        ARInvoice.unit_nama.label('un_nm'),
                                        ARInvoice.rekening_id.label('rek_id'),
                                        ARInvoice.rek_kode.label('rek_kd'),
                                        ARInvoice.rek_nama.label('rek_nm'),
                                        ARInvoice.kode.label('kd'),
                                        ARInvoice.wp_nama.label('wp_nm'),
                                        ARInvoice.dasar.label('dasar'),
                                        ARInvoice.pokok.label('pokok'),
                                        ARInvoice.denda.label('denda'),
                                        ARInvoice.bunga.label('bunga'),
                                        ARInvoice.jumlah.label('jumlah')
                                ).filter(ARInvoice.tgl_tetap.between(awal,akhir)
                                ).order_by(ARInvoice.unit_kode,
                                           ARInvoice.rek_kode,
                                           ARInvoice.kode,
                                           ARInvoice.jumlah
                                )
                generator = lap9Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
        
        elif url_dict['act']=='Laporan_7' :
            print "--------- Status Jenis Lap  --------- ",jenis
            print "--------- Status Pembayaran --------- ",bayar
            print "--------- ID Rekening --------------- ",rek
            print "--------- Status H2H ---------------- ",h2h
            print "--------- ID Unit ------------------- ",unit
            print "--------- Tanggal Awal -------------- ",awal
            print "--------- Tanggal Akhir ------------- ",akhir
            if group_in(req, 'bendahara'):
                if h2h=='1':
                    query = DBSession.query(ARSspd.bayar.label('bayar'),
                                            ARSspd.bunga.label('bunga'),
                                            ARSspd.tgl_bayar.label('tgl'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).join(ARInvoice
                                    ).filter(ARSspd.tgl_bayar.between(awal,akhir),
                                             ARSspd.bayar!=0,
                                             ARSspd.bank_id!=0
                                    ).order_by(ARSspd.tgl_bayar,
                                               ARInvoice.kode
                                    )
                elif h2h=='2':
                    query = DBSession.query(ARSspd.bayar.label('bayar'),
                                            ARSspd.bunga.label('bunga'),
                                            ARSspd.tgl_bayar.label('tgl'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).join(ARInvoice
                                    ).filter(ARSspd.tgl_bayar.between(awal,akhir),
                                             ARSspd.bayar!=0,
                                             ARSspd.bank_id==None
                                    ).order_by(ARSspd.tgl_bayar,
                                               ARInvoice.kode
                                    )
                else:
                    query = DBSession.query(ARSspd.bayar.label('bayar'),
                                            ARSspd.bunga.label('bunga'),
                                            ARSspd.tgl_bayar.label('tgl'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).join(ARInvoice
                                    ).filter(ARSspd.tgl_bayar.between(awal,akhir),
                                             ARSspd.bayar!=0,
                                    ).order_by(ARSspd.tgl_bayar,
                                               ARInvoice.kode
                                    )
                x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
                y = '%s' % x
                z = int(y)     
                print "----------- Unit_id --------- ",z
                query = query.filter(ARInvoice.unit_id==z)
                print "--------- Query ------------- ",query
                    
                generator = lap7benGenerator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            else:
                if h2h=='1':
                    query = DBSession.query(ARSspd.bayar.label('bayar'),
                                            ARSspd.bunga.label('bunga'),
                                            ARSspd.tgl_bayar.label('tgl'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).join(ARInvoice
                                    ).filter(ARSspd.tgl_bayar.between(awal,akhir),
                                             ARSspd.bayar!=0,
                                             ARSspd.bank_id!=0
                                    ).order_by(ARInvoice.unit_kode,
                                               ARSspd.tgl_bayar,
                                               ARInvoice.kode,
                                               ARInvoice.rek_kode
                                    )
                elif h2h == '2':
                    query = DBSession.query(ARSspd.bayar.label('bayar'),
                                            ARSspd.bunga.label('bunga'),
                                            ARSspd.tgl_bayar.label('tgl'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).join(ARInvoice
                                    ).filter(ARSspd.tgl_bayar.between(awal,akhir),
                                             ARSspd.bayar!=0,
                                             ARSspd.bank_id == None
                                    ).order_by(ARInvoice.unit_kode,
                                               ARSspd.tgl_bayar,
                                               ARInvoice.kode,
                                               ARInvoice.rek_kode
                                    )
                else:
                    query = DBSession.query(ARSspd.bayar.label('bayar'),
                                            ARSspd.bunga.label('bunga'),
                                            ARSspd.tgl_bayar.label('tgl'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).join(ARInvoice
                                    ).filter(ARSspd.tgl_bayar.between(awal,akhir),
                                             ARSspd.bayar!=0
                                    ).order_by(ARInvoice.unit_kode,
                                               ARSspd.tgl_bayar,
                                               ARInvoice.kode,
                                               ARInvoice.rek_kode
                                    )
                generator = lap7Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
                
        elif url_dict['act']=='Laporan_10' :
            if group_in(req, 'bendahara'):
                query = DBSession.query(ARTbp.unit_id.label('un_id'),
                                        ARTbp.unit_kode.label('un_kd'),
                                        ARTbp.unit_nama.label('un_nm'),
                                        ARTbp.rekening_id.label('rek_id'),
                                        ARTbp.rek_kode.label('rek_kd'),
                                        ARTbp.rek_nama.label('rek_nm'),
                                        ARTbp.kode.label('kd'),
                                        ARTbp.invoice_kode.label('invoice_kode'),
                                        ARTbp.tgl_terima.label('tgl_terima'),
                                        ARTbp.periode_1.label('periode_1'),
                                        ARTbp.periode_2.label('periode_2'),
                                        ARTbp.jatuh_tempo.label('jatuh_tempo'),
                                        ARTbp.wp_nama.label('wp_nm'),
                                        ARTbp.op_nama.label('op_nm'),
                                        ARTbp.dasar.label('dasar'),
                                        ARTbp.pokok.label('pokok'),
                                        ARTbp.denda.label('denda'),
                                        ARTbp.bunga.label('bunga'),
                                        ARTbp.jumlah.label('jumlah')
                                ).filter(ARTbp.tgl_terima.between(awal,akhir),
                                         ARTbp.unit_kode.ilike('%%%s%%' % unit_kd)
                                ).order_by(ARTbp.unit_kode,
                                           ARTbp.tgl_terima,
                                           ARTbp.kode,
                                           ARTbp.rek_kode,
                                )
                                
                generator = lap10Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response 
            else:
                query = DBSession.query(ARTbp.unit_id.label('un_id'),
                                        ARTbp.unit_kode.label('un_kd'),
                                        ARTbp.unit_nama.label('un_nm'),
                                        ARTbp.rekening_id.label('rek_id'),
                                        ARTbp.rek_kode.label('rek_kd'),
                                        ARTbp.rek_nama.label('rek_nm'),
                                        ARTbp.kode.label('kd'),
                                        ARTbp.invoice_kode.label('invoice_kode'),
                                        ARTbp.tgl_terima.label('tgl_terima'),
                                        ARTbp.periode_1.label('periode_1'),
                                        ARTbp.periode_2.label('periode_2'),
                                        ARTbp.jatuh_tempo.label('jatuh_tempo'),
                                        ARTbp.wp_nama.label('wp_nm'),
                                        ARTbp.op_nama.label('op_nm'),
                                        ARTbp.dasar.label('dasar'),
                                        ARTbp.pokok.label('pokok'),
                                        ARTbp.denda.label('denda'),
                                        ARTbp.bunga.label('bunga'),
                                        ARTbp.jumlah.label('jumlah')
                                ).filter(ARTbp.tgl_terima.between(awal,akhir)
                                ).order_by(ARTbp.unit_kode,
                                           ARTbp.tgl_terima,
                                           ARTbp.kode,
                                           ARTbp.rek_kode,
                                )
                                
                generator = lap10budGenerator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response 

        elif url_dict['act']=='Laporan_11' :
            if group_in(req, 'bendahara'):
                ## kondisi status Bayar ##
                cek_bayar = bayar;
                if(cek_bayar=='1'):
                    bayar=0;
                elif(cek_bayar=='2'):
                    bayar=1; 
                
                if(cek_bayar=='1'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                             #ARInvoice.is_tbp==0,
                                             ARInvoice.status_bayar==bayar,
                                             ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.unit_kode,
                                               ARInvoice.rek_kode,
                                               ARInvoice.kode
                                    )
                elif (cek_bayar=='2'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                             #or_(ARInvoice.status_bayar==bayar,
                                             #    ARInvoice.is_tbp==1),
                                             ARInvoice.status_bayar==bayar,
                                             ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.unit_kode,
                                               ARInvoice.rek_kode,
                                               ARInvoice.kode
                                    )
                elif(cek_bayar=='3'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                             ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.unit_kode,
                                               ARInvoice.rek_kode,
                                               ARInvoice.kode
                                    )
                generator = lap11Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
                
            else:
                ## kondisi status Bayar ##
                cek_bayar = bayar;
                if(cek_bayar=='1'):
                    bayar=0;
                elif(cek_bayar=='2'):
                    bayar=1; 
                
                if(cek_bayar=='1'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                             #ARInvoice.is_tbp==0,
                                             ARInvoice.status_bayar==bayar,
                                             #ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.unit_kode,
                                               ARInvoice.rek_kode,
                                               ARInvoice.kode
                                    )
                elif (cek_bayar=='2'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                             #or_(ARInvoice.status_bayar==bayar,
                                             #    ARInvoice.is_tbp==1),
                                             ARInvoice.status_bayar==bayar,
                                             #ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.unit_kode,
                                               ARInvoice.rek_kode,
                                               ARInvoice.kode
                                    )
                elif(cek_bayar=='3'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                             #ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.unit_kode,
                                               ARInvoice.rek_kode,
                                               ARInvoice.kode
                                    )
                generator = lap11budGenerator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response

        elif url_dict['act']=='Laporan_12' :
            if group_in(req, 'bendahara'):
                ## kondisi status Bayar ##
                cek_bayar = bayar;
                if(cek_bayar=='1'):
                    bayar=0;
                elif(cek_bayar=='2'):
                    bayar=1; 
                
                if(cek_bayar=='1'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                            #ARInvoice.is_tbp==0,
                                            ARInvoice.status_bayar==bayar,
                                            ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.unit_kode,
                                            ARInvoice.rek_kode,
                                            ARInvoice.kode
                                    )
                elif(cek_bayar=='2'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                            #or_(ARInvoice.status_bayar==bayar,
                                            #    ARInvoice.is_tbp==1),
                                            ARInvoice.status_bayar==bayar,
                                            ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.unit_kode,
                                            ARInvoice.rek_kode,
                                            ARInvoice.kode
                                    )
                elif(cek_bayar=='3'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                            ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.rek_kode,
                                            ARInvoice.unit_kode, 
                                            ARInvoice.kode
                                    )
                                
                generator = lap12Generator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
                
            else:
                ## kondisi status Bayar ##
                cek_bayar = bayar;
                if(cek_bayar=='1'):
                    bayar=0;
                elif(cek_bayar=='2'):
                    bayar=1; 
                
                if(cek_bayar=='1'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                            #ARInvoice.is_tbp==0,
                                            ARInvoice.status_bayar==bayar,
                                            #ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.unit_kode,
                                            ARInvoice.rek_kode,
                                            ARInvoice.kode
                                    )
                elif(cek_bayar=='2'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                            #or_(ARInvoice.status_bayar==bayar,
                                            #    ARInvoice.is_tbp==1),
                                            ARInvoice.status_bayar==bayar,
                                            #ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.unit_kode,
                                            ARInvoice.rek_kode,
                                            ARInvoice.kode
                                    )
                elif(cek_bayar=='3'):
                    query = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                            ARInvoice.unit_kode.label('un_kd'),
                                            ARInvoice.unit_nama.label('un_nm'),
                                            ARInvoice.rekening_id.label('rek_id'),
                                            ARInvoice.rek_kode.label('rek_kd'),
                                            ARInvoice.rek_nama.label('rek_nm'),
                                            ARInvoice.kode.label('kd'),
                                            ARInvoice.wp_nama.label('wp_nm'),
                                            ARInvoice.dasar.label('dasar'),
                                            ARInvoice.pokok.label('pokok'),
                                            ARInvoice.denda.label('denda'),
                                            ARInvoice.bunga.label('bunga'),
                                            ARInvoice.jumlah.label('jumlah')
                                    ).filter(ARInvoice.tgl_tetap.between(awal,akhir),
                                            #ARInvoice.unit_kode.ilike('%%%s%%' % unit_kd)
                                    ).order_by(ARInvoice.rek_kode,
                                            ARInvoice.unit_kode, 
                                            ARInvoice.kode
                                    )
                                
                generator = lap12budGenerator()
                pdf = generator.generate(query)
                response=req.response
                response.content_type="application/pdf"
                response.content_disposition='filename=output.pdf' 
                response.write(pdf)
                return response
            
        ##----------------------------- End Laporan -----------------##

        
        ###################### USER
        elif url_dict['act']=='r001' :
            # function case when alchemy -> case([(User.status==1,"Aktif"),],else_="Tidak Aktif").label("status")
            # iWan Mampir
            query = DBSession.query(User.user_name.label('username'), User.email, case([(User.status==1,"Aktif"),],else_="Tidak Aktif").label("status"), User.last_login_date.label('last_login'), User.registered_date).\
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
        ###################### JENISPAJAK
        # function case when alchemy -> case([(JnsPajak.status==1,"Aktif"),],else_="Tidak Aktif").label("status")
        # iWan Mampir
        elif url_dict['act']=='semua_sektor' :
            query = DBSession.query(JnsPajak.kode, JnsPajak.nama, case([(JnsPajak.status==1,"Aktif"),],else_="Tidak Aktif").label("status")).order_by(JnsPajak.kode).all()
            generator = semua_sektorGenerator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### SUBJEK PAJAK
        # function case when alchemy -> case([(SubjekPajak.status==1,"Aktif"),],else_="Tidak Aktif").label("status")
        # iWan Mampir
        elif url_dict['act']=='r009' :
            query = DBSession.query(SubjekPajak.kode, SubjekPajak.nama, SubjekPajak.alamat_1, SubjekPajak.alamat_2, case([(SubjekPajak.status==1,"Aktif"),],else_="Tidak Aktif").label("status")).order_by(SubjekPajak.kode).all()
            generator = r009Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        ###################### OBJEK PAJAK
        # function case when alchemy -> case([(SubjekPajak.status==1,"Aktif"),],else_="Tidak Aktif").label("status")
        # iWan Mampir
        elif url_dict['act']=='r010' :
            query = DBSession.query(ObjekPajak).join(SubjekPajak).join(Pajak).join(Wilayah).order_by(SubjekPajak.kode).all()
            generator = r010Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ###################### ARINVOICE FAST PAY
        elif url_dict['act']=='r101' :
            print "---- Awal ------ ",awal
            print "---- Akhir ----- ",akhir
            query = DBSession.query(ARInvoice
                            ).filter(ARInvoice.id==id,
                                     ARInvoice.status_grid==1,
                                     #ARInvoice.tgl_tetap.between(awal,akhir)
                            ).order_by(ARInvoice.kode)
            if u != 1:
                query = query.filter(ARInvoice.owner_id==u) 
            generator = r101Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ###################### ARINVOICE
        elif url_dict['act']=='r100' :
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
        # function trim to_char alchemy -> func.trim(func.to_char(ARInvoice.tarif,'999,999,999,990')).label('tarif'),
        # iWan Mampir
        elif url_dict['act']=='r200' :
            print '*********tgl_akhir********',tgl_akhir
            query = DBSession.query(ARSspd.id, 
            ARInvoice.kode,
            ARInvoice.wp_kode,
            ARInvoice.wp_nama,
            ARInvoice.op_kode,
            ARInvoice.op_nama,
            ARInvoice.rek_kode,
            ARInvoice.rek_nama,
            func.trim(func.to_char(ARSspd.bayar,'999,999,999,990')).label('bayar'),
            ARSspd.tgl_bayar, 
            ).join(ARInvoice
            ).filter(and_(ARSspd.tgl_bayar>=tgl_awal, ARSspd.tgl_bayar<=tgl_akhir) 
            ).order_by(ARSspd.id).all()
            generator = r200Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
        elif url_dict['act']=='r200frm' :
            query = DBSession.query(ARSspd.id,
            ARSspd.tgl_bayar,
            ARInvoice.wp_kode,
            ARInvoice.wp_nama,
            ARInvoice.op_kode,
            ARInvoice.op_nama,
            ARInvoice.rek_kode,
            ARInvoice.rek_nama,
            ARInvoice.unit_kode,
            ARInvoice.unit_nama,
            ARInvoice.kode,
            func.trim(func.to_char(ARInvoice.tarif,'999,999,999,990')).label('tarif'),
            func.trim(func.to_char(ARInvoice.dasar,'999,999,999,990')).label('dasar'),
            func.trim(func.to_char(ARInvoice.pokok,'999,999,999,990')).label('pokok'),
            func.trim(func.to_char(ARInvoice.bunga,'999,999,999,990')).label('bunga'),
            func.trim(func.to_char(ARInvoice.denda,'999,999,999,990')).label('denda'),
            func.trim(func.to_char(ARSspd.bayar,'999,999,999,990')).label('bayar'),
            ).join(ARInvoice
            ).filter(ARSspd.id==id, 
            )#.order_by(ARSspd.id).all()
            generator = r200frmGenerator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ###################### ARSTS
        elif url_dict['act']=='r300' :
            query = DBSession.query(ARSts.id, 
                                    ARSts.kode, 
                                    ARSts.nama, 
                                    ARSts.tgl_sts, 
                                    Unit.kode.label('unit_kd'), 
                                    Unit.nama.label('unit_nm'),
                                    Unit.alamat.label('unit_al'),
                                    ARStsItem.rek_kode.label('rek_kd'), 
                                    ARStsItem.rek_nama.label('rek_nm'), 
                                    # ARStsItem.jumlah, 
                                    func.trim(func.to_char(ARStsItem.jumlah,'999,999,999,990')).label('jumlah'), 
                                    func.trim(func.to_char(ARSts.jumlah,'999,999,999,990')).label('jumlah_sts'), 
                                    ARStsItem.kode.label('no_bayar')
                            ).filter(ARSts.id==id,
                                     ARSts.unit_id==Unit.id, 
                                     ARStsItem.sts_id==ARSts.id, 
                                     ARStsItem.invoice_id==ARInvoice.id, 
                                     ARStsItem.rekening_id==Rekening.id,
                            ).order_by(ARStsItem.rek_kode).all()
            generator = r300Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ### SPTPD RINCIAN ###
        elif url_dict['act']=='sptpd_rincian' :
            query = DBSession.query(Sptpd.id, 
                                    Sptpd.kode, 
                                    Sptpd.nama,  
                                    InvoiceDet.sektor_nm, 
                                    Sptpd.tgl_sptpd, 
                                    Sptpd.periode_1, 
                                    Sptpd.periode_2, 
                                    InvoiceDet.wilayah_nm, 
                                    InvoiceDet.peruntukan_nm,
                                    InvoiceDet.produk_nm, 
                                    InvoiceDet.nama.label('wp'),                                    
                                    InvoiceDet.volume,  
                                    InvoiceDet.dpp, 
                                    InvoiceDet.tarif, 
                                    InvoiceDet.total_pajak,    
                            ).filter(Sptpd.id==req.params['sptpd_id'],
                                     InvoiceDet.sptpd_id==Sptpd.id
                            ).order_by(Sptpd.kode,
                                       InvoiceDet.sektor_nm,
                                       InvoiceDet.wilayah_nm,
                                       InvoiceDet.nama,
                                       InvoiceDet.peruntukan_nm,
                                       InvoiceDet.produk_nm
                            ).all()
            generator = rSptpdRincianGenerator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ### SPTPD SSPD ###
        elif url_dict['act']=='sptpd_sspd' :
            query = DBSession.query(Sptpd.id, 
                                    Sptpd.nama,  
                                    Sptpd.wp_alamat_1,  
                                    InvoiceDet.produk_nm, 
                                    Sptpd.periode_1, 
                                    Sptpd.periode_2, 
                                    Sptpd.tgl_sptpd, 
                                    SubjekPajak.kode,
                                    func.sum(InvoiceDet.total_pajak).label('total_pajak')
                            ).filter(Sptpd.id==req.params['sptpd_id'],
                                     InvoiceDet.sptpd_id==Sptpd.id,
                                     SubjekPajak.id==Sptpd.subjek_pajak_id
                            ).group_by(Sptpd.id, 
                                    SubjekPajak.kode, 
                                    Sptpd.nama,  
                                    Sptpd.wp_alamat_1,  
                                    InvoiceDet.produk_nm,
                                    Sptpd.periode_1, 
                                    Sptpd.periode_2, 
                                    Sptpd.tgl_sptpd, 
                            ).order_by(Sptpd.kode,
                                       InvoiceDet.produk_nm
                            ).all()
            generator = rSptpdSspdGenerator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ### SPTPD Lampiran ###
        elif url_dict['act']=='sptpd_lampiran' :
            query = DBSession.query(Sptpd.id, 
                                    Sptpd.kode, 
                                    Sptpd.nama,  
                                    InvoiceDet.sektor_nm, 
                                    Sptpd.tgl_sptpd, 
                                    Sptpd.periode_1,
                                    Sptpd.periode_2,
                                    InvoiceDet.produk_nm,  
                                    InvoiceDet.tarif, 
                                    func.sum(InvoiceDet.volume).label('volume'),  
                                    func.sum(InvoiceDet.dpp).label('dpp'), 
                                    func.sum(InvoiceDet.total_pajak).label('total_pajak'),                                     
                            ).filter(Sptpd.id==req.params['sptpd_id'],
                                     InvoiceDet.sptpd_id==Sptpd.id
                            ).group_by(Sptpd.id, 
                                    Sptpd.kode, 
                                    Sptpd.nama,  
                                    InvoiceDet.sektor_nm, 
                                    Sptpd.tgl_sptpd, 
                                    Sptpd.periode_1,  
                                    Sptpd.periode_2, 
                                    InvoiceDet.produk_nm,  
                                    InvoiceDet.tarif,
                            ).order_by(Sptpd.kode,
                                       InvoiceDet.sektor_nm,
                                       InvoiceDet.produk_nm,
                            ).all()
            generator = rSptpdLampiranGenerator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        ### SPTPD ###
        elif url_dict['act']=='sptpd' :
            query = DBSession.query(Sptpd.id, 
                                    Sptpd.kode, 
                                    Sptpd.nama,  
                                    InvoiceDet.sektor_nm, 
                                    Sptpd.tgl_sptpd, 
                                    Sptpd.periode_1,
                                    Sptpd.periode_2,
                                    InvoiceDet.produk_nm,  
                                    InvoiceDet.tarif, 
                                    func.sum(InvoiceDet.volume).label('volume'),  
                                    func.sum(InvoiceDet.dpp).label('dpp'), 
                                    func.sum(InvoiceDet.total_pajak).label('total_pajak'),                                     
                            ).filter(Sptpd.id==req.params['sptpd_id'],
                                     InvoiceDet.sptpd_id==Sptpd.id
                            ).group_by(Sptpd.id, 
                                    Sptpd.kode, 
                                    Sptpd.nama,  
                                    InvoiceDet.sektor_nm,   
                                    InvoiceDet.tarif,
                                    Sptpd.tgl_sptpd, 
                                    Sptpd.periode_1,  
                                    Sptpd.periode_2, 
                                    InvoiceDet.produk_nm,
                            ).order_by(Sptpd.kode,
                                       InvoiceDet.sektor_nm,
                                       InvoiceDet.tarif,
                                       InvoiceDet.produk_nm,
                            ).all()
            generator = rSptpdLampiranGenerator()
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
      
class rSptpdRincianGenerator(JasperGenerator):
    def __init__(self):
        super(rSptpdRincianGenerator, self).__init__()
        self.reportname = get_rpath('sptpd_rincian.jrxml')
        self.xpath = '/webr/sptpd_rincian'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'sptpd_rincian')
            ET.SubElement(xml_greeting, "id").text  = unicode(row.id)      
            ET.SubElement(xml_greeting, "kode").text  = row.kode               
            ET.SubElement(xml_greeting, "nama").text  = row.nama                
            ET.SubElement(xml_greeting, "sektor_nm").text = row.sektor_nm    
            ET.SubElement(xml_greeting, "produk_nm").text = row.produk_nm               
            ET.SubElement(xml_greeting, "wilayah_nm").text = row.wilayah_nm         
            ET.SubElement(xml_greeting, "peruntukan_nm").text  = row.peruntukan_nm               
            ET.SubElement(xml_greeting, "wp").text = row.wp            
            ET.SubElement(xml_greeting, "tgl_sptpd").text  = unicode(row.tgl_sptpd)       
            ET.SubElement(xml_greeting, "periode_1").text  = unicode(row.periode_1)       
            ET.SubElement(xml_greeting, "periode_2").text  = unicode(row.periode_2)       
            ET.SubElement(xml_greeting, "volume").text  = unicode(row.volume)        
            ET.SubElement(xml_greeting, "dpp").text = unicode(row.dpp)                
            ET.SubElement(xml_greeting, "tarif").text = unicode(row.tarif)           
            ET.SubElement(xml_greeting, "total_pajak").text = unicode(row.total_pajak)       
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda               
        return self.root  
      
class rSptpdSspdGenerator(JasperGenerator):
    def __init__(self):
        super(rSptpdSspdGenerator, self).__init__()
        self.reportname = get_rpath('sptpd_sspd.jrxml')
        self.xpath = '/webr/sptpd_sspd'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'sptpd_sspd')
            ET.SubElement(xml_greeting, "id").text  = unicode(row.id)      
            ET.SubElement(xml_greeting, "kode").text  = row.kode               
            ET.SubElement(xml_greeting, "nama").text  = row.nama             
            ET.SubElement(xml_greeting, "alamat_1").text  = row.wp_alamat_1     
            ET.SubElement(xml_greeting, "produk_nm").text = row.produk_nm              
            ET.SubElement(xml_greeting, "periode_1").text  = unicode(row.periode_1)        
            ET.SubElement(xml_greeting, "periode_2").text  = unicode(row.periode_2)           
            ET.SubElement(xml_greeting, "tgl_sptpd").text  = unicode(row.tgl_sptpd)           
            ET.SubElement(xml_greeting, "total_pajak").text = unicode(row.total_pajak)       
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda               
        return self.root  
        
class rSptpdLampiranGenerator(JasperGenerator):
    def __init__(self):
        super(rSptpdLampiranGenerator, self).__init__()
        self.reportname = get_rpath('sptpd_lampiran.jrxml')
        self.xpath = '/webr/sptpd_lampiran'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'sptpd_lampiran')
            ET.SubElement(xml_greeting, "id").text  = unicode(row.id)      
            ET.SubElement(xml_greeting, "kode").text  = row.kode               
            ET.SubElement(xml_greeting, "nama").text  = row.nama                
            ET.SubElement(xml_greeting, "sektor_nm").text = row.sektor_nm    
            ET.SubElement(xml_greeting, "produk_nm").text = row.produk_nm                    
            ET.SubElement(xml_greeting, "tgl_sptpd").text  = unicode(row.tgl_sptpd)       
            ET.SubElement(xml_greeting, "periode_1").text  = unicode(row.periode_1)        
            ET.SubElement(xml_greeting, "periode_2").text  = unicode(row.periode_2)      
            ET.SubElement(xml_greeting, "volume").text  = unicode(row.volume)        
            ET.SubElement(xml_greeting, "dpp").text = unicode(row.dpp)                
            ET.SubElement(xml_greeting, "tarif").text = unicode(row.tarif)           
            ET.SubElement(xml_greeting, "total_pajak").text = unicode(row.total_pajak)       
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda               
        return self.root 
        
class rSptpdGenerator(JasperGenerator):
    def __init__(self):
        super(rSptpdGenerator, self).__init__()
        self.reportname = get_rpath('sptpd.jrxml')
        self.xpath = '/webr/sptpd'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'sptpd')
            ET.SubElement(xml_greeting, "id").text  = unicode(row.id)      
            ET.SubElement(xml_greeting, "kode").text  = row.kode               
            ET.SubElement(xml_greeting, "nama").text  = row.nama                
            ET.SubElement(xml_greeting, "sektor_nm").text = row.sektor_nm    
            ET.SubElement(xml_greeting, "produk_nm").text = row.produk_nm                    
            ET.SubElement(xml_greeting, "tgl_sptpd").text  = unicode(row.tgl_sptpd)       
            ET.SubElement(xml_greeting, "periode_1").text  = unicode(row.periode_1)        
            ET.SubElement(xml_greeting, "periode_2").text  = unicode(row.periode_2)      
            ET.SubElement(xml_greeting, "volume").text  = unicode(row.volume)        
            ET.SubElement(xml_greeting, "dpp").text = unicode(row.dpp)                
            ET.SubElement(xml_greeting, "tarif").text = unicode(row.tarif)           
            ET.SubElement(xml_greeting, "total_pajak").text = unicode(row.total_pajak)       
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda               
        return self.root          
        
## ----------------- LAPORAN -------------------------------------------##
class lap1Generator(JasperGenerator):
    def __init__(self):
        super(lap1Generator, self).__init__()
        self.reportname = get_rpath('Lap1.jrxml')
        self.xpath = '/webr/lap1'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap1')
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
        return self.root
        
class lap2Generator(JasperGenerator):
    def __init__(self):
        super(lap2Generator, self).__init__()
        self.reportname = get_rpath('Lap2.jrxml')
        self.xpath = '/webr/lap2'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap2')
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text     = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text  = row.wp_nm
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
        return self.root
        
class lap3Generator(JasperGenerator):
    def __init__(self):
        super(lap3Generator, self).__init__()
        self.reportname = get_rpath('Lap3.jrxml')
        self.xpath = '/webr/lap3'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap3')
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
        return self.root
        
class lap4Generator(JasperGenerator):
    def __init__(self):
        super(lap4Generator, self).__init__()
        self.reportname = get_rpath('Lap4.jrxml')
        self.xpath = '/webr/lap4'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap4')
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text     = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text  = row.wp_nm
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
        return self.root
        
class lap5Generator(JasperGenerator):
    def __init__(self):
        super(lap5Generator, self).__init__()
        self.reportname = get_rpath('Lap5.jrxml')
        self.xpath = '/webr/lap5'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap5')
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
        return self.root
        
class lap6Generator(JasperGenerator):
    def __init__(self):
        super(lap6Generator, self).__init__()
        self.reportname = get_rpath('Lap6.jrxml')
        self.xpath = '/webr/lap6'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap6')
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
        return self.root
        
class lap7Generator(JasperGenerator):
    def __init__(self):
        super(lap7Generator, self).__init__()
        self.reportname = get_rpath('Lap7.jrxml')
        self.xpath = '/webr/lap7'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        ttd=DBSession.query(Pegawai.kode.label('pg_kd'),
                             Pegawai.nama.label('pg_nm')
                     ).filter(Pegawai.user_id==u
                     ).first()
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap7')
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text     = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text  = row.wp_nm
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "bayar").text  = unicode(row.bayar)
            ET.SubElement(xml_greeting, "tgl").text    = unicode(row.tgl)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
            ET.SubElement(xml_greeting, "awal").text   = awal
            ET.SubElement(xml_greeting, "akhir").text  = akhir
            #ET.SubElement(xml_greeting, "pg_kd").text  = ttd.pg_kd
            #ET.SubElement(xml_greeting, "pg_nm").text  = ttd.pg_nm
        return self.root
        
class lap7benGenerator(JasperGenerator):
    def __init__(self):
        super(lap7benGenerator, self).__init__()
        self.reportname = get_rpath('Lap7bendahara.jrxml')
        self.xpath = '/webr/lap7ben'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        ttd=DBSession.query(Pegawai.kode.label('pg_kd'),
                            Pegawai.nama.label('pg_nm')
                     ).filter(Pegawai.user_id==u
                     ).first()
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap7ben')
            ET.SubElement(xml_greeting, "kd").text     = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text  = row.wp_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "bayar").text  = unicode(row.bayar)
            ET.SubElement(xml_greeting, "tgl").text    = unicode(row.tgl)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
            ET.SubElement(xml_greeting, "awal").text   = awal
            ET.SubElement(xml_greeting, "akhir").text  = akhir
            ET.SubElement(xml_greeting, "pg_kd").text  = ttd.pg_kd
            ET.SubElement(xml_greeting, "pg_nm").text  = ttd.pg_nm
            ET.SubElement(xml_greeting, "un_al").text  = unit_al
        return self.root
        
class lap8Generator(JasperGenerator):
    def __init__(self):
        super(lap8Generator, self).__init__()
        self.reportname = get_rpath('Lap8.jrxml')
        self.xpath = '/webr/lap8'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        ttd=DBSession.query(Pegawai.kode.label('pg_kd'),
                             Pegawai.nama.label('pg_nm')
                     ).filter(Pegawai.user_id==u
                     ).first()
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap8')
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text     = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text  = row.wp_nm
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
            ET.SubElement(xml_greeting, "awal").text   = awal
            ET.SubElement(xml_greeting, "akhir").text  = akhir
            #ET.SubElement(xml_greeting, "pg_kd").text  = ttd.pg_kd
            #ET.SubElement(xml_greeting, "pg_nm").text  = ttd.pg_nm
        return self.root
        
class lap8benGenerator(JasperGenerator):
    def __init__(self):
        super(lap8benGenerator, self).__init__()
        self.reportname = get_rpath('Lap8bendahara.jrxml')
        self.xpath = '/webr/lap8ben'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        ttd=DBSession.query(Pegawai.kode.label('pg_kd'),
                             Pegawai.nama.label('pg_nm')
                     ).filter(Pegawai.user_id==u
                     ).first()
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap8ben')
            ET.SubElement(xml_greeting, "kd").text     = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text  = row.wp_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
            ET.SubElement(xml_greeting, "awal").text   = awal
            ET.SubElement(xml_greeting, "akhir").text  = akhir
            ET.SubElement(xml_greeting, "pg_kd").text  = ttd.pg_kd
            ET.SubElement(xml_greeting, "pg_nm").text  = ttd.pg_nm
            ET.SubElement(xml_greeting, "un_al").text  = unit_al
        return self.root
        
class lap9Generator(JasperGenerator):
    def __init__(self):
        super(lap9Generator, self).__init__()
        self.reportname = get_rpath('Lap9.jrxml')
        self.xpath = '/webr/lap9'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        ttd=DBSession.query(Pegawai.kode.label('pg_kd'),
                             Pegawai.nama.label('pg_nm')
                     ).filter(Pegawai.user_id==u
                     ).first()
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap9')
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text     = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text  = row.wp_nm
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
            ET.SubElement(xml_greeting, "awal").text   = awal
            ET.SubElement(xml_greeting, "akhir").text  = akhir
            #ET.SubElement(xml_greeting, "pg_kd").text  = ttd.pg_kd
            #ET.SubElement(xml_greeting, "pg_nm").text  = ttd.pg_nm
        return self.root
        
class lap9benGenerator(JasperGenerator):
    def __init__(self):
        super(lap9benGenerator, self).__init__()
        self.reportname = get_rpath('Lap9bendahara.jrxml')
        self.xpath = '/webr/lap9ben'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        ttd=DBSession.query(Pegawai.kode.label('pg_kd'),
                             Pegawai.nama.label('pg_nm')
                     ).filter(Pegawai.user_id==u
                     ).first()
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap9ben')
            ET.SubElement(xml_greeting, "kd").text     = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text  = row.wp_nm
            ET.SubElement(xml_greeting, "rek_id").text = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text = row.rek_nm
            ET.SubElement(xml_greeting, "un_id").text  = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text  = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text  = row.un_nm
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
            ET.SubElement(xml_greeting, "awal").text   = awal
            ET.SubElement(xml_greeting, "akhir").text  = akhir
            ET.SubElement(xml_greeting, "un_al").text  = unit_al
            ET.SubElement(xml_greeting, "pg_kd").text  = ttd.pg_kd
            ET.SubElement(xml_greeting, "pg_nm").text  = ttd.pg_nm
        return self.root
        
## iWan mampir
class lap10Generator(JasperGenerator):
    def __init__(self):
        super(lap10Generator, self).__init__()
        self.reportname = get_rpath('Lap10.jrxml')
        self.xpath = '/webr/lap10'
        self.root = ET.Element('webr') 
 
    def generate_xml(self, tobegreeted):
        ttd=DBSession.query(Pegawai.kode.label('pg_kd'),
                             Pegawai.nama.label('pg_nm')
                     ).filter(Pegawai.user_id==u
                     ).first()
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap10')
            ET.SubElement(xml_greeting, "un_id").text        = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text        = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text        = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text       = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text       = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text       = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text           = row.kd
                        
            ET.SubElement(xml_greeting, "invoice_kode").text = row.invoice_kode
            ET.SubElement(xml_greeting, "tgl_terima").text   = unicode(row.tgl_terima)
            ET.SubElement(xml_greeting, "periode_1").text    = unicode(row.periode_1)
            ET.SubElement(xml_greeting, "periode_2").text    = unicode(row.periode_2)
            ET.SubElement(xml_greeting, "jatuh_tempo").text  = unicode(row.jatuh_tempo)
            ET.SubElement(xml_greeting, "wp_nm").text        = row.wp_nm
            ET.SubElement(xml_greeting, "op_nm").text        = row.op_nm
                                                             
            ET.SubElement(xml_greeting, "dasar").text        = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text        = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text        = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text        = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text       = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text         = logo_pemda
            ET.SubElement(xml_greeting, "unit_kd").text      = unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text      = unit_nm
            ET.SubElement(xml_greeting, "awal").text         = awal
            ET.SubElement(xml_greeting, "akhir").text        = akhir
            ET.SubElement(xml_greeting, "un_al").text        = unit_al
            ET.SubElement(xml_greeting, "pg_kd").text        = ttd.pg_kd
            ET.SubElement(xml_greeting, "pg_nm").text        = ttd.pg_nm
        return self.root
        
class lap10budGenerator(JasperGenerator):
    def __init__(self):
        super(lap10budGenerator, self).__init__()
        self.reportname = get_rpath('Lap10bud.jrxml')
        self.xpath = '/webr/lap10bud'
        self.root = ET.Element('webr') 
 
    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap10bud')
            ET.SubElement(xml_greeting, "un_id").text        = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text        = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text        = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text       = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text       = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text       = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text           = row.kd
                        
            ET.SubElement(xml_greeting, "invoice_kode").text = row.invoice_kode
            ET.SubElement(xml_greeting, "tgl_terima").text   = unicode(row.tgl_terima)
            ET.SubElement(xml_greeting, "periode_1").text    = unicode(row.periode_1)
            ET.SubElement(xml_greeting, "periode_2").text    = unicode(row.periode_2)
            ET.SubElement(xml_greeting, "jatuh_tempo").text  = unicode(row.jatuh_tempo)
            ET.SubElement(xml_greeting, "wp_nm").text        = row.wp_nm
            ET.SubElement(xml_greeting, "op_nm").text        = row.op_nm
                                                             
            ET.SubElement(xml_greeting, "dasar").text        = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text        = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text        = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text        = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text       = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text         = logo_pemda
            ET.SubElement(xml_greeting, "awal").text         = awal
            ET.SubElement(xml_greeting, "akhir").text        = akhir
        return self.root

class lap11Generator(JasperGenerator):
    def __init__(self):
        super(lap11Generator, self).__init__()
        self.reportname = get_rpath('Lap11.jrxml')
        self.xpath = '/webr/lap11'
        self.root = ET.Element('webr') 
 
    def generate_xml(self, tobegreeted):
        ttd=DBSession.query(Pegawai.kode.label('pg_kd'),
                             Pegawai.nama.label('pg_nm')
                     ).filter(Pegawai.user_id==u
                     ).first()
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap11')
            ET.SubElement(xml_greeting, "un_id").text   = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text   = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text   = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text  = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text  = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text  = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text      = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text   = row.wp_nm
            ET.SubElement(xml_greeting, "dasar").text   = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text   = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text   = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text   = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text  = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text    = logo_pemda
            ET.SubElement(xml_greeting, "unit_kd").text = unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = unit_nm
            ET.SubElement(xml_greeting, "awal").text    = awal
            ET.SubElement(xml_greeting, "akhir").text   = akhir
            ET.SubElement(xml_greeting, "un_al").text   = unit_al
            ET.SubElement(xml_greeting, "pg_kd").text   = ttd.pg_kd
            ET.SubElement(xml_greeting, "pg_nm").text   = ttd.pg_nm
        return self.root

class lap11budGenerator(JasperGenerator):
    def __init__(self):
        super(lap11budGenerator, self).__init__()
        self.reportname = get_rpath('Lap11bud.jrxml')
        self.xpath = '/webr/lap11bud'
        self.root = ET.Element('webr') 
 
    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap11bud')
            ET.SubElement(xml_greeting, "un_id").text   = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text   = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text   = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text  = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text  = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text  = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text      = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text   = row.wp_nm
            ET.SubElement(xml_greeting, "dasar").text   = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text   = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text   = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text   = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text  = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text    = logo_pemda
            ET.SubElement(xml_greeting, "awal").text    = awal
            ET.SubElement(xml_greeting, "akhir").text   = akhir
        return self.root

class lap12Generator(JasperGenerator):
    def __init__(self):
        super(lap12Generator, self).__init__()
        self.reportname = get_rpath('Lap12.jrxml')
        self.xpath = '/webr/lap12'
        self.root = ET.Element('webr') 
 
    def generate_xml(self, tobegreeted):
        ttd=DBSession.query(Pegawai.kode.label('pg_kd'),
                             Pegawai.nama.label('pg_nm')
                     ).filter(Pegawai.user_id==u
                     ).first()
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap12')
            ET.SubElement(xml_greeting, "un_id").text   = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text   = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text   = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text  = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text  = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text  = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text      = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text   = row.wp_nm
            ET.SubElement(xml_greeting, "dasar").text   = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text   = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text   = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text   = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text  = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text    = logo_pemda
            ET.SubElement(xml_greeting, "unit_kd").text = unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text = unit_nm
            ET.SubElement(xml_greeting, "awal").text    = awal
            ET.SubElement(xml_greeting, "akhir").text   = akhir
            ET.SubElement(xml_greeting, "un_al").text   = unit_al
            ET.SubElement(xml_greeting, "pg_kd").text   = ttd.pg_kd
            ET.SubElement(xml_greeting, "pg_nm").text   = ttd.pg_nm
        return self.root

class lap12budGenerator(JasperGenerator):
    def __init__(self):
        super(lap12budGenerator, self).__init__()
        self.reportname = get_rpath('Lap12bud.jrxml')
        self.xpath = '/webr/lap12bud'
        self.root = ET.Element('webr') 
 
    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'lap12bud')
            ET.SubElement(xml_greeting, "un_id").text   = unicode(row.un_id)
            ET.SubElement(xml_greeting, "un_kd").text   = row.un_kd
            ET.SubElement(xml_greeting, "un_nm").text   = row.un_nm
            ET.SubElement(xml_greeting, "rek_id").text  = unicode(row.rek_id)
            ET.SubElement(xml_greeting, "rek_kd").text  = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text  = row.rek_nm
            ET.SubElement(xml_greeting, "kd").text      = row.kd
            ET.SubElement(xml_greeting, "wp_nm").text   = row.wp_nm
            ET.SubElement(xml_greeting, "dasar").text   = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text   = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text   = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text   = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text  = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text    = logo_pemda
            ET.SubElement(xml_greeting, "awal").text    = awal
            ET.SubElement(xml_greeting, "akhir").text   = akhir
        return self.root
        
## ----------------------------- End Laporan ----------------------------------------##        

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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
        return self.root

#JnsPajak
class semua_sektorGenerator(JasperGenerator):
    def __init__(self):
        super(semua_sektorGenerator, self).__init__()
        self.reportname = get_rpath('semua_sektor.jrxml')
        self.xpath = '/webr/semua_sektor'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'semua_sektor')
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "nama").text = row.nama
            ET.SubElement(xml_greeting, "status").text = row.status 
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
        return self.root
        
#ARINVOICE FAST PAY
class r101Generator(JasperGenerator):
    def __init__(self):
        super(r101Generator, self).__init__()
        self.reportname = get_rpath('epayment.jrxml')
        self.xpath = '/webr/epayment'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'epayment')
            ET.SubElement(xml_greeting, "kd_bayar").text  = row.kode
            ET.SubElement(xml_greeting, "wp_nama").text   = row.wp_nama
            ET.SubElement(xml_greeting, "op_nama").text   = row.op_nama
            ET.SubElement(xml_greeting, "unit_kd").text   = row.unit_kode
            ET.SubElement(xml_greeting, "unit_nm").text   = row.unit_nama
            ET.SubElement(xml_greeting, "rek_kd").text    = row.rek_kode
            ET.SubElement(xml_greeting, "rek_nm").text    = row.rek_nama
            ET.SubElement(xml_greeting, "periode1").text  = unicode(row.periode_1)
            ET.SubElement(xml_greeting, "periode2").text  = unicode(row.periode_2)
            ET.SubElement(xml_greeting, "tgl_tetap").text = unicode(row.tgl_tetap)
            ET.SubElement(xml_greeting, "tgl_jt_tempo").text = unicode(row.jatuh_tempo)
            ET.SubElement(xml_greeting, "dasar").text  = unicode(row.dasar)
            ET.SubElement(xml_greeting, "tarif").text  = unicode(row.tarif)
            ET.SubElement(xml_greeting, "pokok").text  = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text  = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text  = unicode(row.bunga)
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "logo").text   = logo_pemda
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
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "wp_kode").text = row.wp_kode
            ET.SubElement(xml_greeting, "wp_nama").text = row.wp_nama
            ET.SubElement(xml_greeting, "op_kode").text = row.op_kode
            ET.SubElement(xml_greeting, "op_nama").text = row.op_nama
            ET.SubElement(xml_greeting, "rek_nama").text = row.rek_nama
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.bayar)
            ET.SubElement(xml_greeting, "tgl_bayar").text = unicode(row.tgl_bayar)
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
        return self.root
class r200frmGenerator(JasperGenerator):
    def __init__(self):
        super(r200frmGenerator, self).__init__()
        self.reportname = get_rpath('R2000FRM.jrxml')
        self.xpath = '/webr/arsspdfrm'
        self.root = ET.Element('webr') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'arsspdfrm')
            ET.SubElement(xml_greeting, "id").text = unicode(row.id)
            ET.SubElement(xml_greeting, "kode").text = row.kode
            ET.SubElement(xml_greeting, "wp_kode").text = row.wp_kode
            ET.SubElement(xml_greeting, "wp_nama").text = row.wp_nama
            ET.SubElement(xml_greeting, "op_kode").text = row.op_kode
            ET.SubElement(xml_greeting, "op_nama").text = row.op_nama
            ET.SubElement(xml_greeting, "rek_kode").text = row.rek_kode
            ET.SubElement(xml_greeting, "rek_nama").text = row.rek_nama
            ET.SubElement(xml_greeting, "unit_kode").text = row.unit_kode
            ET.SubElement(xml_greeting, "unit_nama").text = row.unit_nama 
            ET.SubElement(xml_greeting, "tarif").text = unicode(row.tarif)
            ET.SubElement(xml_greeting, "dasar").text = unicode(row.dasar)
            ET.SubElement(xml_greeting, "pokok").text = unicode(row.pokok)
            ET.SubElement(xml_greeting, "denda").text = unicode(row.denda)
            ET.SubElement(xml_greeting, "bunga").text = unicode(row.bunga) 
            ET.SubElement(xml_greeting, "jumlah").text = unicode(row.bayar)
            ET.SubElement(xml_greeting, "tgl_bayar").text = unicode(row.tgl_bayar)
            ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
            ET.SubElement(xml_greeting, "id").text         = unicode(row.id)
            ET.SubElement(xml_greeting, "kode").text       = row.kode
            ET.SubElement(xml_greeting, "nama").text       = row.nama
            ET.SubElement(xml_greeting, "tgl_sts").text    = unicode(row.tgl_sts)
            ET.SubElement(xml_greeting, "unit_kd").text    = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text    = row.unit_nm
            ET.SubElement(xml_greeting, "unit_al").text    = row.unit_al
            ET.SubElement(xml_greeting, "rek_kd").text     = row.rek_kd
            ET.SubElement(xml_greeting, "rek_nm").text     = row.rek_nm
            ET.SubElement(xml_greeting, "jumlah").text     = unicode(row.jumlah)
            ET.SubElement(xml_greeting, "jumlah_sts").text = unicode(row.jumlah_sts)
            # ET.SubElement(xml_greeting, "jumlah").text = row.jumlah
            ET.SubElement(xml_greeting, "no_bayar").text   = row.no_bayar
            ET.SubElement(xml_greeting, "logo").text       = logo_pemda
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
        ET.SubElement(xml_greeting, "logo").text = logo_pemda
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
