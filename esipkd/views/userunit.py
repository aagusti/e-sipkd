from email.utils import parseaddr
from sqlalchemy import not_, or_, func
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
from ..models import (
    DBSession,
    User,
    )
from ..models.isipkd import(
    Unit,
    UserUnit,
    )
from daftar import deferred_user, daftar_user, deferred_unit, daftar_unit, auto_unit_nm, auto_user_nm
from datatables import (
    ColumnDT, DataTables)

from esipkd.tools import DefaultTimeZone, _DTstrftime, _DTnumberformat, _DTactive, STATUS

SESS_ADD_FAILED = 'userunit add failed'
SESS_EDIT_FAILED = 'userunit edit failed'

########                    
# List #
########    
@view_config(route_name='user-unit', renderer='templates/userunit/list.pt',
             permission='read')
def view_list(request):
    rows = DBSession.query(User).filter(User.id > 0).order_by('email')
    return dict(rows=rows)
    

#######    
# Add #
#######

def form_validator(form, value):
    def err_unit():
        raise colander.Invalid(form,
            'User Unit sudah ada dalam database')
    q = DBSession.query(UserUnit).filter(UserUnit.user_id==value['user_id'],
                                         UserUnit.unit_id==value['unit_id'])
    found = q.first()
    if found:
        err_unit()

class AddSchema(colander.Schema):
    user_id  = colander.SchemaNode(
                    colander.Integer(),
                    widget = deferred_user,
                    oid="user_id",
                    title="User")
    """
    user_nm = colander.SchemaNode(
                    colander.String(),
                    widget = auto_user_nm,
                    oid = "user_nm",
                    title="User")
    """
    unit_id = colander.SchemaNode(
                    colander.Integer(),
                    widget = deferred_unit,
                    oid="unit_id",
                    title="OPD")
    """
    unit_nm  = colander.SchemaNode(
                    colander.String(),
                    widget = auto_unit_nm,
                    oid = 'unit_nm',
                    title="OPD")
    """

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_user = daftar_user(),
                         daftar_unit = daftar_unit())
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, userunit, row=None):
    user = DBSession.query(User).filter_by(id=values['user_id']).first()
    unit = DBSession.query(Unit).filter_by(id=values['unit_id']).first()
    userunit = UserUnit.set_one(None, user, unit)
    query_unit_member(values)
    return user

def query_unit_member(values):
    row_unit = DBSession.query(Unit).filter_by(id=values['unit_id']).first()
    row_unit.member_count = DBSession.query(
                                  func.count(UserUnit.user_id).label('c')).filter(
                                             UserUnit.unit_id==values['unit_id']).first().c
    DBSession.add(row_unit)
    
def save_request(values, request, row=None):
    row = save(values, request.user, row)
    request.session.flash('User OPD sudah disimpan.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('user-unit'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='user-unit-add', renderer='templates/userunit/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            #controls['email'] = controls['email'] or controls['userunit_name']+'@local'
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                #request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('user-unit-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)#.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(UserUnit).filter(UserUnit.user_id==request.matchdict['id'],
                                            UserUnit.unit_id==request.matchdict['id2'])
    
def id_not_found(request):    
    msg = 'User %s Unit ID %s not found.' % (request.matchdict['id'],request.matchdict['id2'])
    request.session.flash(msg, 'error')
    return route_list(request)

"""@view_config(route_name='user-unit-edit', renderer='templates/userunit/edit.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            #controls['email'] = controls['email'] or controls['userunit_name']+'@local'
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('user-unit-edit',id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    return dict(form=form.render(appstruct=values))
"""

##########
# Delete #
##########    
@view_config(route_name='user-unit-delete', renderer='templates/userunit/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    values= {}
    if request.POST:
        if 'delete' in request.POST:
            values['user_id'] = request.matchdict['id']
            values['unit_id'] = request.matchdict['id2']
            msg = 'User ID %d OPD %d has been deleted.' % (row.user_id, row.unit_id)
            DBSession.query(UserUnit).filter(UserUnit.user_id==values['user_id'],
                                             UserUnit.unit_id==values['unit_id']).delete()
            query_unit_member(values)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
                 
##########
# Action #
##########    
@view_config(route_name='user-unit-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('user_id'))
        columns.append(ColumnDT('unit_id'))
        columns.append(ColumnDT('user_name'))
        columns.append(ColumnDT('nama'))
        
        query = DBSession.query(UserUnit.user_id, UserUnit.unit_id, User.user_name, Unit.nama).\
                          join(User).join(Unit)
        rowTable = DataTables(req, UserUnit, query, columns)
        return rowTable.output_result()

    if url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('user_id'))
        columns.append(ColumnDT('unit_id'))
        columns.append(ColumnDT('user_name'))
        columns.append(ColumnDT('nama'))
        
        query = DBSession.query(UserUnit.user_id, UserUnit.unit_id, User.user_name, Unit.nama).\
                          join(User).join(Unit).\
                          filter(or_(User.user_name.ilike('%%%s%%' % cari),Unit.nama.ilike('%%%s%%' % cari)))
        rowTable = DataTables(req, UserUnit, query, columns)
        return rowTable.output_result()
