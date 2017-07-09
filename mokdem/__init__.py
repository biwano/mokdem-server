from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
import webtest

from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker

from .model import db, Base
from .helpers import parse_setting
from .security import groupfinder
from .setup import Setup


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    config = Configurator(settings=settings)
    # Security policies
    authn_policy = AuthTktAuthenticationPolicy(
        settings['authorization.secret'], callback=groupfinder,
        hashalg='sha512')
    config.set_authentication_policy(authn_policy)
    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)

    engine = engine_from_config(settings, prefix='sqlalchemy.config.')
    config.registry.dbmaker = sessionmaker(bind=engine)
    config.add_request_method(db, reify=True)

#    config.include('pyramid_jinja2')
    config.add_static_view('app', 'app', cache_max_age=3600)
    config.add_route('auth_register', 'api/auth/register', request_method='POST')
    config.add_route('auth_info', 'api/auth/info', request_method='GET')
    config.add_route('auth_login', 'api/auth/info', request_method='POST')
    config.add_route('auth_logout', 'api/auth/info', request_method='DELETE')
#    config.add_route('home', '/')
    config.scan()

    app = config.make_wsgi_app()

    if (parse_setting(settings, 'sqlalchemy.drop')):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        test_app = webtest.TestApp(app)
        Setup(test_app)
    else:
        Base.metadata.create_all(engine)

    return app