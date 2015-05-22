import colander
import informixdb
from datetime import (datetime, date)

from time import (strptime, strftime, time, sleep)
from sqlalchemy import (not_, or_, text)
from pyramid.view import (view_config,)
from pyramid.httpexceptions import (HTTPFound,)
from deform import (Form, widget, ValidationFailure,)
from datatables import (ColumnDT, DataTables)
from ..tools import (email_validator,BULANS, captcha_submit, get_settings)
from ..models import (DBSession)
from ..models.isipkd import (Pkb)
from ..models.informix import EngInformix

SESS_ADD_FAILED = 'user add failed'
SESS_EDIT_FAILED = 'user edit failed'

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
    no_rangka    = colander.SchemaNode(
                      colander.String(),
                      widget =  widget.TextInputWidget(max=40),
                      validator=form_validator,
                      title = 'No. Rangka'
                      )
    no_ktp       = colander.SchemaNode(
                      colander.String(),
                      title = 'No. Identitas',
                      oid="no_ktp"
                      )
    email        = colander.SchemaNode(
                      colander.String(),
                      validator=email_validator,
                      title = 'E-Mail'
                      )
    no_hp        = colander.SchemaNode(
                      colander.String(),
                      title = 'No. Handphone',
                      oid="no_hp"
                      )
    kd_status    = colander.SchemaNode(
                      colander.Integer(),
                      title='Status.bayar',
                      missing=colander.drop,
                      oid="kd_status"
                      )
    no_rangka1   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'No. Rangka',
                      oid="no_rangka1"
                      )
    no_ktp1      = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'No. Identitas',
                      oid="no_ktp1"
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
    nr    = colander.SchemaNode(
                      colander.String(),
                      oid="nr"
                      )
    nk       = colander.SchemaNode(
                      colander.String(),
                      oid="nk"
                      )
    em        = colander.SchemaNode(
                      colander.String(),
                      oid="em"
                      )
    nh        = colander.SchemaNode(
                      colander.String(),
                      oid="nh"
                      )
    cd        = colander.SchemaNode(
                      colander.String(),
                      oid="cd"
                      )
    ct        = colander.SchemaNode(
                      colander.String(),
                      oid="ct"
                      )
                          
def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
     
def save(request, values, row=None):
    engInformix = EngInformix()

    sql = """INSERT INTO v_smsdft (no_rangka, no_ktp, email, no_hp, ivr,
                         tg_pros_daftar, jam_daftar, kd_status, flag_sms)
                  VALUES('{no_rangka}', '{no_ktp}', '{email}', '{no_hp}', '{ivr}', 
                         '{c_date}' , '{c_time}', '{kd_status}', '{flag_sms}')"""
                         
    row = engInformix.execute(sql.format(
            no_rangka = values['no_rangka'],
            no_ktp    = values['no_ktp'],
            email     = values['email'],
            no_hp     = values['no_hp'],
            ivr       = '11',
            c_date    = values['c_date'],
            c_time    = values['c_time'],
            kd_status = 0, 
            flag_sms  = 0))
            
    tm_awal    = datetime.now()
    row_result = None

    sql_result = """
        SELECT * FROM  v_smsdft 
        WHERE no_rangka= '{no_rangka}' and no_ktp= '{no_ktp}'
              and email = '{email}' and no_hp='{no_hp}' and ivr= '{ivr}'
              and tg_pros_daftar='{c_date}' and jam_daftar='{c_time}'
              and kd_status='{kd_status}'
    """.format(
                    no_rangka = values['no_rangka'],
                    no_ktp    = values['no_ktp'],
                    email     = values['email'],
                    no_hp     = values['no_hp'],
                    ivr       = '11',
                    c_date    = values['c_date'],
                    c_time    = values['c_time'],
                    kd_status = 1)
                  
    trx_timeout        = 10
    delay_after_insert = 1
    awal = time()
    p    = None
    msg  = None
    
    while time() - awal < trx_timeout:
        sleep(delay_after_insert)
        try:
            p = engInformix.fetchone(sql_result)
        except informixdb.OperationalError, msg:
            msg = msg
            break
        except informixdb.ProgrammingError, msg:
            msg = msg
            break
        if p:
            break
    print p       
    print '--------------------Message-------------------------',msg
    print '----------------P Hasil Select----------------------',p
    return p    

def save_request(values, request, row=None):
    #values['no_rangka'] = values['no_rangka']
    #values['no_ktp']    = values['no_ktp']
    #values['email']     = values['email']
    #values['no_hp']     = values['no_hp']
    row = save(request, values, row)
    request.session.flash('PKB sudah disimpan.')
    return row
    
def route_list(request):
    return HTTPFound(location=request.route_url('pkb-add'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='pkb', renderer='templates/pkb/add.pt',
             )#permission='view')
@view_config(route_name='pkb-add', renderer='templates/pkb/add.pt',
             )#permission='view')
def view_add(request):
    req = request
    found = 0
    settings = get_settings()
    print 'X--------_______Setting Informix______--------X',settings
    private_key = settings['recaptcha.private_key']
    data_key    = settings['recaptcha.private_key']

    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
                if private_key:
                    response = captcha_submit(
                        data_key,
                        req.params['g-recaptcha-response'],
                        private_key, None 
                        )
                    if not response.is_valid:
                        req.session.flash(response.error_code,'error')
                        return dict(form=form, private_key=private_key, found=found)                
            except ValidationFailure, e:
                return dict(form=form, private_key=private_key, found=found)
            ctrl=dict(controls)
            c_now  = datetime.now()
            ctrl['c_date'] = c_now.strftime('%m-%d-%Y')
            ctrl['c_time'] = c_now.strftime('%H:%M:%S')
            row = save_request(ctrl, request)
            found = 1
            print '----------------Row Hasil Select 1------------------',row
            print '----------------CTRL Hasil Select ------------------',ctrl
            return HTTPFound(location=request.route_url('pkb-edit',nr=ctrl['no_rangka'],
                                                                   nk=ctrl['no_ktp'],
                                                                   em=ctrl['email'],
                                                                   nh=ctrl['no_hp'],
                                                                   cd=ctrl['c_date'],
                                                                   ct=ctrl['c_time'],))

        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form, private_key=private_key, found=found)

def query_id(request):
    engInformix = EngInformix()
    
    sql_result1 = """
        SELECT * FROM  v_smsdft 
        WHERE no_rangka= '{no_rangka}' and no_ktp= '{no_ktp}'
              and email = '{email}' and no_hp='{no_hp}' and ivr= '{ivr}'
              and tg_pros_daftar='{c_date}' and jam_daftar='{c_time}'
              and kd_status='{kd_status}'
    """.format(
                    no_rangka = request.matchdict['nr'],
                    no_ktp    = request.matchdict['nk'],
                    email     = request.matchdict['em'],
                    no_hp     = request.matchdict['nh'],
                    c_date    = request.matchdict['cd'],
                    c_time    = request.matchdict['ct'],
                    ivr       = '11',
                    kd_status = 1)
    x = engInformix.fetchone(sql_result1)
    print '----------------Row Hasil X-------------------------',x
    return x
    
@view_config(route_name='pkb-edit', renderer='templates/pkb/edit.pt',
             )#permission='view')
def view_edit(request):
    req   = request
    found = 0
    row   = query_id(request)
    print '----------------Row Hasil Params--------------------',row
    
    settings = get_settings()
    print 'X--------_______Setting Informix______--------X',settings
    private_key = settings['recaptcha.private_key']
    data_key    = settings['recaptcha.private_key']
    
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
                if private_key:
                    response = captcha_submit(
                        data_key,
                        req.params['g-recaptcha-response'],
                        private_key, None 
                        )
                    if not response.is_valid:
                        req.session.flash(response.error_code,'error')
                        return dict(form=form, private_key=private_key, found=found)                
            except ValidationFailure, e:
                return dict(form=form, private_key=private_key, found=found)
            ctrl=dict(controls)
            c_now  = datetime.now()
            ctrl['c_date'] = c_now.strftime('%m-%d-%Y')
            ctrl['c_time'] = c_now.strftime('%H:%M:%S')
            row = save_request(ctrl, request)
            found = 1
            print '----------------Row Hasil Select--------------------',row
            return HTTPFound(location=request.route_url('pkb-edit',nr=ctrl['no_rangka'],
                                                                   nk=ctrl['no_ktp'],
                                                                   em=ctrl['email'],
                                                                   nh=ctrl['no_hp'],
                                                                   cd=ctrl['c_date'],
                                                                   ct=ctrl['c_time'],))

        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
        
    values = {}
    values['kd_status']       = row and row.kd_status      or 0     
    values['flag_sms']        = row and row.flag_sms       or 0 
    values['no_rangka1']      = row and row.no_rangka      or request.matchdict['nr'] 
    values['no_ktp1']         = row and row.no_ktp         or request.matchdict['nk']  
    values['no_rangka']       = row and row.no_rangka      or request.matchdict['nr'] 
    values['no_ktp']          = row and row.no_ktp         or request.matchdict['nk'] 
    values['email']           = row and row.email          or request.matchdict['em'] 
    values['no_hp']           = row and row.no_hp          or request.matchdict['nh']    
    values['tg_pros_daftar']  = row and row.tg_pros_daftar or request.matchdict['cd'] 
    values['jam_daftar']      = row and row.jam_daftar     or request.matchdict['ct'] 
    values['ket']             = row and row.ket            or None 
    values['kd_bayar']        = row and row.kd_bayar       or None 
    values['kd_wil']          = row and row.kd_wil         or None 
    values['kd_wil_proses']   = row and row.kd_wil_proses  or None 
    values['nm_pemilik']      = row and row.nm_pemilik     or None 
    values['no_polisi']       = row and row.no_polisi      or None 
    values['warna_tnkb']      = row and row.warna_tnkb     or None 
    values['milik_ke']        = row and row.milik_ke       or None 
    values['nm_merek_kb']     = row and row.nm_merek_kb    or None 
    values['nm_model_kb']     = row and row.nm_model_kb    or None 
    values['th_buatan']       = row and row.th_buatan      or None 
    values['tg_akhir_pjklm']  = row and row.tg_akhir_pjklm or None 
    values['tg_akhir_pjkbr']  = row and row.tg_akhir_pjkbr or None 
    values['tg_bayar_bank']   = row and row.tg_bayar_bank  or None 
    values['jam_bayar_bank']  = row and row.jam_bayar_bank or None 
    values['kd_trn_bank']     = row and row.kd_trn_bank    or None 
    values['kd_trn_dpd']      = row and row.kd_trn_dpd     or None 
    values['ivr']             = row and row.ivr            or None 
    values['bbn_pok']         = row and row.bbn_pok  or 0
    values['bbn_den']         = row and row.bbn_den  or 0
    values['pkb_pok']         = row and row.pkb_pok  or 0
    values['pkb_den']         = row and row.pkb_den  or 0
    values['swd_pok']         = row and row.swd_pok  or 0
    values['swd_den']         = row and row.swd_den  or 0
    values['adm_stnk']        = row and row.adm_stnk or 0 
    values['adm_tnkb']        = row and row.adm_tnkb or 0
    values['jumlah']          = row and row.jumlah   or 0
    

    form.set_appstruct(values) 
    return dict(form=form, private_key=private_key, found=found)
