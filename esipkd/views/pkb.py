import colander
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
    no_rangka = colander.SchemaNode(
                    colander.String(),
                    widget =  widget.TextInputWidget(max=5),
                    validator=form_validator
                    )
    nik = colander.SchemaNode(
                    colander.String()
                    )
    email = colander.SchemaNode(
                    colander.String(),
                    validator=email_validator
                    )
    no_handphone = colander.SchemaNode(
                    colander.String()
                    )

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    pass
    
def save_request(values, request, row=None):
    engInformix = EngInformix()
    
    c_now = datetime.now()
    c_date = c_now.strftime('%m-%d-%Y')
    c_time = c_now.strftime('%H:%M:%S')
    sql = """INSERT INTO v_daftsms (no_rangka, no_ktp, email, no_hp, ivr,
                         tg_pros_daftar, jam_daftar, kd_status, flag_sms)
                  VALUES('{no_rangka}', '{no_ktp}', '{email}', '{no_hp}', '{ivr}', 
                         '{c_date}' , '{c_time}', '{kd_status}', '{flag_sms}')"""
                         
    row = engInformix.execute(sql.format(
            no_rangka = values['no_rangka'],
            no_ktp = values['nik'],
            email  = values['email'],
            no_hp   = values['no_handphone'],
            ivr     = '11',
            c_date  = c_date ,
            c_time  = c_time,
            kd_status = '0', 
            flag_sms  = '0'))
            
    tm_awal = datetime.now()
    row_result = None
    sql_result = """
          SELECT * FROM  v_daftsms 
          WHERE no_rangka= '{no_rangka}' and no_ktp= '{no_ktp}'
                and email = '{email}' and no_hp='{no_hp}' and ivr= '{ivr}'
                and tg_pros_daftar='{c_date}' and jam_daftar='{c_time}'
                and kd_status='{kd_status}'
        """.format(
                  no_rangka = values['no_rangka'],
                  no_ktp = values['nik'],
                  email  = values['email'],
                  no_hp   = values['no_handphone'],
                  ivr     = '11',
                  c_date  = c_date ,
                  c_time  = c_time,
                  kd_status = '0')
    trx_timeout = 10
    delay_after_insert = 1
    awal = time()
    p = None
    msg = None
    while time() - awal < trx_timeout:
        sleep(delay_after_insert)
        try:
            p = engInformix.fetchone(sql_result)
        except informixdb.OperationalError, msg:
            msg =  msg
            break
        except informixdb.ProgrammingError, msg:
            msg =  msg
            break
        if p:
            break
    print p       
        
    return HTTPFound(location=request.route_url('pkb-edit', row=p, msg=msg))
    
def route_list(request):
    return HTTPFound(location=request.route_url('pkb'))
    
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
    private_key = settings['recaptcha.private_key']
    data_key = settings['recaptcha.private_key']

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
                #request.session[SESS_ADD_FAILED] = e.render()               
                #return HTTPFound(location=request.route_url('pkb-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form, private_key=private_key)

@view_config(route_name='pkb-edit', renderer='templates/pkb/add.pt',
             permission='view')
def view_edit(request):
    pass