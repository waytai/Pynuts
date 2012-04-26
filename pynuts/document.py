import os
import docutils
import jinja2
import docutils.core
import mimetypes
from flask import Response, render_template, request, redirect, flash, url_for
from werkzeug.datastructures import Headers
from jinja2 import ChoiceLoader
from weasyprint import HTML
from docutils.writers.html4css1 import Writer

from .environment import create_environment
from .fs import GitFS, GitLoader


class MetaDocument(type):
    """Metaclass for document classes."""
    def __init__(cls, name, bases, dict_):
        if cls.repository:
            # TODO: find a better endpoint name than the name of the class
            cls._resource = cls.__name__
            cls._pynuts.documents[cls._resource] = cls
            cls._pynuts.add_url_rule(
                '/_resource/%s/<document_id>/<version>/<path:filename>' % (
                    cls._resource),
                cls._resource, cls.static_route)
            if not os.path.isabs(cls.model):
                cls.model = os.path.join(cls._pynuts.root_path, cls.model)
            if cls.settings is None:
                cls.settings = {}
            super(MetaDocument, cls).__init__(name, bases, dict_)


class Document(object):
    """Class Document."""
    __metaclass__ = MetaDocument

    _resource = None

    settings = None
    pdf_css = None
    html_css = None
    repository = None
    document_id_template = None
    model = None

    # Templates
    edit_template = 'edit_document.jinja2'

    def __init__(self, document_id, version=None):
        self.document_id = document_id
        self.git = GitFS(self.repository, branch=self.branch, commit=version)
        self.environment = create_environment()
        self.environment.loader = ChoiceLoader((
            GitLoader(self.git), self.environment.loader))

    @property
    def branch(self):
        """Branch name of the document."""
        return 'refs/documents/%s' % self.document_id

    @property
    def archive_branch(self):
        """Branch name of the document archives."""
        return 'refs/documents/%s' % self.document_id

    @property
    def version(self):
        """Actual git version of the document."""
        return self.git.commit.id

    def history(self):
        """Yield the parent documents."""
        git = GitFS(self.repository, branch=self.branch)
        for version in git.history():
            yield type(self)(self.document_id, version=version)

    def archive_history(self):
        """Yield the parent documents stored as archives."""
        git = GitFS(self.repository, branch=self.archive_branch)
        for version in git.history():
            yield type(self)(self.document_id, version=version)

    @classmethod
    def from_data(cls, version=None, **kwargs):
        """Create an instance of the class from the given data."""
        return cls(cls.document_id_template.format(**kwargs), version=version)

    def resource_base64(self, filename, **kwargs):
        """Resource content encoded in base64."""
        mimetype, _ = mimetypes.guess_type(filename)
        return 'data:%s;base64,%s' % (
            mimetype or '',
            self.git.read(filename).encode('base64').replace('\n', ''))

    def resource_url(self, filename):
        """Resource URL for the application."""
        return url_for(
            self._resource, document_id=self.document_id, filename=filename,
            version=self.version)

    @classmethod
    def static_route(cls, document_id, filename, version):
        """Serve static files for documents."""
        mimetype, _ = mimetypes.guess_type(filename)
        return Response(
            cls(document_id, version).git.read(filename), mimetype=mimetype)

    @classmethod
    def generate_HTML(cls, part='index.rst.jinja2', resource_type='url',
                      **kwargs):
        """Generate the HTML of the document.

        :param part: part of the document to render.
        :param resource_type: external resource type: 'url' or 'base64'.

        """
        document = cls.from_data(**kwargs)
        template = document.environment.get_template(part)
        resource = getattr(document, 'resource_%s' % resource_type)
        source = template.render(resource=resource, **kwargs)
        parts = docutils.core.publish_parts(
            source=source, writer=Writer(),
            settings_overrides=document.settings)
        return parts

    @classmethod
    def generate_PDF(cls, **kwargs):
        """Generate PDF from the document."""
        html = cls.generate_HTML('base64', **kwargs)['whole']
        # TODO: stylesheets
        return HTML(string=html.encode('utf-8')).write_pdf()

    @classmethod
    def download_PDF(cls, filename=None, **kwargs):
        """Return a HTTP response with PDF document as file in attachment.

        :param filename: filename of the attached document.

        """
        headers = Headers()
        headers.add('Content-Disposition', 'attachment', filename=filename)
        return Response(
            cls.generate_PDF(**kwargs), mimetype='application/pdf',
            headers=headers)

    @classmethod
    def archive(cls, **kwargs):
        """Archive the current version of the document."""
        document = cls.from_data(**kwargs)
        tree_id = document.git.commit.tree
        # TODO: add data into the tree
        commit_id = document.git.store_commit(
            tree_id, [document.git.repository.refs[document.archive_branch]],
            'Pynuts', 'Archive %s' % document.document_id)
        document.git.repository.refs[document.archive_branch] = commit_id

    @classmethod
    def create(cls, **kwargs):
        """Create the ReST document.

        Return ``True`` if the document has been created, ``False`` if the
        document id was already used.

        """
        document = cls.from_data(**kwargs)
        tree_id = document.git.store_directory(cls.model)
        commit_id = document.git.store_commit(
            tree_id, None, 'Pynuts', 'Create %s' % document.document_id)
        return document.git.repository.refs.add_if_new(
            document.branch, commit_id)

    @classmethod
    def edit(cls, template, part='index.html.jinja2', redirect_url=None,
             **kwargs):
        """Return the template where you can edit the ReST document.

        :param template: your application template.
        :param redirect_url: the route you want to go after saving.

        Return ``True`` if the document has been edited, ``False`` if the
        document id was already used.

        """
        if request.method == 'POST':
            document = cls.from_data(
                version=request.form['_old_commit'], **kwargs)
            blob_id = document.git.store_string(
                request.form['document'].encode('utf-8'))
            tree_id = document.git.tree.add(part, 0100644, blob_id)
            commit_id = document.git.store_commit(
                tree_id, [document.version.commit],
                'Pynuts', 'Edit %s' % document.document_id)
            if document.git.repository.refs.set_if_equals(
                document.branch, document.version, commit_id):
                flash('The document was saved.', 'ok')
                if redirect_url:
                    return redirect(redirect_url)
            else:
                flash('A conflict happened.', 'error')
        return render_template(template, cls=cls, **kwargs)

    @classmethod
    def view_edit(cls, part='index.html.jinja2', **kwargs):
        """Render the HTML for edit_template."""
        document = cls.from_data(**kwargs)
        template = document.environment.get_template(cls.edit_template)
        text = document.git.read(part).decode('utf-8')
        return jinja2.Markup(template.render(
            cls=cls, text=text, old_commit=document.git.commit.id, **kwargs))

    @classmethod
    def html(cls, template, **kwargs):
        """Return the HTML document template."""
        return render_template(template, cls=cls, **kwargs)

    @classmethod
    def view_html(cls, part='index.html.jinja2', **kwargs):
        """Generate a HTML document ready to include in Jinja templates.

        :param part: part of the HTML to render (check docutils writer).

        """
        return jinja2.Markup(cls.generate_HTML(**kwargs)['html_body'])
