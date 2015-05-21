from email.utils import parseaddr
from sqlalchemy import not_, func
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
      Wilayah,
      Pajak,
      Rekening,
      ARInvoice
      )

from datatables import (
    ColumnDT, DataTables)
    
from daftar import (STATUS, deferred_status,
                    daftar_subjekpajak, deferred_subjekpajak,
                    daftar_wilayah, deferred_wilayah,
                    daftar_unit, deferred_unit,
                    daftar_pajak, deferred_pajak,
                    )

SESS_ADD_FAILED = 'Gagal tambah Objek Pajak'
SESS_EDIT_FAILED = 'Gagal edit Objek Pajak'
from daftar import STATUS
########                    
# List #
########    
@view_config(route_name='op', renderer='templates/op/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    

#######    
# Add #
#######

class AddSchema(colander.Schema):
    subjekpajak_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_subjekpajak,
                    title="Penyetor"
                    )
    wilayah_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_wilayah,
                    title="Wilayah"
                    )
    unit_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_unit,
                    title="OPD",
                    #title="SKPD/Unit Kerja"
                    )
                    
    pajak_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_pajak,
                    title="Rekening"
                    )
    kode   = colander.SchemaNode(
                    colander.String(),
                    widget=widget.HiddenWidget(),
                    oid="kode",
                    missing=colander.drop)
    nama = colander.SchemaNode(
                    colander.String(),
                    widget=widget.HiddenWidget(),
                    oid="nama",
                    missing=colander.drop)
    status = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status,
                    title="Status")

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True),
            title="")
                    

def get_form(request, class_form):
    schema = class_form()
    schema = schema.bind(daftar_status=STATUS,
                         daftar_subjekpajak=daftar_subjekpajak(),
                         daftar_pajak=daftar_pajak(),
                         daftar_unit=daftar_unit(),
                         daftar_wilayah=daftar_wilayah())
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    if not row:
        row = ObjekPajak()
    row.from_dict(values)
    p = values['pajak_id']
    x = values['kode']
    y = values['nama']
    if not x and not y:
        row1 = DBSession.query(Pajak).filter(Pajak.id==p).first()
        row.kode = row1.kode
        row.nama = row1.nama
        print "********------",row.kode, "********--------", row.nama
    
    #if values['password']:
    #    row.password = values['password']
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    print "****",values, "****", request
    row = save(values, row)
    request.session.flash('Objek %s sudah disimpan.' % row.kode)
        
def route_list(request):
    return HTTPFound(location=request.route_url('op'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='op-add', renderer='templates/op/add.pt',
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
                #request.session[SESS_ADD_FAILED] = e.render()               
                #return HTTPFound(location=request.route_url('op-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ObjekPajak).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Objek ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='op-edit', renderer='templates/op/edit.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    id  = row.id
    
    if not row:
        return id_not_found(request)
    x = DBSession.query(ARInvoice).filter(ARInvoice.objek_pajak_id==id).first()
    if x:
        request.session.flash('Tidak bisa diedit, karena objek sudah digunakan di daftar bayar.','error')
        return route_list(request)
        
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='op-delete', renderer='templates/op/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    id = row.id
    
    x = DBSession.query(ARInvoice).filter(ARInvoice.objek_pajak_id==id).first()
    if x:
        request.session.flash('Tidak bisa dihapus, karena objek sudah digunakan di daftar bayar.','error')
        return route_list(request)
        
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Objek %s sudah dihapus.' % (row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())

##########
# Action #
##########    
@view_config(route_name='op-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('subjekpajaks.kode'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('pajaks.kode'))
        columns.append(ColumnDT('wilayahs.nama'))
        columns.append(ColumnDT('status'))
        query = DBSession.query(ObjekPajak).join(SubjekPajak).join(Pajak).join(Wilayah)
        rowTable = DataTables(req, ObjekPajak, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='hon':
            term = 'term' in params and params['term'] or '' 
            subjek_pajak_id = 'subjek_pajak_id' in params and params['subjek_pajak_id'] or 0
            x = request.user.id
            rows = DBSession.query(ObjekPajak).join(SubjekPajak).join(Pajak).\
                             filter(ObjekPajak.nama.ilike('%%%s%%' % term),
                                    ObjekPajak.subjekpajak_id==SubjekPajak.id,
                                    SubjekPajak.id==subjek_pajak_id,
                                    ObjekPajak.pajak_id==Pajak.id,
                                    SubjekPajak.user_id==x).all()
            r = []
            for k in rows:
                print k
                d={}
                d['id']          = k.id
                d['value']       = k.nama
                d['sp_id']       = k.subjekpajaks.id
                d['sp_nm']       = k.subjekpajaks.nama
                d['unit_id']     = k.units.id
                d['unit_nm']     = k.units.nama
                d['tarif']       = k.pajaks.tarif
                
                r.append(d)
            return r             
