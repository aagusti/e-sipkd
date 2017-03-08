import sys
import re
from email.utils import parseaddr
from sqlalchemy import not_, func, or_, desc
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
      UnitRekening,
      UserUnit,
      Anggaran
      )

from daftar import STATUS, deferred_status, daftar_rekening, deferred_rekening, daftar_rekening1, deferred_rekening1, auto_rekening_nm    
from ..security import group_in
from datatables import (
    ColumnDT, DataTables)

from esipkd.tools import DefaultTimeZone, _DTstrftime, _DTnumberformat, _DTactive

SESS_ADD_FAILED = 'Gagal tambah anggaran'
SESS_EDIT_FAILED = 'Gagal edit anggaran'

########                    
# List #
########    
@view_config(route_name='anggaran', renderer='templates/anggaran/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode rekening anggaran %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Anggaran).filter_by(id=uid)
        r = q.first()
    else:
        r = None
    q = DBSession.query(Anggaran).filter_by(kode=value['kode'])
    found = q.first()
    if r:
        if found and found.id != r.id:
            err_kode()

class AddSchema(colander.Schema):
    moneywidget = widget.MoneyInputWidget(
            size=20, options={'allowZero':True,
                              'precision':0
                              })
    kode        = colander.SchemaNode(
                    colander.String(),
                    missing = colander.drop,
                    widget=widget.HiddenWidget(),
                    oid="kode")
    nama        = colander.SchemaNode(
                    colander.String(),
                    missing = colander.drop,
                    widget=widget.HiddenWidget(),
                    oid="nama")
    rekening_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid="rekening_id")
    rekening_kd = colander.SchemaNode(
                    colander.String(),
                    oid="rekening_kd",
                    title="Kode Rekening")
    rekening_nm = colander.SchemaNode(
                    colander.String(),
                    oid="rekening_nm",
                    title="Uraian Rekening")
    murni       = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "murni")
    perubahan   = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "perubahan")
    tahun       = colander.SchemaNode(
                    colander.Integer(),
                    missing = colander.drop)
    status      = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status,
                    title="Status")
    

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
        row = Anggaran()
    row.from_dict(values)
    print "----- LEWAT -------------------"
    row.murni     = re.sub("[^0-9]", "", row.murni)
    row.perubahan = re.sub("[^0-9]", "", row.perubahan)
    
    if not row.kode:
        k = DBSession.query(Rekening.kode).filter(Rekening.id==row.rekening_id).first()
        row.kode = k
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
    row = save(values, row)
    request.session.flash('Anggaran %s %s sudah disimpan.' % (row.kode, row.nama))
        
def route_list(request):
    return HTTPFound(location=request.route_url('anggaran'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='anggaran-add', renderer='templates/anggaran/add.pt',
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
                #return HTTPFound(location=request.route_url('anggaran-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, form) #, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Anggaran).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Anggaran ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='anggaran-edit', renderer='templates/anggaran/add.pt',
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
                return HTTPFound(location=request.route_url('anggaran-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        del request.session[SESS_EDIT_FAILED]
        return dict(form=form)
    values = row.to_dict()
    values['rekening_kd'] = row.rekenings and row.rekenings.kode or ''
    values['rekening_nm'] = row.rekenings and row.rekenings.nama or ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='anggaran-delete', renderer='templates/anggaran/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Anggaran %s Tahun %s sudah berhasil dihapus.' % (row.kode, row.tahun)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,form=form.render())

##########
# Action #
##########    
@view_config(route_name='anggaran-act', renderer='json',
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
        columns.append(ColumnDT('murni',     filter=_DTnumberformat))
        columns.append(ColumnDT('perubahan', filter=_DTnumberformat))
        columns.append(ColumnDT('tahun'))
        columns.append(ColumnDT('status', filter=_DTactive))
        query = DBSession.query(Anggaran.id,
                                Anggaran.kode,
                                Anggaran.nama,
                                Anggaran.murni,
                                Anggaran.perubahan,
                                Anggaran.tahun,
                                Anggaran.status,
                        ).order_by(desc(Anggaran.tahun),
                                   Anggaran.kode,
                                   Anggaran.nama
                        )               
        rowTable = DataTables(req, Anggaran, query, columns)
        return rowTable.output_result()

    elif url_dict['act']=='hon':
        term    = 'term'    in params and params['term']    or '' 
        unit_id = 'unit_id' in params and params['unit_id'] or '' 
        qry = DBSession.query(Anggaran.id, Anggaran.nama, Rekening.kode).\
                  join(Rekening).join(UnitRekening).\
                  filter(Anggaran.status==1)
        qry = qry.filter(Anggaran.nama.ilike('%%%s%%' % term))
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
        
from ..reports.rml_report import open_rml_row, open_rml_pdf, pdf_response
def query_reg():
    return DBSession.query(Anggaran.kode.label('a'), 
                           Anggaran.nama.label('b'), 
                           func.trim(func.to_char(Anggaran.murni,'999,999,999,990')).label('c'),
                           func.trim(func.to_char(Anggaran.perubahan,'999,999,999,990')).label('d'),
                           Anggaran.tahun.label('e'),
                   ).order_by(desc(Anggaran.tahun),
                              Anggaran.kode,
                              Anggaran.nama
                   ) 
    
########                    
# CSV #
########          
@view_config(route_name='anggaran-csv', renderer='csv')
def view_csv(request):
    global unit_id,unit_kd,unit_nm,unit_al
    ses = request.session
    params = request.params
    url_dict = request.matchdict
    u = request.user.id    
    
    if group_in(request, 'bendahara'):
        unit_id = DBSession.query(UserUnit.unit_id
                          ).filter(UserUnit.user_id==u
                          ).first()
        unit_id = '%s' % unit_id
        unit_id = int(unit_id) 
        
        unit = DBSession.query(Unit.kode.label('kode'),
                               Unit.nama.label('nama'),
                               Unit.alamat.label('alamat')
                       ).filter(UserUnit.unit_id==unit_id, 
                                Unit.id==unit_id
                       ).first()
        unit_kd = '%s' % unit.kode
        unit_nm = '%s' % unit.nama
        unit_al = '%s' % unit.alamat
        
    if url_dict['csv']=='reg' :
        query = query_reg()
        if group_in(request, 'bendahara'):
            query = query.join(Rekening).join(UnitRekening).\
                    filter(UnitRekening.unit_id==unit_id)
                          
        row = query
        header = 'Kode Rekening','Uraian Rekening','Murni','Perubahan','Tahun'
        rows = []
        for item in row.all():
            rows.append(list(item))
        
        # override attributes of response
        filename = 'Anggaran_Rekening.csv'
        request.response.content_disposition = 'attachment;filename=' + filename

    return {
      'header': header,
      'rows'  : rows,
    } 
        
##########
# PDF    #
##########    
@view_config(route_name='anggaran-pdf', permission='read')
def view_pdf(request):
    global unit_id,unit_nm,unit_al,unit_kd
    params   = request.params
    url_dict = request.matchdict
    u = request.user.id  
    
    if group_in(request, 'bendahara'):
        unit_id = DBSession.query(UserUnit.unit_id
                          ).filter(UserUnit.user_id==u
                          ).first()
        unit_id = '%s' % unit_id
        unit_id = int(unit_id) 
        
        unit = DBSession.query(Unit.kode.label('kode'),
                               Unit.nama.label('nama'),
                               Unit.alamat.label('alamat')
                       ).filter(UserUnit.unit_id==unit_id, 
                                Unit.id==unit_id
                       ).first()
        unit_kd = '%s' % unit.kode
        unit_nm = '%s' % unit.nama
        unit_al = '%s' % unit.alamat
    
    if url_dict['pdf']=='reg' :
        nm = "BADAN PENDAPATAN DAERAH"
        al = "Jl. Soekarno Hatta, No. 528, Bandung"
        
        query = query_reg()
        if group_in(request, 'bendahara'):
            query = query.join(Rekening).join(UnitRekening).\
                    filter(UnitRekening.unit_id==unit_id)
                          
        rml_row = open_rml_row('anggaran.row.rml')
        rows=[]
        for r in query.all():
            s = rml_row.format(kode=r.a, 
                               nama=r.b, 
                               murni=r.c, 
                               perubahan=r.d, 
                               tahun=r.e)
            rows.append(s)
        if group_in(request, 'bendahara'):            
            pdf, filename = open_rml_pdf('anggaran.rml', rows2=rows,  
                                                         un_nm=unit_nm,
                                                         un_al=unit_al)
        else:            
            pdf, filename = open_rml_pdf('anggaran.rml', rows2=rows,  
                                                         un_nm=nm,
                                                         un_al=al)
        return pdf_response(request, pdf, filename)