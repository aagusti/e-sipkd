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
      ARTbp,
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
                    auto_op_nm, auto_unit_nm, auto_unit_nm2, auto_wp_nm
                    )
########                    
# List #
########    
@view_config(route_name='artbp', renderer='templates/artbp/list.pt',
             permission='read')
def view_list(request):
    awal = 'awal' in request.GET and request.GET['awal'] or datetime.now().strftime('%Y-%m-%d')
    akhir = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')
    return dict(rows={"awal":awal, "akhir":akhir})

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode invoice %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Uraian  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(ARTbp).filter_by(id=uid)
        r = q.first()
    else:
        r = None
            
class MasterAddSchema(colander.Schema):
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
    subjek_pajak_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    title="Penyetor",
                    oid = "subjek_pajak_id"
                    )
    subjek_pajak_nm = colander.SchemaNode(
                    colander.String(),
                    #widget=auto_wp_nm,
                    title="Penyetor",
                    oid = "subjek_pajak_nm"
                    )
    wp_nama = colander.SchemaNode(
                    colander.String(),
                    title="Nama Lain",
                    oid = "wp_nama"
                    )                    
    wp_alamat_1 = colander.SchemaNode(
                    colander.String(),
                    title="Alamat Pertama",
                    oid = "wp_alamat_1"
                    )

    wp_alamat_2 = colander.SchemaNode(
                    colander.String(),
                    title="Alamat Kedua",
                    oid = "wp_alamat_2"
                    )                  

    objek_pajak_id = colander.SchemaNode(
                    colander.Integer(),
                    title="Objek",
                    widget=widget.HiddenWidget(),
                    oid = "objek_pajak_id"
                    )
                    
    objek_pajak_nm = colander.SchemaNode(
                    colander.String(),
                    #widget=auto_op_nm,
                    title="Objek",
                    oid = "objek_pajak_nm"
                    )
                    
    op_nama = colander.SchemaNode(
                    colander.String(),
                    title="Nama OP Lainnya",
                    oid = "op_nama"
                    )                    
    op_alamat_1 = colander.SchemaNode(
                    colander.String(),
                    title="Alamat Pertama",
                    oid = "op_alamat_1"
                    )

    op_alamat_2 = colander.SchemaNode(
                    colander.String(),
                    title="Alamat Kedua",
                    oid = "op_alamat_2"
                    )                  

    # rekening_id = colander.SchemaNode(
                    # colander.String(),
                    # #widget=widget.HiddenWidget(),
                    # title="Rekening ID",
                    # oid = "rekening_id"
                    # )                  
                    
    # rekening_nm = colander.SchemaNode(
                    # colander.String(),
                    # title="Rekening",
                    # oid = "rekening_nm"
                    # )                  
                    
    kode   = colander.SchemaNode(
                    colander.String(),
                    title="Kode",
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
    tgl_terima = colander.SchemaNode(
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
                    missing=colander.drop,
                    title = "Tarif (%)"
                    )
    pokok = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    missing=colander.drop,
                    oid = "pokok"
                    )
    terutang = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "terutang"
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

class AdminAddSchema(MasterAddSchema):
    unit_nm = colander.SchemaNode(
                    colander.String(),
                    widget=auto_unit_nm2, 
                    title="OPD",
                    oid="unit_nm"
                    )
                    
class UserAddSchema(MasterAddSchema):
    unit_nm = colander.SchemaNode(
                    colander.String(),
                    widget=widget.TextInputWidget(readonly=True),
                    title="OPD",
                    oid="unit_nm"
                    )
                    
class AdminEditSchema(AdminAddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True)
            )
                    
class UserEditSchema(UserAddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True)
            )

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind()#daftar_status=STATUS,
                         #daftar_subjekpajak=daftar_subjekpajak(),
                         #daftar_unit=daftar_unit(),
                         #daftar_objekpajak=daftar_objekpajak(),
                         #)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(request, values, row=None):
    if not row:
        row = ARTbp()
        row.create_date = datetime.now()
        row.create_uid  = request.user.id
    row.from_dict(values)
    #row.update_date = datetime.now()
    row.update_uid  = request.user.id
    row.dasar       = re.sub("[^0-9]", "", row.dasar)
    row.tarif       = re.sub("[^0-9]", "", row.tarif)
    row.pokok       = re.sub("[^0-9]", "", row.pokok)
    #row.penambah    = re.sub("[^0-9]", "", row.penambah)
    #row.pengurang   = re.sub("[^0-9]", "", row.pengurang)
    row.denda       = re.sub("[^0-9]", "", row.denda)
    row.bunga       = re.sub("[^0-9]", "", row.bunga)
    row.jumlah      = re.sub("[^0-9]", "", row.jumlah)
    
    if not row.tahun_id:
        row.tahun_id = datetime.now().strftime('%Y')
        
    # unit = Unit.get_by_id(row.unit_id)
    # row.unit_kd = unit.kode
    # row.unit_nm = unit.nama
    
    ref = Unit.get_by_id(row.unit_id)
    row.unit_kode = ref.kode
    row.unit_nama = ref.nama
    
    #ref = SubjekPajak.get_by_id(row.subjek_pajak_id)
    #row.wp_kode = ref.kode
    #row.wp_nama = ref.nama
    #row.wp_alamat_1 = ref.alamat_1
    #row.wp_alamat_2 = ref.alamat_2
    
    ref = ObjekPajak.get_by_id(row.objek_pajak_id)
    row.op_kode = ref.kode
    row.op_nama = ref.nama
    #row.op_alamat_1 = ref.alamat_1
    #row.op_alamat_2 = ref.alamat_2
    row.wilayah_id = ref.wilayah_id
    row.rekening_id = ref.pajaks.rekening_id
    row.rek_kode = ref.pajaks.rekenings.kode
    row.rek_nama = ref.pajaks.rekenings.nama
    
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
    
    #prefix  = '20' 
    tanggal = datetime.now().strftime('%d')
    bulan   = datetime.now().strftime('%m')
    tahun   = datetime.now().strftime('%y')
    
    if not row.kode and not row.no_id:
        if prefix == '20':
            tbp_no = DBSession.query(func.max(ARTbp.no_id)).\
                                   filter(ARTbp.tahun_id==row.tahun_id,
                                          ARTbp.unit_id==row.unit_id,
                                          func.substr(ARTbp.kode,1,2)=='20').scalar()
            print "--------- no ID TBP BUD------------",tbp_no
        elif prefix == '21':
            tbp_no = DBSession.query(func.max(ARTbp.no_id)).\
                                   filter(ARTbp.tahun_id==row.tahun_id,
                                          ARTbp.unit_id==row.unit_id,
                                          func.substr(ARTbp.kode,1,2)=='21').scalar()
            print "--------- no ID TBP Ben------------",tbp_no
        if not tbp_no:
            row.no_id = 1
        else:
            row.no_id = tbp_no+1

    row.kode = "".join([prefix, #2
                        str(tahun).rjust(2,'0'),
                        #str(bulan).rjust(2,'0'),
                        str(row.unit_id).rjust(4,'0'),
                        str(row.no_id).rjust(8,'0')])
    
    row.owner_id = request.user.id
    row.invoice_kode = '-'
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(request, values, row)
    request.session.flash('No TBP %s sudah disimpan.' % row.kode)
        
def route_list(request):
    return HTTPFound(location=request.route_url('artbp'))
    
def session_failed(request, session_name):
    try:
        session_name.set_appstruct(request.session[SESS_ADD_FAILED])
    except:
        pass
    r = dict(form=session_name) #request.session[session_name])
    del request.session[SESS_ADD_FAILED]
    return r
    
@view_config(route_name='artbp-add', renderer='templates/artbp/add.pt',
             permission='add')
def view_add(request):
    values = {}
    #if request.user.id>1:
    if group_in(request, 'bendahara'):
        form = get_form(request, UserAddSchema)
        row = DBSession.query(Unit.id, Unit.nama).join(UserUnit).\
                  filter(UserUnit.user_id==request.user.id).first()
        if not row:
            request.session.flash('Default OPD tidak ditemukan')
            return route_list(request)
        values['unit_id']   = row.id
        values['unit_nm']   = row.nama
    else:    
        form = get_form(request, AdminAddSchema)
        
    if request.POST:
        if 'simpan' in request.POST:
            if not 'unit_nm' in request.POST:    
                request.POST['unit_nm']   = values['unit_nm']

            controls = request.POST.items()
            print "------------- Control --------- ",controls
            controls_dicted = dict(controls)

            try:
                c = form.validate(controls)
                print "------------- Validasi -------- ",c
            except ValidationFailure, e:
                print "------------- Gagal ----------- ",controls
                return dict(form=form)
            
            save_request(dict(controls), request)
    
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, form) #SESS_ADD_FAILED)
        
    values['tgl_terima']  = datetime.now() #.strftime('%d-%m-%Y')
    values['jatuh_tempo'] = datetime.now() #.strftime('%d-%m-%Y')
    values['periode_1']   = datetime.now() #.strftime('%d-%m-%Y')
    values['periode_2']   = datetime.now() #.strftime('%d-%m-%Y')
    form.set_appstruct(values)
    return dict(form=form, is_unit=0, is_sp=0)

########
# Edit #
########
def query_id(request):
    query = DBSession.query(ARTbp).filter(ARTbp.id==request.matchdict['id'])
    if request.user.id != 1:
        query = query.join(Unit).join(UserUnit).\
                      filter(UserUnit.user_id==request.user.id)
    return query                     
    
def id_not_found(request):    
    msg = 'No Bayar ID %s tidak ditemukan atau sudah dibayar.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='artbp-edit', renderer='templates/artbp/add.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    uid  = row.id
    kode = row.kode

    if not row:
        return id_not_found(request)
    if row.status_invoice:
        request.session.flash('Data sudah masuk di Nomor Bayar', 'error')
        return route_list(request)
    if request.user.id>1:
        form = get_form(request, UserAddSchema)
    else:    
        form = get_form(request, AdminAddSchema)
        
    if request.POST:
        if 'simpan' in request.POST:
            if not 'unit_nm' in request.POST:    
                request.POST['unit_nm']   = row.units.nama
            controls = request.POST.items()
            
            # # Cek kode
            # a = form.validate(controls)
            # b = a['kode']
            # c = "%s" % b
            # cek = DBSession.query(ARInvoice).filter(ARInvoice.kode==c).first()
            # if cek:
                # kode1 = DBSession.query(ARInvoice).filter(ARInvoice.id==uid).first()
                # d     = kode1.kode
                # if d!=c:
                    # request.session.flash('Kode Bayar %s sudah digunakan' % b, 'error')
                    # return HTTPFound(location=request.route_url('artbp-edit',id=row.id))
                    
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                #request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('artbp-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['objek_pajak_nm']  = row.objekpajaks.nama
    values['subjek_pajak_nm'] = row.subjekpajaks.nama
    values['unit_nm'] = row.units.nama
    #print values
    form.set_appstruct(values)
    return dict(form=form)

###########
# Posting #
###########     
def save_request2(request, row1=None):
    row1 = ARInvoice()
    #request.session.flash('TBP sudah diposting dan dibuat No.Bayar.')
    return row1
    
@view_config(route_name='artbp-posting', renderer='templates/artbp/posting.pt',
             permission='read')
def view_posting(request):
    awal  = 'awal'  in request.GET and request.GET['awal']  or datetime.now().strftime('%Y-%m-%d')
    akhir = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')
    
    form = Form(colander.Schema(),buttons=('posting','batal'))
    if request.POST:
        if 'posting' in request.POST: 
            #Update status pada ARInvoice
            rows = DBSession.query(ARTbp.wilayah_id.label('wil_id'),
                                   ARTbp.unit_id.label('un_id'),
                                   ARTbp.unit_kode.label('un_kd'),
                                   ARTbp.unit_nama.label('un_nm'),
                                   ARTbp.rekening_id.label('rek_id'),
                                   ARTbp.rek_kode.label('rek_kd'),
                                   ARTbp.rek_nama.label('rek_nm'),
                                   ARTbp.op_kode.label('op_kd'),
                                   ARTbp.op_nama.label('op_nm'),
                                   ARTbp.op_alamat_1.label('op_a1'),
                                   ARTbp.op_alamat_2.label('op_a2'),
                                   func.sum(ARTbp.dasar).label('dasar'),
                                   ARTbp.tarif.label('tarif'),
                                   func.sum(ARTbp.pokok).label('pokok'),
                                   func.sum(ARTbp.terutang).label('terutang'),
                                   func.sum(ARTbp.denda).label('denda'),
                                   func.sum(ARTbp.bunga).label('bunga'),
                                   func.sum(ARTbp.jumlah).label('jumlah')
                           ).filter(ARTbp.tgl_terima.between(awal,akhir),
                                    ARTbp.status_invoice==0
                           ).group_by(ARTbp.wilayah_id,
                                      ARTbp.unit_id,
                                      ARTbp.unit_kode,
                                      ARTbp.unit_nama,
                                      ARTbp.rekening_id,
                                      ARTbp.rek_kode,
                                      ARTbp.rek_nama,
                                      ARTbp.op_kode,
                                      ARTbp.op_nama,
                                      ARTbp.op_alamat_1,
                                      ARTbp.op_alamat_2,
                                      ARTbp.tarif
                           )
            if group_in(request, 'bendahara'):
                rows = rows.join(Unit).join(UserUnit).\
                        filter(UserUnit.user_id==request.user.id)
            n=0
            for row in rows:
                i = ARInvoice()
                i.create_date  = datetime.now()
                i.create_uid   = request.user.id
                i.tahun_id     = datetime.now().strftime('%Y')
                i.unit_id      = row.un_id
                i.unit_kode    = row.un_kd
                i.unit_nama    = row.un_nm
                i.rekening_id  = row.rek_id
                i.rek_kode     = row.rek_kd
                i.rek_nama     = row.rek_nm
                i.wilayah_id   = row.wil_id
                i.op_kode      = row.op_kd
                i.op_nama      = row.op_nm
                i.op_alamat_1  = row.op_a1
                i.op_alamat_2  = row.op_a2
                i.owner_id     = request.user.id
                i.status_bayar = 0
                i.status_grid  = 1
                i.is_tbp       = 1
                i.dasar        = row.dasar
                i.tarif        = row.tarif
                i.pokok        = row.pokok
                i.denda        = row.denda
                i.bunga        = row.bunga
                i.jumlah       = row.jumlah
                i.periode_1    = datetime.now()
                i.periode_2    = datetime.now()
                i.tgl_tetap    = datetime.now()
                i.jatuh_tempo  = datetime.now()
                
                ref = Wilayah.get_by_id(i.wilayah_id)
                i.wilayah_kode = ref.kode
                
                u = request.user.id
                print '----------------User_Login---------------',u
                x = DBSession.query(UserGroup.group_id).filter(UserGroup.user_id==u).first()
                y = '%s' % x
                z = int(y)        
                print '----------------Group_id-----------------',z
                
                if z == 2:
                    prefix  = '21'
                    i.wp_kode = "".join([prefix, 
                                         re.sub("[^0-9]", "", i.wilayah_kode), 
                                         re.sub("[^0-9]", "", i.unit_kode)])
                    i.wp_nama = 'BENDAHARA'
                    i.wp_alamat_1 = '-'
                    i.wp_alamat_2 = '-'
                else:
                    prefix  = '20' 
                    i.wp_kode = "".join([prefix, re.sub("[^0-9]", "", i.wilayah_kode)])
                    i.wp_nama = 'BUD'
                    i.wp_alamat_1 = '-'
                    i.wp_alamat_2 = '-'

                tanggal = datetime.now().strftime('%d')
                bulan   = datetime.now().strftime('%m')
                tahun   = datetime.now().strftime('%y')
                
                if prefix == '20':
                    invoice_no = DBSession.query(func.max(ARInvoice.no_id)).\
                                           filter(ARInvoice.tahun_id==i.tahun_id,
                                                  ARInvoice.wilayah_id==i.wilayah_id,
                                                  ARInvoice.tgl_tetap==datetime.now().strftime('%Y-%m-%d'),
                                                  func.substr(ARInvoice.kode,1,2)=='20').scalar()
                    print "--------- Invoice No ---------- ",invoice_no
                elif prefix == '21':
                    invoice_no = DBSession.query(func.max(ARInvoice.no_id)).\
                                           filter(ARInvoice.tahun_id==i.tahun_id,
                                                  ARInvoice.wilayah_id==i.wilayah_id,
                                                  ARInvoice.tgl_tetap==datetime.now().strftime('%Y-%m-%d'),
                                                  func.substr(ARInvoice.kode,1,2)=='21').scalar()
                    print "--------- Invoice No ---------- ",invoice_no
                    
                if not invoice_no:
                    i.no_id = 1
                else:
                    i.no_id = invoice_no+1
                
                i.kode = "".join([prefix, re.sub("[^0-9]", "", i.wilayah_kode), 
                                    str(tanggal).rjust(2,'0'), 
                                    str(bulan).rjust(2,'0'),
                                    str(tahun).rjust(2,'0'),
                                    str(i.no_id).rjust(4,'0')])
                    
                n = n + 1
                DBSession.add(i)
                DBSession.flush()

                id1 = i.id
                kd1 = i.kode
                rows1 = DBSession.query(ARTbp
                                ).filter(ARTbp.tgl_terima.between(awal,akhir),
                                         ARTbp.status_invoice==0,
                                         ARTbp.wilayah_id==row.wil_id,
                                         ARTbp.unit_id==row.un_id,
                                         ARTbp.rek_kode==row.rek_kd
                                ).all()
                for row1 in rows1:
                   row1.status_invoice=1
                   row1.invoice_id=id1
                   row1.invoice_kode=kd1
                   save_request2(request, row1)
        return route_list(request)
    return dict(message='Posting TBP Sukses', form=form.render())  



##########
# Delete #
##########    
@view_config(route_name='artbp-delete', renderer='templates/artbp/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return id_not_found(request)
    
    if row.status_invoice:
        request.session.flash('Data sudah masuk di No Bayar', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('hapus', 'batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'TBP ID %d %s sudah dihapus.' % (row.id, row.kode)
            q = DBSession.query(ARTbp).filter(ARTbp.id==request.matchdict['id']).delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
    
##########
# Action #
##########    
@view_config(route_name='artbp-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    user     = req.user
    if url_dict['act']=='grid':
        awal = 'awal' in request.GET and request.GET['awal'] or datetime.now().strftime('%Y-%m-%d')
        akhir = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')	
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('wp_nama'))
        columns.append(ColumnDT('op_nama'))
        columns.append(ColumnDT('rek_kode'))
        columns.append(ColumnDT('tgl_terima', filter=_DTstrftime))
        columns.append(ColumnDT('denda',      filter=_DTnumberformat))
        columns.append(ColumnDT('bunga',      filter=_DTnumberformat))
        columns.append(ColumnDT('jumlah',     filter=_DTnumberformat))
        columns.append(ColumnDT('status_invoice'))
        columns.append(ColumnDT('invoice_kode'))
        query = DBSession.query(ARTbp)\
                         .filter(ARTbp.tgl_terima.between(awal,akhir))\
                         .order_by(desc(ARTbp.tgl_terima),desc(ARTbp.kode))
        if group_in(request, 'bendahara'):
            query = query.join(Unit).join(UserUnit).\
                    filter(UserUnit.user_id==request.user.id)
        rowTable = DataTables(req, ARTbp, query, columns)
        return rowTable.output_result()           

from ..reports.rml_report import open_rml_row, open_rml_pdf, pdf_response
def query_reg():
    return DBSession.query(ARTbp.kode.label('a'), 
                           ARTbp.wp_nama.label('b'), 
                           ARTbp.rek_kode.label('c'), 
                           ARTbp.op_nama.label('d'), 
                           ARTbp.tgl_terima.label('e'), 
                           func.trim(func.to_char(ARTbp.terutang,'999,999,999,990')).label('f'), 
                           func.trim(func.to_char(ARTbp.jumlah,'999,999,999,990')).label('g'),
                           ARTbp.invoice_kode.label('h'), 
                   ).order_by(ARTbp.tgl_terima,ARTbp.unit_kode,ARTbp.rek_kode) 
def query_cetak():
    return DBSession.query(ARTbp.kode.label('a'), 
                           ARTbp.wp_nama.label('b'), 
                           ARTbp.wp_alamat_1.label('c'),
                           ARTbp.rek_kode.label('d'), 
                           ARTbp.rek_nama.label('e'), 
                           func.trim(func.to_char(ARTbp.terutang,'999,999,999,990')).label('f'), 
                           func.trim(func.to_char(ARTbp.denda,'999,999,999,990')).label('g'), 
                           func.trim(func.to_char(ARTbp.bunga,'999,999,999,990')).label('h'), 
                           func.trim(func.to_char(ARTbp.jumlah,'999,999,999,990')).label('i'),
                           ARTbp.tgl_terima.label('j'),
                           ARTbp.unit_nama.label('k'),                            
                   ).order_by(ARTbp.unit_kode,ARTbp.rek_kode)                   
    
########                    
# CSV #
########          
@view_config(route_name='artbp-csv', renderer='csv')
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
        #if request.user.id != 1:
        if group_in(request, 'bendahara'):
            query = query.join(Unit).join(UserUnit).\
                    filter(UserUnit.user_id==u)
                    
        row = query.filter(ARTbp.tgl_terima.between(awal,akhir))#.first()
        print "-- ROW -- ",row
        header = 'No. TBP','Penyetor','Objek','Uraian','Tgl. Terima','Terutang','Jumlah','No. Bayar' #row.keys()
        rows = []
        for item in row.all():
            rows.append(list(item))

        # override attributes of response
        filename = 'TBP_%s_sd_%s.csv' %(awal, akhir)
        request.response.content_disposition = 'attachment;filename=' + filename

    return {
      'header': header, 
      'rows'  : rows,
    } 
        
##########
# PDF    #
##########    
@view_config(route_name='artbp-pdf', permission='read')
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
            query = query.join(Unit).join(UserUnit).\
                    filter(UserUnit.user_id==u)
                    
        rml_row = open_rml_row('artbp.row.rml')
        rows=[]
        for r in query.filter(ARTbp.tgl_terima.between(awal,akhir)).all():
            s = rml_row.format(kode=r.a, 
                               wp=r.b, 
                               rek_k=r.c, 
                               rek_n=r.d, 
                               terima=r.e.strftime('%d-%m-%Y'),
                               terutang=r.f, 
                               jumlah=r.g, 
                               inv=r.h)
            rows.append(s)   
        print "--- ROWS ---- ",rows  
        if group_in(request, 'bendahara'):
            pdf, filename = open_rml_pdf('artbp.rml', rows2=rows, 
                                                      un_nm=unit_nm,
                                                      un_al=unit_al,
                                                      awal=awal,
                                                      akhir=akhir)
        else:       
            pdf, filename = open_rml_pdf('artbp_bud.rml', rows2=rows, 
                                                          awal=awal,
                                                          akhir=akhir)        
        return pdf_response(request, pdf, filename)
        
    if url_dict['pdf']=='cetak' :
        query = query_cetak()
        rml_row = open_rml_row('artbp_cetak.row.rml')
        rows=[]
        print "--- awal ----- ",awal
        print "--- akhir ---- ",akhir
        print "--- id TBP --- ",id1
        print "--- QUERY ---- ",query.first()
        
        for r in query.filter(ARTbp.tgl_terima.between(awal,akhir),ARTbp.id==id1).all():
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
                               un_nm=r.k)                               
            rows.append(s)   
        print "--- ROWS ---- ",rows    
        pdf, filename = open_rml_pdf('artbp_cetak.rml', rows2=rows)
        return pdf_response(request, pdf, filename)
        