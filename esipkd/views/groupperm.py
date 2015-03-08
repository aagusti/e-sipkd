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
from ..models import (
    DBSession,
    Route,
    Group,
    GroupRoutePermission,
    )
from datatables import (
    ColumnDT, DataTables)

from esipkd.tools import DefaultTimeZone, _DTstrftime, _DTnumberformat, _DTactive, STATUS

SESS_ADD_FAILED = 'groupperm add failed'
SESS_EDIT_FAILED = 'groupperm edit failed'

########                    
# List #
########    
@view_config(route_name='groupperm', renderer='templates/groupperm/list.pt',
             permission='edit')
def view_list(request):
    #rows = DBSession.query(User).filter(User.id > 0).order_by('email')
    return dict(rows=None)
    

#######    
# Add #
#######

def form_validator(form, value):
    def err_group():
        raise colander.Invalid(form,
            'Group Permission  sudah ada dalam database')
    q = DBSession.query(GroupRoutePermission).filter(GroupRoutePermission.route_id==value['route_id'],
                                             GroupRoutePermission.group_id==value['group_id'])
    found = q.first()
    if found:
        err_group()

class AddSchema(colander.Schema):
    group_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.SelectWidget(values=DBSession.query(Group.id,Group.group_name).all()),
                    title="Group")
    route_id  = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.SelectWidget(values=DBSession.query(Route.id,Route.nama).all()),
                    title="Route")

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS)
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, groupperm, row=None):
    #route = DBSession.query(Route).filter_by(id=values['route_id']).first()
    #group = DBSession.query(Group).filter_by(id=values['group_id']).first()
    groupperm = GroupRoutePermission()
    groupperm.from_dict(values)
    DBSession.add(groupperm)
    DBSession.flush()
    return groupperm
    
def save_request(values, request, row=None):
    row = save(values, request.user, row)
    request.session.flash('groupperm sudah disimpan.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('groupperm'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='groupperm-add', renderer='templates/groupperm/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            #controls['email'] = controls['email'] or controls['groupperm_name']+'@local'
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('groupperm-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(GroupRoutePermission).filter(GroupRoutePermission.route_id==request.matchdict['id2'],
                                             GroupRoutePermission.group_id==request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Group ID %s Route %s not found.' % (request.matchdict['id'],request.matchdict['id2'])
    request.session.flash(msg, 'error')
    return route_list(request)

"""@view_config(route_name='groupperm-edit', renderer='templates/groupperm/edit.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            #controls['email'] = controls['email'] or controls['groupperm_name']+'@local'
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('groupperm-edit',
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
@view_config(route_name='groupperm-delete', renderer='templates/groupperm/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Group %s Route ID %s sudah dihapus.' % (row.groups.group_name, 
                                                           row.routes.nama)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())
                 

##########
# Action #
##########    
@view_config(route_name='groupperm-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('group_id'))
        columns.append(ColumnDT('route_id'))
        columns.append(ColumnDT('group_name'))
        columns.append(ColumnDT('route_name'))
        
        query = DBSession.query(GroupRoutePermission.route_id, 
                                GroupRoutePermission.group_id, 
                                Route.nama.label('route_name'), 
                                Group.group_name).\
                          join(Route).join(Group)
        rowTable = DataTables(req, GroupRoutePermission, query, columns)
        return rowTable.output_result()
