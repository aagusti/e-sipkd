import sys
import re
from email.utils import parseaddr
from sqlalchemy import not_, func
from datetime import datetime
from time import gmtime, strftime
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
from ..tools import _DTnumberformat,_DTstrftime
from ..models import DBSession
from ..models.isipkd import(
      ObjekPajak,
      SubjekPajak,
      Unit,
      UserUnit,
      Wilayah,
      Pajak,
      Rekening,
      ARSts
      )
from ..models.__init__ import(
      UserGroup
      )
from ..security import group_in
from datatables import (
    ColumnDT, DataTables)

SESS_ADD_FAILED = 'Gagal tambah STS'
SESS_EDIT_FAILED = 'Gagal edit STS'
from daftar import (STATUS, deferred_status,
                    daftar_subjekpajak, deferred_subjekpajak,
                    daftar_objekpajak, deferred_objekpajak,
                    daftar_wilayah, deferred_wilayah,
                    daftar_unit, deferred_unit,
                    daftar_pajak, deferred_pajak,
                    )
########                    
# List #
########    
@view_config(route_name='arsts', renderer='templates/arsts/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
    

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode STS %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Uraian  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(ARSts).filter_by(id=uid)
        r = q.first()
    else:
        r = None
            
class AddSchema(colander.Schema):
    moneywidget = widget.MoneyInputWidget(
            size=20, options={'allowZero':True,
                              'precision':0
                              })
            
    #unit_id = colander.SchemaNode(
    #                colander.Integer(),
    #                widget=deferred_unit,
    #                title="OPD"
                    #title="SKPD"
    #                )
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
    kode   = colander.SchemaNode(
                    colander.String(),
                    title="Kode STS",
                    missing = colander.drop,
                    )
                    
    nama   = colander.SchemaNode(
                    colander.String(),
                    title="Uraian"
                    )
    tgl_sts = colander.SchemaNode(
                    colander.Date(),
                    )
    jumlah = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    )

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True),
            oid='id'
            )
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS,
                         daftar_subjekpajak=daftar_subjekpajak(),
                         daftar_unit=daftar_unit(),
                         daftar_objekpajak=daftar_objekpajak(),
                         )
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, row=None):
    if not row:
        row = ARSts()
    row.from_dict(values)
    row.jumlah = re.sub("[^0-9]", "", row.jumlah)
    
    if not row.tahun_id:
        row.tahun_id = datetime.now().strftime('%Y')
        
    ref = Unit.get_by_id(row.unit_id)
    row.unit_kode = ref.kode
    row.unit_nama = ref.nama
    
    if not row.kode and not row.no_id:
        invoice_no = DBSession.query(func.max(ARSts.no_id)).\
                               filter(ARSts.tahun_id==row.tahun_id,
                                      ARSts.unit_id==row.unit_id).scalar()
        if not invoice_no:
            row.no_id = 1
        else:
            row.no_id = invoice_no+1
            
    row.kode = "".join([str(row.tahun_id), re.sub("[^0-9]", "", row.unit_kode),
                        str(row.no_id).rjust(6,'0')])
                        
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, row)
    request.session.flash('STS %s %s sudah disimpan.' % (row.kode, row.nama))
    return row
        
def route_list(request):
    return HTTPFound(location=request.route_url('arsts'))
    
def session_failed(request, session_name):
    try:
        session_name.set_appstruct(request.session[SESS_ADD_FAILED])
    except:
        pass
    r = dict(form=session_name) #request.session[session_name])
    del request.session[SESS_ADD_FAILED]
    return r
    
@view_config(route_name='arsts-add', renderer='templates/arsts/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    values = {}
    u = request.user.id
    print '----------------User_Login---------------',u
    if u!=1:
        x = DBSession.query(UserGroup.group_id).filter(UserGroup.user_id==u).first()
        y = '%s' % x
        z = int(y)        
        print '----------------Group_id-----------------',z
        
        if z == 2:
            print '----------------User_id-------------------',u
            a = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            b = '%s' % a
            c = int(b)
            values['unit_id'] = c
            print '----------------Unit id-------------------------',values['unit_id'] 
            unit = DBSession.query(Unit.nama.label('unm')
                           ).filter(Unit.id==c,
                           ).first()
            values['unit_nm'] = unit.unm
            print '----------------Unit nama-----------------------',values['unit_nm'] 

    values['tgl_sts']   = datetime.now()
    form.set_appstruct(values)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            row = save_request(dict(controls), request)
            return HTTPFound(location=request.route_url('arsts-edit',
                                  id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, form) #SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ARSts).filter(ARSts.id==request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'STS ID %s tidak ditemukan atau sudah dibayar.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='arsts-edit', renderer='templates/arsts/add.pt',
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
                return HTTPFound(location=request.route_url('arsts-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_nm'] = row and row.units.nama or None
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='arsts-delete', renderer='templates/arsts/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return id_not_found(request)
    if row.jumlah:
        request.session.flash('Data tidak dapat dihapus, karena masih mempunyai item.', 'error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'STS ID %d %s sudah dihapus.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())

##########
# Action #
##########    
@view_config(route_name='arsts-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    user     = req.user
    u        = request.user.id
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('tgl_sts', filter=_DTstrftime))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('jumlah',  filter=_DTnumberformat))
        
        query = DBSession.query(ARSts).\
                                join(Unit)
        if group_in(request, 'bendahara'):
            x = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            y = '%s' % x
            z = int(y)     
            print "- Unit_id --------- ",z
            
            query = query.filter(ARSts.unit_id==z)
            
        rowTable = DataTables(req, ARSts, query, columns)
        return rowTable.output_result()