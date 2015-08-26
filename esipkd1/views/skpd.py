from email.utils import parseaddr
from sqlalchemy import not_
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
import re
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from ..models import DBSession
from ..models.isipkd import(
      Unit,
      UserUnit,
      User
      )
from ..models.__init__ import(
      UserGroup
      )
from datatables import (
    ColumnDT, DataTables)

SESS_ADD_FAILED = 'Gagal tambah rekening'
SESS_EDIT_FAILED = 'Gagal edit rekening'

########                    
# List #
########    
@view_config(route_name='skpd', renderer='templates/skpd/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    

#######    
# Add #
#######
def email_validator(node, value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        raise colander.Invalid(node, 'Invalid email format')

def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode Rekening %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Uraian  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Unit).filter_by(id=uid)
        r = q.first()
    else:
        r = None
    q = DBSession.query(Unit).filter_by(kode=value['kode'])
    found = q.first()
    if r:
        if found and found.id != r.id:
            err_kode()
    elif found:
        err_email()
    if 'nama' in value: # optional
        found = Unit.get_by_nama(value['nama'])
        if r:
            if found and found.id != r.id:
                err_name()
        elif found:
            err_name()

@colander.deferred
def deferred_summary(node, kw):
    values = kw.get('daftar_summary', [])
    return widget.SelectWidget(values=values)
    
SUMMARIES = (
    (1, 'Header'),
    (0, 'Detail'),
    )    

class AddSchema(colander.Schema):
    kode   = colander.SchemaNode(
                    colander.String(),
                              )
    nama = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop)
    level_id = colander.SchemaNode(
                    colander.Integer())
    is_summary = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.SelectWidget(values=SUMMARIES),
                    title="Header")


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_summary=SUMMARIES)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    if not row:
        row = Unit()
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
    request.session.flash('Rekening %s sudah disimpan.' % row.kode)
        
def route_list(request):
    return HTTPFound(location=request.route_url('skpd'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='skpd-add', renderer='templates/skpd/add.pt',
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
                return HTTPFound(location=request.route_url('skpd-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)#.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(Unit).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Rekening ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='skpd-edit', renderer='templates/skpd/edit.pt',
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
                return HTTPFound(location=request.route_url('skpd-edit',
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
@view_config(route_name='skpd-delete', renderer='templates/skpd/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Rekening ID %d %s has been deleted.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# Action #
##########    
@view_config(route_name='skpd-act', renderer='json',
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
        columns.append(ColumnDT('is_summary'))
        query = DBSession.query(Unit)
        rowTable = DataTables(req, Unit, query, columns)
        return rowTable.output_result()

    elif url_dict['act']=='hon':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Unit.id, Unit.nama
                       ).filter( Unit.is_summary==0,
                                 Unit.nama.ilike('%%%s%%' % term)).all()
        r = []
        for k in rows:
            d={}
            d['id']    = k[0]
            d['value'] = k[1]
            d['nama']  = k[1]
            r.append(d)
        return r 

    elif url_dict['act']=='hon_reg':
        term = 'term' in params and params['term'] or '' 
        unit_id = 'unit_id' in params and params['unit_id'] or 0
        print '---------------Unit---------------',unit_id

        rows = DBSession.query(Unit.id, Unit.nama
                       ).filter( Unit.id==unit_id,
                                 Unit.nama.ilike('%%%s%%' % term)).all()
        r = []
        for k in rows:
            d={}
            d['id']    = k[0]
            d['value'] = k[1]
            d['nama']  = k[1]
            r.append(d)
        print '---------------Unit---------------',r
        return r   

    elif url_dict['act']=='hon_ob':
        term = 'term' in params and params['term'] or '' 
        unit_id = 'unit_id' in params and params['unit_id'] or 0
        print '---------------Unit Param----------------',unit_id
        
        rows = DBSession.query(Unit.id, Unit.nama
                       ).filter(Unit.id==unit_id,
                                Unit.nama.ilike('%%%s%%' % term)).all()
        r = []
        for k in rows:
            d={}
            d['id']    = k[0]
            d['value'] = k[1]
            d['nama']  = k[1]
            r.append(d)
        print '---------------Unit------------------',r
        return r 
    
    elif url_dict['act']=='hon_fast':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Unit.id, Unit.nama
                       ).filter(Unit.nama.ilike('%%%s%%' % term), Unit.level_id==3).all()
        r = []
        for k in rows:
            d={}
            d['id']    = k[0]
            d['value'] = k[1]
            d['nama']  = k[1]
            r.append(d)
        print '---------------Unit------------------',r
        return r
		
    elif url_dict['act']=='hon_wp':
        term = 'term' in params and params['term'] or '' 
        u = request.user.id
        print '---------------User Login----------------',u
        
        a = DBSession.query(UserGroup.group_id).filter(UserGroup.user_id==u).first()
        b = '%s' % a
        c = int(b)        
        print '----------------Group_id-----------------',c
        
        if c == 1: #Untuk login WP
            x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            if x=='None' or not x:
                return {'success':False}
                
            y = '%s' % x
            z = int(y)        
            print '---------------Unit_id---------------',z
            
            rows = DBSession.query(Unit.id, Unit.nama
                           ).filter( Unit.id==z,
                                     Unit.nama.ilike('%%%s%%' % term), Unit.level_id==3).all()
            r = []
            for k in rows:
                d={}
                d['id']    = k[0]
                d['value'] = k[1]
                d['nama']  = k[1]
                r.append(d)
            print '---------------Unit------------------',r
            return r     
            
        elif c == 2: #Untuk login Bendahara
            x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            if x=='None' or not x:
                return {'success':False}

            y = '%s' % x
            z = int(y)        
            print '---------------Unit_id---------------',z
            
            rows = DBSession.query(Unit.id, Unit.nama
                           ).filter( Unit.id==z,
                                     Unit.nama.ilike('%%%s%%' % term), Unit.level_id==3).all()
            r = []
            for k in rows:
                d={}
                d['id']    = k[0]
                d['value'] = k[1]
                d['nama']  = k[1]
                r.append(d)
            print '---------------Unit------------------',r
            return r 
            
        elif c == 3: #Untuk login Admin
            rows = DBSession.query(Unit.id, Unit.nama
                           ).filter(Unit.nama.ilike('%%%s%%' % term), Unit.level_id==3).all()
            r = []
            for k in rows:
                d={}
                d['id']    = k[0]
                d['value'] = k[1]
                d['nama']  = k[1]
                r.append(d)
            print '---------------Unit------------------',r
            return r 
            
        else: #Untuk login BUD
            rows = DBSession.query(Unit.id, Unit.nama
                           ).filter(Unit.nama.ilike('%%%s%%' % term), Unit.level_id==3).all()
            r = []
            for k in rows:
                d={}
                d['id']    = k[0]
                d['value'] = k[1]
                d['nama']  = k[1]
                r.append(d)
            print '---------------Unit------------------',r
            return r 
                