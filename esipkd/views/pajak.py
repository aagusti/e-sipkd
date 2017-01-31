from email.utils import parseaddr
from sqlalchemy import not_
from datetime import datetime
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
      Pajak,
      Rekening,
      UnitRekening
      )

from daftar import STATUS, deferred_status, daftar_rekening, deferred_rekening, daftar_rekening1, deferred_rekening1, auto_rekening_nm
      
from datatables import (
    ColumnDT, DataTables)

from esipkd.tools import DefaultTimeZone, _DTstrftime, _DTnumberformat, _DTactive

SESS_ADD_FAILED = 'Gagal tambah pajak'
SESS_EDIT_FAILED = 'Gagal edit pajak'

########                    
# List #
########    
@view_config(route_name='pajak', renderer='templates/pajak/list.pt',
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
            'Kode pajak %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Pajak).filter_by(id=uid)
        r = q.first()
    else:
        r = None
    q = DBSession.query(Pajak).filter_by(kode=value['kode'])
    found = q.first()
    if r:
        if found and found.id != r.id:
            err_kode()

class AddSchema(colander.Schema):
    rekening_select = DBSession.query(Rekening.id,Rekening.nama).\
                      filter(Rekening.level_id==5).all()
    
    kode        = colander.SchemaNode(
                    colander.String())
    nama        = colander.SchemaNode(
                    colander.String(),
                    missing = colander.drop)
    rekening_id = colander.SchemaNode(
                    colander.Integer(),
                    widget = deferred_rekening1,
                    oid="rekening_id",
                    title="Rekening")
    """
    rekening_nm = colander.SchemaNode(
                    colander.String(),
                    widget=auto_rekening_nm,
                    oid="rekening_nm",
                    title="Rekening")
    """
    tahun   = colander.SchemaNode(
                    colander.Integer(),
                    missing = colander.drop
                    )
    tarif   = colander.SchemaNode(
                    colander.Integer(),
                    title='Tarif (%)')
    status  = colander.SchemaNode(
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
                         daftar_rekening1=daftar_rekening1())
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    if not row:
        row = Pajak()
    row.from_dict(values)
    if not row.nama:
        x = DBSession.query(Rekening.nama).filter(Rekening.id==row.rekening_id).first()
        row.nama = x
    if not row.tahun:
        row.tahun = datetime.now().strftime('%Y')
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    print "****",values, "****", request
    row = save(values, row)
    request.session.flash('Pajak %s %s sudah disimpan.' % (row.kode, row.nama))
        
def route_list(request):
    return HTTPFound(location=request.route_url('pajak'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='pajak-add', renderer='templates/pajak/add.pt',
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
                return HTTPFound(location=request.route_url('pajak-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)#.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(Pajak).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Pajak ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='pajak-edit', renderer='templates/pajak/edit.pt',
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
                return HTTPFound(location=request.route_url('pajak-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        #return session_failed(request, SESS_EDIT_FAILED)
        del request.session[SESS_EDIT_FAILED]
        return dict(form=form)
    values = row.to_dict()
    #values['rekening_nm'] =row.rekenings.nama
    #print values
    form.set_appstruct(values)
    return dict(form=form)#.render(appstruct=values))

##########
# Delete #
##########    
@view_config(route_name='pajak-delete', renderer='templates/pajak/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Pajak ID %d %s has been deleted.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# Action #
##########    
@view_config(route_name='pajak-act', renderer='json',
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
        columns.append(ColumnDT('rekening'))
        columns.append(ColumnDT('tahun'))
        columns.append(ColumnDT('tarif'))
        columns.append(ColumnDT('status', filter=_DTactive))
        
        query = DBSession.query(Pajak.id,
                                Pajak.kode,
                                Pajak.nama,
                                Pajak.status,
                                Pajak.tahun,
                                Pajak.tarif,
                                Rekening.nama.label('rekening'),
                                ).\
                join(Rekening)                
        rowTable = DataTables(req, Pajak, query, columns)
        return rowTable.output_result()

    elif url_dict['act']=='hon':
        term    = 'term'    in params and params['term']    or '' 
        unit_id = 'unit_id' in params and params['unit_id'] or '' 
        qry = DBSession.query(Pajak.id, Pajak.nama, Rekening.kode).\
                  join(Rekening).join(UnitRekening).\
                  filter(Pajak.status==1)
        qry = qry.filter(Pajak.nama.ilike('%%%s%%' % term))
        qry = qry.filter(UnitRekening.unit_id==unit_id)
        rows = qry.all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            d['rekening_kd'] = k[2]
            r.append(d)
        return r

    elif url_dict['act']=='hon_fast':
        term    = 'term'    in params and params['term']    or '' 
        unit_id = 'unit_id' in params and params['unit_id'] or '' 
        qry = DBSession.query(Pajak.id, Pajak.nama, Pajak.tarif).\
                  join(Rekening).join(UnitRekening).\
                  filter(Pajak.status==1)
        qry = qry.filter(Pajak.nama.ilike('%%%s%%' % term))
        qry = qry.filter(UnitRekening.unit_id==unit_id)
        rows = qry.all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            d['tarif']       = k[2]
            r.append(d)
        return r

    elif url_dict['act']=='hon_tbp_new':
        term    = 'term'    in params and params['term']    or '' 
        unit_id = 'unit_id' in params and params['unit_id'] or '' 
        qry = DBSession.query(Pajak.id, Pajak.nama, Pajak.tarif).\
                  join(Rekening).join(UnitRekening).\
                  filter(Pajak.status==1)
        qry = qry.filter(Pajak.nama.ilike('%%%s%%' % term))
        qry = qry.filter(UnitRekening.unit_id==unit_id)
        rows = qry.all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            d['tarif']       = k[2]
            r.append(d)
        return r