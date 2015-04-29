import colander
from datetime import (datetime, date)
from time import (strptime, strftime)
from sqlalchemy import (not_, or_)
from pyramid.view import (view_config,)
from pyramid.httpexceptions import (HTTPFound,)
from deform import (Form, widget, ValidationFailure,)
from datatables import (ColumnDT, DataTables)

from ..tools import (email_validator,BULANS, captcha_submit)
from ..models import (DBSession)
from ..models.isipkd import (Pkb)

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
    row = {}
    row['email'] = 'aagusti@1'
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Tunggu beberapa saat email atau SMS akan segera dikirim.')
        
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
    private_key = '6LcGLQATAAAAABtqq0J20BATKsZPGXwBVj6i5zk_'
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
                response = captcha_submit(
                    '6LcGLQATAAAAAPlQuLEaUUrmAO845hlNKbZeUr1J', #req.args['recaptcha_challenge_field']
                    req.params['g-recaptcha-response'],
                    private_key, None 
                    )
                    
                     
                if not response.is_valid:
                    req.session.flash(response.error_code,'error')
                    return dict(form=form)                
            except ValidationFailure, e:
                return dict(form=form)
                #request.session[SESS_ADD_FAILED] = e.render()               
                #return HTTPFound(location=request.route_url('pkb-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)
