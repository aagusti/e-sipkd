import sys
import re
from email.utils import parseaddr
from sqlalchemy import not_, func, desc
from datetime import datetime
from time import gmtime, strftime, strptime
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
from ..tools import _DTnumberformat
from ..models import DBSession
from ..models.isipkd import(
      Pegawai, ObjekPajak, SubjekPajak, ARInvoice,
      Unit, Wilayah, Pajak, Rekening,
      User, UserUnit
      )

from datatables import (
    ColumnDT, DataTables)
    
from ..security import group_finder, group_in

SESS_ADD_FAILED = 'Gagal tambah Tagihan'
SESS_EDIT_FAILED = 'Gagal edit Tagihan'
from daftar import (STATUS, deferred_status,
                    daftar_subjekpajak, deferred_subjekpajak,
                    daftar_objekpajak, deferred_objekpajak,
                    daftar_wilayah, deferred_wilayah,
                    daftar_unit, deferred_unit,
                    daftar_pajak, deferred_pajak,
                    auto_op_nm, auto_unit_nm, auto_wp_nm, auto_wp_nm4
                    )
########                    
# List #
########    
@view_config(route_name='arinvoicewp', renderer='templates/arinvoice/list_wp.pt',
             permission='read')
def view_list(request):
    awal  = 'awal'  in request.GET and request.GET['awal']  or datetime.now().strftime('%Y-%m-%d')
    akhir = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')
    return dict(rows={"awal":awal, "akhir":akhir})
    

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode invoice %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Uraian  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(ARInvoice).filter_by(id=uid)
        r = q.first()
    else:
        r = None
            
class AddSchema(colander.Schema):
    moneywidget = widget.MoneyInputWidget(
            size=20, options={'allowZero':True,
                              'precision':0
                              })
            
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
    subjek_pajak_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    title="Penyetor",
                    oid = "subjek_pajak_id"
                    )
    subjek_pajak_nm = colander.SchemaNode(
                    colander.String(),
                    widget=auto_wp_nm4,
                    title="Penyetor",
                    oid = "subjek_pajak_nm"
                    )
    subjek_pajak_us = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid = "subjek_pajak_us"
                    )
    subjek_pajak_un = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid = "subjek_pajak_un"
                    )
    objek_pajak_id = colander.SchemaNode(
                    colander.Integer(),
                    title="Objek",
                    widget=widget.HiddenWidget(),
                    oid = "objek_pajak_id"
                    )
    objek_pajak_nm = colander.SchemaNode(
                    colander.String(),
                    widget=auto_op_nm,
                    title="Objek",
                    oid = "objek_pajak_nm"
                    )
    wilayah_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid = "wilayah_id"
                    )
                    
    kode   = colander.SchemaNode(
                    colander.String(),
                    title="Kode Bayar",
                    missing = colander.drop,
                    )
                    
    periode_1 = colander.SchemaNode(
                    colander.Date(),
                    title="Periode 1",
                    widget = widget.DateInputWidget()
                    )
    periode_2 = colander.SchemaNode(
                    colander.Date(),
                    title="Periode 2"
                    )
    tgl_tetap = colander.SchemaNode(
                    colander.Date(),
                    )
    jatuh_tempo = colander.SchemaNode(
                    colander.Date(),
                    )
    dasar = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "dasar"
                    )
    tarif = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "tarif",
                    missing=colander.drop
                    )
    pokok = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    missing=colander.drop,
                    oid = "pokok"
                    )
    denda = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "denda"
                    )
    bunga = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    oid = "bunga"
                    )
    jumlah = colander.SchemaNode(
                    colander.Integer(),
                    default = 0,
                    widget = moneywidget,
                    missing=colander.drop,
                    oid = "jumlah"
                    )

#class WpAddSchema(MasterAddSchema):
#    unit_nm = colander.SchemaNode(
#                    colander.String(),
#                    widget=widget.TextInputWidget(readonly=True),
#                    title="OPD",
#                    oid="unit_nm"
#                    )
#    subjek_pajak_nm = colander.SchemaNode(
#                    colander.String(),
#                    widget=widget.TextInputWidget(readonly=True),
#                    title="Penyetor",
#                    oid = "subjek_pajak_nm"
#                    )
#                    
#    wp_nama = colander.SchemaNode(
#                    colander.String(),
#                    widget=widget.TextInputWidget(readonly=True),
#                    title="Nama Lain",
#                    oid = "wp_nama"
#                    )
#                    
#    wp_alamat_1 = colander.SchemaNode(
#                    colander.String(),
#                    widget=widget.TextInputWidget(readonly=True),
#                    title="Alamat Subjek",
#                    oid = "wp_alamat_1"
#                    )
#
#    wp_alamat_2 = colander.SchemaNode(
#                    colander.String(),
#                    widget=widget.TextInputWidget(readonly=True),
#                    title="Alamat Subjek",
#                    oid = "wp_alamat_2"
#                    )
                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True)
            )
            
#class WpEditSchema(WpAddSchema):
#    id = colander.SchemaNode(colander.Integer(),
#            missing=colander.drop,
#            widget=widget.HiddenWidget(readonly=True)
#            )
        
def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS,
                         daftar_subjekpajak=daftar_subjekpajak(),
                         daftar_unit=daftar_unit(),
                         daftar_objekpajak=daftar_objekpajak(),
                         )
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(request, values, row=None):
    if not row:
        row = ARInvoice()
        row.create_date = datetime.now()
        row.create_uid  = request.user.id
    row.from_dict(values)
    #row.update_date = datetime.now()
    row.update_uid  = request.user.id
    row.dasar  = re.sub("[^0-9]", "", row.dasar)
    row.tarif  = re.sub("[^0-9]", "", row.tarif)
    row.pokok  = re.sub("[^0-9]", "", row.pokok)
    row.denda  = re.sub("[^0-9]", "", row.denda)
    row.bunga  = re.sub("[^0-9]", "", row.bunga)
    row.jumlah = re.sub("[^0-9]", "", row.jumlah)
    
    if not row.tahun_id:
        row.tahun_id = datetime.now().strftime('%Y')
        
    unit = Unit.get_by_id(row.unit_id)
    row.unit_kd = unit.kode
    row.unit_nm = unit.nama
    
    ref = Unit.get_by_id(row.unit_id)
    row.unit_kode = ref.kode
    row.unit_nama = ref.nama
    
    ref = SubjekPajak.get_by_id(row.subjek_pajak_id)
    row.wp_kode = ref.kode
    row.wp_nama = ref.nama
    row.wp_alamat_1 = ref.alamat_1
    row.wp_alamat_2 = ref.alamat_2
    
    ref = ObjekPajak.get_by_id(row.objek_pajak_id)
    row.op_kode = ref.kode
    row.op_nama = ref.nama
    row.op_alamat_1 = ref.alamat_1
    row.op_alamat_2 = ref.alamat_2
    #row.wilayah_id = ref.wilayah_id
    row.rekening_id = ref.pajaks.rekening_id
    row.rek_kode = ref.pajaks.rekenings.kode
    row.rek_nama = ref.pajaks.rekenings.nama
    
    ref = Wilayah.get_by_id(row.wilayah_id)
    row.wilayah_kode = ref.kode
    
    #-- Perubahan pada No bayar dan filter tanggal 14-062017 --#
    tgl_tetap = values['tgl_tetap']
    prefix  = '22' 
    #tanggal = datetime.now().strftime('%d')
    #bulan   = datetime.now().strftime('%m')
    #tahun   = datetime.now().strftime('%y')
    tgl_tetap_new = datetime.strptime(values['tgl_tetap'], '%Y-%m-%d').date()
    tanggal = tgl_tetap_new.day
    bulan   = tgl_tetap_new.month
    tahun   = tgl_tetap_new.strftime('%y')
    
    if not row.kode and not row.no_id:
        invoice_no = DBSession.query(func.max(ARInvoice.no_id)).\
                               filter(ARInvoice.tahun_id==row.tahun_id,
                                      ARInvoice.wilayah_id==row.wilayah_id,
                                      #ARInvoice.tgl_tetap==datetime.now().strftime('%Y-%m-%d'),
                                      ARInvoice.tgl_tetap==tgl_tetap_new,
                                      func.substr(ARInvoice.kode,1,2)=='22').scalar()
        print "--------- Invoice No ------- ",invoice_no
        if not invoice_no:
            row.no_id = 1
        else:
            row.no_id = invoice_no+1

        row.kode = "".join([prefix, re.sub("[^0-9]", "", row.wilayah_kode), 
                            str(tanggal).rjust(2,'0'), 
                            str(bulan).rjust(2,'0'),
                            str(tahun).rjust(2,'0'),
                            str(row.no_id).rjust(4,'0')])
    row.owner_id = request.user.id
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(request, values, row)
    request.session.flash('No Bayar %s sudah disimpan.' % row.kode)
        
def route_list(request):
    return HTTPFound(location=request.route_url('arinvoicewp'))
    
def session_failed(request, session_name):
    try:
        session_name.set_appstruct(request.session[SESS_ADD_FAILED])
    except:
        pass
    r = dict(form=session_name) #request.session[session_name])
    del request.session[SESS_ADD_FAILED]
    return r
    
@view_config(route_name='arinvoicewp-add', renderer='templates/arinvoice/add_wp.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    values = {}

    u = request.user.id
    if u != 1 :
        a = DBSession.query(User.email).filter(User.id==u).first()
        #print '----------------Email---------------------',a
        rows = DBSession.query(SubjekPajak.id.label('sid'), SubjekPajak.nama.label('snm'), SubjekPajak.unit_id.label('sui'), SubjekPajak.user_id.label('sus'),
                       ).filter(SubjekPajak.email==a,
                       ).first()
        values['subjek_pajak_id'] = rows.sid
        #print '----------------Subjek id---------------------- ',values['subjek_pajak_id']
        values['subjek_pajak_nm'] = rows.snm                   
        #print '----------------Subjek nama-------------------- ',values['subjek_pajak_nm']
        values['subjek_pajak_us'] = rows.sus                   
        #print '----------------Subjek user-------------------- ',values['subjek_pajak_us']
        values['subjek_pajak_un'] = rows.sui                   
        #print '---------------- Subjek unit ------------------ ',values['subjek_pajak_un']
        values['unit_id'] = rows.sui                           
        #print '---------------- Unit ID ---------------------- ',values['unit_id'] 
        unit = DBSession.query(Unit.nama.label('unm')
                       ).filter(Unit.id==values['unit_id'],
                       ).first()
        values['unit_nm'] = unit.unm
        #print '----------------Unit nama---------------------- ',values['unit_nm'] 

    values['tgl_tetap']   = datetime.now()
    values['jatuh_tempo'] = datetime.now()
    values['periode_1']   = datetime.now()
    values['periode_2']   = datetime.now()
    form.set_appstruct(values)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)
            
            # Cek Kode
            if not controls_dicted['kode']=='':
                a = form.validate(controls)
                b = a['kode']
                c = "%s" % b
                cek = DBSession.query(ARInvoice).filter(ARInvoice.kode==c).first()
                if cek :
                    request.session.flash('Kode Bayar %s sudah digunakan.' % b, 'error')
                    return HTTPFound(location=request.route_url('arinvoicewp-add'))

            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, form) 
    return dict(form=form, is_unit=0, is_sp=0)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ARInvoice).filter(ARInvoice.id==request.matchdict['id'])
    if group_in(request, 'wp'):
        query = query.join(SubjekPajak).filter(SubjekPajak.email==request.user.email)
    return query
    
def id_not_found(request):    
    msg = 'No Bayar ID %s tidak ditemukan atau sudah dibayar.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='arinvoicewp-edit', renderer='templates/arinvoice/add_wp.pt',
             permission='edit')
def view_edit(request):
    row  = query_id(request).first()
    uid  = row.id
    kode = row.kode
    
    if not row:
        return id_not_found(request)
    if row.status_bayar:
        request.session.flash('Data sudah masuk di Penerimaan', 'error')
        return route_list(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            #if 'unit_nm' not in request.POST:
            #    request.POST['unit_nm'] = row.unit_nama
            #if 'subjek_pajak_nm' not in request.POST:
            #    request.POST['subjek_pajak_nm'] = row.wp_nama
            #    request.POST['wp_nama']         = row.wp_nama
            #    request.POST['wp_alamat_1']     = row.wp_alamat_1
            #    request.POST['wp_alamat_2']     = row.wp_alamat_2
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)             
                return HTTPFound(location=request.route_url('arinvoicewp-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['objek_pajak_nm']  = row.objekpajaks  and row.objekpajaks.nama     or row.op_nama
    values['subjek_pajak_nm'] = row.subjekpajaks and row.subjekpajaks.nama    or row.wp_nama
    values['subjek_pajak_us'] = row.subjekpajaks and row.subjekpajaks.user_id or 0
    values['subjek_pajak_un'] = row.subjekpajaks and row.subjekpajaks.unit_id or 0
    values['objek_pajak_id']  = row.objek_pajak_id  or 0 
    values['subjek_pajak_id'] = row.subjek_pajak_id or 0 
    values['unit_nm']         = row.units.nama
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='arinvoicewp-delete', renderer='templates/arinvoice/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return id_not_found(request)
    if row.status_bayar:
        request.session.flash('Data sudah masuk di Penerimaan', 'error')
        return route_list(request)
        
    if row.arsspds:
        form = Form(colander.Schema(), buttons=('batal',))
    else:
        form = Form(colander.Schema(), buttons=('hapus', 'batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'No Bayar ID %d %s sudah dihapus.' % (row.id, row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

##########
# Action #
##########    
def qry_arinv():
    return DBSession.query(ARInvoice).\
                            join(Unit)

@view_config(route_name='arinvoicewp-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    user     = req.user
    awal     = 'awal'  in request.GET and request.GET['awal']  or datetime.now().strftime('%Y-%m-%d')
    akhir    = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')
    if url_dict['act']=='grid':
        u = request.user.id
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('wp_nama'))
        columns.append(ColumnDT('op_kode'))
        columns.append(ColumnDT('op_nama'))
        columns.append(ColumnDT('rek_nama'))
        columns.append(ColumnDT('jumlah',  filter=_DTnumberformat))
        columns.append(ColumnDT('unit_nama'))
        query = DBSession.query(ARInvoice
                        ).filter(ARInvoice.status_grid==0,
                                 ARInvoice.tgl_tetap.between(awal,akhir)
                        ).order_by(desc(ARInvoice.tgl_tetap),desc(ARInvoice.kode))
        if u != 1:
            query = query.filter(ARInvoice.owner_id==u)
        rowTable = DataTables(req, ARInvoice, query, columns)
        return rowTable.output_result()           

from ..reports.rml_report import open_rml_row, open_rml_pdf, pdf_response
def query_reg():
    return DBSession.query(ARInvoice.kode.label('a'), 
                           ARInvoice.wp_nama.label('b'), 
                           ARInvoice.rek_kode.label('c'), 
                           ARInvoice.op_nama.label('d'),  
                           ARInvoice.tgl_tetap.label('e'), 
                           func.trim(func.to_char(ARInvoice.jumlah,'999,999,999,990')).label('f'),
                           ARInvoice.unit_nama.label('g'),
                   ).order_by(ARInvoice.tgl_tetap,ARInvoice.kode)
def query_cetak():
    return DBSession.query(ARInvoice.kode.label('a'), 
                           ARInvoice.wp_nama.label('b'), 
                           ARInvoice.wp_alamat_1.label('c'),
                           ARInvoice.rek_kode.label('d'), 
                           ARInvoice.rek_nama.label('e'), 
                           func.trim(func.to_char(ARInvoice.pokok,'999,999,999,990')).label('f'), 
                           func.trim(func.to_char(ARInvoice.denda,'999,999,999,990')).label('g'), 
                           func.trim(func.to_char(ARInvoice.bunga,'999,999,999,990')).label('h'), 
                           func.trim(func.to_char(ARInvoice.jumlah,'999,999,999,990')).label('i'),
                           ARInvoice.tgl_tetap.label('j'), 
                           ARInvoice.unit_nama.label('k'),
                   ).order_by(ARInvoice.unit_kode,ARInvoice.rek_kode)   
    
########                    
# CSV #
########          
@view_config(route_name='arinvoicewp-csv', renderer='csv')
def view_csv(request):
    ses = request.session
    params = request.params
    url_dict = request.matchdict
    u = request.user.id    
    awal  = 'awal' in request.params and request.params['awal']\
            or datetime.now().strftime('%Y-%m-%d')
    akhir = 'akhir' in request.params and request.params['akhir']\
            or datetime.now().strftime('%Y-%m-%d')
    if url_dict['csv']=='reg' :
        query = query_reg()
        if u != 1:
            query = query.filter(ARInvoice.owner_id==u)
                          
        row = query.filter(ARInvoice.tgl_tetap.between(awal,akhir),
                           ARInvoice.status_grid==0)#.first()
        #print "-- ROW -- ",row
        header = 'No. Bayar','Penyetor','Objek','Uraian','Tgl. Tetap','Jumlah','OPD' #row.keys()
        rows = []
        for item in row.all():
            rows.append(list(item))
        
        # override attributes of response
        filename = 'Tagihan_WP_%s_sd_%s.csv' %(awal, akhir)
        request.response.content_disposition = 'attachment;filename=' + filename

    return {
      'header': header,
      'rows'  : rows,
    } 
        
##########
# PDF    #
##########    
@view_config(route_name='arinvoicewp-pdf', permission='read')
def view_pdf(request):
    global awal,akhir,unit_nm,unit_al,unit_kd
    params   = request.params
    url_dict = request.matchdict
    u = request.user.id
    
    if group_in(request, 'wp'):
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
        
    awal  = 'awal' in request.params and request.params['awal']\
            or datetime.now().strftime('%Y-%m-%d')
    akhir = 'akhir' in request.params and request.params['akhir']\
            or datetime.now().strftime('%Y-%m-%d')
    id1   = 'id1' in request.params and request.params['id1']
    
    if url_dict['pdf']=='reg' :
        nm = "BADAN PENDAPATAN DAERAH"
        al = "Jl. Soekarno Hatta, No. 528, Bandung"
        query = query_reg()
        if u != 1:
             query = query.filter(ARInvoice.owner_id==u)
                          
        rml_row = open_rml_row('arinvoicewp.row.rml')
        rows=[]
        for r in query.filter(ARInvoice.tgl_tetap.between(awal,akhir),
                              ARInvoice.status_grid==0).all():
            s = rml_row.format(kode=r.a, 
                               wp=r.b, 
                               rek_k=r.c, 
                               rek_n=r.d, 
                               terutang=r.e.strftime('%d-%m-%Y'), 
                               jumlah=r.f, 
                               unit=r.g)
            rows.append(s)      
        if group_in(request, 'wp'):
            pdf, filename = open_rml_pdf('arinvoicewp.rml', rows2=rows, 
                                                            un_nm=unit_nm,
                                                            un_al=unit_al,
                                                            awal=awal,
                                                            akhir=akhir)
        else:       
            pdf, filename = open_rml_pdf('arinvoicewp.rml', rows2=rows, 
                                                            awal=awal,
                                                            akhir=akhir, 
                                                            un_nm=nm,
                                                            un_al=al)
        return pdf_response(request, pdf, filename)
        
    if url_dict['pdf']=='cetak' :
        query = query_cetak()
        rml_row = open_rml_row('arinvoicewp_cetak.row.rml')
        rows=[]
        
        for r in query.filter(ARInvoice.tgl_tetap.between(awal,akhir),ARInvoice.id==id1).all():
            s = rml_row.format(kode=r.a, 
                               wp_n=r.b, 
                               wp_a=r.c, 
                               rek_k=r.d, 
                               rek_n=r.e, 
                               terutang=r.f, 
                               denda=r.g, 
                               bunga=r.h, 
                               jumlah=r.i,
                               terima=r.j.strftime('%d/%m/%Y'),
                               unit=r.k )
            rows.append(s)   
        print "--- ROWS ---- ",rows    
        pdf, filename = open_rml_pdf('arinvoicewp_cetak.rml', rows2=rows)
        return pdf_response(request, pdf, filename)