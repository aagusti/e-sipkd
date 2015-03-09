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
      Rekening
      )

from datatables import (
    ColumnDT, DataTables)

SESS_ADD_FAILED = 'Gagal tambah Objek Pajak'
SESS_EDIT_FAILED = 'Gagal edit Objek Pajak'
from daftar import (STATUS, deferred_status,
                    daftar_subjekpajak, deferred_subjekpajak,
                    daftar_wilayah, deferred_wilayah,
                    daftar_unit, deferred_unit,
                    daftar_pajak, deferred_pajak,
                    )
########                    
# List #
########    
@view_config(route_name='sptpd', renderer='templates/sptpd/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode sptpd %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Uraian  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(ObjekPajak).filter_by(id=uid)
        r = q.first()
    else:
        r = None
    q = DBSession.query(ObjekPajak).filter_by(kode=value['kode'])
    found = q.first()
    if r:
        if found and found.id != r.id:
            err_kode()
    elif found:
        err_email()
    if 'nama' in value: # sptpdtional
        found = ObjekPajak.get_by_nama(value['nama'])
        if r:
            if found and found.id != r.id:
                err_name()
        elif found:
            err_name()
            
class AddSchema(colander.Schema):
    subjekpajak_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_subjekpajak,
                    title="Subjek Pajak"
                    )
    wilayah_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_wilayah,
                    title="Wilayah"
                    )
    unit_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_unit,
                    title="SKPD"
                    )
                    
    pajak_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_pajak,
                    title="Pajak"
                    )
    kode   = colander.SchemaNode(
                    colander.String(),
                              )
    nama = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    title="Uraian")
    status = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status,
                    title="Status")

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS,
                         daftar_subjekpajak=daftar_subjekpajak(),
                         )
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    if not row:
        row = ObjekPajak()
    row.from_dict(values)
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
    request.session.flash('SPTPD %s sudah disimpan.' % row.kode)
        
def route_list(request):
    return HTTPFound(location=request.route_url('sptpd'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='sptpd-add', renderer='templates/sptpd/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('sptpd-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(ObjekPajak).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'sptpd ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='sptpd-edit', renderer='templates/sptpd/edit.pt',
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
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('sptpd-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    return dict(form=form.render(appstruct=values))

##########
# Delete #
##########    
@view_config(route_name='sptpd-delete', renderer='templates/sptpd/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'sptpd ID %d %s has been deleted.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# Action #
##########    
@view_config(route_name='sptpd-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('registrasi'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('pajak'))
        columns.append(ColumnDT('wilayah'))
        columns.append(ColumnDT('status'))
        query = DBSession.query(ObjekPajak.id, ObjekPajak.kode,ObjekPajak.nama,
                                Rekening.kode.label('pajak'), SubjekPajak.kode.label('registrasi'),
                                Wilayah.nama.label('wilayah'), ObjekPajak.status).\
                                join(SubjekPajak).join(Wilayah).join(Pajak).join(Rekening)
                          
        rowTable = DataTables(req, ObjekPajak, query, columns)
        return rowTable.output_result()
