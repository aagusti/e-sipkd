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
from ..models import DBSession, User
from ..models.isipkd import(
      Pegawai,
      Jabatan,
      Unit
      )

from daftar import (STATUS, deferred_status, 
                    daftar_jabatan, deferred_jabatan,
                    daftar_unit, deferred_unit)
      
from datatables import (
    ColumnDT, DataTables)

from esipkd.tools import DefaultTimeZone, _DTstrftime, _DTnumberformat, _DTactive


SESS_ADD_FAILED = 'Gagal tambah pegawai'
SESS_EDIT_FAILED = 'Gagal edit pegawai'

########                    
# List #
########    
@view_config(route_name='pegawai', renderer='templates/pegawai/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode pegawai %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_user(email):
        raise colander.Invalid(form,
            'User ID untuk Pegawai %s sudah ada email # %s' % (value['nama'], email))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Pegawai).filter_by(id=uid)
        r = q.first()
    else:
        r = None
    q = DBSession.query(Pegawai).filter_by(kode=value['kode'])
    found = q.first()
    if r:
        if found and found.id != r.id:
            err_kode()
        if r and r.user_id and value['login']:
            err_user(r.users.email)
class AddSchema(colander.Schema):
    kode   = colander.SchemaNode(
                    colander.String(),
                    title="NIP")
    nama = colander.SchemaNode(
                    colander.String())
                    
    unit_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_unit,
                    title="OPD")
           
    jabatan_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_jabatan,
                    title="Jabatan")
           
    status = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status,
                    title="Status")
                    
    login = colander.SchemaNode(
                    colander.Boolean(),
                    missing = colander.drop,
                    title="Buat Login")
    

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS, daftar_jabatan=daftar_jabatan(),
                         daftar_unit=daftar_unit())
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    login = None
    if 'login' in values and values['login']:
        login = User()
        login.user_password = values['kode']
        login.status=values['status'] 
        login.user_name=values['nama']
        login.email=values['kode']+'@local'
        DBSession.add(login)
        DBSession.flush()
    if not row:
        row = Pegawai()
    row.user_id = 'login' in values and values['login'] and not row.user_id and login.id or None
    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
        
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, row)
    request.session.flash('Pegawai <strong>%s</strong> sudah disimpan.' % row.nama)
        
def route_list(request):
    return HTTPFound(location=request.route_url('pegawai'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='pegawai-add', renderer='templates/pegawai/add.pt',
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
                return HTTPFound(location=request.route_url('pegawai-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)#.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(Pegawai).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'pegawai ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='pegawai-edit', renderer='templates/pegawai/edit.pt',
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
                return HTTPFound(location=request.route_url('pegawai-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    #print values
    form.set_appstruct(values)
    
    return dict(form=form)#.render(appstruct=values))

##########
# Delete #
##########    
@view_config(route_name='pegawai-delete', renderer='templates/pegawai/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'pegawai ID %d %s has been deleted.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# Action #
##########    
@view_config(route_name='pegawai-act', renderer='json',
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
        columns.append(ColumnDT('skpd'))
        columns.append(ColumnDT('jabatan'))
        columns.append(ColumnDT('status', filter=_DTactive))
        
        query = DBSession.query(Pegawai.id,
                                Pegawai.kode,
                                Pegawai.nama,
                                Pegawai.status,
                                Jabatan.nama.label('jabatan'),
                                Unit.nama.label('skpd')
                                ).\
                join(Jabatan).join(Unit)
                
        rowTable = DataTables(req, Pegawai, query, columns)
        return rowTable.output_result()
