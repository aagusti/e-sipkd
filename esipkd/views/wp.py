import re
from email.utils import parseaddr
from sqlalchemy import not_, func, or_, desc
from datetime import datetime
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
from ..tools import (email_validator,BULANS, captcha_submit, get_settings)
from ..models import DBSession, User, UserGroup, Group
from ..models.isipkd import(
      SubjekPajak,
      ARInvoice,
      Unit,
      UserUnit,
      ObjekPajak
      )
from ..security import group_in
from datatables import (
    ColumnDT, DataTables)
from daftar import (STATUS, deferred_status,
                    daftar_user, deferred_user)


SESS_ADD_FAILED = 'Gagal tambah wp'
SESS_EDIT_FAILED = 'Gagal edit wp'

########                    
# List #
########    
@view_config(route_name='wp', renderer='templates/wp/list.pt',
             permission='read')
def view_list(request):
    return dict(rows={})

#######    
# Add #
#######
def form_validator(form, value):
    def err_kode():
        raise colander.Invalid(form,
            'Kode wp %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Nama  %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    def err_user():
        raise colander.Invalid(form,
            'User ID  %s sudah digunakan oleh ID %d' % (
                value['user_id'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(SubjekPajak).filter_by(id=uid)
        r = q.first()
    else:
        r = None
    #q = DBSession.query(SubjekPajak).filter_by(kode=value['kode'])
    #found = q.first()
    #if r:
    #    if found and found.id != r.id:
    #        err_kode()
    #elif found:
    #    err_kode()
    if 'nama' in value: # optional
        found = SubjekPajak.get_by_nama(value['nama'])
        if r:
            if found and found.id != r.id:
                err_name()
        elif found:
            err_name()
    if 'user_id' in value and int(value['user_id'])>0:
        found = SubjekPajak.get_by_user_wp(value['user_id'])
        if r:
            if found and found.id != r.id:
                err_user()
        elif found:
            err_user()
    if 'login' in value: # and int(value['user_id'])==0:
        found = User.get_by_name(value['nama'])
        if r:
            if found and found.id != r.id:
                err_user()
        elif found:
            err_user()

class AddSchema(colander.Schema):
    '''
    user_id  = colander.SchemaNode(
                    colander.Integer(),
                    widget = deferred_user,
                    #oid="user_id",
                    title="User")
    '''
    kode     = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    title ="No. Registrasi"
               )
    nama     = colander.SchemaNode(
                    colander.String()
               )
    alamat_1 = colander.SchemaNode(
                    colander.String(),
                    title ="Alamat"
               )
    alamat_2 = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    title ="Alamat ke-2"
               )
    kelurahan = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop
               )
    kecamatan = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop
               )
    kota     = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    title ="Kabupaten/Kota"
               )
    provinsi = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop
               )
               
    status   = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status,
                    title="Status")
    login    = colander.SchemaNode(
                    colander.Boolean(),
                    missing = colander.drop,
                    title='Buat Login'
               )
    email    = colander.SchemaNode(
                  colander.String(),
                  validator=email_validator,
                  title = 'E-Mail',
                  missing=colander.drop,
                  oid = 'email'
                  )
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
                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.Integer(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True),
            title="")
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS,
                         daftar_user=daftar_user(),
                         )
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(request, values, row=None):
    login = None

    if not row:
        row = SubjekPajak()
    row.from_dict(values)
    
    ref = Unit.get_by_id(row.unit_id)
    row.unit_kode = ref.kode
    row.unit_lvl  = ref.level_id
    prefix  = '00'
    
    if not row.kode and not row.no_id:
        penyetor_no = DBSession.query(func.max(SubjekPajak.no_id)).\
                               filter(SubjekPajak.unit_id==row.unit_id).scalar()
        print "--------- Penyetor No ---------- ",penyetor_no
        if not penyetor_no:
            row.no_id = 1
        else:
            row.no_id = penyetor_no+1
    if row.unit_lvl == 3:
        row.kode = "".join([re.sub("[^0-9]", "", row.unit_kode), 
                            prefix,
                            str(row.no_id).rjust(6,'0')])
    else:
        row.kode = "".join([re.sub("[^0-9]", "", row.unit_kode), 
                            str(row.no_id).rjust(6,'0')])
    
    #Sementara untuk user yg masuk ke Subjek adalah user yg login dan yg menginputkan data subjek (Bukan subjek yg dibuatkan user login)
    if login:
        row.user_id=request.user.id #login.id
    else:
        row.user_id=request.user.id
        
    if not row.user_id:
        row.user_id=None
        
    DBSession.add(row)
    DBSession.flush()
    
    if 'login' in values and values['login']:
        login = User()
        login.status        = values['status'] 
        login.user_name     = values['email']
        login.email         = values['email']
        login.password      = row.kode
        DBSession.add(login)
        DBSession.flush()
        
        if login.id:
            q = DBSession.query(UserGroup).join(Group).filter(UserGroup.user_id==login.id,
                                                Group.group_name=='wp').first()
            if not q:
                usergroup = UserGroup()
                usergroup.user_id  = login.id
                usergroup.group_id = DBSession.query(Group.id).filter_by(group_name='wp').scalar()
                DBSession.add(usergroup)
                DBSession.flush()
                
                userunit = UserUnit()
                userunit.user_id  = login.id
                userunit.unit_id = DBSession.query(Unit.id).filter_by(id=row.unit_id).scalar()
                DBSession.add(userunit)
                DBSession.flush()
                
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(request, values, row)
    print '----------------ROW-------------------',row
    if row:
        request.session.flash('Penyetor %s %s sudah disimpan.' % (row.kode, row.nama))
        
def route_list(request):
    return HTTPFound(location=request.route_url('wp'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='wp-add', renderer='templates/wp/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    
    values = {}
    u = request.user.id
    print '----------------User_Login---------------',u
    if u != 1 :
        x = DBSession.query(UserGroup.group_id).filter(UserGroup.user_id==u).first()
        y = '%s' % x
        z = int(y)        
        print '----------------Group_id-----------------',z
        
        if z == 2:
            print '----------------User_id-------------------',u
            a = DBSession.query(UserUnit.unit_id).filter(UserUnit.user_id==u).first()
            b = '%s' % a
            c = int(b)
            values['unit_id'] = c
            print '----------------Unit id-------------------------',values['unit_id'] 
            unit = DBSession.query(Unit.nama.label('unm')
                           ).filter(Unit.id==c,
                           ).first()
            values['unit_nm'] = unit.unm
            print '----------------Unit nama-----------------------',values['unit_nm'] 

    form.set_appstruct(values)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)

            #Cek Email sama ato tidak
            a = form.validate(controls)
            print '-------------F------------',a
            b = controls_dicted['email']
            d = a['login']
            e = "%s" % d
            if e == 'True':
                if b != '':
                    c = "%s" % b
                    cek = DBSession.query(User).filter(User.email==c).first()
                    if cek :
                        request.session.flash('Email sudah digunakan.', 'error')
                        return HTTPFound(location=request.route_url('wp-add'))
                else:
                    request.session.flash('Email harus diisi.','error')
                    return HTTPFound(location=request.route_url('wp-add'))
            else:
                if b != '':
                    c = "%s" % b
                    cek = DBSession.query(User).filter(User.email==c).first()
                    if cek :
                        request.session.flash('Email sudah digunakan.', 'error')
                        return HTTPFound(location=request.route_url('wp-add'))

            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                #request.session[SESS_ADD_FAILED] = e.render()               
                #return HTTPFound(location=request.route_url('wp-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(SubjekPajak).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Penyetor ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='wp-edit', renderer='templates/wp/edit.pt',
             permission='edit')
def view_edit(request):
    row = query_id(request).first()
    uid = row.id
    email = row.email
    found = 0
    
    if not row:
        return id_not_found(request)
    x = DBSession.query(ARInvoice).filter(ARInvoice.subjek_pajak_id==uid).first()
    if x:
        request.session.flash('Tidak bisa diedit, karena penyetor sudah digunakan di daftar bayar.','error')
        return route_list(request)
    y = DBSession.query(User.email).filter(User.email==email).first()
    
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)

            #Cek Email sama ato tidak
            a = form.validate(controls)
            print '-------------F------------',a
            b = controls_dicted['email']
            d = a['login']
            e = "%s" % d
            if e == 'True':
                if b != '':
                    c = "%s" % b
                    cek = DBSession.query(User).filter(User.email==c).first()
                    if cek :
                        request.session.flash('Email sudah digunakan.', 'error')
                        return HTTPFound(location=request.route_url('wp-edit',id=row.id))
                else:
                    request.session.flash('Email harus diisi.','error')
                    return HTTPFound(location=request.route_url('wp-edit',id=row.id))
                        
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                #request.session[SESS_EDIT_FAILED] = e.render()               
                #return HTTPFound(location=request.route_url('wp-edit',
                #                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    
    values['alamat_2']  = row and row.alamat_2  or ''
    values['kelurahan'] = row and row.kelurahan or ''
    values['kecamatan'] = row and row.kecamatan or ''
    values['kota']      = row and row.kota      or ''
    values['provinsi']  = row and row.provinsi  or ''
    values['email']     = row and row.email     or ''
    
    if y:        
        found = 1 
    values['login']  = found
    
    #cek = DBSession.query(User).filter(User.email==row.email).first()
    #if cek:
    #    values['login']  = True
    
    values['unit_nm'] = row and row.units.nama or None
    
    form.set_appstruct(values)
    return dict(form=form, found=found)

##########
# Delete #
##########    
@view_config(route_name='wp-delete', renderer='templates/wp/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    id = row.id
    
    x = DBSession.query(ObjekPajak).filter(ObjekPajak.subjekpajak_id==id).first()
    if x:
        request.session.flash('Tidak bisa dihapus, karena penyetor sudah digunakan di Objek Pajak.','error')
        return route_list(request)
        
    y = DBSession.query(ARInvoice).filter(ARInvoice.subjek_pajak_id==id).first()
    if y:
        request.session.flash('Tidak bisa dihapus, karena penyetor sudah digunakan di daftar bayar.','error')
        return route_list(request)
        
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Penyetor %s %s sudah dihapus.' % (row.kode, row.nama)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())

##########
# Action #
##########    
@view_config(route_name='wp-act', renderer='json',
             permission='read')
def view_act(request):
    req      = request
    params   = req.params
    url_dict = req.matchdict
    u        = request.user.id
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('alamat_1'))
        columns.append(ColumnDT('alamat_2'))
        columns.append(ColumnDT('status'))
        columns.append(ColumnDT('units.nama'))
        
        query = DBSession.query(SubjekPajak
                        ).join(Unit
                        ).filter(SubjekPajak.status_grid==0
                        ).order_by(Unit.kode,desc(SubjekPajak.kode))
        if group_in(request, 'bendahara'):
            query = query.join(UserUnit).filter(UserUnit.user_id==u) 
            
        rowTable = DataTables(req, SubjekPajak, query, columns)
        return rowTable.output_result()

    elif url_dict['act']=='hon':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(SubjekPajak.id, SubjekPajak.nama
                  ).filter(SubjekPajak.nama.ilike('%%%s%%' % term),
                           SubjekPajak.status==1,
                           SubjekPajak.status_grid==0
                  ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            r.append(d)
        return r              

    elif url_dict['act']=='hon_tbp':
        term    = 'term'    in params and params['term']    or '' 
        unit_id = 'unit_id' in params and params['unit_id'] or '' 
        if group_in(request, 'bendahara'):
            print "----- Unit TBP ----- ",unit_id
            rows = DBSession.query(SubjekPajak.id, 
                                   SubjekPajak.nama, 
                                   SubjekPajak.alamat_1, 
                                   SubjekPajak.alamat_2
                           ).join(Unit
                           ).outerjoin(UserUnit
                           ).filter(SubjekPajak.nama.ilike('%%%s%%' % term),
                                    SubjekPajak.status==1,
                                    SubjekPajak.status_grid==0,
                                    Unit.id==SubjekPajak.unit_id,
                                    UserUnit.unit_id==Unit.id,
                                    UserUnit.user_id==u                                         
                           ).all()
        else:
            rows = DBSession.query(SubjekPajak.id, 
                                   SubjekPajak.nama, 
                                   SubjekPajak.alamat_1, 
                                   SubjekPajak.alamat_2
                           ).filter(SubjekPajak.nama.ilike('%%%s%%' % term),
                                    SubjekPajak.status==1,
                                    SubjekPajak.status_grid==0,
                                    SubjekPajak.unit_id==unit_id                                       
                           ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            d['alamat_1']    = k[2]
            d['alamat_2']    = k[3]
            r.append(d)
        return r                      

    ## Invoice BUD ##
    elif url_dict['act']=='hon1':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(SubjekPajak.id, 
                               SubjekPajak.nama, 
                               SubjekPajak.user_id, 
                               SubjekPajak.unit_id,
                               SubjekPajak.alamat_1
                  ).filter(SubjekPajak.nama.ilike('%%%s%%' % term),
                           SubjekPajak.status==1,
                           SubjekPajak.status_grid==0 
                  ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            d['user']        = k[2]
            d['unit']        = k[3]
            d['alamat']      = k[4]
            r.append(d)
        return r                  

    ## Invoice Bendahara ##
    elif url_dict['act']=='hon2':
        term = 'term' in params and params['term'] or '' 
        u = request.user.id
        rows = DBSession.query(SubjekPajak.id, 
                               SubjekPajak.nama, 
                               SubjekPajak.user_id, 
                               SubjekPajak.unit_id,
                               SubjekPajak.alamat_1
                       ).join(Unit
                       ).outerjoin(UserUnit
                       ).filter(SubjekPajak.nama.ilike('%%%s%%' % term),
                                SubjekPajak.status==1,
                                SubjekPajak.status_grid==0,
                                Unit.id==SubjekPajak.unit_id,
                                UserUnit.unit_id==Unit.id,
                                UserUnit.user_id==u                                         
                       ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            d['user']        = k[2]
            d['unit']        = k[3]
            d['alamat']      = k[4]
            r.append(d)
        return r                  

    ## Invoice WP ##
    elif url_dict['act']=='hon3':
        term = 'term' in params and params['term'] or '' 
        u = request.user.id
        a = DBSession.query(User.email).filter(User.id==u).first()
        rows = DBSession.query(SubjekPajak.id, SubjekPajak.nama, SubjekPajak.user_id, SubjekPajak.unit_id
                  ).filter(SubjekPajak.nama.ilike('%%%s%%' % term), 
                           SubjekPajak.email==a,
                           SubjekPajak.status==1,
                           SubjekPajak.status_grid==0
                  ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            d['user']        = k[2]
            d['unit']        = k[3]
            r.append(d)
        return r   
        
    elif url_dict['act']=='ho_objek':
        term = 'term' in params and params['term'] or '' 
        u = request.user.id
        print '----------------User_Login---------------',u
        if u != 1:
            x = DBSession.query(UserGroup.group_id).filter(UserGroup.user_id==u).first()
            y = '%s' % x
            z = int(y)        
            print '----------------Group_id-----------------',z
            
            if z == 1:
                a = DBSession.query(User.email).filter(User.id==u).first()
                print '----------------Email--------------------',a
                rows = DBSession.query(SubjekPajak.id, SubjekPajak.nama, SubjekPajak.user_id, SubjekPajak.unit_id
                               ).filter(SubjekPajak.email==a,
                                        SubjekPajak.nama.ilike('%%%s%%' % term),
                                        SubjekPajak.status==1,
                                        SubjekPajak.status_grid==0 
                               ).all()
                r = []
                for k in rows:
                    d={}
                    d['id']          = k[0]
                    d['value']       = k[1]
                    d['user']        = k[2]
                    d['unit']        = k[3]
                    r.append(d)
                print '----------------Penyetor-----------------',r
                return r
             
            elif z == 2:
                print '----------------User_id------------------',u
                rows = DBSession.query(SubjekPajak.id, SubjekPajak.nama, SubjekPajak.user_id, SubjekPajak.unit_id
                               ).join(Unit
                               ).outerjoin(UserUnit
                               ).filter(SubjekPajak.nama.ilike('%%%s%%' % term),
                                        SubjekPajak.status==1,
                                        SubjekPajak.status_grid==0,
                                        Unit.id==SubjekPajak.unit_id,
                                        UserUnit.unit_id==Unit.id,
                                        UserUnit.user_id==u                                         
                               ).all()
                #if group_in(request, 'bendahara'):
                #    rows = query.join(UserUnit).filter(UserUnit.user_id==u) 
                r = []
                for k in rows:
                    d={}
                    d['id']          = k[0]
                    d['value']       = k[1]
                    d['user']        = k[2]
                    d['unit']        = k[3]
                    r.append(d)
                print '----------------Bendahara----------------',r
                return r
            
            else:
                rows = DBSession.query(SubjekPajak.id, SubjekPajak.nama, SubjekPajak.user_id, SubjekPajak.unit_id
                               ).filter(SubjekPajak.nama.ilike('%%%s%%' % term),
                                        SubjekPajak.status==1,
                                        SubjekPajak.status_grid==0
                               ).all()
                r = []
                for k in rows:
                    d={}
                    d['id']          = k[0]
                    d['value']       = k[1]
                    d['user']        = k[2]
                    d['unit']        = k[3]
                    r.append(d)
                print '----------------BUD----------------------',r
                return r  
        else:
            rows = DBSession.query(SubjekPajak.id, SubjekPajak.nama, SubjekPajak.user_id, SubjekPajak.unit_id
                           ).filter(SubjekPajak.nama.ilike('%%%s%%' % term),
                                    SubjekPajak.status==1,
                                    SubjekPajak.status_grid==0 
                           ).all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['user']        = k[2]
                d['unit']        = k[3]
                r.append(d)
            print '----------------ADMIN--------------------',r
            return r     

from ..reports.rml_report import open_rml_row, open_rml_pdf, pdf_response
def query_reg():
    return DBSession.query(SubjekPajak.kode, 
                           SubjekPajak.nama, 
                           SubjekPajak.alamat_1, 
                           SubjekPajak.kelurahan,
                           SubjekPajak.kecamatan,
                           SubjekPajak.kota,
                           SubjekPajak.email, 
                           Unit.nama.label('unit')
                   ).join(Unit
                   ).filter(SubjekPajak.status_grid==0
                   ).order_by(Unit.kode,
                              SubjekPajak.kode
                   )
    
########                    
# CSV #
########          
@view_config(route_name='wp-csv', renderer='csv')
def view_csv(request):
    ses = request.session
    params = request.params
    url_dict = request.matchdict 
    u = request.user.id
    a = datetime.now().strftime('%d-%m-%Y')
    if url_dict['csv']=='reg' :
        query = query_reg()
        if group_in(request, 'bendahara'):
            query = query.join(UserUnit).filter(UserUnit.user_id==u)
            
        row = query.first()
        print "-- ROW -- ",row
        header = row.keys()
        rows = []
        for item in query.all():
            rows.append(list(item))

        # override attributes of response
        filename = 'Penyetor_%s.csv' %(a)
        request.response.content_disposition = 'attachment;filename=' + filename

    return {
      'header': header,
      'rows'  : rows,
    } 
        
##########
# PDF    #
##########    
@view_config(route_name='wp-pdf', permission='read')
def view_pdf(request):
    global awal,akhir,unit_nm,unit_al,unit_kd
    params   = request.params
    url_dict = request.matchdict
    u = request.user.id
    
    if group_in(request, 'bendahara'):
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
        
    if url_dict['pdf']=='reg' :
        nm = "BADAN PENDAPATAN DAERAH"
        al = "Jl. Soekarno Hatta, No. 528, Bandung"
        query = query_reg()
        
        if group_in(request, 'bendahara'):
            query = query.join(UserUnit).filter(UserUnit.user_id==u)
        
        rml_row = open_rml_row('wp.row.rml')
        rows=[]
        for r in query.all():
            s = rml_row.format(kode=r.kode, 
                               nama=r.nama, 
                               alamat=r.alamat_1, 
                               kelurahan=r.kelurahan, 
                               kecamatan=r.kecamatan, 
                               kota=r.kota, 
                               email=r.email, 
                               unit=r.unit)
            rows.append(s)     
            
        if group_in(request, 'bendahara'):
            pdf, filename = open_rml_pdf('wp.rml', rows2=rows, 
                                                   un_nm=unit_nm,
                                                   un_al=unit_al)
        else:
            pdf, filename = open_rml_pdf('wp.rml', rows2=rows, 
                                                   un_nm=nm,
                                                   un_al=al)
        return pdf_response(request, pdf, filename)