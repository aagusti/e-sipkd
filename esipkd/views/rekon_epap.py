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
from ..models.isipkd import (Pkb, Pap)
from ..models.informix import EngInformix

SESS_ADD_FAILED  = 'rekon_epap add failed'
SESS_EDIT_FAILED = 'rekon_epap edit failed'

########                    
# List #
########    
@view_config(route_name='rekon-epap', renderer='templates/rekon-epap/list.pt',
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
    kd_bayar      = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Kode Bayar',
                      oid="kd_bayar"
                      )
    kd_status    = colander.SchemaNode(
                      colander.Integer(),
                      title='Status.bayar',
                      missing=colander.drop,
                      oid="kd_status"
                      )
    npwpd   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'NPWPD',
                      oid="npwpd"
                      )
    nm_perus   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Nama',
                      oid="nm_perus"
                      )
    al_perus   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Alamat',
                      oid="al_perus"
                      )
    vol_air    = colander.SchemaNode(
                      colander.Integer(),
                      title='Volume',
                      missing=colander.drop,
                      oid="vol_air"
                      )
    npa    = colander.SchemaNode(
                      colander.Integer(),
                      title='NPS',
                      missing=colander.drop,
                      oid="npa"
                      )
    bea_pok_pjk    = colander.SchemaNode(
                      colander.Integer(),
                      title='Bea Pokok Pjk',
                      missing=colander.drop,
                      oid="bea_pok_pjk"
                      )
    bea_den_pjk    = colander.SchemaNode(
                      colander.Integer(),
                      title='Bea Denda Pjk',
                      missing=colander.drop,
                      oid="bea_den_pjk"
                      )
    m_pjk_bln   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Bulan',
                      oid="m_pjk_bln"
                      )
    m_pjk_thn   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Tahun',
                      oid="m_pjk_thn"
                      )
    tgl_tetap   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Tgl. Penetapan',
                      oid="tgl_tetap"
                      )
    tgl_jt_tempo   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Tgl. Jth Tempo',
                      oid="tgl_jt_tempo"
                      )
    keterangan   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Keterangan',
                      oid="keterangan"
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
        row = Pap()
    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    return row

def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(request, values, row)
    request.session.flash('PAP sudah proses.')
    return row
    
def route_list(request):
    return HTTPFound(location=request.route_url('rekon-epap'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
def query_id(request):
    return DBSession.query(Pap).filter_by(id=request.matchdict['id'])

def id_not_found(request):    
    msg = 'Rekon E-PAP ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)
	
@view_config(route_name='rekon-epap-edit', renderer='templates/rekon-epap/edit.pt',
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
                return HTTPFound(location=request.route_url('rekon-epap-edit', id=row.id))
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
@view_config(route_name='rekon-epap-delete', renderer='templates/rekon-epap/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Rekon E-PAP ID %d berhasil dihapus.' % (row.id)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
	
##########
# Action #
##########    
@view_config(route_name='rekon-epap-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kd_bayar'))
        columns.append(ColumnDT('m_pjk_bln'))
        columns.append(ColumnDT('m_pjk_thn'))
        columns.append(ColumnDT('npwpd'))
        columns.append(ColumnDT('nm_perus'))
        columns.append(ColumnDT('keterangan'))
        columns.append(ColumnDT('bea_pok_pjk',  filter=_DTnumberformat))
        columns.append(ColumnDT('bea_den_pjk',  filter=_DTnumberformat))
        query = DBSession.query(Pap)
        rowTable = DataTables(req, Pap, query, columns)
        return rowTable.output_result()