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
from ..models import DBSession, User, UserGroup, Group
from ..models.isipkd import(
      SubjekPajak,
      )

from datatables import (
    ColumnDT, DataTables)

from daftar import (STATUS, deferred_status,
                    daftar_user, deferred_user)


SESS_ADD_FAILED = 'Gagal tambah wp'
SESS_EDIT_FAILED = 'Gagal edit wp'

########                    
# List #
########    
@view_config(route_name='wp', renderer='templates/wp/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode wp %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Nama  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    def err_user():
        raise colander.Invalid(form,
            'User ID  %s sudah digunakan oleh ID %d' % (
                value['user_id'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(SubjekPajak).filter_by(id=uid)
        r = q.first()
    else:
        r = None
    q = DBSession.query(SubjekPajak).filter_by(kode=value['kode'])
    found = q.first()
    if r:
        if found and found.id != r.id:
            err_kode()
    elif found:
        err_kode()
        
    if 'nama' in value: # optional
        found = SubjekPajak.get_by_nama(value['nama'])
        if r:
            if found and found.id != r.id:
                err_name()
        elif found:
            err_name()
    if 'user_id' in value and int(value['user_id'])>0:
        found = SubjekPajak.get_by_user(value['user_id'])
        if r:
            if found and found.id != r.id:
                err_user()
        elif found:
            err_user()
    if 'login' in value and int(value['user_id'])==0:
        found = User.get_by_name(value['kode'])
        if r:
            if found and found.id != r.id:
                err_user()
        elif found:
            err_user()

class AddSchema(colander.Schema):
    kode     = colander.SchemaNode(
                    colander.String(),
               )
    nama     = colander.SchemaNode(
                    colander.String()
               )
    alamat_1 = colander.SchemaNode(
                    colander.String()
               )
    alamat_2 = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop
               )
    kelurahan= colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop
               )
    kecamatan= colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop
               )
    kota     = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop
               )
    propinsi = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop
               )
               
    status   = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status,
                    title="Status")
    user_id  = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_user,
                    default=0,
                    title="User")
    login    = colander.SchemaNode(
                    colander.Boolean(),
                    missing = colander.drop,
                    title='Buat Login'
               )
               
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS,
                         daftar_user=daftar_user(),
                         )
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    login = None
    if 'login' in values and values['login'] and int(values['user_id'])==0:
        login = User()
        login.user_password = values['kode']
        login.status=values['status'] 
        login.user_name=values['kode']
        login.email=values['kode']+'@ws'
        DBSession.add(login)
        DBSession.flush()
        
    if not row:
        row = SubjekPajak()
    row.from_dict(values)
    if login:
        row.user_id=login.id
    if not row.user_id:
        row.user_id=None
        
    DBSession.add(row)
    DBSession.flush()
    if row.user_id:
        q = DBSession.query(UserGroup).join(Group).filter(UserGroup.user_id==row.user_id,
                                            Group.group_name=='wp').first()
        if not q:
            usergroup = UserGroup()
            usergroup.user_id = row.user_id
            usergroup.group_id = DBSession.query(Group.id).filter_by(group_name='wp').scalar()
            DBSession.add(usergroup)
            DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, row)
    request.session.flash('wp %s sudah disimpan.' % row.kode)
        
def route_list(request):
    return HTTPFound(location=request.route_url('wp'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='wp-add', renderer='templates/wp/add.pt',
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
                return HTTPFound(location=request.route_url('wp-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(SubjekPajak).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'wp ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='wp-edit', renderer='templates/wp/edit.pt',
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
                return HTTPFound(location=request.route_url('wp-edit',
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
@view_config(route_name='wp-delete', renderer='templates/wp/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'wp ID %d %s has been deleted.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# Action #
##########    
@view_config(route_name='wp-act', renderer='json',
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
        columns.append(ColumnDT('alamat_1'))
        columns.append(ColumnDT('alamat_2'))
        columns.append(ColumnDT('status'))
        query = DBSession.query(SubjekPajak)
        rowTable = DataTables(req, SubjekPajak, query, columns)
        return rowTable.output_result()
