import sys
import re
import os
import xlrd
from email.utils import parseaddr
from sqlalchemy import not_, func, cast, BigInteger, String, or_, desc
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
    FileData,
    )
from deform.interfaces import FileUploadTempStore
from ..tools import _DTnumberformat, create_now, UploadFiles, get_settings, file_type,_DTstrftime
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
      InvoiceDet,
      User,
      Produk,
      Peruntukan,
      Sptpd,
      Sektor
      )
from ..models.__init__ import(
      UserGroup
      )
from datatables import (
    ColumnDT, DataTables)
    
from daftar import (STATUS, deferred_status,
                    daftar_subjekpajak, deferred_subjekpajak,
                    daftar_wilayah, deferred_wilayah,
                    daftar_unit, deferred_unit,
                    daftar_pajak, deferred_pajak, auto_wp_nm2, auto_pajak_nm, auto_unit_nm_sptpd
                    )
from daftar import STATUS
from ..security import group_finder,group_in

SESS_ADD_FAILED = 'Gagal tambah SPTPD WAPU'
SESS_EDIT_FAILED = 'Gagal edit SPTPD WAPU'

########                    
# List #
########    
@view_config(route_name='sptpd-wapu', renderer='templates/wapu/list.pt',
             permission='read')
def view_list(request):
    awal  = 'awal'  in request.GET and request.GET['awal']  or datetime.now().strftime('%Y-%m-%d')
    akhir = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')
    return dict(rows={"awal":awal, "akhir":akhir})
    
##########
# Action #
##########    
def qry_arinv():
    return DBSession.query(ARInvoice).join(Unit)
                            
@view_config(route_name='sptpd-wapu-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    awal     = 'awal'  in request.GET and request.GET['awal']  or datetime.now().strftime('%Y-%m-%d')
    akhir    = 'akhir' in request.GET and request.GET['akhir'] or datetime.now().strftime('%Y-%m-%d')
    
    if url_dict['act']=='grid':
        u = request.user.id
        print '--------user--------',u
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('wp_nama'))
        columns.append(ColumnDT('tgl_sptpd' , filter=_DTstrftime))
        columns.append(ColumnDT('jumlah', filter=_DTnumberformat))
        columns.append(ColumnDT('status_invoice'))
        query = DBSession.query(Sptpd
                        ).filter(Sptpd.tgl_sptpd.between(awal,akhir)
                        ).order_by(desc(Sptpd.tgl_sptpd),desc(Sptpd.kode))
        if group_in(request, 'bendahara'):
            query = query.join(Unit).join(UserUnit).\
                    filter(UserUnit.user_id==request.user.id)
        rowTable = DataTables(req, Sptpd, query, columns)
        return rowTable.output_result()

#######    
# Add #
#######
tmpstore = FileUploadTempStore()
        
class Uploads(colander.SequenceSchema):
    upload  = colander.SchemaNode(
                FileData(),
                widget=widget.FileUploadWidget(tmpstore),
                validator = None,
                title="Upload File CSV"
                )
             
class AddSchema(colander.Schema):
    moneywidget = widget.MoneyInputWidget(
                  size=20, 
                  options={'allowZero':True,
                           'precision':0})
            
    unit_id         = colander.SchemaNode(
                      colander.Integer(),
                      widget=widget.HiddenWidget(),
                      oid="unit_id",
                      title="OPD",
                      )
    unit_kd         = colander.SchemaNode(
                      colander.String(),
                      #widget=auto_unit_nm2, 
                      title="OPD",
                      oid="unit_kd"
                      )
    unit_nm         = colander.SchemaNode(
                      colander.String(),
                      widget=auto_unit_nm_sptpd, 
                      #title="OPD",
                      oid="unit_nm"
                      )
    subjek_pajak_id = colander.SchemaNode(
                      colander.Integer(),
                      widget=widget.HiddenWidget(),
                      oid = "subjek_pajak_id"
                      )
    subjek_pajak_nm = colander.SchemaNode(
                      colander.String(),
                      title="Wajib Pungut",
                      oid = "subjek_pajak_nm"
                      )
    #wp_nama         = colander.SchemaNode(
    #                    colander.String(),
    #                    title="Nama Lain",
    #                    oid = "wp_nama"
    #                    )                    
    #wp_alamat_1     = colander.SchemaNode(
    #                    colander.String(),
    #                    title="Alamat",
    #                    missing = colander.drop,
    #                    oid = "wp_alamat_1"
    #                    )                 

    #rekening_id     = colander.SchemaNode(
    #                  colander.Integer(),
    #                  widget=widget.HiddenWidget(),
    #                  oid = "rekening_id"
    #                  )    
    #rekening_nm     = colander.SchemaNode(
    #                  colander.String(),
    #                  title="Kode Rekening",
    #                  oid = "rekening_nm"
    #                  )
                    
    #kode            = colander.SchemaNode(
    #                  colander.String(),
    #                  title="No. SPTPD",
    #                  oid = "kode",
    #                  missing = colander.drop,
    #                  )
    nama            = colander.SchemaNode(
                      colander.String(),
                      title="Uraian SPTPD",
                      oid = "nama",
                      missing = colander.drop,
                      )
    periode_1       = colander.SchemaNode(
                      colander.Date(),
                      title="Periode",
                      oid = "periode_1",
                      widget = widget.DateInputWidget()
                      )
    periode_2       = colander.SchemaNode(
                      colander.Date(),
                      title="Periode 2",
                      oid = "periode_2",
                      )
    tgl_sptpd       = colander.SchemaNode(
                      colander.Date(),
                      oid = "tgl_sptpd",
                      title="Tgl. SPTPD",
                      )
    jumlah          = colander.SchemaNode(
                      colander.String(),
                      default = 0,
                      missing=colander.drop,
                      oid = "jum"
                      )
    uploads         = Uploads()

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True),
            oid='id')
                    
def get_form(request, class_form):
    schema = class_form()
    schema = schema.bind(daftar_status=STATUS)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(request, values, row=None):
    if not row:
        row = Sptpd()
        row.create_date = datetime.now()
        row.create_uid  = request.user.id
    row.from_dict(values)
    row.update_uid  = request.user.id
    row.jumlah      = re.sub("[^0-9]", "", row.jumlah)
    
    if not row.tahun_id:
        row.tahun_id = datetime.now().strftime('%Y')
    if not row.wp_alamat_1:
        row.wp_alamat_1 = '-'    
    if not row.wp_alamat_2:
        row.wp_alamat_2 = '-'
    
    ref = Unit.get_by_id(row.unit_id)
    row.unit_kode   = ref.kode
    row.unit_nama   = ref.nama
    row.unit_alamat = ref.alamat
    
    ref = SubjekPajak.get_by_id(row.subjek_pajak_id)
    row.wp_kode = ref.kode
    row.wp_nama = ref.nama
    row.wp_alamat_1 = ref.alamat_1
    row.wp_alamat_2 = ref.alamat_2
    
    #ref = Rekening.get_by_id(row.rekening_id)
    #row.rek_kode = ref.kode
    #row.rek_nama = ref.nama
    
    u = request.user.id
    if u!=1:
        print '----------------User_Login---------------',u
        x = DBSession.query(UserGroup.group_id).filter(UserGroup.user_id==u).first()
        y = '%s' % x
        z = int(y)        
        print '----------------Group_id-----------------',z
        
        if z == 2:
            prefix  = '21'
        else:
            prefix  = '20'
    else:
        prefix  = '20'
        
    tanggal = datetime.now().strftime('%d')
    bulan   = datetime.now().strftime('%m')
    tahun   = datetime.now().strftime('%y')
    
    if not row.kode and not row.no_id:
        if prefix == '20':
            sptpd_no = DBSession.query(func.max(Sptpd.no_id)).\
                                   filter(Sptpd.tahun_id==row.tahun_id,
                                          Sptpd.unit_id==row.unit_id,
                                          func.substr(Sptpd.kode,1,2)=='20').scalar()
        elif prefix == '21':
            sptpd_no = DBSession.query(func.max(Sptpd.no_id)).\
                                   filter(Sptpd.tahun_id==row.tahun_id,
                                          Sptpd.unit_id==row.unit_id,
                                          func.substr(Sptpd.kode,1,2)=='21').scalar()
        if not sptpd_no:
            row.no_id = 1
        else:
            row.no_id = sptpd_no+1

    row.kode = "".join([prefix,  
                        str(tahun).rjust(2,'0'),
                        str(row.unit_id).rjust(4,'0'),
                        str(row.no_id).rjust(8,'0')])
    print "----------- LEWAT kdieu ------------"
    DBSession.add(row)
    DBSession.flush()
    print "----------- LEWAT kdieu ------------",row
    return row
    
def get_seq(controls, name):
    start = False
    key_value = ':'.join([name, 'sequence'])
    r = []
    for key, value in controls:
        if key == '__start__' and value == key_value:
            start = True
            continue
        if key == '__end__' and value == key_value:
            start = False
        if start:
            r.append(value)
    return r
    
class DbUpload(UploadFiles):
    def save_request1(self, row1=None):
        row1 = Sptpd()
        return row1   
    
    def save_request2(self, rows=None):
        rows = Sptpd()
        return rows
        
    def __init__(self):
        settings = get_settings()
        dir_path = os.path.realpath(settings['static_files'])
        UploadFiles.__init__(self, dir_path)
        
    def save(self, request, names, sptpd_id):
        fileslist = request.POST.getall(names)
        for f in fileslist:
            fullpath = UploadFiles.save(self, f)
            print '-------- Full------- : ',fullpath
            xl_workbook = xlrd.open_workbook(fullpath)
            sheet_names = xl_workbook.sheet_names()
            print '-------- Sheet Names : ',sheet_names
            xl_sheet = xl_workbook.sheet_by_name(sheet_names[0])

            row = xl_sheet.row(0)  # 1st row

            from xlrd.sheet import ctype_text   
            
            print('(Column #) type:value')
            for idx, cell_obj in enumerate(row):
                cell_type_str = ctype_text.get(cell_obj.ctype, 'unknown type')
                print('(%s) %s %s' % (idx, cell_type_str, cell_obj.value))
            
            ##--------------- Menampilkan data per Baris dan Kolom ---------------##
            num_cols = xl_sheet.ncols                   # Variabel nomor Kolom
            for row_idx in range(1, xl_sheet.nrows):    # Array dimulai dari Baris Isi
                print ('-'*60)                          # Pembatas
                print ('Row: %s' % row_idx)             # Menampilkan nomor Baris
                
                a1  = xl_sheet.cell(row_idx, 0)         # Variabel untuk Baris dan Kolom yg diambil contoh a1=xl_sheet.cell(Baris 1, Kolom 0)
                a11 = a1.value                          # Variabel ke-2 untuk mengambil Nilai dari variabel diatas
                print "-------- Sektor --------- ",a11
                
                a2  = xl_sheet.cell(row_idx, 1)
                a21 = a2.value
                print "-------- Wilayah -------- ",a21
                
                a3  = xl_sheet.cell(row_idx, 2)
                a31 = a3.value
                print "-------- Pengguna ------- ",a31
                
                a4  = xl_sheet.cell(row_idx, 3)
                a41 = a4.value
                print "-------- Peruntukan ----- ",a41
                
                a5  = xl_sheet.cell(row_idx, 4)
                a51 = a5.value
                print "-------- Jenis BBM ------ ",a51
                
                a6  = xl_sheet.cell(row_idx, 5)
                a61 = a6.value
                print "-------- Volume --------- ",a61
                
                a7  = xl_sheet.cell(row_idx, 6)
                a71 = a7.value
                print "-------- DPP ------------ ",a71
                
                a8  = xl_sheet.cell(row_idx, 7)
                a81 = a8.value
                print "-------- Tarif ---------- ",a81
                
                a9  = xl_sheet.cell(row_idx, 8)
                a91 = a9.value
                print "-------- Total ---------- ",a91
                
                #for col_idx in range(0, num_cols):  # Iterate through columns
                #    cell_obj = xl_sheet.cell(row_idx, col_idx)  # Get cell object by row, col
                #    print ('Column: [%s] cell_obj: [%s]' % (col_idx, cell_obj))
        
                row = InvoiceDet()            
                row.sptpd_id        = sptpd_id
                row.volume          = a61       
                row.dpp             = a71       
                row.harga_jual      = a71/a61   
                row.tarif           = a81       
                row.total_pajak     = a91       
                row.nama            = a31       
                row.alamat          = '-'       
                row.keterangan      = '-'       
                
                sktr = DBSession.query(Sektor.id.label('pi'),
                                       Sektor.kode.label('pk'),
                                       Sektor.nama.label('pn'),
                              ).filter(Sektor.nama.ilike('%s%%' % a11) 
                              ).first()
                if not sktr:
                    return 'Sektor %s tidak ditemukan' % a11 
                row.sektor_nm       = sktr.pn    
                row.sektor_id       = sktr.pi    
                
                pro = DBSession.query(Produk.id.label('pi'),
                                      Produk.kode.label('pk'),
                                      Produk.nama.label('pn'),
                              ).filter(Produk.nama.ilike('%s%%' % a51) 
                              ).first()
                if not pro:
                    return 'Produk %s tidak ditemukan' % a51 
                row.produk_nm       = pro.pn    
                row.produk_id       = pro.pi    
                row.p_kode          = pro.pk    
                
                per = DBSession.query(Peruntukan.id.label('peri'),
                                      Peruntukan.kode.label('perk'),
                                      Peruntukan.nama.label('pern'),
                              ).filter(Peruntukan.nama.ilike('%%%s%%' % a41) 
                              ).first()
                if not per:
                    return 'Peruntukan %s tidak ditemukan' % a41 
                row.peruntukan_id   = per.peri  
                row.peruntukan_nm   = per.pern  
                
                wil = DBSession.query(Wilayah.id.label('wili'),
                                      Wilayah.kode.label('wilk'),
                                      Wilayah.nama.label('wiln'),
                              ).filter(Wilayah.nama.ilike('%%%s%%' % a21) 
                              ).first()
                if not wil:
                    return 'Wilayah %s tidak ditemukan' % a21 
                row.wilayah_id      = wil.wili 
                row.wilayah_nm      = wil.wiln 
                
                sptpd = DBSession.query(Sptpd.subjek_pajak_id.label('sp')
                              ).join(SubjekPajak
                              ).filter(Sptpd.id == sptpd_id,
                                       Sptpd.subjek_pajak_id == SubjekPajak.id
                              ).first()
                                          
                row.subjek_pajak_id = sptpd.sp
                DBSession.add(row)
                
            DBSession.flush()       

            row2 = DBSession.query(func.sum(InvoiceDet.dpp).label('a'),
                                   func.sum(InvoiceDet.total_pajak).label('b')
                           ).filter(InvoiceDet.sptpd_id==sptpd_id
                           ).all()
            print '----- Item keseluruhan -----: ',row2
            for rowa in row2:
                g1 = rowa.a
                g2 = rowa.b
            
            row1 = DBSession.query(Sptpd).filter(Sptpd.id==sptpd_id).first()   
            row1.jumlah = g2
            self.save_request1(row1)   
            #return row1            
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(request, values, row)
    if row:
        print "----------- LEWAT KDIEU ------------",row
        dbu = DbUpload()
        xls_ret=dbu.save(request, 'upload', row.id)
        if xls_ret:
            request.session.flash("Gagal proses %s " % xls_ret, "error")
        else:
            request.session.flash('SPTPD No. %s sudah disimpan.' % row.kode)
    return row
        
def route_list(request):
    return HTTPFound(location=request.route_url('sptpd-wapu'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='sptpd-wapu-add', renderer='templates/wapu/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)

    values = {}
    values['tgl_sptpd']   = datetime.now()
    values['periode_1']   = datetime.now()
    values['periode_2']   = datetime.now()
    
    u = request.user.id
    if u != 1:
        print '----------------User_Login---------------',u
        x = DBSession.query(UserGroup.group_id).filter(UserGroup.user_id==u).first()
        y = '%s' % x
        z = int(y)        
        print '----------------Group_id-----------------',z
        
        if z == 1: ## Wapu ##
            a = DBSession.query(User.email).filter(User.id==u).first()
            print '----------------Email---------------------',a
            rows = DBSession.query(SubjekPajak.id.label('sid'), 
                                   SubjekPajak.kode.label('skd'),
                                   SubjekPajak.nama.label('snm'), 
                                   SubjekPajak.unit_id.label('sui'), 
                                   SubjekPajak.user_id.label('sus'),
                           ).filter(SubjekPajak.email==a,
                           ).first()
            values['subjek_pajak_id'] = rows.sid
            print '----------------Subjek id-----------------------',values['subjek_pajak_id']
            values['subjek_pajak_nm'] = rows.snm
            print '----------------Subjek nama---------------------',values['subjek_pajak_nm']
            values['unit_id'] = rows.sui
            print '----------------Subjek unit---------------------',values['unit_id'] 
            unit = DBSession.query(Unit.nama.label('unm'),
                                   Unit.kode.label('unk')
                           ).filter(Unit.id==values['unit_id'],
                           ).first()
            values['unit_kd'] = unit.unk
            values['unit_nm'] = unit.unm
            print '----------------Unit nama-----------------------',values['unit_nm'] 
    
        elif z == 2: ## Bendahara ##
            print '----------------User_id-------------------',u
            a = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            b = '%s' % a
            c = int(b)
            values['unit_id'] = c
            print '----------------Unit id-------------------------',values['unit_id'] 
            unit = DBSession.query(Unit.nama.label('unm'),
                                   Unit.kode.label('unk')
                           ).filter(Unit.id==c,
                           ).first()
            values['unit_kd'] = unit.unk
            values['unit_nm'] = unit.unm
            print '----------------Unit nama-----------------------',values['unit_nm'] 

    form.set_appstruct(values)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            print "--------------- Control ADD -------",controls
            row = save_request(dict(controls), request)
            print "--------------- Row ADD -----------",row
            return HTTPFound(location=request.route_url('sptpd-wapu-edit',id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Sptpd).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'SPTPD ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='sptpd-wapu-edit', renderer='templates/wapu/edit.pt',
             permission='edit')
def view_edit(request):
    row  = query_id(request).first()
    id   = row.id
    kode = row.kode
    
    if not row:
        return id_not_found(request)
    if row.status_invoice:
        request.session.flash('Data sudah masuk di Nomor Bayar', 'error')
        return route_list(request)
        
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            print "---------------control-------------",controls
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['subjek_pajak_nm'] = row and row.subjekpajaks.nama  or ''
    #values['wp_nama']         = row and row.wp_nama            or ''
    #values['wp_alamat_1']     = row and row.wp_alamat_1        or ''
    #values['rekening_nm']     = row and row.rek_nama           or ''
    values['unit_kd']         = row and row.unit_kode          or ''
    values['unit_nm']         = row and row.unit_nama          or ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='sptpd-wapu-delete', renderer='templates/wapu/delete.pt',
             permission='delete')
def view_delete(request):
    q   = query_id(request)
    row = q.first()
    id  = row.id
    
    if not row:
        return id_not_found(request)
    if row.status_invoice:
        request.session.flash('Data sudah masuk di Nomor Bayar', 'error')
        return route_list(request)
        
    x = DBSession.query(InvoiceDet).filter(InvoiceDet.sptpd_id==id).first()
    if x:
        request.session.flash('Tidak bisa dihapus, karena masih mempunyai detail.','error')
        return route_list(request)
        
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'SPTPD no. %s sudah berhasil dihapus.' % (row.kode)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())