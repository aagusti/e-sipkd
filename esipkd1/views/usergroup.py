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
    Group,
    UserGroup,
    )
from daftar import deferred_user, daftar_user, deferred_group, daftar_group, auto_group_nm, auto_user_nm
from datatables import (
    ColumnDT, DataTables)

from esipkd.tools import DefaultTimeZone, _DTstrftime, _DTnumberformat, _DTactive, STATUS

SESS_ADD_FAILED = 'usergroup add failed'
SESS_EDIT_FAILED = 'usergroup edit failed'

########                    
# List #
########    
@view_config(route_name='usergroup', renderer='templates/usergroup/list.pt',
             permission='edit')
def view_list(request):
    rows = DBSession.query(User).filter(User.id > 0).order_by('email')
    return dict(rows=rows)
    

#######    
# Add #
#######

def form_validator(form, value):
    def err_group():
        raise colander.Invalid(form,
            'User Group  sudah ada dalam database')
    q = DBSession.query(UserGroup).filter(UserGroup.user_id==value['user_id'],
                                             UserGroup.group_id==value['group_id'])
    found = q.first()
    if found:
        err_group()

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
    group_id = colander.SchemaNode(
                    colander.Integer(),
                    widget = deferred_group,
                    oid="group_id",
                    title="Group")
    """
    group_nm  = colander.SchemaNode(
                    colander.String(),
                    widget = auto_group_nm,
                    oid = 'group_nm',
                    title="Group")
    """

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_user  = daftar_user(),
                         daftar_group = daftar_group())
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, usergroup, row=None):
    user = DBSession.query(User).filter_by(id=values['user_id']).first()
    group = DBSession.query(Group).filter_by(id=values['group_id']).first()
    usergroup = UserGroup.set_one(None, user, group)
    query_group_member(values)
    return user

def query_group_member(values):
    row_group = DBSession.query(Group).filter_by(id=values['group_id']).first()
    row_group.member_count = DBSession.query(
                                  func.count(UserGroup.user_id).label('c')).filter(
                                       UserGroup.group_id==values['group_id']).first().c
    DBSession.add(row_group)
    
def save_request(values, request, row=None):
    row = save(values, request.user, row)
    request.session.flash('UserGroup sudah disimpan.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('usergroup'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='usergroup-add', renderer='templates/usergroup/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            #controls['email'] = controls['email'] or controls['usergroup_name']+'@local'
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                #request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('usergroup-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)#.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(UserGroup).filter(UserGroup.user_id==request.matchdict['id'],
                                             UserGroup.group_id==request.matchdict['id2'])
    
def id_not_found(request):    
    msg = 'User %s Group ID %s not found.' % (request.matchdict['id'],request.matchdict['id2'])
    request.session.flash(msg, 'error')
    return route_list(request)

"""@view_config(route_name='usergroup-edit', renderer='templates/usergroup/edit.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            #controls['email'] = controls['email'] or controls['usergroup_name']+'@local'
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('usergroup-edit',
                                  id=row.id))
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
@view_config(route_name='usergroup-delete', renderer='templates/usergroup/delete.pt',
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
            values['user_id']  = request.matchdict['id']
            values['group_id'] = request.matchdict['id2']
            msg = 'User ID %d Group %d has been deleted.' % (row.user_id, row.group_id)
            DBSession.query(UserGroup).filter(UserGroup.user_id==values['user_id'],
                                              UserGroup.group_id==values['group_id']).delete()
            query_group_member(values)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())
                 

##########
# Action #
##########    
@view_config(route_name='usergroup-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('user_id'))
        columns.append(ColumnDT('group_id'))
        columns.append(ColumnDT('user_name'))
        columns.append(ColumnDT('group_name'))
        
        query = DBSession.query(UserGroup.user_id, UserGroup.group_id, User.user_name, Group.group_name).\
                          join(User).join(Group)
        rowTable = DataTables(req, UserGroup, query, columns)
        return rowTable.output_result()

    if url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('user_id'))
        columns.append(ColumnDT('group_id'))
        columns.append(ColumnDT('user_name'))
        columns.append(ColumnDT('group_name'))
        
        query = DBSession.query(UserGroup.user_id, UserGroup.group_id, User.user_name, Group.group_name).\
                          join(User).join(Group).\
                          filter(or_(User.user_name.ilike('%%%s%%' % cari),Group.group_name.ilike('%%%s%%' % cari)))
        rowTable = DataTables(req, UserGroup, query, columns)
        return rowTable.output_result()
