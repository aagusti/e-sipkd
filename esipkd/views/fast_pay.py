import sys
import re
from email.utils import parseaddr
from sqlalchemy import not_, func, or_, desc
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
from ..tools import _DTnumberformat
from ..models import DBSession
from ..models.isipkd import(
      Pegawai, ObjekPajak, SubjekPajak, ARInvoice,
      Unit, Wilayah, Pajak, Rekening, UserUnit, 
      ARSts, ARStsItem, ARSspd
      )
from ..models.__init__ import(
      UserGroup
      )
from datatables import (
    ColumnDT, DataTables)
    
from ..security import group_finder,group_in

SESS_ADD_FAILED = 'Gagal tambah pembayaran cepat'
SESS_EDIT_FAILED = 'Gagal edit pembayaran cepat'

from daftar import (STATUS, deferred_status,
                    daftar_subjekpajak, deferred_subjekpajak,
                    daftar_objekpajak, deferred_objekpajak,
                    daftar_wilayah, deferred_wilayah,
                    daftar_unit, deferred_unit,
                    daftar_pajak, deferred_pajak,
                    auto_op_nm, auto_unit_nm, auto_wp_nm, auto_wp_nm1
                    )
########                    
# List #
########    
@view_config(route_name='fast-pay', renderer='templates/fast-pay/list.pt',
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
            'Kode pembayaran cepat %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Uraian  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(ARInvoice).filter_by(id=uid)
        r = q.first()
    else:
        r = None
            
class AddSchema(colander.Schema):
    moneywidget = widget.MoneyInputWidget(
            size=20, options={'allowZero':True,
                              'precision':0
                              })
            
    unit_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid="unit_id",
                    title="OPD",
                    )
    unit_nm = colander.SchemaNode(
                    colander.String(),
                    title="OPD",
                    oid="unit_nm"
                    )
    wilayah_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_wilayah,
                    title="Wilayah"
                    )
    wp_kode = colander.SchemaNode(
                    colander.String(),
                    title="Kode Penyetor",
                    oid = "wp_kode"
                    )
    wp_nama = colander.SchemaNode(
                    colander.String(),
                    title="Nama Penyetor",
                    oid = "wp_nama"
                    )
    wp_alamat_1 = colander.SchemaNode(
                    colander.String(),
                    title="Alamat",
                    oid = "wp_alamat_1"
                    )
    wp_alamat_2 = colander.SchemaNode(
                    colander.String(),
                    title="Alamat lain",
                    oid = "wp_alamat_2",
                    missing=colander.drop,
                    )
    pajak_id = colander.SchemaNode(
                    colander.String(),
                    widget=widget.HiddenWidget(),
                    oid="pajak_id",
                    )

    pajak_nm = colander.SchemaNode(
                    colander.String(),
                    title="Rekening",
                    oid="pajak_nm"
                    )
           
    kode   = colander.SchemaNode(
                    colander.String(),
                    title="Kode Bayar",
                    missing = colander.drop,
                    )
                    
    periode_1 = colander.SchemaNode(
                    colander.Date(),
                    title="Periode 1",
                    widget = widget.DateInputWidget()
                    )
    periode_2 = colander.SchemaNode(
                    colander.Date(),
                    title="Periode 2"
                    )
    tgl_tetap = colander.SchemaNode(
                    colander.Date(),
                    )
    jatuh_tempo = colander.SchemaNode(
                    colander.Date(),
                    )
    dasar = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "dasar"
                    )
    tarif = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "tarif",
                    missing=colander.drop
                    )
    pokok = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    missing=colander.drop,
                    oid = "pokok"
                    )
    denda = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "denda"
                    )
    bunga = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "bunga"
                    )
    jumlah = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    missing=colander.drop,
                    oid = "jumlah"
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
                         daftar_wilayah=daftar_wilayah(),
                         daftar_unit=daftar_unit(),
                         daftar_objekpajak=daftar_objekpajak(),
                         )
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(request, values, row=None):
    if not row:
        row = ARInvoice()
        row.create_date = datetime.now()
        row.create_uid  = request.user.id
    row.from_dict(values)
    #row.update_date = datetime.now()
    row.update_uid  = request.user.id
    row.dasar  = re.sub("[^0-9]", "", row.dasar)
    row.tarif  = re.sub("[^0-9]", "", row.tarif)
    row.pokok  = re.sub("[^0-9]", "", row.pokok)
    row.denda  = re.sub("[^0-9]", "", row.denda)
    row.bunga  = re.sub("[^0-9]", "", row.bunga)
    row.jumlah = re.sub("[^0-9]", "", row.jumlah)
    
    if not row.tahun_id:
        row.tahun_id = datetime.now().strftime('%Y')
        
    unit = Unit.get_by_id(row.unit_id)
    row.unit_kd = unit.kode
    row.unit_nm = unit.nama
    
    ref = Unit.get_by_id(row.unit_id)
    row.unit_kode = ref.kode
    row.unit_nama = ref.nama
    
    ref = Pajak.get_by_id(values['pajak_id'])
    row.rekening_id = ref.rekening_id
    row.rek_kode    = ref.rekenings.kode
    row.rek_nama    = ref.rekenings.nama
    row.op_kode     = ref.kode
    row.op_nama     = ref.nama
    
    ref = Wilayah.get_by_id(row.wilayah_id)
    row.wilayah_kode = ref.kode
    
    u = request.user.id
    print '----------------User_Login---------------',u
    x = DBSession.query(UserGroup.group_id).filter(UserGroup.user_id==u).first()
    y = '%s' % x
    z = int(y)        
    print '----------------Group_id-----------------',z
    
    if z == 2:
        prefix  = '21'
    else:
        prefix  = '20' 

    tanggal = datetime.now().strftime('%d')
    bulan   = datetime.now().strftime('%m')
    tahun   = datetime.now().strftime('%y')
    
    if not row.kode and not row.no_id:
        if prefix == '20':
            invoice_no = DBSession.query(func.max(ARInvoice.no_id)).\
                                   filter(ARInvoice.tahun_id==row.tahun_id,
                                          ARInvoice.wilayah_id==row.wilayah_id,
                                          ARInvoice.tgl_tetap==datetime.now().strftime('%Y-%m-%d'),
                                          func.substr(ARInvoice.kode,1,2)=='20').scalar()
            print "--------- Invoice No ---------- ",invoice_no
        elif prefix == '21':
            invoice_no = DBSession.query(func.max(ARInvoice.no_id)).\
                                   filter(ARInvoice.tahun_id==row.tahun_id,
                                          ARInvoice.wilayah_id==row.wilayah_id,
                                          ARInvoice.tgl_tetap==datetime.now().strftime('%Y-%m-%d'),
                                          func.substr(ARInvoice.kode,1,2)=='21').scalar()
            print "--------- Invoice No ---------- ",invoice_no
            
        if not invoice_no:
            row.no_id = 1
        else:
            row.no_id = invoice_no+1

    row.kode = "".join([prefix, re.sub("[^0-9]", "", row.wilayah_kode), 
                        str(tanggal).rjust(2,'0'), 
                        str(bulan).rjust(2,'0'),
                        str(tahun).rjust(2,'0'),
                        str(row.no_id).rjust(4,'0')])
    
    row.owner_id    = request.user.id
    row.status_grid = 1
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(request, values, row)
    request.session.flash('No pembayaran cepat %s sudah disimpan.' % row.kode)
        
def route_list(request):
    return HTTPFound(location=request.route_url('fast-pay'))
    
def session_failed(request, session_name):
    try:
        session_name.set_appstruct(request.session[SESS_ADD_FAILED])
    except:
        pass
    r = dict(form=session_name) 
    del request.session[SESS_ADD_FAILED]
    return r
    
@view_config(route_name='fast-pay-add', renderer='templates/fast-pay/add.pt',
             permission='add')
def view_add(request):
    
    form = get_form(request, AddSchema)
    values = {}
    values['tgl_tetap']   = datetime.now()
    values['jatuh_tempo'] = datetime.now()
    values['periode_1']   = datetime.now()
    values['periode_2']   = datetime.now()

    u = request.user.id
    print '----------------User_Login---------------',u
    if u != 1 :
        x = DBSession.query(UserGroup.group_id).filter(UserGroup.user_id==u).first()
        y = '%s' % x
        z = int(y)        
        print '----------------Group_id-----------------',z
        
        if z == 2:
            print '----------------User_id-------------------',u
            a = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            b = '%s' % a
            c = int(b)
            values['unit_id'] = c
            print '----------------Unit id-------------------------',values['unit_id'] 
            unit = DBSession.query(Unit.nama.label('unm')
                           ).filter(Unit.id==c,
                           ).first()
            values['unit_nm'] = unit.unm
            print '----------------Unit nama-----------------------',values['unit_nm'] 

    form.set_appstruct(values)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)
            
            # Cek Kode
            if not controls_dicted['kode']=='':
                a = form.validate(controls)
                b = a['kode']
                c = "%s" % b
                cek = DBSession.query(ARInvoice).filter(ARInvoice.kode==c).first()
                if cek :
                    request.session.flash('Kode Bayar %s sudah digunakan.' % b, 'error')
                    return HTTPFound(location=request.route_url('fast-pay-add'))

            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, form)
    return dict(form=form, is_unit=0, is_sp=0)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ARInvoice).filter(ARInvoice.id==request.matchdict['id'],)
    
def id_not_found(request):    
    msg = 'No pembayaran cepat ID %s tidak ditemukan atau sudah dibayar.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='fast-pay-edit', renderer='templates/fast-pay/add.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    uid  = row.id
    kode = row.kode

    if not row:
        return id_not_found(request)
    if row.status_bayar:
        request.session.flash('Data sudah masuk di Penerimaan', 'error')
        return route_list(request)
    if row.is_sts:
        request.session.flash('Data sudah masuk di STS', 'error')
        return route_list(request)
        
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            print "--------- control ---------- ",controls
            try:
                c = form.validate(controls)
                print "--------- validasi --------- ",c
            except ValidationFailure, e:
                print "--------- gagal ------------ ",controls
                return dict(form=form)             
                return HTTPFound(location=request.route_url('fast-pay-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()

    x = DBSession.query(Pajak).filter(Pajak.rekening_id==row.rekening_id).first()
    values['pajak_id']     = x.id
    values['pajak_nm']     = x.nama
    values['unit_nm']      = row.units.nama
    values['wp_alamat_2']  = row and row.wp_alamat_2 or '' 
    form.set_appstruct(values)
    return dict(form=form)

###########
# Posting #
###########     
def save_request2(request, row1=None):
    row1 = ARInvoice()
    return row1  
    
def save_request3(request, row2=None):
    row2 = ARSts()
    return row2

@view_config(route_name='fast-pay-posting', renderer='templates/fast-pay/posting.pt',
             permission='read')
def view_posting(request):
    awal  = 'awal'  in request.GET and request.GET['awal']  or datetime.now().strftime('%Y-%m-%d')
    akhir = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')
    
    form = Form(colander.Schema(),buttons=('posting','batal'))
    if request.POST:
        if 'posting' in request.POST: 
            u = request.user.id
            rows1 = DBSession.query(ARInvoice.unit_id.label('un_id'),
                                    ARInvoice.unit_kode.label('un_kd'),
                                    ARInvoice.unit_nama.label('un_nm')
                           ).filter(ARInvoice.status_grid==1,
                                    ARInvoice.tgl_tetap.between(awal,akhir),
                                    ARInvoice.is_sts==0,
                                    ARInvoice.is_sspd==1
                                    #or_(ARInvoice.is_tbp==1,
                                    #    ARInvoice.is_sspd==1)
                           ).group_by(ARInvoice.unit_id,
                                      ARInvoice.unit_kode,
                                      ARInvoice.unit_nama
                           ).order_by(ARInvoice.unit_kode)
            if u != 1:
                rows1 = rows1.filter(ARInvoice.owner_id==u)
            for row in rows1:
                print "--------- Data Unit ----------- ",row
                a = ARSts()
                x  = datetime.now().strftime('%d-%m-%Y')
                x1 = row.un_kd
                
                a.create_date = datetime.now()
                a.create_uid  = u
                a.nama        = "Setoran tanggal %s" % x + " atas unit %s" % x1
                a.tahun_id    = datetime.now().strftime('%Y')
                a.tgl_sts     = datetime.now().strftime('%Y-%m-%d')
                a.unit_id     = row.un_id
                a.unit_kode   = row.un_kd
                a.unit_nama   = row.un_nm
                
                sts_no = DBSession.query(func.max(ARSts.no_id)).\
                                   filter(ARSts.tahun_id==a.tahun_id,
                                          ARSts.unit_id==a.unit_id).scalar()
                if not sts_no:
                    a.no_id = 1
                else:
                    a.no_id = sts_no+1
                        
                a.kode = "".join([str(a.tahun_id), re.sub("[^0-9]", "", a.unit_kode),
                                    str(a.no_id).rjust(6,'0')])
                DBSession.add(a)
                DBSession.flush()
                print "--------- Data STS ------------ ",a
                b  = a.id
                b1 = a.unit_id
                
                rows = DBSession.query(ARInvoice.id.label('inv_id'),
                                       ARInvoice.kode.label('kd'),
                                       ARInvoice.rekening_id.label('rek_id'),
                                       ARInvoice.rek_kode.label('rek_kd'),
                                       ARInvoice.rek_nama.label('rek_nm'),
                                       ARInvoice.jumlah.label('jumlah'),
                                       ARInvoice.is_sspd.label('is_sspd')
                               ).filter(ARInvoice.status_grid==1,
                                        ARInvoice.tgl_tetap.between(awal,akhir),
                                        ARInvoice.is_sts==0,
                                        ARInvoice.is_sspd==1,
                                        #or_(ARInvoice.is_tbp==1,
                                        #    ARInvoice.is_sspd==1),
                                        ARInvoice.unit_id==b1
                               ).order_by(ARInvoice.rek_kode,
                                          ARInvoice.kode)
                if u != 1:
                    rows = rows.filter(ARInvoice.owner_id==u)
                for row1 in rows:
                    print "--------- Data Invoice -------- ",row1
                    items=ARStsItem()
                    items.sts_id      = b
                    items.invoice_id  = row1.inv_id
                    items.kode        = row1.kd
                    items.rekening_id = row1.rek_id
                    items.rek_kode    = row1.rek_kd
                    items.rek_nama    = row1.rek_nm
                    items.jumlah      = row1.jumlah
                    DBSession.add(items)
                    DBSession.flush()
                    print "--------- Data STS Item ------- ",items
                    if row1.is_sspd!=0:
                        sspd = DBSession.query(ARSspd
                                       ).filter(ARSspd.arinvoice_id==row1.inv_id,
                                                ARSspd.bayar!=0
                                       ).first()
                        sspd.posted=1
                        DBSession.add(sspd)
                        DBSession.flush()
                        
                    inv = DBSession.query(ARInvoice
                                   ).filter(ARInvoice.id==row1.inv_id
                                   ).first()
                    inv.is_sts=1
                    DBSession.add(inv)
                    DBSession.flush()
                    print "----- Data Invoice Update ----- ",inv
                    
                jumlah = DBSession.query(func.sum(ARStsItem.jumlah)).\
                                   filter(ARStsItem.sts_id==b).scalar()
                print "--------- Jum STS Item -------- ",jumlah
                if jumlah:
                    rows2 = DBSession.query(ARSts
                                   ).filter(ARSts.id==b
                                   ).first()
                    rows2.jumlah=jumlah
                    DBSession.add(rows2)
                    DBSession.flush()
                    print "--------- STS terbaru nya ----- ",rows2
        return route_list(request)
    return dict(message='Posting No.Bayar Sukses', form=form.render())  
    
##########
# Delete #
##########    
@view_config(route_name='fast-pay-delete', renderer='templates/fast-pay/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return id_not_found(request)
    if row.status_bayar:
        request.session.flash('Data sudah masuk di Penerimaan', 'error')
        return route_list(request)
    if row.is_sts:
        request.session.flash('Data sudah masuk di STS', 'error')
        return route_list(request)
        
    if row.arsspds:
        form = Form(colander.Schema(), buttons=('batal',))
    else:
        form = Form(colander.Schema(), buttons=('hapus', 'batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'No pembayaran cepat ID %d %s sudah dihapus.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# Action #
##########    
@view_config(route_name='fast-pay-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    user     = req.user
    awal     = 'awal'  in request.GET and request.GET['awal']  or datetime.now().strftime('%Y-%m-%d')
    akhir    = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')
    if url_dict['act']=='grid':
        u = request.user.id
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('wp_nama'))
        columns.append(ColumnDT('op_kode'))
        columns.append(ColumnDT('op_nama'))
        columns.append(ColumnDT('rek_nama'))
        columns.append(ColumnDT('jumlah',  filter=_DTnumberformat))
        columns.append(ColumnDT('unit_nama'))
        columns.append(ColumnDT('is_tbp'))
        columns.append(ColumnDT('is_sts'))
        query = DBSession.query(ARInvoice
                        ).filter(ARInvoice.status_grid==1,
                                 ARInvoice.tgl_tetap.between(awal,akhir)
                        ).order_by(desc(ARInvoice.tgl_tetap),desc(ARInvoice.kode))
        if u != 1:
            query = query.filter(ARInvoice.owner_id==u)        
        rowTable = DataTables(req, ARInvoice, query, columns)
        return rowTable.output_result()           

from ..reports.rml_report import open_rml_row, open_rml_pdf, pdf_response
def query_reg():
    return DBSession.query(ARInvoice.kode.label('a'), 
                           ARInvoice.wp_nama.label('b'), 
                           ARInvoice.rek_kode.label('c'), 
                           ARInvoice.op_nama.label('d'),  
                           ARInvoice.tgl_tetap.label('e'), 
                           func.trim(func.to_char(ARInvoice.jumlah,'999,999,999,990')).label('f'),
                           ARInvoice.unit_nama.label('g'),
                   ).order_by(ARInvoice.tgl_tetap,ARInvoice.kode)
def query_cetak():
    return DBSession.query(ARInvoice.kode.label('a'), 
                           ARInvoice.wp_nama.label('b'), 
                           ARInvoice.wp_alamat_1.label('c'),
                           ARInvoice.rek_kode.label('d'), 
                           ARInvoice.rek_nama.label('e'), 
                           func.trim(func.to_char(ARInvoice.pokok,'999,999,999,990')).label('f'), 
                           func.trim(func.to_char(ARInvoice.denda,'999,999,999,990')).label('g'), 
                           func.trim(func.to_char(ARInvoice.bunga,'999,999,999,990')).label('h'), 
                           func.trim(func.to_char(ARInvoice.jumlah,'999,999,999,990')).label('i'),
                           ARInvoice.tgl_tetap.label('j'), 
                           ARInvoice.unit_nama.label('k'),
                   ).order_by(ARInvoice.unit_kode,ARInvoice.rek_kode)   
    
########                    
# CSV #
########          
@view_config(route_name='fast-pay-csv', renderer='csv')
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
        if u != 1:
            query = query.filter(ARInvoice.owner_id==u)
                          
        row = query.filter(ARInvoice.tgl_tetap.between(awal,akhir),
                           ARInvoice.status_grid==1)#.first()
        #print "-- ROW -- ",row
        header = 'No. Bayar','Penyetor','Objek','Uraian','Tgl. Tetap','Jumlah','OPD' #row.keys()
        rows = []
        for item in row.all():
            rows.append(list(item))
        
        # override attributes of response
        filename = 'Tagihan_Cepat_%s_sd_%s.csv' %(awal, akhir)
        request.response.content_disposition = 'attachment;filename=' + filename

    return {
      'header': header,
      'rows'  : rows,
    } 
        
##########
# PDF    #
##########    
@view_config(route_name='fast-pay-pdf', permission='read')
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
        if u != 1:
             query = query.filter(ARInvoice.owner_id==u)
                          
        rml_row = open_rml_row('fast_pay.row.rml')
        rows=[]
        for r in query.filter(ARInvoice.tgl_tetap.between(awal,akhir),
                              ARInvoice.status_grid==1).all():
            s = rml_row.format(kode=r.a, 
                               wp=r.b, 
                               rek_k=r.c, 
                               rek_n=r.d, 
                               terutang=r.e.strftime('%d-%m-%Y'), 
                               jumlah=r.f, 
                               unit=r.g)
            rows.append(s)   
        print "--- ROWS ---- ",rows    
        if group_in(request, 'bendahara'):
            pdf, filename = open_rml_pdf('fast_pay_ben.rml', rows2=rows, 
                                                      un_nm=unit_nm,
                                                      un_al=unit_al,
                                                      awal=awal,
                                                      akhir=akhir)
        else:       
            pdf, filename = open_rml_pdf('fast_pay.rml', rows2=rows, 
                                                      awal=awal,
                                                      akhir=akhir) 
        #pdf, filename = open_rml_pdf('fast_pay.rml', rows2=rows)
        return pdf_response(request, pdf, filename)
        
    if url_dict['pdf']=='cetak' :
        query = query_cetak()
        rml_row = open_rml_row('fast_pay_cetak.row.rml')
        rows=[]
        print "--- awal ----- ",awal
        print "--- akhir ---- ",akhir
        print "--- id TBP --- ",id1
        print "--- QUERY ---- ",query.first()
        
        for r in query.filter(ARInvoice.tgl_tetap.between(awal,akhir),ARInvoice.id==id1).all():
            s = rml_row.format(kode=r.a, 
                               wp_n=r.b, 
                               wp_a=r.c, 
                               rek_k=r.d, 
                               rek_n=r.e, 
                               terutang=r.f, 
                               denda=r.g, 
                               bunga=r.h, 
                               jumlah=r.i,
                               terima=r.j.strftime('%d/%m/%Y'),
                               unit=r.k )
            rows.append(s)   
        print "--- ROWS ---- ",rows    
        pdf, filename = open_rml_pdf('fast_pay_cetak.rml', rows2=rows)
        return pdf_response(request, pdf, filename)
