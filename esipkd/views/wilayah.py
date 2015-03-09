from email.utils import parseaddr
from sqlalchemy import not_
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
      Wilayah,
      )
from daftar import (
     deferred_wilayah, daftar_wilayah)
from datatables import (
    ColumnDT, DataTables)

SESS_ADD_FAILED = 'Gagal tambah wilayah'
SESS_EDIT_FAILED = 'Gagal edit wilayah'

########                    
# List #
########    
@view_config(route_name='wilayah', renderer='templates/wilayah/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode wilayah %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Uraian  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Wilayah).filter_by(id=uid)
        r = q.first()
    else:
        r = None
    q = DBSession.query(Wilayah).filter_by(kode=value['kode'])
    found = q.first()
    if r:
        if found and found.id != r.id:
            err_kode()
    elif found:
        err_email()
    if 'nama' in value: # optional
        found = Wilayah.get_by_nama(value['nama'])
        if r:
            if found and found.id != r.id:
                err_name()
        elif found:
            err_name()

class AddSchema(colander.Schema):
    kode   = colander.SchemaNode(
                    colander.String(),
                              )
    nama = colander.SchemaNode(
                    colander.String())
    level_id = colander.SchemaNode(
                    colander.Integer(),
                    title="Level")
    parent_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_wilayah,
                    title="Parent",
                    missing=colander.drop)

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_wilayah=daftar_wilayah())
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    if not row:
        row = Wilayah()
    row.from_dict(values)
    if not row.parent_id or row.parent_id==0 or row.parent_id=='0':
        row.parent_id=None
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, row)
    request.session.flash('wilayah %s sudah disimpan.' % row.kode)
        
def route_list(request):
    return HTTPFound(location=request.route_url('wilayah'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='wilayah-add', renderer='templates/wilayah/add.pt',
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
                return HTTPFound(location=request.route_url('wilayah-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(Wilayah).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'wilayah ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='wilayah-edit', renderer='templates/wilayah/edit.pt',
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
                return HTTPFound(location=request.route_url('wilayah-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['parent_id'] = 'parent_id' in values and values['parent_id']==None and -1 or values['parent_id']
    #print values['parent_id'], values['parent_id']==None
    return dict(form=form.render(appstruct=values))

##########
# Delete #
##########    
@view_config(route_name='wilayah-delete', renderer='templates/wilayah/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'wilayah ID %d %s has been deleted.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# Action #
##########    
@view_config(route_name='wilayah-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('level_id'))
        columns.append(ColumnDT('parent_id'))
        query = DBSession.query(Wilayah)
        rowTable = DataTables(req, Wilayah, query, columns)
        return rowTable.output_result()
