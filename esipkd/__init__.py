import locale
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import has_permission
from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.interfaces import IRoutesMapper
from pyramid.httpexceptions import (
    default_exceptionresponse_view,
    HTTPFound, HTTPNotFound
    )

from sqlalchemy import engine_from_config

from .security import group_finder, get_user
from .models import (
    DBSession,
    Base,
    init_model,
    )
from .tools import DefaultTimeZone

# http://stackoverflow.com/questions/9845669/pyramid-inverse-to-add-notfound-viewappend-slash-true    
class RemoveSlashNotFoundViewFactory(object):
    def __init__(self, notfound_view=None):
        if notfound_view is None:
            notfound_view = default_exceptionresponse_view
        self.notfound_view = notfound_view

    def __call__(self, context, request):
        if not isinstance(context, Exception):
            # backwards compat for an append_notslash_view registered via
            # config.set_notfound_view instead of as a proper exception view
            context = getattr(request, 'exception', None) or context
        path = request.path
        registry = request.registry
        mapper = registry.queryUtility(IRoutesMapper)
        if mapper is not None and path.endswith('/'):
            noslash_path = path.rstrip('/')
            for route in mapper.get_routes():
                if route.match(noslash_path) is not None:
                    qs = request.query_string
                    if qs:
                        noslash_path += '?' + qs
                    return HTTPFound(location=noslash_path)
        return self.notfound_view(context, request)
    
    
# https://groups.google.com/forum/#!topic/pylons-discuss/QIj4G82j04c
def url_has_permission(request, permission):
    return has_permission(permission, request.context, request)

@subscriber(BeforeRender)
def add_global(event):
     event['permission'] = url_has_permission

def get_title(request):
    route_name = request.matched_route.name
    #return titles[route_name]
    return  None
routes = [    
    ('home', '/', 'Home'),
    ('login', '/login', 'Login'),
    ('logout', '/logout', None),
    ('forbidden', '/forbidden', 'Forbidden'),
    
    ('password', '/password', 'Change password'),
    ('user', '/user', 'Users'),
    ('user-act', '/user/{act}/act', ''),
    ('user-add', '/user/add', 'Add user'),
    ('user-edit', '/user/{id}/edit', 'Edit user'),
    ('user-delete', '/user/{id}/delete', 'Hapus user'),   
    
    ('group', '/group', 'Group'),
    ('group-act', '/group/{act}/act', ''),
    ('group-add', '/group/add', 'Tambah Group'),
    ('group-edit', '/group/{id}/edit', 'Edit Group'),
    ('group-delete', '/group/{id}/delete', 'Hapus Group'),
    
    ('pkb', '/pkb', 'Pajak Kendaraan Bermotor'),     
    ('pkb-add', '/pkb/add', 'Pajak Kendaraan Bermotor'),

    ('pap', '/pap', 'Pajak Air Permukaan'),     
    ('pap-add', '/pap/add', 'Pajak Air Permukaan'),
    
    ('pbbkb', '/pbbkb', 'PBB-KB'),
    ('pbbkb-act', '/pbbkb/{act}/act', ''),
    ('pbbkb-add', '/pbbkb/add', 'Tambah PBB-KB'),
    ('pbbkb-edit', '/pbbkb/{id}/edit', 'Edit PBB-KB'),
    ('pbbkb-delete', '/pbbkb/{id}/delete', 'Hapus PBB-KB'),
    
    ('hibah', '/hibah', 'Hibah'),
    ('hibah-act', '/hibah/{act}/act', ''),
    ('hibah-add', '/hibah/add', 'Tambah Hibah'),
    ('hibah-edit', '/hibah/{id}/edit', 'Edit Hibah'),
    ('hibah-delete', '/hibah/{id}/delete', 'Hapus Hibah'),

    ('lain', '/lain', 'Lain-lain'),
    ('lain-add', '/lain/add', 'Tambah Lain-lain'),
    ('lain-edit', '/lain/{id}/edit', 'Edit Lain-lain'),    
    ('lain-act', '/lain/{act}/act', ''),
    ('lain-delete', '/lain/{id}/delete', 'Hapus Lain-lain'),

    ('coa', '/coa', 'COA'),
    ('coa-act', '/coa/{act}/act', ''),
    ('coa-add', '/coa/add', 'Tambah COA'),
    ('coa-edit', '/coa/{id}/edit', 'Edit COA'),
    ('coa-delete', '/coa/{id}/delete', 'Hapus COA'),

    ('skpd', '/skpd', 'SKPD/Unit'),
    ('skpd-act', '/skpd/{act}/act', ''),
    ('skpd-add', '/skpd/add', 'Tambah SKPD/Unit'),
    ('skpd-edit', '/skpd/{id}/edit', 'Edit SKPD/Unit'),
    ('skpd-delete', '/skpd/{id}/delete', 'Hapus SKPD/Unit'),

    ('jabatan', '/jabatan', 'Jabatan'),
    ('jabatan-act', '/jabatan/{act}/act', ''),
    ('jabatan-add', '/jabatan/add', 'Tambah Jabatan'),
    ('jabatan-edit', '/jabatan/{id}/edit', 'Edit Jabatan'),
    ('jabatan-delete', '/jabatan/{id}/delete', 'Hapus Jabatan'),
    
    ('pegawai', '/pegawai', 'Pegawai'),
    ('pegawai-act', '/pegawai/{act}/act', ''),
    ('pegawai-add', '/pegawai/add', 'Tambah Pegawai'),
    ('pegawai-edit', '/pegawai/{id}/edit', 'Edit Pegawai'),
    ('pegawai-delete', '/pegawai/{id}/delete', 'Hapus Pegawai'),

    ('pajak', '/pajak', 'Pajak'),
    ('pajak-act', '/pajak/{act}/act', ''),
    ('pajak-add', '/pajak/add', 'Tambah Pajak'),
    ('pajak-edit', '/pajak/{id}/edit', 'Edit Pajak'),
    ('pajak-delete', '/pajak/{id}/delete', 'Hapus Pajak'),
    
    ('wilayah', '/wilayah', 'Wilayah'),
    ('wilayah-act', '/wilayah/{act}/act', ''),
    ('wilayah-add', '/wilayah/add', 'Tambah Wilayah'),
    ('wilayah-edit', '/wilayah/{id}/edit', 'Edit Wilayah'),
    ('wilayah-delete', '/wilayah/{id}/delete', 'Hapus Wilayah'),

    ('wp', '/wp', 'Wajib Pajak'),
    ('wp-act', '/wp/{act}/act', ''),
    ('wp-add', '/wp/add', 'Tambah Wajib Pajak'),
    ('wp-edit', '/wp/{id}/edit', 'Edit Wajib Pajak'),
    ('wp-delete', '/pegawai/{id}/delete', 'Hapus Wajib Pajak'),
    
    ('op', '/op', 'Objek Pajak'),
    ('op-act', '/op/{act}/act', ''),
    ('op-add', '/op/add', 'Tambah Objek Pajak'),
    ('op-edit', '/op/{id}/edit', 'Edit Objek Pajak'),
    ('op-delete', '/op/{id}/delete', 'Hapus Objek Pajak'),
    ]

main_title = 'esipkd'
titles = {}
for name, path, title in routes:
    if title:
        titles[name] = ' - '.join([main_title, title])
    

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    init_model()

    session_factory = session_factory_from_settings(settings)
    if 'localization' not in settings:
        settings['localization'] = 'id_ID.UTF-8'
    locale.setlocale(locale.LC_ALL, settings['localization'])        
    if 'timezone' not in settings:
        settings['timezone'] = DefaultTimeZone
    config = Configurator(settings=settings,
                          root_factory='esipkd.models.RootFactory',
                          session_factory=session_factory)
    config.include('pyramid_beaker')                          
    config.include('pyramid_chameleon')

    authn_policy = AuthTktAuthenticationPolicy('sosecret',
                    callback=group_finder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()                          
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_request_method(get_user, 'user', reify=True)
    config.add_request_method(get_title, 'title', reify=True)
    #config.add_notfound_view(RemoveSlashNotFoundViewFactory())        
                          
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static')
    for name, path, title in routes:
        config.add_route(name, path)
    config.scan()
    return config.make_wsgi_app()
