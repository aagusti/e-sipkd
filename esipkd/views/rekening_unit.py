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
    UnitRekening,
    Rekening
    )
from daftar import deferred_rekening, daftar_rekening, deferred_rekening1, daftar_rekening1, deferred_unit, daftar_unit, auto_unit_nm, auto_user_nm
from datatables import (
    ColumnDT, DataTables)

from esipkd.tools import DefaultTimeZone, _DTstrftime, _DTnumberformat, _DTactive, STATUS

SESS_ADD_FAILED = 'rekeningunit add failed'
SESS_EDIT_FAILED = 'rekeningunit edit failed'

########                    
# List #
########    
@view_config(route_name='rekening-unit', renderer='templates/rekeningunit/list.pt',
             permission='read')
def view_list(request):
    rows = DBSession.query(Rekening).filter(Rekening.id > 0).order_by('kode')
    return dict(rows=rows)
    

#######    
# Add #
#######

def form_validator(form, value):
    def err_unit():
        raise colander.Invalid(form,
            'Rekening Unit sudah ada dalam database')
    q = DBSession.query(UnitRekening).filter(UnitRekening.rekening_id==value['rekening_id'],
                                             UnitRekening.unit_id==value['unit_id'])
    found = q.first()
    if found:
        err_unit()

class AddSchema(colander.Schema):
    unit_id = colander.SchemaNode(
                    colander.Integer(),
                    widget = deferred_unit,
                    oid="unit_id",
                    title="OPD")
    rekening_id  = colander.SchemaNode(
                    colander.Integer(),
                    widget = deferred_rekening1,
                    oid="rekening_id",
                    title="Rekening")
    """
    user_nm = colander.SchemaNode(
                    colander.String(),
                    widget = auto_user_nm,
                    oid = "user_nm",
                    title="User")
    """
    """
    unit_nm  = colander.SchemaNode(
                    colander.String(),
                    widget = auto_unit_nm,
                    oid = 'unit_nm',
                    title="OPD")
    """

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_rekening1 = daftar_rekening1(),
                         daftar_unit     = daftar_unit())
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, rekeningunit, row=None):
    rekening = DBSession.query(Rekening).filter_by(id=values['rekening_id']).first()
    unit     = DBSession.query(Unit).filter_by(id=values['unit_id']).first()
    rekeningunit = UnitRekening.set_one(None, rekening, unit)
    query_unit_member(values)
    return rekening

def query_unit_member(values):
    row_unit = DBSession.query(Unit).filter_by(id=values['unit_id']).first()
    row_unit.member_count = DBSession.query(
                                  func.count(UnitRekening.rekening_id).label('c')).filter(
                                             UnitRekening.unit_id==values['unit_id']).first().c
    DBSession.add(row_unit)
    
def save_request(values, request, row=None):
    row = save(values, request, row)
    request.session.flash('Rekening OPD sudah disimpan.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('rekening-unit'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='rekening-unit-add', renderer='templates/rekeningunit/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            #controls['email'] = controls['email'] or controls['rekeningunit_name']+'@local'
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                #request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('rekening-unit-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)#.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(UnitRekening).filter(UnitRekening.rekening_id==request.matchdict['id'],
                                                UnitRekening.unit_id==request.matchdict['id2'])
    
def id_not_found(request):    
    msg = 'Rekening %s Unit ID %s not found.' % (request.matchdict['id'],request.matchdict['id2'])
    request.session.flash(msg, 'error')
    return route_list(request)

"""@view_config(route_name='user-unit-edit', renderer='templates/rekeningunit/edit.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            #controls['email'] = controls['email'] or controls['rekeningunit_name']+'@local'
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
@view_config(route_name='rekening-unit-delete', renderer='templates/rekeningunit/delete.pt',
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
            values['rekening_id'] = request.matchdict['id']
            values['unit_id']     = request.matchdict['id2']
            msg = 'Rekening ID %d OPD %d has been deleted.' % (row.rekening_id, row.unit_id)
            DBSession.query(UnitRekening).filter(UnitRekening.rekening_id==values['rekening_id'],
                                                 UnitRekening.unit_id==values['unit_id']).delete()
            query_unit_member(values)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
                 
##########
# Action #
##########    
@view_config(route_name='rekening-unit-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('rekening_id'))
        columns.append(ColumnDT('unit_id'))
        columns.append(ColumnDT('unit_nm'))
        columns.append(ColumnDT('nama'))
        
        query = DBSession.query(UnitRekening.rekening_id, 
                                UnitRekening.unit_id, 
                                Unit.nama.label('unit_nm'), 
                                Rekening.nama).\
                          join(Rekening).join(Unit)
        rowTable = DataTables(req, UnitRekening, query, columns)
        return rowTable.output_result()

    if url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('rekening_id'))
        columns.append(ColumnDT('unit_id'))
        columns.append(ColumnDT('unit_nm'))
        columns.append(ColumnDT('nama'))
        
        query = DBSession.query(UnitRekening.rekening_id, 
                                UnitRekening.unit_id, 
                                Unit.nama.label('unit_nm'), 
                                Rekening.nama).\
                          join(Rekening).join(Unit).\
                          filter(or_(Rekening.nama.ilike('%%%s%%' % cari),Unit.nama.ilike('%%%s%%' % cari)))
        rowTable = DataTables(req, UnitRekening, query, columns)
        return rowTable.output_result()
