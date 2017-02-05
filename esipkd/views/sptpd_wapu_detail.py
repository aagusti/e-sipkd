import sys
import re
from email.utils import parseaddr
from sqlalchemy import not_, func, cast, BigInteger, String
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from ..models import DBSession
from ..models.isipkd import(
      ObjekPajak,
      SubjekPajak,
      Unit,
      UserUnit,
      Wilayah,
      Pajak,
      Rekening,
      ARInvoice,
      InvoiceDet,
      Sptpd,
      User,
      Sektor,
      Produk,
      Peruntukan
      )
from ..models.__init__ import(
      UserGroup
      )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from time import gmtime, strftime
from ..tools import create_now, _DTnumberformat

SESS_ADD_FAILED = 'Tambah sptpd-invoice-detail gagal'
SESS_EDIT_FAILED = 'Edit sptpd-invoice-detail gagal'

##########                    
# Action #
##########    
@view_config(route_name='sptpd-invoice-detail-act', renderer='json',
             permission='read')
def view_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        # defining columns
        sptpd_id = url_dict['sptpd_id'].isdigit() and url_dict['sptpd_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))                # 0
        columns.append(ColumnDT('sptpd_id'))          # 1
        columns.append(ColumnDT('produk_id'))         # 2
        columns.append(ColumnDT('peruntukan_id'))     # 3
        columns.append(ColumnDT('produks.kode'))      # 4
        columns.append(ColumnDT('sektor_nm'))         # 5
        columns.append(ColumnDT('wilayah_nm'))        # 6
        columns.append(ColumnDT('nama'))              # 7
        columns.append(ColumnDT('peruntukans.nama'))  # 8
        columns.append(ColumnDT('produks.nama'))      # 9
        columns.append(ColumnDT('volume',     filter=_DTnumberformat)) # 10
        columns.append(ColumnDT('harga_jual', filter=_DTnumberformat)) # 11
        columns.append(ColumnDT('dpp',        filter=_DTnumberformat)) # 12
        columns.append(ColumnDT('tarif')) #,      filter=_DTnumberformat)) # 13
        columns.append(ColumnDT('total_pajak',filter=_DTnumberformat)) # 14
        columns.append(ColumnDT('alamat'))            # 15
        columns.append(ColumnDT('keterangan'))        # 16
        columns.append(ColumnDT('wilayah_id'))        # 17
        
        query = DBSession.query(InvoiceDet).\
                          join(Sptpd,Produk,Peruntukan).\
                          filter(InvoiceDet.sptpd_id==sptpd_id,
                                 InvoiceDet.produk_id==Produk.id,
                                 InvoiceDet.peruntukan_id==Peruntukan.id,
                                 InvoiceDet.wilayah_id==Wilayah.id
                          )
                          
        rowTable = DataTables(req, InvoiceDet, query, columns)
        return rowTable.output_result()

#######    
# Add #
#######
@view_config(route_name='sptpd-invoice-detail-add', renderer='json',
             permission='add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    sptpd_id = 'sptpd_id' in url_dict and url_dict['sptpd_id'] or 0
    controls = dict(request.POST.items())
    
    invoice_item_id = 'invoice_item_id' in controls and controls['invoice_item_id'] or 0
    produk_id       = 'produk_id'       in controls and controls['produk_id']       or 0
    wilayah_id      = 'wilayah_id'      in controls and controls['wilayah_id']      or 0
    peruntukan_id   = 'peruntukan_id'   in controls and controls['peruntukan_id']   or 0
    
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    invoice = DBSession.query(Sptpd)\
                          .filter(Sptpd.id==sptpd_id).first()
    if not invoice:
        return {"success": False, 'msg':'Tagihan SPTPD WAPU tidak ditemukan'}
    
    #Cek apakah produk sudah terpakai apa belum
    produk = DBSession.query(InvoiceDet)\
                      .filter(InvoiceDet.sptpd_id == sptpd_id,
                              InvoiceDet.produk_id == produk_id).first()
    if produk:
        return {"success": False, 'msg':'Item produk tidak boleh sama.'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if invoice_item_id:
        row = DBSession.query(InvoiceDet)\
                  .join(Sptpd)\
                  .filter(InvoiceDet.id==invoice_item_id,
                          InvoiceDet.sptpd_id==sptpd_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = InvoiceDet()
            
    row.sptpd_id      = sptpd_id
    row.produk_id       = controls['produk_id']
    row.peruntukan_id   = controls['peruntukan_id']
    row.p_kode          = controls['p_kode']
    row.produk_nm       = controls['produk_nm']
    row.peruntukan_nm   = controls['peruntukan_nm']
    row.wilayah_id      = controls['wilayah_id']
    row.wilayah_nm      = controls['wilayah_nm']
    row.volume          = controls['volume'].replace('.','')
    row.harga_jual      = controls['harga_jual'].replace('.','')
    
    a = float(controls['volume'].replace('.',''))*float(controls['harga_jual'].replace('.',''))
    row.dpp = int(float(a))
    
    row.nama            = controls['p_nama']
    row.alamat          = controls['p_almt']
    row.keterangan      = controls['p_ket']
    
    #inv = DBSession.query(ARInvoice.subjek_pajak_id.label('sp'),
    #                      ARInvoice.objek_pajak_id.label('op'),
    #                      ObjekPajak.pajak_id.label('pid'),
    #                      ObjekPajak.wilayah_id.label('wid'),
    #                      Pajak.tarif.label('ptr'),
    #                      Wilayah.nama.label('wnm'),
    #                      Sektor.nama.label('snm'),
    #              ).join(ObjekPajak, SubjekPajak
    #              ).filter(ARInvoice.id == invoice_id,
    #                       ARInvoice.subjek_pajak_id == SubjekPajak.id,
    #                       ARInvoice.objek_pajak_id == ObjekPajak.id,
    #              ).outerjoin(Wilayah, ObjekPajak.wilayah_id == Wilayah.id
    #              ).outerjoin(Pajak, ObjekPajak.pajak_id == Pajak.id
    #              ).outerjoin(Sektor, Pajak.sektor_id == Sektor.id
    #              ).first()
                              
    #row.subjek_pajak_id = inv.sp
    #row.objek_pajak_id  = inv.op
    #row.pajak_id        = inv.pid
    row.sektor_nm       = controls['sektor_nm']
    row.tarif           = controls['tarif']
    
    b = float(row.dpp)*float(row.tarif/100)
    row.total_pajak     = int(float(b))
    
    DBSession.add(row)
    DBSession.flush()
    
    x = row.invoice_id
    #------------------------Dasar Invoice-------------------#
    d = DBSession.query(func.sum(InvoiceDet.dpp)).filter(InvoiceDet.sptpd_id == x).first()
    d1 = "%s" % d
    if d1 == 'None':
        d1 = 0
        das = d1
    else:
        das = d1
    #------------------------Pokok Invoice-------------------#   
    p = DBSession.query(func.sum(InvoiceDet.total_pajak)).filter(InvoiceDet.sptpd_id == x).first()
    p1 = "%s" % p
    if p1 == 'None':
        p1 = 0
        pok = p1
    else:
        pok = p1
        
    #------------------------Denda Invoice-------------------#   
    #de = DBSession.query(ARInvoice.denda).filter(ARInvoice.id == x).first()
    #de1 = "%s" % de
    #------------------------Bunga Invoice-------------------#   
    #b = DBSession.query(ARInvoice.bunga).filter(ARInvoice.id == x).first()
    #bu1 = "%s" % b
    #------------------------Jumlah Invoice------------------#
    ju = float(p1)
    juu = int(float(ju))
    ju1 = "%s" % juu
    if ju1 == 'None':
        ju1 = 0
        jum = ju1
    else:
        jum = ju1
    #------------------------Tarif Invoice-------------------#
    t = float(d1)/float(ju1)
    ta1 = "%s" % t
    if ta1 == 'None':
        ta1 = 0
        tar = ta1[0:4]
    else:
        tar = ta1[0:4]
        
    print'****--Sum DPP---------**** ',das
    print'****--Sum Total-------**** ',pok
    print'****--Denda-----------**** ',de1
    print'****--Bunga-----------**** ',bu1
    print'****--Jumlah----------**** ',jum
    print'****--Tarif-----------**** ',tar
    print'****--Tarif Awal------**** ',ta1
    
    return {"success": True, 'id': row.id, "msg":'Success tambah item produk.', 'das':das, 'pok':pok, 'jum':jum, 'tar':tar}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('sptpd-invoice-detail'))
    
def query_id(request):
    return DBSession.query(InvoiceDet).filter(InvoiceDet.id==request.matchdict['id'],
                                              InvoiceDet.sptpd_id==request.matchdict['sptpd_id'])
    
def id_not_found(request):    
    msg = 'SPTPD WAPU ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
   
##########
# Delete #
##########  
def save_request1(self, row1=None):
    row1 = Sptpd()
    return row1
        
@view_config(route_name='sptpd-invoice-detail-delete', renderer='json',
             permission='delete')
def view_delete(request):
    q   = query_id(request)
    row = q.first()
    x   = row.sptpd_id
    z   = row.tarif
    
    if not row:
        return {'success':False, "msg":self.id_not_found()}

    msg = 'Data sudah dihapus'
    query_id(request).delete()
    DBSession.flush()   
    
    #------------------------Dasar Invoice-------------------#
    d = DBSession.query(func.sum(InvoiceDet.dpp)).filter(InvoiceDet.sptpd_id == x).first()
    d1 = "%s" % d
    if d1 == 'None':
        d1 = 0
        das = d1
    else:
        das = d1
    #------------------------Pokok Invoice-------------------#   
    p = DBSession.query(func.sum(InvoiceDet.total_pajak)).filter(InvoiceDet.sptpd_id == x).first()
    p1 = "%s" % p
    if p1 == 'None':
        p1 = 0
        pok = p1
    else:
        pok = p1
        
    ju = float(p1) 
    juu = int(float(ju))
    ju1 = "%s" % juu
    if ju1 == 'None':
        ju1 = 0
        jum = ju1
    else:
        jum = ju1
    
    print'****--Sum DPP---------**** ',das
    print'****--Sum Total-------**** ',pok
    print'****--Jumlah----------**** ',jum
    
    row1 = DBSession.query(Sptpd).filter(Sptpd.id==x).first()   
    row1.jumlah = jum
    save_request1(row1) 
    #return route_list(request)
    #return HTTPFound(location=request.route_url('sptpd-wapu-edit',
    #                 id=x))
    return {'success':True, "msg":msg, 'das':das, 'pok':pok, 'jum':jum, 'tar':z}
    