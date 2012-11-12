"""__init__ file for Pynuts."""

__version__ = '0.3'

import os
import flask
from werkzeug.utils import cached_property
from flask_sqlalchemy import SQLAlchemy
from flask.ext.uploads import configure_uploads, patch_request_class
from dulwich.repo import Repo

from . import document, rights, view
from .environment import create_environment


class Pynuts(object):
    """Create the Pynuts class, inheriting from flask.Flask

    :param app: a Flask application object
    :type app: flask.Flask

    .. seealso::
      `Flask Application <http://flask.pocoo.org/docs/api/>`_

    """
    def __init__(self, app, *args, **kwargs):

        self.app = app

        # Pynuts default config
        # Can be overwritten by setting these parameters in the application config
        self.app.config.setdefault('CSRF_ENABLED', False)
        self.app.config.setdefault('UPLOADS_DEFAULT_DEST',
            os.path.join(app.instance_path, 'uploads'))
        self.app.config.setdefault('PYNUTS_DOCUMENT_REPOSITORY',
            'documents.git')

        self.documents = {}
        self.views = {}

        # Serve files from the Pynuts static folder
        # at the /_pynuts/static/<path:filename> URL
        self.app.add_url_rule('/_pynuts/static/<path:filename>',
                          '_pynuts-static', static)

        class Document(document.Document):
            """Document base class of the application."""
            _pynuts = self

        self.Document = Document

        class Context(object):
            """Context base class of the application.

            You can get or set any element in the context stored in
            the `g` flask object.

            Example : Set the current time of the request in the context, using
            datetime :

            @app.before_request
            def set_request_time():
                g.context.request_time = datetime.now().strftime('%Y/%m/%d')

            """
            __metaclass__ = rights.MetaContext
            _pynuts = self

            def __getitem__(self, key):
                return getattr(self, key)

            def __setitem__(self, key, value):
                setattr(self, key, value)

            def get(self, key, default=None):
                return getattr(self, key, default)

        self.Context = Context

        class ModelView(view.ModelView):
            """Model view base class of the application."""
            _pynuts = self
            # Create a new Jinja2 environment with Pynuts helpers
            environment = create_environment(_pynuts.jinja_env.loader)

        self.ModelView = ModelView

        self.before_request(self.create_context)

    @cached_property
    def document_repository(self):
        """Return the path to the document repository."""
        return Repo(self.document_repository_path)

    def render_rest(self, document_type, part='index.rst.jinja2',
                    **kwargs):
        """Return the generated ReST version of the document."""
        return self.documents[document_type].generate_rest(part, **kwargs)

    def create_context(self):
        """Create the request context."""
        flask.g.context = self._context_class()

    def add_upload_sets(self, upload_sets, upload_max_size=16777216):
        """Configure the app with the argument upload sets."""
        configure_uploads(self.app, upload_sets)
        patch_request_class(self.app, upload_max_size)  # limit the size of uploads to 16MB


    @property
    def uploads_default_dest(self):
        """Access to the UPLOADS_DEFAULT_DEST configuration."""
        return self.config.get('UPLOADS_DEFAULT_DEST')


def static(filename):
    """ Return files from Pynuts static folder.

    :param filename: the basename of the file contained in Pynuts static folder
    """
    return flask.send_from_directory(
        os.path.join(os.path.dirname(__file__), 'static'), filename)
