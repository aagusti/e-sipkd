from email.utils import parseaddr
from sqlalchemy import not_, func
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
      Produk,
      )
from daftar import (
     deferred_wilayah, daftar_wilayah, auto_wilayah_nm, deferred_wilayah1, daftar_wilayah1)
from datatables import (
    ColumnDT, DataTables)

SESS_ADD_FAILED = 'Gagal tambah produk'
SESS_EDIT_FAILED = 'Gagal edit produk'

########                    
# List #
########    
@view_config(route_name='sptpd-produk', renderer='templates/produk/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    
##########
# Action #
##########    
@view_config(route_name='sptpd-produk-act', renderer='json',
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
        columns.append(ColumnDT('status'))
        
        query = DBSession.query(Produk)
        rowTable = DataTables(req, Produk, query, columns)
        return rowTable.output_result()   

    elif url_dict['act']=='hon_produk':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Produk.id, 
                               Produk.nama, 
                               Produk.kode
                       ).filter(Produk.nama.ilike('%%%s%%' % term) 
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            d['kode']        = k[2]
            r.append(d)
        return r     

from ..reports.rml_report import open_rml_row, open_rml_pdf, pdf_response
def query_reg():
    return DBSession.query(Produk.kode, Produk.nama).order_by(Produk.kode)
    
########      
########                    
# CSV #
########          
@view_config(route_name='sptpd-produk-csv', renderer='csv')
def view_csv(request):
    ses = request.session
    params = request.params
    url_dict = request.matchdict 
    u = request.user.id
    a = datetime.now().strftime('%d-%m-%Y')
    if url_dict['csv']=='reg' :
        query = query_reg()
        row = query.first()
        header = row.keys()
        rows = []
        for item in query.all():
            rows.append(list(item))

        # override attributes of response
        filename = 'Produk_BBM_%s.csv' %(a)
        request.response.content_disposition = 'attachment;filename=' + filename

    return {
      'header': header,
      'rows'  : rows,
    } 
        
##########
# PDF    #
##########    
@view_config(route_name='sptpd-produk-pdf', permission='read')
def view_pdf(request):
    params   = request.params
    url_dict = request.matchdict
    if url_dict['pdf']=='reg' :
        query = query_reg()
        rml_row = open_rml_row('produk.row.rml')
        rows=[]
        for r in query.all():
            s = rml_row.format(kode=r.kode, nama=r.nama)
            rows.append(s)
            
        pdf, filename = open_rml_pdf('produk.rml', rows=rows)
        return pdf_response(request, pdf, filename)  

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode Produk %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Uraian  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Produk).filter_by(id=uid)
        r = q.first()
    else:
        r = None
    q = DBSession.query(Produk).filter_by(kode=value['kode'])
    found = q.first()
    if r:
        if found and found.id != r.id:
            err_kode()
    elif found:
        err_kode()
    if 'nama' in value: # optional
        found = Produk.get_by_nama(value['nama'])
        if r:
            if found and found.id != r.id:
                err_name()
        elif found:
            err_name()

@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (0, 'Tidak Aktif'),
    (1, 'Aktif'),
    )   

class AddSchema(colander.Schema):
    kode    = colander.SchemaNode(
              colander.String(),
              oid = "kode",
              title = "Kode",)
    nama    = colander.SchemaNode(
              colander.String(),
              oid = "nama",
              title = "Nama",)
    status  = colander.SchemaNode(
              colander.Integer(),
              widget=deferred_status)

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    if not row:
        row = Produk()
    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, row)
    request.session.flash('Produk %s sudah disimpan.' % row.nama)
        
def route_list(request):
    return HTTPFound(location=request.route_url('sptpd-produk'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='sptpd-produk-add', renderer='templates/produk/add.pt',
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
                return HTTPFound(location=request.route_url('sptpd-produk-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Produk).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Produk ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='sptpd-produk-edit', renderer='templates/produk/edit.pt',
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
                return HTTPFound(location=request.route_url('sptpd-produk-edit',id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='sptpd-produk-delete', renderer='templates/produk/delete.pt',
             permission='delete')
def view_delete(request):
    q   = query_id(request)
    row = q.first()
    uid = row.id
    
    if not row:
        return id_not_found(request)
        
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Produk ID %d %s berhasil dihapus.' % (row.id, row.nama)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())