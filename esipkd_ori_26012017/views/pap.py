import colander
import informixdb
import re
from datetime import (datetime, date)
from time import (strptime, strftime, time, sleep)
from sqlalchemy import (not_, or_, text)
from pyramid.view import (view_config,)
from pyramid.httpexceptions import (HTTPFound,)
from deform import (Form, widget, ValidationFailure,)
from datatables import (ColumnDT, DataTables)
from recaptcha.client import captcha

from ..tools import (email_validator,BULANS, captcha_submit, get_settings,npwpd_validator)
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

def deferred_bulan(node, kw):
    values = kw.get('bulans', [])
    return widget.SelectWidget(values=values)
    
BULANS = (('','Pilih Bulan'),
          ('01','Januari'),
          ('02','Februari'),
          ('03','Maret'),
          ('04','April'),
          ('05','Mei'),
          ('06','Juni'),
          ('07','Juli'),
          ('08','Agustus'),
          ('09','September'),
          ('10','Oktober'),
          ('11','November'),
          ('12','Desember'),
          )
  
def deferred_tahun(node, kw):
    values = kw.get('tahuns', [])
    return widget.SelectWidget(values=values)
    
TAHUNS = (('','Pilih Tahun'),
          ('1990','1990'),('1991','1991'),('1992','1992'),('1993','1993'),('1994','1994'),
          ('1995','1995'),('1996','1996'),('1997','1997'),('1998','1998'),('1999','1999'),
          ('2000','2000'),('2001','2001'),('2002','2002'),('2003','2003'),('2004','2004'),
          ('2005','2005'),('2006','2006'),('2007','2007'),('2008','2008'),('2009','2009'),
          ('2010','2010'),('2011','2011'),('2012','2012'),('2013','2013'),('2014','2014'),
          ('2015','2015'),('2016','2016'),('2017','2017'),('2018','2018'),('2019','2019'),
          ('2020','2020'),('2021','2021'),('2022','2022'),('2023','2023'),('2024','2024'),
          ('2025','2025'),('2026','2026'),('2027','2027'),('2028','2028'),('2029','2029'),
          ('2030','2030'),
          )
          
class AddSchema(colander.Schema):
    npwpd     = colander.SchemaNode(
                    colander.String(),
                    widget = widget.TextInputWidget(max=14),
                    #validator=npwpd_validator,
                    title = "NPWPD",
                    oid="npwpd"
                    )
    m_pjk_bln = colander.SchemaNode(
                    colander.String(),
                    widget=widget.SelectWidget(values=BULANS),
                    title = "Bulan",
                    oid="m_pjk_bln"
                    )
    m_pjk_thn = colander.SchemaNode(
                    colander.String(),
                    widget = widget.SelectWidget(values=TAHUNS),
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

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(request, values, row=None):
    engInformix = EngInformix()
    
    sql_result = """
        SELECT * FROM  v_jupntepap 
        WHERE npwpd= '{npwpd}' and m_pjk_bln= '{m_pjk_bln}'
              and m_pjk_thn = '{m_pjk_thn}' 
    """.format(
                    npwpd     = values['npwpd'],
                    m_pjk_bln = values['m_pjk_bln'],
                    m_pjk_thn = values['m_pjk_thn'])
                    #kd_status = 2)
                    
    p = engInformix.fetchone(sql_result)
    print '----------------P Hasil Select----------------------',p
    return p 
    
def save_request(values, request, row=None):
    values['npwpd']     = values['npwpd']
    values['m_pjk_bln'] = values['m_pjk_bln']
    values['m_pjk_thn'] = values['m_pjk_thn']
    row = save(request, values, row)
    return row
    
def route_list(request):
    return HTTPFound(location=request.route_url('pap-add'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='pap', renderer='templates/pap/add.pt',
             )#permission='view')
@view_config(route_name='pap-add', renderer='templates/pap/add.pt',
             )#permission='view')
def view_add(request):
    req = request
    found = 0
    settings = get_settings()
    print 'X--------_______SETTING INFORMIX______--------X',settings
    private_key = settings['recaptcha.private_key']
    data_key    = settings['recaptcha.private_key']
    
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            a = form.validate(controls)
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
            if not row:
                request.session.flash('Data PAP tidak ditemukan', 'error') 
                values = {}
                values['npwpd']     = a['npwpd']
                values['m_pjk_bln'] = a['m_pjk_bln']
                values['m_pjk_thn'] = a['m_pjk_thn']
                form.set_appstruct(values) 
                return dict(form=form)
                return route_list(request)
            else:
                request.session.flash('Data PAP ditemukan.')
                found = 1
            print '----------------Row Hasil Select--------------------',row
            return HTTPFound(location=request.route_url('pap-edit',nr=row.npwpd,
                                                                   nk=row.m_pjk_bln,
                                                                   em=row.m_pjk_thn))

        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form, private_key=private_key, found=found)
    
def query_id(request):
    engInformix = EngInformix()
    
    sql_result1 = """
        SELECT * FROM  v_jupntepap 
        WHERE npwpd= '{npwpd}' and m_pjk_bln= '{m_pjk_bln}'
              and m_pjk_thn = '{m_pjk_thn}'
    """.format(
                    npwpd     = request.matchdict['nr'],
                    m_pjk_bln = request.matchdict['nk'],
                    m_pjk_thn = request.matchdict['em'])
                    #kd_status = 2)
                    
    x = engInformix.fetchone(sql_result1)
    print '----------------X Hasil Select----------------------',x
    return x 

@view_config(route_name='pap-edit', renderer='templates/pap/edit.pt',
             )#permission='view')
def view_edit(request):
    req   = request
    found = 0
    row   = query_id(request)
    print '----------------Row Hasil Params--------------------',row
    
    settings = get_settings()
    print 'X--------_______SETTING INFORMIX______--------X',settings
    private_key = settings['recaptcha.private_key']
    data_key    = settings['recaptcha.private_key']
    
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            a = form.validate(controls)
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
            if not row:
                request.session.flash('Data PAP tidak ditemukan', 'error')
                values = {}
                values['npwpd']     = a['npwpd']
                values['m_pjk_bln'] = a['m_pjk_bln']
                values['m_pjk_thn'] = a['m_pjk_thn']
                form.set_appstruct(values) 
                return dict(form=form)
                return route_list(request)
            else:
                request.session.flash('Data PAP ditemukan.')
                found = 1
            print '----------------Row Hasil Select--------------------',row
            return HTTPFound(location=request.route_url('pap-edit',nr=row.npwpd,
                                                                   nk=row.m_pjk_bln,
                                                                   em=row.m_pjk_thn))
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
        
    values = {}
    values['npwpd']         = row and row.npwpd        or request.matchdict['nr']
    values['m_pjk_bln']     = row and row.m_pjk_bln    or request.matchdict['nk']
    values['m_pjk_thn']     = row and row.m_pjk_thn    or request.matchdict['em'] 
    values['kd_status']     = row and row.kd_status    or 0    
    values['kd_bayar']      = row and row.kd_bayar     or None  
    values['npwpd1']        = row and row.npwpd        or request.matchdict['nr']
    values['nm_perus']      = row and row.nm_perus     or None      
    values['al_perus']      = row and row.al_perus     or None
    values['m_pjk_bln1']    = row and row.m_pjk_bln    or request.matchdict['nk']
    values['m_pjk_thn1']    = row and row.m_pjk_thn    or request.matchdict['em'] 
    values['tgl_tetap']     = row and row.tgl_tetap    or None
    values['tgl_jt_tempo']  = row and row.tgl_jt_tempo or None     
    values['keterangan']    = row and row.keterangan   or None
    values['vol_air']       = row and row.vol_air      or 0
    values['npa']           = row and row.npa          or 0
    values['bea_pok_pjk']   = row and row.bea_pok_pjk  or 0
    values['bea_den_pjk']   = row and row.bea_den_pjk  or 0

    form.set_appstruct(values) 
    return dict(form=form, private_key=private_key, found=found)
