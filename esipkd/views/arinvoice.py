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
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from ..tools import _DTnumberformat
from ..models import DBSession
from ..models.isipkd import(
      Pegawai, ObjekPajak, SubjekPajak, ARInvoice,
      Unit, Wilayah, Pajak, Rekening
      )

from datatables import (
    ColumnDT, DataTables)
    
from ..security import group_finder

SESS_ADD_FAILED = 'Gagal tambah Tagihan'
SESS_EDIT_FAILED = 'Gagal edit Tagihan'
from daftar import (STATUS, deferred_status,
                    daftar_subjekpajak, deferred_subjekpajak,
                    daftar_objekpajak, deferred_objekpajak,
                    daftar_wilayah, deferred_wilayah,
                    daftar_unit, deferred_unit,
                    daftar_pajak, deferred_pajak,
                    auto_op_nm
                    )
########                    
# List #
########    
@view_config(route_name='arinvoice', renderer='templates/arinvoice/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    

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
                    title="SKPD",
                    )
    unit_nm = colander.SchemaNode(
                    colander.String(),
                    title="SKPD",
                    oid="unit_nm"
                    )
                    
    subjek_pajak_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    title="Subjek Pajak",
                    oid = "subjek_pajak_id"
                    )
                    
    subjek_pajak_nm = colander.SchemaNode(
                    colander.String(),
                    title="Subjek Pajak",
                    oid = "subjek_pajak_nm"
                    )
                    
    objek_pajak_id = colander.SchemaNode(
                    colander.Integer(),
                    title="Objek Pajak",
                    widget=widget.HiddenWidget(),
                    oid = "objek_pajak_id"
                    )
    objek_pajak_nm = colander.SchemaNode(
                    colander.String(),
                    widget=auto_op_nm,
                    title="Objek Pajak",
                    oid = "objek_pajak_nm"
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
                    )
    tarif = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    )
    pokok = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    )
    denda = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    )
    bunga = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    )
    jumlah = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
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
        row = ARInvoice()
    row.from_dict(values)
    row.dasar  = re.sub("[^0-9]", "", row.dasar)
    row.pokok  = re.sub("[^0-9]", "", row.pokok)
    row.denda  = re.sub("[^0-9]", "", row.denda)
    row.bunga  = re.sub("[^0-9]", "", row.bunga)
    row.tarif  = re.sub("[^0-9]", "", row.tarif)
    row.jumlah = re.sub("[^0-9]", "", row.jumlah)
    
    if not row.tahun_id:
        row.tahun_id = datetime.now().strftime('%Y')
        
    unit = Unit.get_by_id(row.unit_id)
    row.unit_kd = unit.kode
    row.unit_nm = unit.nama
    
    ref = Unit.get_by_id(row.unit_id)
    row.unit_kode = ref.kode
    row.unit_nama = ref.nama
    ref = SubjekPajak.get_by_id(row.subjek_pajak_id)
    row.wp_kode = ref.kode
    row.wp_nama = ref.nama
    row.wp_alamat_1 = ref.alamat_1
    row.wp_alamat_2 = ref.alamat_2
    
    ref = ObjekPajak.get_by_id(row.objek_pajak_id)
    row.op_kode = ref.kode
    row.op_nama = ref.nama
    row.op_alamat_1 = ref.alamat_1
    row.op_alamat_2 = ref.alamat_2
    row.rekening_id = ref.pajaks.rekening_id
    row.rek_kode = ref.pajaks.rekenings.kode
    row.rek_nama = ref.pajaks.rekenings.nama
    
    if not row.kode and not row.no_id:
        invoice_no = DBSession.query(func.max(ARInvoice.no_id)).\
                               filter(ARInvoice.tahun_id==row.tahun_id,
                                      ARInvoice.unit_id==row.unit_id).scalar()
        if not invoice_no:
            row.no_id = 1
        else:
            row.no_id = invoice_no+1
    row.kode = "".join([str(row.tahun_id), re.sub("[^0-9]", "", row.unit_kode),
                        str(row.no_id).rjust(6,'0')])
    #if values['password']:
    #    row.password = values['password']
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, row)
    request.session.flash('No Bayar %s sudah disimpan.' % row.kode)
        
def route_list(request):
    return HTTPFound(location=request.route_url('arinvoice'))
    
def session_failed(request, session_name):
    try:
        session_name.set_appstruct(request.session[SESS_ADD_FAILED])
    except:
        pass
    r = dict(form=session_name) #request.session[session_name])
    del request.session[SESS_ADD_FAILED]
    return r
    
@view_config(route_name='arinvoice-add', renderer='templates/arinvoice/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                #request.session[SESS_ADD_FAILED] = request.params   
                #print e.render()
                #return HTTPFound(location=request.route_url('arinvoice-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, form) #SESS_ADD_FAILED)
    return dict(form=form, is_unit=0, is_sp=0)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ARInvoice).filter(ARInvoice.id==request.matchdict['id'],
                         ARInvoice.status_bayar==0)
    
def id_not_found(request):    
    msg = 'No Bayar ID %s tidak ditemukan atau sudah dibayar.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='arinvoice-edit', renderer='templates/arinvoice/add.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                #request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('arinvoice-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['objek_pajak_nm'] = row.objekpajaks.nama
    values['subjek_pajak_nm'] = row.subjekpajaks.nama
    values['unit_nm'] = row.units.nama
    #print values
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='arinvoice-delete', renderer='templates/arinvoice/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    if row.arsspds:
        form = Form(colander.Schema(), buttons=('cancel',))
    else:
        form = Form(colander.Schema(), buttons=('delete', 'cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'No Bayar ID %d %s sudah dihapus.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# Action #
##########    
def qry_arinv():
    return DBSession.query(ARInvoice).\
                            join(Unit)

@view_config(route_name='arinvoice-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    user = req.user
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('wp_kode'))
        columns.append(ColumnDT('op_kode'))
        columns.append(ColumnDT('op_nama'))
        columns.append(ColumnDT('rek_nama'))
        #columns.append(ColumnDT('pokok'))
        #columns.append(ColumnDT('denda'))
        #columns.append(ColumnDT('bunga'))
        columns.append(ColumnDT('jumlah',  filter=_DTnumberformat))
        columns.append(ColumnDT('unit_nama'))
        if 'g:wp' in group_finder(req.user.email,req):
            rows = SubjekPajak.get_by_user(user.id)
            ids = []
            if rows:
                for r in rows:
                    ids.append(r.id)
            query = qry_arinv().\
                    filter(ARInvoice.subjek_pajak_id.in_(ids))
                    
        if 'g:bendahara' in group_finder(req.user.email,req):
            rows = Pegawai.get_by_user(user.id)
            
            ids = []
            if rows:
                for r in rows:
                    ids.append(r.unit_id)
            query = qry_arinv().\
                    filter(ARInvoice.unit_id.in_(ids))
                    
        elif req.user.id==1 or 'g:admin' in group_finder(req.user.email,req):
            query = qry_arinv()
                          
        rowTable = DataTables(req, ARInvoice, query, columns)
        return rowTable.output_result()
