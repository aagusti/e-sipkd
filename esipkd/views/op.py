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
      ObjekPajak,
      SubjekPajak,
      Unit,
      UserUnit,
      Wilayah,
      Pajak,
      Rekening,
      ARInvoice,
      User
      )
from ..models.__init__ import(
      UserGroup
      )
from ..security import group_in
from datatables import (
    ColumnDT, DataTables)
    
from daftar import (STATUS, deferred_status,
                    daftar_subjekpajak, deferred_subjekpajak,
                    daftar_wilayah, deferred_wilayah,
                    daftar_unit, deferred_unit,
                    daftar_pajak, deferred_pajak, auto_wp_nm2, auto_pajak_nm
                    )

SESS_ADD_FAILED = 'Gagal tambah Objek Pajak'
SESS_EDIT_FAILED = 'Gagal edit Objek Pajak'
from daftar import STATUS
########                    
# List #
########    
@view_config(route_name='op', renderer='templates/op/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    

#######    
# Add #
#######

class AddSchema(colander.Schema):
    subjekpajak_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    title="Penyetor",
                    oid = "subjekpajak_id"
                    )
    subjekpajak_nm = colander.SchemaNode(
                    colander.String(),
                    widget=auto_wp_nm2,
                    title="Penyetor",
                    oid = "subjekpajak_nm"
                    )
    subjekpajak_us = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid = "subjekpajak_us"
                    )
    subjekpajak_un = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid = "subjekpajak_un"
                    )
    unit_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid="unit_id",
                    title="OPD",
                    )
    unit_nm = colander.SchemaNode(
                    colander.String(),
                    title="OPD",
                    oid="unit_nm"
                    )
    wilayah_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_wilayah,
                    title="Wilayah"
                    )
    pajak_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid="pajak_id",
                    #widget=deferred_pajak,
                    #title="Rekening"
                    )

    pajak_nm = colander.SchemaNode(
                    colander.String(),
                    #widget=auto_pajak_nm,
                    title="Rekening",
                    oid="pajak_nm"
                    )
    kode   = colander.SchemaNode(
                    colander.String(),
                    widget=widget.HiddenWidget(),
                    oid="kode",
                    missing=colander.drop)
    nama = colander.SchemaNode(
                    colander.String(),
                    widget=widget.HiddenWidget(),
                    oid="nama",
                    missing=colander.drop)
    status = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status,
                    title="Status")

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True),
            title="")
                    

def get_form(request, class_form):
    schema = class_form()
    schema = schema.bind(daftar_status=STATUS,
                         daftar_subjekpajak=daftar_subjekpajak(),
                         daftar_pajak=daftar_pajak(),
                         #daftar_unit=daftar_unit(),
                         daftar_wilayah=daftar_wilayah())
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    if not row:
        row = ObjekPajak()
    row.from_dict(values)

    p = values['pajak_id']
    x = values['kode']
    y = values['nama']
    if not x and not y:
        row1 = DBSession.query(Pajak).filter(Pajak.id==p).first()
        row.kode = row1.kode
        row.nama = row1.nama
        print "********------",row.kode, "********--------", row.nama
    row.alamat_1='-'
    row.alamat_2='-'
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    print "****",values, "****", request
    row = save(values, row)
    request.session.flash('Objek %s sudah disimpan.' % row.kode)
        
def route_list(request):
    return HTTPFound(location=request.route_url('op'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='op-add', renderer='templates/op/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    values = {}
    #u = request.user.id
    #print '----------------User_Login---------------',u
    #x = DBSession.query(UserGroup.group_id).filter(UserGroup.user_id==u).first()
    #y = '%s' % x
    #z = int(y)        
    #print '----------------Group_id-----------------',z
    #
    #if z == 1:
    #    a = DBSession.query(User.email).filter(User.id==u).first()
    #    print '----------------Email---------------------',a
    #    rows = DBSession.query(SubjekPajak.id.label('sid'), SubjekPajak.nama.label('snm'), SubjekPajak.unit_id.label('sui'), SubjekPajak.user_id.label('sus'),
    #                   ).filter(SubjekPajak.email==a,
    #                   ).first()
    #    values['subjekpajak_id'] = rows.sid
    #    print '----------------Subjek id-----------------------',values['subjekpajak_id']
    #    values['subjekpajak_nm'] = rows.snm
    #    print '----------------Subjek nama---------------------',values['subjekpajak_nm']
    #    values['subjekpajak_us'] = rows.sus
    #    print '----------------Subjek user---------------------',values['subjekpajak_us']
    #    values['subjekpajak_un'] = rows.sui
    #    print '----------------Subjek unit 1-------------------',values['subjekpajak_un']
    #    values['unit_id'] = rows.sui
    #    print '----------------Subjek unit---------------------',values['unit_id'] 
    #    unit = DBSession.query(Unit.nama.label('unm')
    #                   ).filter(Unit.id==values['unit_id'],
    #                   ).first()
    #    values['unit_nm'] = unit.unm	
    #    print '----------------Unit nama-----------------------',values['unit_nm'] 
	#	
    #elif z == 2:
    #    print '----------------User_id-------------------',u
    #    a = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
    #    b = '%s' % a
    #    c = int(b)
    #    values['unit_id'] = c
    #    print '----------------Unit id-------------------------',values['unit_id'] 
    #    unit = DBSession.query(Unit.nama.label('unm')
    #                   ).filter(Unit.id==c,
    #                   ).first()
    #    values['unit_nm'] = unit.unm
    #    print '----------------Unit nama-----------------------',values['unit_nm'] 

    #form.set_appstruct(values)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
                #TODO: Cek WP/BENDAHARA disini
            except ValidationFailure, e:
                return dict(form=form)
            
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    query = DBSession.query(ObjekPajak).filter_by(id=request.matchdict['id'])
    if group_in(request, 'wp'):
        query = query.join(SubjekPajak).filter(SubjekPajak.email==request.user.email)
    elif group_in(request, 'bendahara'):
        query = query.join(SubjekPajak).join(Unit).filter(Unit.id==SubjekPajak.unit_id)
        query = query.join(UserUnit).filter(UserUnit.unit_id==Unit.id,
                                            UserUnit.user_id==request.user.id)        
    return query    
        
def id_not_found(request):    
    msg = 'Objek ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='op-edit', renderer='templates/op/edit.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    #id  = row.id
    
    if not row:
        return id_not_found(request)
    #x = DBSession.query(ARInvoice).filter(ARInvoice.objek_pajak_id==id).first()
    #if x:
    #    request.session.flash('Tidak bisa diedit, karena objek sudah digunakan di daftar bayar.','error')
    #    return route_list(request)
        
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['subjekpajak_nm'] = row and row.subjekpajaks.nama or None
    values['unit_id']        = row and row.subjekpajaks.units.id or None
    values['unit_nm']        = row and row.units.nama        or None
    values['pajak_nm']       = row and row.pajaks.nama       or None
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='op-delete', renderer='templates/op/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    id = row.id
    
    x = DBSession.query(ARInvoice).filter(ARInvoice.objek_pajak_id==id).first()
    if x:
        request.session.flash('Tidak bisa dihapus, karena objek sudah digunakan di daftar bayar.','error')
        return route_list(request)
        
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Objek %s sudah dihapus.' % (row.kode)
            q = DBSession.query(ObjekPajak).filter_by(id=request.matchdict['id']).delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())

##########
# Action #
##########    
@view_config(route_name='op-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    x        = request.user.id
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('subjekpajaks.kode'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('pajaks.kode'))
        columns.append(ColumnDT('wilayahs.nama'))
        columns.append(ColumnDT('status'))
        columns.append(ColumnDT('units.nama'))
        query = DBSession.query(ObjekPajak).join(SubjekPajak).join(Unit).outerjoin(Pajak).\
                          outerjoin(Wilayah).filter(ObjekPajak.status_grid==0)
        if group_in(request, 'wp'):
            query = query.filter(SubjekPajak.email==request.user.email)
        elif group_in(request, 'bendahara'):
            query = query.filter(Unit.id==SubjekPajak.unit_id)
            query = query.join(UserUnit).filter(UserUnit.unit_id==Unit.id,
                                                UserUnit.user_id==x)             
        rowTable = DataTables(req, ObjekPajak, query, columns)
        return rowTable.output_result()

    elif url_dict['act']=='hon':
        term = 'term' in params and params['term'] or '' 
        subjek_pajak_id = 'subjek_pajak_id' in params and params['subjek_pajak_id'] or 0
        rows = DBSession.query(ObjekPajak).join(SubjekPajak).join(Pajak).\
                         filter(ObjekPajak.nama.ilike('%%%s%%' % term),
                                ObjekPajak.status==1,
                                ObjekPajak.status_grid==0,
                                ObjekPajak.subjekpajak_id==SubjekPajak.id,
                                SubjekPajak.id==subjek_pajak_id,
                                ObjekPajak.pajak_id==Pajak.id).all()
        r = []
        for k in rows:
            print k
            d={}
            d['id']          = k.id
            d['value']       = k.nama
            d['sp_id']       = k.subjekpajaks.id
            d['sp_nm']       = k.subjekpajaks.nama
            d['unit_id']     = k.units.id
            d['unit_nm']     = k.units.nama
            d['tarif']       = k.pajaks.tarif
            d['wil']         = k.wilayah_id
            
            r.append(d)
        return r             

    elif url_dict['act']=='hon_tbp':
        term = 'term' in params and params['term'] or '' 
        subjek_pajak_id = 'subjek_pajak_id' in params and params['subjek_pajak_id'] or 0
        rows = DBSession.query(ObjekPajak).join(SubjekPajak).join(Pajak).\
                         filter(ObjekPajak.nama.ilike('%%%s%%' % term),
                                ObjekPajak.status==1,
                                ObjekPajak.status_grid==0,
                                ObjekPajak.subjekpajak_id==SubjekPajak.id,
                                SubjekPajak.id==subjek_pajak_id,
                                ObjekPajak.pajak_id==Pajak.id).all()
        r = []
        for k in rows:
            print k
            d={}
            d['id']          = k.id
            d['value']       = k.nama
            d['sp_id']       = k.subjekpajaks.id
            d['sp_nm']       = k.subjekpajaks.nama
            d['unit_id']     = k.units.id
            d['unit_nm']     = k.units.nama
            d['alamat_1']    = k.alamat_1
            d['alamat_2']    = k.alamat_2
            d['tarif']       = k.pajaks.tarif
            
            r.append(d)
        return r             
    
    elif url_dict['act']=='hon1':
        x = request.user.id
        term = 'term' in params and params['term'] or '' 
        d    = DBSession.query(User.email).filter(User.id==x).first()

        rows = DBSession.query(ObjekPajak).join(SubjekPajak).join(Pajak).\
                         filter(ObjekPajak.nama.ilike('%%%s%%' % term),
                                ObjekPajak.status==1,
                                ObjekPajak.status_grid==0,
                                ObjekPajak.subjekpajak_id==SubjekPajak.id,
                                SubjekPajak.email==d,
                                ObjekPajak.pajak_id==Pajak.id).all()
        r = []
        for k in rows:
            print k
            d={}
            d['id']          = k.id
            d['value']       = k.nama
            d['sp_id']       = k.subjekpajaks.id
            d['sp_nm']       = k.subjekpajaks.nama
            d['unit_id']     = k.units.id
            d['unit_nm']     = k.units.nama
            d['tarif']       = k.pajaks.tarif
            d['wil']         = k.wilayah_id
            
            r.append(d)
        return r                    

from ..reports.rml_report import open_rml_row, open_rml_pdf, pdf_response
def query_reg():
    return DBSession.query(ObjekPajak.nama.label('c'), 
                           SubjekPajak.nama.label('a'), 
                           Pajak.kode.label('b'), 
                           Wilayah.nama.label('d'),
                           Unit.nama.label('unit')
                   ).join(SubjekPajak
                   ).join(Unit
                   ).outerjoin(Pajak
                   ).outerjoin(Wilayah
                   ).filter(ObjekPajak.status_grid==0
                   ).order_by(ObjekPajak.kode)
    
########                    
# CSV #
########          
@view_config(route_name='op-csv', renderer='csv')
def view_csv(request):
    ses = request.session
    params = request.params
    url_dict = request.matchdict 
    u = request.user.id
    a = datetime.now().strftime('%d-%m-%Y')
    if url_dict['csv']=='reg' :
        query = query_reg()
        if group_in(request, 'wp'):
            query = query.filter(SubjekPajak.email==request.user.email)
        elif group_in(request, 'bendahara'):
            query = query.filter(SubjekPajak.unit_id==Unit.id)
            query = query.join(UserUnit).filter(UserUnit.unit_id==Unit.id,
                                                UserUnit.user_id==u)  
                          
        row = query.first()
        print "-- ROW -- ",row
        header = 'Objek_Pajak','Penyetor','Rekening','Wilayah','OPD' #row.keys()
        rows = []
        for item in query.all():
            rows.append(list(item))

        # override attributes of response
        filename = 'ObjekPajak_%s.csv' %(a)
        request.response.content_disposition = 'attachment;filename=' + filename

    return {
      'header': header,
      'rows'  : rows,
    } 
        
##########
# PDF    #
##########    
@view_config(route_name='op-pdf', permission='read')
def view_pdf(request):
    global awal,akhir,unit_nm,unit_al,unit_kd
    params   = request.params
    url_dict = request.matchdict
    u = request.user.id
    
    if group_in(request, 'bendahara'):
        unit_id = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
        unit_id = '%s' % unit_id
        unit_id = int(unit_id) 
        
        unit_kd = DBSession.query(Unit.kode).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
        unit_kd = '%s' % unit_kd
        
        unit_nm = DBSession.query(Unit.nama).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
        unit_nm = '%s' % unit_nm
        
        unit_al = DBSession.query(Unit.alamat).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
        unit_al = '%s' % unit_al
    elif group_in(request, 'wp'):
        unit_id = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
        unit_id = '%s' % unit_id
        unit_id = int(unit_id) 
        
        unit_kd = DBSession.query(Unit.kode).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
        unit_kd = '%s' % unit_kd
        
        unit_nm = DBSession.query(Unit.nama).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
        unit_nm = '%s' % unit_nm
        
        unit_al = DBSession.query(Unit.alamat).filter(UserUnit.unit_id==unit_id, Unit.id==unit_id).first()
        unit_al = '%s' % unit_al
        
    if url_dict['pdf']=='reg' :
        query = query_reg()
        if group_in(request, 'wp'):
            query = query.filter(SubjekPajak.email==request.user.email)
        elif group_in(request, 'bendahara'):
            query = query.filter(SubjekPajak.unit_id==Unit.id)
            query = query.join(UserUnit).filter(UserUnit.unit_id==Unit.id,
                                                UserUnit.user_id==u)
                          
        rml_row = open_rml_row('op.row.rml')
        rows=[]
        for r in query.all():
            s = rml_row.format(kode=r.a, 
                               nama=r.b, 
                               alamat=r.c, 
                               email=r.d, 
                               unit=r.unit)
            rows.append(s)   
        print "--- ROWS ---- ",rows   
        if group_in(request, 'bendahara'):        
            pdf, filename = open_rml_pdf('op_ben.rml', rows2=rows, 
                                                       un_nm=unit_nm,
                                                       un_al=unit_al)
        elif group_in(request, 'wp'):        
            pdf, filename = open_rml_pdf('op_wp.rml', rows2=rows, 
                                                       un_nm=unit_nm,
                                                       un_al=unit_al)
        else:
            pdf, filename = open_rml_pdf('op.rml', rows2=rows)
        return pdf_response(request, pdf, filename)