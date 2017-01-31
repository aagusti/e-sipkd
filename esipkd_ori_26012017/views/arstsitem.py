import sys
import re
from email.utils import parseaddr
from sqlalchemy import not_, func, or_
from datetime import datetime
from time import gmtime, strftime
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
from ..tools import _DTnumberformat, _DTstrftime
from ..models import DBSession
from ..models.isipkd import(
      Unit,
      Wilayah,
      Pajak,
      Rekening,
      ARSspd,
      ARSts,
      ARStsItem,
      ARInvoice,
      Unit
      )

from datatables import (
    ColumnDT, DataTables)

SESS_ADD_FAILED = 'Gagal tambah Pembayaran'
SESS_EDIT_FAILED = 'Gagal edit Pembayaran'
from daftar import (STATUS, deferred_status,
                    hitung_bunga
                    )
########                    
# List #
########    
    

#######    
# Add #
#######
           
def route_list(request):
    return HTTPFound(location=request.route_url('arsts-edit', id = request.session['sts_id']))
    
def session_failed(request, session_name):
    try:
        session_name.set_appstruct(request.session[SESS_ADD_FAILED])
    except:
        pass
    r = dict(form=session_name) #request.session[session_name])
    del request.session[SESS_ADD_FAILED]
    return r

def query_invoice(kode):
    return DBSession.query(ARInvoice).\
       filter(ARInvoice.kode==kode,
              ARInvoice.status_bayar==0).first()

def query_invoice_id(id):
    return DBSession.query(ARInvoice).\
       filter(ARInvoice.id==id).first()

                      
@view_config(route_name='arstsitem-add', renderer='templates/arstsitem/add.pt',
             permission='add')
def view_add(request):
    #Nambahin kondisi balik ke sts
    if 'balik' == request.matchdict['id']:
        return route_list(request)
    elif 'all' == request.matchdict['id']:
        rows = DBSession.query(ARInvoice).\
                        filter(ARInvoice.unit_id==request.session['unit_id'],
                               ARInvoice.is_sts==0,
                               or_(ARInvoice.is_tbp==1,
                                   ARInvoice.is_sspd==1)).all()
    else:
        rows = DBSession.query(ARInvoice).\
                        filter(ARInvoice.unit_id==request.session['unit_id'],
                               ARInvoice.id ==  request.matchdict['id'],
                               ARInvoice.is_sts==0,
                               or_(ARInvoice.is_tbp==1,
                                   ARInvoice.is_sspd==1)).all()
    for row in rows:
        items=ARStsItem()
        items.sts_id      = request.session['sts_id']
        items.invoice_id  = row.id
        items.kode        = row.kode
        items.rekening_id = row.rekening_id
        items.rek_kode    = row.rek_kode
        items.rek_nama    = row.rek_nama
        items.jumlah      = row.jumlah       #row.bayar-row.bunga
        DBSession.add(items)
        DBSession.flush()
        #print 'A'
        #if row.bunga>0:
        #    items=ARStsItem()
        #    items.sts_id=request.session['sts_id']
        #    items.sspd_id=row.id
        #    items.rekening_id= row.arinvoices.objek_pajaks.denda_rekening_id
        #    items.jumlah=row.bunga
        #    DBSession.add(items)
        #    DBSession.flush()
        if row.is_sspd!=0:
            sspd = DBSession.query(ARSspd).filter(ARSspd.arinvoice_id==row.id,ARSspd.bayar!=0).first()
            sspd.posted=1
            DBSession.add(sspd)
            DBSession.flush()
            
        row.is_sts = 1
        DBSession.add(row)
        DBSession.flush()
        
    jumlah = DBSession.query(func.sum(ARStsItem.jumlah)).\
                       filter(ARStsItem.sts_id==request.session['sts_id']).scalar()
    if jumlah:
        rows = DBSession.query(ARSts).filter(ARSts.id==request.session['sts_id']).first()
        rows.jumlah=jumlah
        DBSession.add(rows)
        DBSession.flush()
    return route_list(request)
    

########
# Edit #
########
def query_id(request):
    return DBSession.query(ARStsItem).\
                     filter(ARStsItem.sts_id     == request.session['sts_id'],
                            ARStsItem.invoice_id == request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Invoice ID %s tidak ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

##########
# Delete #
##########    
@view_config(route_name='arstsitem-delete', renderer='templates/arstsitem/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    msg = 'Invoice ID %d %s sudah dihapus.' % (row.sts_id, row.invoice_id)

    ### ARStsItem
    jumlah = DBSession.query(ARStsItem.jumlah).\
                       filter(ARStsItem.invoice_id==row.invoice_id).scalar()
    print'------------------Jumlah STS Item------------------',jumlah
    ### ARSts
    jumlah1 = DBSession.query(ARSts.jumlah).\
                       filter(ARSts.id==request.session['sts_id']).scalar()
    print'------------------Jumlah STS-----------------------',jumlah1
    if jumlah:
        hasil = jumlah1-jumlah
        rows = DBSession.query(ARSts).filter(ARSts.id==request.session['sts_id']).first()
        rows.jumlah=hasil
        DBSession.add(rows)
        DBSession.flush()

    #q.delete()
    q= DBSession.query(ARStsItem).\
                 filter(ARStsItem.invoice_id == request.matchdict['id']).delete()
    DBSession.flush()
    
    q = DBSession.query(ARInvoice).filter(ARInvoice.id==request.matchdict['id']).first()
    q.is_sts = 0
    if q.is_sspd!=0:
        sspd = DBSession.query(ARSspd).filter(ARSspd.arinvoice_id==q.id,ARSspd.bayar!=0).first()
        sspd.posted=0
        DBSession.add(sspd)
        DBSession.flush()
    DBSession.add(q)
    DBSession.flush()
    
    
    
    request.session.flash(msg) 
    return route_list(request)
                 
#############
# SSPD LIST #
#############    
def query_sts_id(request):
    return DBSession.query(ARSts).filter_by(id=request.matchdict['id'])
    
@view_config(route_name='arstsitem-list', renderer='templates/arstsitem/list.pt',
             permission='add')
def view_list(request):
    q = query_sts_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    request.session['unit_id'] = row.unit_id
    request.session['sts_id']  = row.id
    #TODO validate user_unit
    
    """if request.POST:
        if 'delete' in request.POST:
            msg = 'Penerimaan ID %d %s sudah dihapus.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    """
    return dict(row={})
        
##########
# Action #
##########    
@view_config(route_name='arstsitem-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    if url_dict['act']=='invoice':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('wp_nama'))
        columns.append(ColumnDT('op_kode'))
        columns.append(ColumnDT('op_nama'))
        #columns.append(ColumnDT('rek_nama'))
        columns.append(ColumnDT('tgl_tetap', filter=_DTstrftime))
        columns.append(ColumnDT('jumlah',    filter=_DTnumberformat))
        columns.append(ColumnDT('is_sspd'))
        columns.append(ColumnDT('is_tbp'))
        columns.append(ColumnDT('status_bayar'))
        
        query = DBSession.query(ARInvoice).\
                          filter(ARInvoice.is_sts==0,
                                 or_(ARInvoice.is_tbp==1,
                                     ARInvoice.is_sspd==1),
                                 ARInvoice.unit_id==request.session['unit_id']).\
                          order_by(ARInvoice.tgl_tetap,ARInvoice.kode)
                          
        rowTable = DataTables(req, ARInvoice, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='grid':
        #Nambahin param sts_id untuk percobaan sementara, karena session sts_id tidak jalan
        sts_id = 'sts_id' in params and params['sts_id'] or 0
        print'----------------------ID STS-------------------------',sts_id 
        columns = []
        columns.append(ColumnDT('invoice_id'))
        columns.append(ColumnDT('sts_id'))
        columns.append(ColumnDT('rekening_id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('rek_kode'))
        columns.append(ColumnDT('rek_nama'))
        columns.append(ColumnDT('jumlah', filter=_DTnumberformat))
        
        query = DBSession.query(ARStsItem).\
                          filter(ARStsItem.sts_id==sts_id).\
                          order_by(ARStsItem.rek_kode,ARStsItem.jumlah)#request.session['sts_id'])
                          
        rowTable = DataTables(req, ARStsItem, query, columns)
        return rowTable.output_result()
