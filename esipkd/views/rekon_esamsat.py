import colander
import informixdb

from datetime import (datetime, date)
from time import (strptime, strftime, time, sleep)
from sqlalchemy import (not_, or_, text)
from pyramid.view import (view_config,)
from pyramid.httpexceptions import (HTTPFound,)
from deform import (Form, widget, ValidationFailure,)
from datatables import (ColumnDT, DataTables)
from ..tools import _DTnumberformat, _DTstrftime
from ..models import (DBSession)
from ..models.isipkd import (Pkb)
from ..models.informix import EngInformix

SESS_ADD_FAILED = 'rekon_esamsat add failed'
SESS_EDIT_FAILED = 'rekon_esamsat edit failed'

########                    
# List #
########    
@view_config(route_name='rekon-esamsat', renderer='templates/rekon-esamsat/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})
	
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


class AddSchema(colander.Schema):
    kd_status    = colander.SchemaNode(
                      colander.String(),
                      title='Status.bayar',
                      missing=colander.drop,
                      oid="kd_status"
                      )
    no_rangka   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'No. Rangka',
                      oid="no_rangka"
                      )
    no_ktp      = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'No. Identitas',
                      oid="no_ktp"
                      )
    email        = colander.SchemaNode(
                      colander.String(),
                      title = 'E-Mail',
                      oid="email"
                      )
    no_hp        = colander.SchemaNode(
                      colander.String(),
                      title = 'No. Handphone',
                      oid="no_hp"
                      )
    kd_bayar      = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Kode Bayar',
                      oid="kd_bayar"
                      )
    tg_bayar_bank = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop, 
                      title = 'Tgl. Bayar',
                      oid="tg_bayar_bank"
                      )
    no_polisi     = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'No. Polisi',
                      oid="no_polisi"
                      )
    ket           = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Keterangan',
                      oid="ket"
                      )
    nm_pemilik    = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Nama Pemilik',
                      oid="nm_pemilik"
                      )
    warna_tnkb    = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Warna TNKB',
                      oid="warna_tnkb"
                      )
    nm_merek_kb   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Merk Kendaraan',
                      oid="nm_merek_kb"
                      )
    nm_model_kb   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Model Kendaraan',
                      oid="nm_model_kb"
                      )
    th_buatan   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Thn. Pembuatan',
                      oid="th_buatan"
                      )
    tg_akhir_pjklm = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Tgl. Pajak Lama',
                      oid="tg_akhir_pjklm"
                      )
    tg_akhir_pjkbr = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Tgl. Pajak Baru',
                      oid="tg_akhir_pjkbr"
                      )                      
    bbn_pok    = colander.SchemaNode(
                      colander.Integer(),
                      missing=colander.drop,
                      title='Pokok BBN',
                      oid="bbn_pok"
                      )
    bbn_den    = colander.SchemaNode(
                      colander.Integer(),
                      missing=colander.drop,
                      title='Denda BBN',
                      oid="bbn_den"
                      )
    pkb_pok    = colander.SchemaNode(
                      colander.Integer(),
                      missing=colander.drop,
                      title='Pokok PKB',
                      oid="pkb_pok"
                      )
    pkb_den    = colander.SchemaNode(
                      colander.Integer(),
                      missing=colander.drop,
                      title='Denda PKB',
                      oid="pkb_den"
                      )
    swd_pok    = colander.SchemaNode(
                      colander.Integer(),
                      missing=colander.drop,
                      title='Pokok SWDKLLJ',
                      oid="swd_pok"
                      )
    swd_den    = colander.SchemaNode(
                      colander.Integer(),
                      missing=colander.drop,
                      title='Denda SWDKLLJ',
                      oid="swd_den"
                      )
    adm_stnk    = colander.SchemaNode(
                      colander.Integer(),
                      missing=colander.drop,
                      title='Adm. STNK',
                      oid="adm_stnk"
                      )
    adm_tnkb    = colander.SchemaNode(
                      colander.Integer(),
                      missing=colander.drop,
                      title='Adm. TNKB',
                      oid="adm_tnkb"
                      )
    jumlah    = colander.SchemaNode(
                      colander.Integer(),
                      missing=colander.drop,
                      title='Jumlah',
                      oid="jumlah"
                      )
    kd_trn_bank    = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'NTB',
                      oid="kd_trn_bank"
                      )
    kd_trn_dpd   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'NTP',
                      oid="kd_trn_dpd"
                      )

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                          
def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
     
def save(request, values, row=None):
    if not row:
        row = Pkb()
    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    return row

def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(request, values, row)
    request.session.flash('PKB sudah proses.')
    return row
    
def route_list(request):
    return HTTPFound(location=request.route_url('rekon-esamsat'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
def query_id(request):
    return DBSession.query(Pkb).filter_by(id=request.matchdict['id'])

def id_not_found(request):    
    msg = 'Rekon E-Samsat ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
	
@view_config(route_name='rekon-esamsat-edit', renderer='templates/rekon-esamsat/edit.pt',
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
                return HTTPFound(location=request.route_url('rekon-esamsat-edit', id=row.id))
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
@view_config(route_name='rekon-esamsat-delete', renderer='templates/rekon-esamsat/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Rekon E-Samsat ID %d berhasil dihapus.' % (row.id)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
	
##########
# Action #
##########    
@view_config(route_name='rekon-esamsat-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kd_bayar'))
        columns.append(ColumnDT('no_ktp'))
        columns.append(ColumnDT('no_rangka'))
        columns.append(ColumnDT('no_hp'))
        columns.append(ColumnDT('email'))
        columns.append(ColumnDT('ket'))
        columns.append(ColumnDT('jumlah',  filter=_DTnumberformat))
        query = DBSession.query(Pkb)
        rowTable = DataTables(req, Pkb, query, columns)
        return rowTable.output_result()