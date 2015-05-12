import colander
import informixdb
from datetime import (datetime, date)

from time import (strptime, strftime, time, sleep)
from sqlalchemy import (not_, or_, text)
from pyramid.view import (view_config,)
from pyramid.httpexceptions import (HTTPFound,)
from deform import (Form, widget, ValidationFailure,)
from datatables import (ColumnDT, DataTables)
from ..tools import (email_validator, BULANS, captcha_submit, get_settings)
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
    id           = colander.SchemaNode(
                      colander.Integer(),
                      oid="id")
                          
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
    print '--------------------------------------',msg
    
    rowd = Pkb()
    rowd.kd_status      = p.kd_status     
    rowd.flag_sms       = p.flag_sms      
    rowd.no_rangka      = p.no_rangka     
    rowd.no_ktp         = p.no_ktp        
    rowd.email          = p.email         
    rowd.no_hp          = p.no_hp         
    rowd.tg_pros_daftar = p.tg_pros_daftar
    rowd.jam_daftar     = p.jam_daftar    
    rowd.ket            = p.ket           
    rowd.kd_bayar       = p.kd_bayar      
    rowd.kd_wil         = p.kd_wil        
    rowd.kd_wil_proses  = p.kd_wil_proses 
    rowd.nm_pemilik     = p.nm_pemilik    
    rowd.no_polisi      = p.no_polisi     
    rowd.warna_tnkb     = p.warna_tnkb    
    rowd.milik_ke       = p.milik_ke      
    rowd.nm_merek_kb    = p.nm_merek_kb   
    rowd.nm_model_kb    = p.nm_model_kb   
    rowd.th_buatan      = p.th_buatan     
    rowd.tg_akhir_pjklm = p.tg_akhir_pjklm
    rowd.tg_akhir_pjkbr = p.tg_akhir_pjkbr
    rowd.bbn_pok        = p.bbn_pok       
    rowd.bbn_den        = p.bbn_den       
    rowd.pkb_pok        = p.pkb_pok       
    rowd.pkb_den        = p.pkb_den       
    rowd.swd_pok        = p.swd_pok       
    rowd.swd_den        = p.swd_den       
    rowd.adm_stnk       = p.adm_stnk      
    rowd.adm_tnkb       = p.adm_tnkb      
    rowd.jumlah         = p.jumlah        
    rowd.tg_bayar_bank  = p.tg_bayar_bank 
    rowd.jam_bayar_bank = p.jam_bayar_bank
    rowd.kd_trn_bank    = p.kd_trn_bank   
    rowd.kd_trn_dpd     = p.kd_trn_dpd    
    rowd.ivr            = p.ivr           
    DBSession.add(rowd)
    DBSession.flush()
    return rowd
    
    #return HTTPFound(location=request.route_url('pkb-edit', row=rowd, msg=msg))
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    #values["amount"]=values["amount"].replace('.','') 
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
             permission='view')
@view_config(route_name='pkb-add', renderer='templates/pkb/add.pt',
             permission='view')
def view_add(request):
    req = request

    settings = get_settings()
    print 'X--------_______SETTING INFORMIX______--------X',settings
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
                        return dict(form=form, private_key=private_key)                
            except ValidationFailure, e:
                return dict(form=form, private_key=private_key)
            row = save_request(dict(controls), request)
            print'rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr',row
            return HTTPFound(location=request.route_url('pkb-edit',id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form, private_key=private_key)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Pkb).filter(Pkb.id==request.matchdict['id'])    
    
@view_config(route_name='pkb-edit', renderer='templates/pkb/add.pt',
             permission='view')
def view_edit(request):
    row  = query_id(request).first()
    print '----------------------------X----------------------------', row
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            print '------X------', controls
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
        
    values = row.to_dict()
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
    values['bbn_pok']         = row.bbn_pok       
    values['bbn_den']         = row.bbn_den       
    values['pkb_pok']         = row.pkb_pok       
    values['pkb_den']         = row.pkb_den       
    values['swd_pok']         = row.swd_pok       
    values['swd_den']         = row.swd_den       
    values['adm_stnk']        = row.adm_stnk      
    values['adm_tnkb']        = row.adm_tnkb      
    values['jumlah']          = row.jumlah        
    values['tg_bayar_bank']   = row.tg_bayar_bank 
    values['jam_bayar_bank']  = row.jam_bayar_bank
    values['kd_trn_bank']     = row.kd_trn_bank   
    values['kd_trn_dpd']      = row.kd_trn_dpd    
    values['ivr']             = row.ivr           

    form.set_appstruct(values) 
    return dict(form=form)
