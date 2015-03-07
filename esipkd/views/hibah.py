import colander
from email.utils import parseaddr
from datetime import (datetime, date)
from time import (strptime, strftime)
from sqlalchemy import (not_, or_)
from pyramid.view import (view_config,)
from pyramid.httpexceptions import (HTTPFound,)
from deform import (Form, widget, ValidationFailure,)
from datatables import (ColumnDT, DataTables)

from ..tools import (email_validator,BULANS)
from ..models import (DBSession)
from ..models.isipkd import (Sptpd, Unit,Rekening,
        UnitRekening,)

SESS_ADD_FAILED = 'gagal tambah data'
SESS_EDIT_FAILED = 'gagal edit data'

#######    
# Add #
#######
def form_validator(form, value):
    def err_no_rangka():
        raise colander.Invalid(form,
            'No Rangka Harus diisi' 
            )
    def err_nik():
        raise colander.Invalid(form,
            'NIK Harus diisi' 
            )
            
    def err_no_handphone():
        raise colander.Invalid(form,
            'No handphone harus diisi' 
            )
                                
    def err_no_handphone():
        raise colander.Invalid(form,
            'Kode validasi harus diisi' 
            )

def get_periode(year=True):
    adate = datetime.now()
    amonth = adate.month - 1
    amonth = amonth>0 and amonth or 12
    if year:
        ayear = amonth<12 and adate.year or adate.year-1
        return ayear
    else:
        return amonth

def get_units():
    q = DBSession.query(Unit.id,Unit.nama).filter(
          Unit.kode.like("1.20.05.%")
        ).order_by(Unit.nama)
    return q.all()
    
def get_rekenings():
    q = DBSession.query(Rekening.id,Rekening.nama).filter(
          Rekening.kode.like('4.3.1.03.02.%'), Rekening.is_summary==0
        ).filter(Rekening.is_summary==0).order_by(Rekening.nama)
    return q.all()
    
class InformasiSchema(colander.Schema):
    nama = colander.SchemaNode(
                    colander.String())
    alamat_1 = colander.SchemaNode(
                    colander.String())
    alamat_2 = colander.SchemaNode(
                    colander.String())
            
class AddSchema(colander.Schema):
    """appstruct = {
        'readonly':'Read Only',
        'readwrite':'Read and Write',
        }
    @colander.deferred
    def deferred_missing(node, kw):
        return appstruct['readonly']
    """    
    no_tagihan = colander.SchemaNode(
                    colander.String(),
                    widget=widget.TextInputWidget(),
                    #missing=deferred_missing,
                    )
    #print '***',dict(get_units())
    skpd       = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.SelectWidget(values=get_units()),
                    title = "SKPD"
                  )
    rekening   = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.SelectWidget(values=get_rekenings()),
                    title = "Rekening"
                  )
    informasi = InformasiSchema()              
    omset = colander.SchemaNode(
                    colander.Decimal(),
                    widget=widget.MoneyInputWidget(
                           size=20, options={'allowZero':False}),
                    title="Nilai"
                    )
    tarif = colander.SchemaNode(
                    colander.Decimal(),
                    widget=widget.HiddenWidget(
                           size=20, options={'allowZero':False},
                           default=1)
                    )

    pokok_pajak = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    default=0)

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    #schema = schema.bind(daftar_status=STATUS)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    """if not row:
        row = User()
    row.from_dict(values)
    if values['password']:
        row.password = values['password']
    DBSession.add(row)
    DBSession.flush()
    return row
    """
    row = {}
    row['email'] = 'aagusti@1'
    return row
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Tunggu beberpa saat.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('pbbkb'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    

########                    
# List #
########    
@view_config(route_name='hibah', renderer='templates/hibah/list.pt',
             permission='exec')
def view_list(request):
    #print request.user.id
    #rows = DBSession.query(Sptpd).filter(Sptpd.create_uid==request.user.id).order_by('tahun','bulan')
    return dict(request=request)
    
    
########                    
# Add #
########    
@view_config(route_name='hibah-add', renderer='templates/hibah/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('hibah-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())
    
########
# Edit #
########
def query_id(request):
    return DBSession.query(Unit).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Rekening ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='hibah-edit', renderer='templates/hibah/edit.pt',
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
                return HTTPFound(location=request.route_url('hibah-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    return dict(form=form.render(appstruct=values))

##########
# Delete #
##########    
@view_config(route_name='hibah-delete', renderer='templates/hibah/delete.pt',
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
@view_config(route_name='hibah-act', renderer='json',
             permission='view')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('no_bayar'))
        columns.append(ColumnDT('tahun'))
        columns.append(ColumnDT('bulan'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('omset'))
        columns.append(ColumnDT('tarif'))
        columns.append(ColumnDT('pokok'))
        columns.append(ColumnDT('status_bayar'))
        
        query = DBSession.query(Sptpd)
        rowTable = DataTables(req, Sptpd, query, columns)
        return rowTable.output_result()
    