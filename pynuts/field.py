"""Wtforms fields created for Pynuts."""

from wtforms import StringField
from wtforms.widgets import html_params, HTMLString


class Editable(object):
    """Contenteditable widget."""
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        return HTMLString(
            u'<div contenteditable="true" %s>%s</div>' %
            (html_params(name=field.name, **kwargs),
             unicode(field._value())))


class EditableField(StringField):
    """Contenteditable field."""
    widget = Editable()
