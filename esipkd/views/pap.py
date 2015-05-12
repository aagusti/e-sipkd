import colander
import informixdb
from datetime import (datetime, date)
from time import (strptime, strftime, time, sleep)
from sqlalchemy import (not_, or_, text)
from pyramid.view import (view_config,)
from pyramid.httpexceptions import (HTTPFound,)
from deform import (Form, widget, ValidationFailure,)
from datatables import (ColumnDT, DataTables)
from recaptcha.client import captcha

from ..tools import (email_validator, BULANS, captcha_submit, get_settings)
from ..models import (DBSession)
from ..models.isipkd import (Pap)
from ..models.informix import EngInformix

SESS_ADD_FAILED = 'user add failed'
SESS_EDIT_FAILED = 'user edit failed'

#######    
# Add #
#######

def form_validator(form, value):
    def err_no_skpd():
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
    npwpd     = colander.SchemaNode(
                    colander.String(),
                    widget = widget.TextInputWidget(max=14),
                    title = "NPWPD :",
                    oid="npwpd"
                    )
    m_pjk_bln = colander.SchemaNode(
                    colander.String(),
                    title = "Bulan",
                    oid="m_pjk_bln"
                    )
    m_pjk_thn = colander.SchemaNode(
                    colander.String(),
                    title = "Tahun",
                    oid="m_pjk_thn"
                    )
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
    npwpd1   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'NPWPD',
                      oid="npwpd1"
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
    m_pjk_bln1   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Bulan',
                      oid="m_pjk_bln1"
                      )
    m_pjk_thn1   = colander.SchemaNode(
                      colander.String(),
                      missing=colander.drop,
                      title = 'Tahun',
                      oid="m_pjk_thn1"
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
    
    sql = """INSERT INTO v_jupntepap (npwpd, m_pjk_bln, m_pjk_thn,kd_status)
                  VALUES('{npwpd}', '{m_pjk_bln}', '{m_pjk_thn}', '{kd_status}')"""
                         
    row = engInformix.execute(sql.format(
            npwpd     = values['npwpd'],
            m_pjk_bln = values['m_pjk_bln'],
            m_pjk_thn = values['m_pjk_thn'],
            #c_date    = c_date ,
            #c_time    = c_time,
            kd_status = 0))
            
    tm_awal    = datetime.now()
    row_result = None

    sql_result = """
        SELECT * FROM  v_jupntepap 
        WHERE npwpd= '{npwpd}' and m_pjk_bln= '{m_pjk_bln}'
              and m_pjk_thn = '{m_pjk_thn}' and kd_status='{kd_status}'
    """.format(
                    npwpd     = values['npwpd'],
                    m_pjk_bln = values['m_pjk_bln'],
                    m_pjk_thn = values['m_pjk_thn'],
                    #c_date    = c_date ,
                    #c_time    = c_time,
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
    
    rowd = Pap()
    rowd.kd_status     = p.kd_status       
    rowd.kd_bayar      = p.kd_bayar      
    rowd.npwpd         = p.npwpd     
    rowd.nm_perus      = p.nm_perus           
    rowd.al_perus      = p.al_perus
    rowd.vol_air       = p.vol_air    
    rowd.npa           = p.npa        
    rowd.bea_pok_pjk   = p.bea_pok_pjk        
    rowd.bea_den_pjk   = p.bea_den_pjk 
    rowd.m_pjk_bln     = p.m_pjk_bln    
    rowd.m_pjk_thn     = p.m_pjk_thn     
    rowd.tgl_tetap     = p.tgl_tetap    
    rowd.tgl_jt_tempo  = p.tgl_jt_tempo      
    rowd.keterangan    = p.keterangan               
    DBSession.add(rowd)
    DBSession.flush()
    return rowd
    
    #return HTTPFound(location=request.route_url('pap-edit', row=rowd, msg=msg))
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(request.user, values, row)
    request.session.flash('Tunggu beberapa saat email atau SMS akan segera dikirim.')
    return row
        
def route_list(request):
    return HTTPFound(location=request.route_url('pap-add'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='pap', renderer='templates/pap/add.pt',
             permission='view')
@view_config(route_name='pap-add', renderer='templates/pap/add.pt',
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
            return HTTPFound(location=request.route_url('pap-edit',id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form, private_key=private_key)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Pap).filter(Pap.id==request.matchdict['id'])    
    
@view_config(route_name='pap-edit', renderer='templates/pap/add.pt',
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
    values['kd_status']     = row.kd_status        
    values['kd_bayar']      = row.kd_bayar      
    values['npwpd1']        = row.npwpd     
    values['nm_perus']      = row.nm_perus           
    values['al_perus']      = row.al_perus
    values['vol_air']       = row.vol_air    
    values['npa']           = row.npa        
    values['bea_pok_pjk']   = row.bea_pok_pjk        
    values['bea_den_pjk']   = row.bea_den_pjk 
    values['m_pjk_bln1']    = row.m_pjk_bln    
    values['m_pjk_thn1']    = row.m_pjk_thn     
    values['tgl_tetap']     = row.tgl_tetap    
    values['tgl_jt_tempo']  = row.tgl_jt_tempo      
    values['keterangan']    = row.keterangan      

    form.set_appstruct(values) 
    return dict(form=form)
    