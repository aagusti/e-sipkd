import sys
import re
from email.utils import parseaddr
from sqlalchemy import not_, func, desc
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
      ObjekPajak,
      SubjekPajak,
      Unit,
      Wilayah,
      Pajak,
      Rekening,
      ARSspd,
      ARInvoice,
      Unit,
      UserUnit
      )
from ..models.__init__ import(
      UserGroup
      )
from ..security import group_in
from datatables import (
    ColumnDT, DataTables)

SESS_ADD_FAILED = 'Gagal tambah Pembayaran'
SESS_EDIT_FAILED = 'Gagal edit Pembayaran'
from daftar import (STATUS, deferred_status,
                    daftar_subjekpajak, deferred_subjekpajak,
                    daftar_objekpajak, deferred_objekpajak,
                    daftar_wilayah, deferred_wilayah,
                    daftar_unit, deferred_unit,
                    daftar_pajak, deferred_pajak,
                    hitung_bunga
                    )
########                    
# List #
########    
@view_config(route_name='arsspd', renderer='templates/arsspd/list.pt',
             permission='read')
def view_list(request):
    awal  = 'awal'  in request.GET and request.GET['awal']  or datetime.now().strftime('%Y-%m-%d')
    akhir = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')
    return dict(rows={"awal":awal, "akhir":akhir})
    

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode sspd %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Uraian  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(ARSspd).filter_by(id=uid)
        r = q.first()
    else:
        r = None
            
class AddSchema(colander.Schema):
    moneywidget = widget.MoneyInputWidget(
            size=20, options={'allowZero':True,
                              'precision':0
                              })
    kode   = colander.SchemaNode(
                    colander.String(),
                    title="Kode Bayar",
                    widget = widget.TextInputWidget(
                              mask = '9999-9.99.99-999999',
                              mask_placeholder = '#',
                              )
                    )
                    
    arinvoice_id = colander.SchemaNode(
                    colander.Integer(),
                    oid = "arinvoice_id",
                    widget=widget.HiddenWidget(readonly=True),
                    missing=colander.drop,
                    default=0
                    )
                    
    unit_nama = colander.SchemaNode(
                    colander.String(),
                    title="OPD",
                    #title="SKPD",
                    oid = "unit_nama",
                    missing=colander.drop
                    )
                    
    wp_nama = colander.SchemaNode(
                    colander.String(),
                    title="Subjek",
                    oid = "wp_nama",
                    missing=colander.drop,                    
                    )
                    
    rek_nama = colander.SchemaNode(
                    colander.String(),
                    title="Rekening",
                    oid = "rek_nama",
                    missing=colander.drop,                    
                    )
                    
    op_nama = colander.SchemaNode(
                    colander.String(),
                    title="Objek",
                    missing=colander.drop,
                    oid = "op_nama"
                    )
    bank_id = colander.SchemaNode(
                    colander.String(),
                    title="Bank",
                    oid = "bank_id",
                    missing=colander.drop,
                    )
    channel_id = colander.SchemaNode(
                    colander.String(),
                    oid = "channel_id",
                    missing=colander.drop
                    )
    ntb = colander.SchemaNode(
                    colander.String(),
                    title="NTB",
                    oid = "ntb",
                    missing=colander.drop,
                    )
    ntp = colander.SchemaNode(
                    colander.String(),
                    oid = "ntp",
                    missing=colander.drop
                    )

    periode_1 = colander.SchemaNode(
                    colander.String(),
                    title="Periode 1",
                    oid = "periode_1",
                    missing=colander.drop,
                    )
    periode_2 = colander.SchemaNode(
                    colander.String(),
                    title="Periode 2",
                    oid = "periode_2",
                    missing=colander.drop
                    )
    tgl_tetap = colander.SchemaNode(
                    colander.String(),
                    oid = "tgl_tetap",
                    )
    jatuh_tempo = colander.SchemaNode(
                    colander.String(),
                    oid = "jatuh_tempo",
                    missing=colander.drop,
                    )
    pokok = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "pokok",
                    missing=colander.drop,
                    )
    denda = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "denda",
                    missing=colander.drop,
                    )
    bunga_awal = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    oid = "bunga_awal",
                    widget = moneywidget,
                    missing=colander.drop,
                    )
                    
    jumlah = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "jumlah",
                    missing=colander.drop,
                    )
                    
    bunga = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "bunga",
                    missing=colander.drop,
                    )
    bayar = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "bayar",
                    missing=colander.drop,
                    )
    tgl_bayar = colander.SchemaNode(
                    colander.Date(),
                    widget = widget.DateInputWidget(),
                    missing=colander.drop
                    )
                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True)
            )
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS,
                         daftar_subjekpajak=daftar_subjekpajak(),
                         daftar_unit=daftar_unit(),
                         daftar_objekpajak=daftar_objekpajak(),
                         )
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    if not row:
        row = ARSspd()
        #row.create_date = datetime.now()
        #row.create_uid  = request.user.id
    row.from_dict(values)
    #row.update_date = datetime.now()
    #row.update_uid  = request.user.id
    row.bunga  = re.sub("[^0-9]", "", row.bunga)
    row.bayar  = re.sub("[^0-9]", "", row.bayar)
    
    if not row.tahun_id:
        row.tahun_id = datetime.now().strftime('%Y')
    if not row.pembayaran_ke:
        invoice_no = DBSession.query(func.count(ARSspd.arinvoice_id)).\
                               filter(ARSspd.tahun_id==row.tahun_id,
                                      ARSspd.arinvoice_id==row.arinvoice_id).scalar()
        print "--------- Invoice No ---------- ",invoice_no
        if not invoice_no:
            row.pembayaran_ke = 1
        else:
            row.pembayaran_ke = invoice_no+1
        
    DBSession.add(row)
    DBSession.flush()
    if int(row.bayar)>0:
        row.arinvoices.status_bayar=1
        row.arinvoices.is_sspd=1
    else:
        row.pembayaran_ke = row.pembayaran_ke
        row.arinvoices.status_bayar=0
        row.arinvoices.is_sspd=0
    DBSession.add(row)
    DBSession.flush()
    
    """inv = DBSession.query(ARInvoice).\
                filter(ARInvoice.id==row.arinvoice_id)
    if inv:
      if row.bayar>0:
          inv.status_bayar=1
      else:
          inv.status_bayar=0
      DBSession.add(inv)
      DBSession.flush()
    """
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, row)
    request.session.flash('Penerimaan sudah disimpan.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('arsspd'))
    
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
              ARInvoice.status_bayar==0,
              ARInvoice.is_sspd==0,
              #ARInvoice.is_tbp==0,
              ARInvoice.is_sts==0).first()

def query_invoice_id(id):
    return DBSession.query(ARInvoice).\
       filter(ARInvoice.id==id).first()
    
@view_config(route_name='arsspd-add', renderer='templates/arsspd/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'cari' in request.POST:
            values = dict(request.POST.items())
            kode = re.sub('[^0-9]',"", values['kode'])
            inv = query_invoice(kode)
            if inv:
              values = inv.to_dict()
              values['bunga_awal']=values['bunga']
              values['arinvoice_id']=values['id']
              values['bunga']=0
              pokok = inv.jumlah
              pay = DBSession.query(func.sum(ARSspd.bayar-ARSspd.bunga)).\
                 filter(ARSspd.arinvoice_id==inv.id).scalar()
              pokok = pokok - (pay or 0)
              denda = hitung_bunga(pokok, inv.jatuh_tempo)
              values['bunga'] = denda
              values['bayar'] = pokok+denda
              values['tgl_bayar'] = datetime.now()
            else:
              request.session.flash('Tagihan %s tidak ditemukan atau Tagihan tersebut hasil dari TBP.' % kode)  
            form.set_appstruct(values)
            return dict(form=form)
            
        elif 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, form) #SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ARSspd).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Penerimaan ID %s tidak ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='arsspd-edit', renderer='templates/arsspd/edit.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    if row.posted:
        request.session.flash('Data sudah diposting pada Menu STS.', 'error')
        return route_list(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('arsspd-edit',
                                  id=row.id))
            values = dict(controls)
            values['bunga']='0'
            values['bayar']='0'
            save_request(values, request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    inv = query_invoice_id(row.arinvoice_id)
    values = inv.to_dict()
    values['bunga_awal']=values['bunga']
    values.update(row.to_dict())
    values['bank_id']    = row and row.bank_id    or '' 
    values['channel_id'] = row and row.channel_id or ''
    values['ntb']        = row and row.ntb        or ''
    values['ntp']        = row and row.ntp        or ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='arsspd-delete', renderer='templates/arsspd/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Penerimaan ID %d %s sudah dihapus.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# Action #
##########    
@view_config(route_name='arsspd-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    user     = req.user
    u        = request.user.id
    awal     = 'awal'  in request.GET and request.GET['awal']  or datetime.now().strftime('%Y-%m-%d')
    akhir    = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('arinvoices.kode'))
        columns.append(ColumnDT('arinvoices.wp_nama'))
        columns.append(ColumnDT('arinvoices.op_kode'))
        columns.append(ColumnDT('arinvoices.op_nama'))
        columns.append(ColumnDT('arinvoices.rek_nama'))
        columns.append(ColumnDT('bayar',  filter=_DTnumberformat))
        columns.append(ColumnDT('tgl_bayar',  filter=_DTstrftime))
        columns.append(ColumnDT('posted'))
        
        query = DBSession.query(ARSspd).join(ARInvoice)\
                         .filter(ARSspd.tgl_bayar.between(awal,akhir))\
                         .order_by(desc(ARSspd.tgl_bayar))
        if group_in(request, 'bendahara'):
            x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            y = '%s' % x
            z = int(y) 
            print "-- Unit ID ------------- ",z 
            
            query = query.filter(ARInvoice.unit_id==z)
            
        rowTable = DataTables(req, ARSspd, query, columns)
        return rowTable.output_result()    

from ..reports.rml_report import open_rml_row, open_rml_pdf, pdf_response
def query_reg():
    return DBSession.query(ARSspd.bayar.label('a'), 
                           ARSspd.tgl_bayar.label('b'), 
                           ARInvoice.kode.label('c'), 
                           ARInvoice.wp_nama.label('d'),  
                           ARInvoice.op_kode.label('e'), 
                           ARInvoice.op_nama.label('f'),
                           ARInvoice.unit_nama.label('g'),
                   ).join(ARInvoice
                   ).order_by(ARSspd.tgl_bayar)
def query_cetak():
    return DBSession.query(ARSspd.bayar.label('a'), 
                           ARSspd.tgl_bayar.label('b'),
                           ARInvoice.wp_nama.label('c'), 
                           ARInvoice.wp_alamat_1.label('d'),
                           ARInvoice.rek_kode.label('e'), 
                           ARInvoice.rek_nama.label('f'), 
                           ARInvoice.denda.label('g'), 
                           ARInvoice.bunga.label('h'), 
                           ARInvoice.jumlah.label('i'),
                           ARInvoice.unit_nama.label('j'),
                   ).join(ARInvoice
                   ).order_by(ARSspd.tgl_bayar)
    
########                    
# CSV #
########          
@view_config(route_name='arsspd-csv', renderer='csv')
def view_csv(request):
    ses = request.session
    params = request.params
    url_dict = request.matchdict 
    u = request.user.id
    awal  = 'awal' in request.params and request.params['awal']\
            or datetime.now().strftime('%Y-%m-%d')
    akhir = 'akhir' in request.params and request.params['akhir']\
            or datetime.now().strftime('%Y-%m-%d')
    if url_dict['csv']=='reg' :
        query = query_reg()
        if group_in(request, 'bendahara'):
            x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            y = '%s' % x
            z = int(y) 
            print "-- Unit ID ------------- ",z 
            query = query.filter(ARInvoice.unit_id==z)
            
        row = query.filter(ARSspd.tgl_bayar.between(awal,akhir),
                           ARSspd.bayar!=0)#.first()
        print "-- ROW -- ",row
        header = 'Jumlah','Tgl. Bayar','No. Bayar','Penyetor','Objek','Uraian','OPD' #row.keys()
        rows = []
        for item in row.all():
            rows.append(list(item))

        # override attributes of response
        filename = 'Penerimaan_%s_sd_%s.csv' %(awal, akhir)
        request.response.content_disposition = 'attachment;filename=' + filename

    return {
      'header': header,
      'rows'  : rows,
    } 
        
##########
# PDF    #
##########    
@view_config(route_name='arsspd-pdf', permission='read')
def view_pdf(request):
    global awal,akhir,unit_nm,unit_al,unit_kd
    params   = request.params
    url_dict = request.matchdict
    u = request.user.id
    
    if group_in(request, 'bendahara'):
        unit_id = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
        unit_id = '%s' % unit_id
        unit_id = int(unit_id) 
        
        unit_kd = DBSession.query(Unit.kode).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
        unit_kd = '%s' % unit_kd
        
        unit_nm = DBSession.query(Unit.nama).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
        unit_nm = '%s' % unit_nm
        
        unit_al = DBSession.query(Unit.alamat).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
        unit_al = '%s' % unit_al
        
    awal  = 'awal' in request.params and request.params['awal']\
            or datetime.now().strftime('%Y-%m-%d')
    akhir = 'akhir' in request.params and request.params['akhir']\
            or datetime.now().strftime('%Y-%m-%d')
    id1   = 'id1' in request.params and request.params['id1']
    
    if url_dict['pdf']=='reg' :
        query = query_reg()
        if group_in(request, 'bendahara'):
            x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            y = '%s' % x
            z = int(y) 
            print "-- Unit ID ------------- ",z 
            query = query.filter(ARInvoice.unit_id==z)
            
        rml_row = open_rml_row('arsspd.row.rml')
        rows=[]
        for r in query.filter(ARSspd.tgl_bayar.between(awal,akhir),
                              ARSspd.bayar!=0).all():
            s = rml_row.format(byr=r.a, 
                               tgl=r.b.strftime('%d-%m-%Y'), 
                               kode=r.c, 
                               wp=r.d, 
                               rek_k=r.e, 
                               rek_n=r.f, 
                               unit=r.g)
            rows.append(s)   
        print "--- ROWS ---- ",rows    
        if group_in(request, 'bendahara'):
            pdf, filename = open_rml_pdf('arsspd.rml', rows2=rows, 
                                                      un_nm=unit_nm,
                                                      un_al=unit_al,
                                                      awal=awal,
                                                      akhir=akhir)
        else:       
            pdf, filename = open_rml_pdf('arsspd_bud.rml', rows2=rows, 
                                                          awal=awal,
                                                          akhir=akhir)
        #pdf, filename = open_rml_pdf('arsspd.rml', rows2=rows)
        return pdf_response(request, pdf, filename)
        
    if url_dict['pdf']=='cetak' :
        query = query_cetak()
        rml_row = open_rml_row('arsspd_cetak.row.rml')
        rows=[]
        print "--- awal ----- ",awal
        print "--- akhir ---- ",akhir
        print "--- id TBP --- ",id1
        print "--- QUERY ---- ",query.first()
        
        for r in query.filter(ARSspd.tgl_bayar.between(awal,akhir),
                              ARSspd.id==id1,
                              ARSspd.bayar!=0).all():
            s = rml_row.format(byr=r.a, 
                               tgl=r.b.strftime('%d-%m-%Y'), 
                               wp_n=r.c, 
                               wp_a=r.d, 
                               rek_k=r.e, 
                               rek_n=r.f, 
                               denda=r.g, 
                               bunga=r.h, 
                               jumlah=r.i,
                               unit=r.j)
            rows.append(s)   
        print "--- ROWS ---- ",rows    
        pdf, filename = open_rml_pdf('arsspd_cetak.rml', rows2=rows)
        return pdf_response(request, pdf, filename)