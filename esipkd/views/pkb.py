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
                      title = 'No. Identitas'
                      )
    email        = colander.SchemaNode(
                      colander.String(),
                      validator=email_validator,
                      title = 'E-Mail'
                      )
    no_hp        = colander.SchemaNode(
                      colander.String(),
                      title = 'No. Handphone'
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
                          
def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
     
def save(request, values, row=None):
    engInformix = EngInformix()
    
    c_now  = datetime.now()
    c_date = c_now.strftime('%m-%d-%Y')
    c_time = c_now.strftime('%H:%M:%S')
    
    sql = """INSERT INTO v_daftsms (no_rangka, no_ktp, email, no_hp, ivr,
                         tg_pros_daftar, jam_daftar, kd_status, flag_sms)
                  VALUES('{no_rangka}', '{no_ktp}', '{email}', '{no_hp}', '{ivr}', 
                         '{c_date}' , '{c_time}', '{kd_status}', '{flag_sms}')"""
                         
    row = engInformix.execute(sql.format(
            no_rangka = values['no_rangka'],
            no_ktp    = values['no_ktp'],
            email     = values['email'],
            no_hp     = values['no_hp'],
            ivr       = '11',
            c_date    = c_date ,
            c_time    = c_time,
            kd_status = 0, 
            flag_sms  = 0))
            
    tm_awal    = datetime.now()
    row_result = None

    sql_result = """
        SELECT * FROM  v_daftsms 
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
                    c_date    = c_date ,
                    c_time    = c_time,
                    kd_status = 0)
                  
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
    #return HTTPFound(location=request.route_url('pkb-edit', rowd=p, msg=msg))

def save_request(values, request, row=None):
    values['no_rangka'] = values['no_rangka']
    values['no_ktp']    = values['no_ktp']
    values['email']     = values['email']
    values['no_hp']     = values['no_hp']
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
            row = save_request(dict(controls), request)
            found = 1
            print '----------------Row Hasil Select--------------------',row
            return HTTPFound(location=request.route_url('pkb-edit',nr=row.no_rangka,
                                                                   nk=row.no_ktp,
                                                                   em=row.email,
                                                                   nh=row.no_hp))

        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form, private_key=private_key, found=found)

def query_id(request):
    engInformix = EngInformix()
    
    sql_result1 = """
        SELECT * FROM  v_daftsms 
        WHERE no_rangka= '{no_rangka}' and no_ktp= '{no_ktp}'
              and email = '{email}' and no_hp='{no_hp}' and ivr= '{ivr}'
              and kd_status='{kd_status}'
    """.format(
                    no_rangka = request.matchdict['nr'],
                    no_ktp    = request.matchdict['nk'],
                    email     = request.matchdict['em'],
                    no_hp     = request.matchdict['nh'],
                    ivr       = '11',
                    kd_status = 0)
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
            row = save_request(dict(controls), request)
            found = 1
            print '----------------Row Hasil Select--------------------',row
            return HTTPFound(location=request.route_url('pkb-edit',nr=row.no_rangka,
                                                                   nk=row.no_ktp,
                                                                   em=row.email,
                                                                   nh=row.no_hp))

        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
        
    values = {}
    values['kd_status']       = row.kd_status     
    values['flag_sms']        = row.flag_sms      
    values['no_rangka1']      = row.no_rangka     
    values['no_ktp1']         = row.no_ktp           
    values['tg_pros_daftar']  = row.tg_pros_daftar
    values['jam_daftar']      = row.jam_daftar    
    values['ket']             = row.ket           
    values['kd_bayar']        = row.kd_bayar      
    values['kd_wil']          = row.kd_wil        
    values['kd_wil_proses']   = row.kd_wil_proses 
    values['nm_pemilik']      = row.nm_pemilik    
    values['no_polisi']       = row.no_polisi     
    values['warna_tnkb']      = row.warna_tnkb    
    values['milik_ke']        = row.milik_ke      
    values['nm_merek_kb']     = row.nm_merek_kb   
    values['nm_model_kb']     = row.nm_model_kb   
    values['th_buatan']       = row.th_buatan     
    values['tg_akhir_pjklm']  = row.tg_akhir_pjklm
    values['tg_akhir_pjkbr']  = row.tg_akhir_pjkbr
    values['tg_bayar_bank']   = row.tg_bayar_bank 
    values['jam_bayar_bank']  = row.jam_bayar_bank
    values['kd_trn_bank']     = row.kd_trn_bank   
    values['kd_trn_dpd']      = row.kd_trn_dpd    
    values['ivr']             = row.ivr  
    
    ## Untuk yang tipe Integer ## 
    if row.bbn_pok == None:
        values['bbn_pok']     = 0
    else:
        values['bbn_pok']     = row.bbn_pok  
    
    if row.bbn_den == None:
        values['bbn_den']     = 0
    else:    
        values['bbn_den']     = row.bbn_den  

    if row.pkb_pok == None:
        values['pkb_pok']     = 0
    else:        
        values['pkb_pok']     = row.pkb_pok  

    if row.pkb_den == None:
        values['pkb_den']     = 0
    else:        
        values['pkb_den']     = row.pkb_den 

    if row.swd_pok == None:
        values['swd_pok']     = 0
    else:        
        values['swd_pok']     = row.swd_pok  
 
    if row.swd_den == None:
        values['swd_den']     = 0
    else: 
        values['swd_den']     = row.swd_den    
    
    if row.adm_stnk == None:
        values['adm_stnk']    = 0
    else:    
        values['adm_stnk']    = row.adm_stnk  
 
    if row.adm_tnkb == None:
        values['adm_tnkb']    = 0
    else: 
        values['adm_tnkb']    = row.adm_tnkb  

    if row.jumlah == None:
        values['jumlah']      = 0
    else:        
        values['jumlah']      = row.jumlah     

    form.set_appstruct(values) 
    return dict(form=form, private_key=private_key, found=found)
