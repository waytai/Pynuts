# -*- coding: utf-8 -*-

# Copyright (C) 2011 Kozea
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Test for Pynuts (all the routes are tested)"""

import json
from flask import url_for
from .helpers import with_client, request
from . import teardown_func, setup_func
from nose.tools import with_setup, raises
from pynuts.document import InvalidId, ConflictError
from complete.exception import NoPermission
from complete.application import app


@with_client
@with_setup(setup_func, teardown_func)
def test_login_post(client):
    """Test the login post."""
    with client.application.test_request_context():
        response = request(
            client.post, url_for('login_post'),
            data={'login': 'fake_login', 'passwd': ''})
        assert 'invalid credentials' in response.data
        response = request(
            client.post, url_for('login_post'),
            data={'login': 'admin', 'passwd': 'root'})


@with_client
@with_setup(setup_func, teardown_func)
def test_logout(client):
    """Test the logout."""
    with client.application.test_request_context():
        response = request(client.get, url_for('logout'))
        assert 'Login required' in response.data
        response = request(client.get, '/', status_code=403)


@with_client
@with_setup(setup_func, teardown_func)
def test_employee_create_fields(client):
    """Check employee create fields."""
    with client.application.test_request_context():
        response = request(client.get, url_for('create_employee'))
        assert 'name="login"' in response.data
        assert 'name="password"' in response.data
        assert 'name="name"' in response.data
        assert 'name="firstname' in response.data
        assert 'name="company"' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_create_employee(client):
    """Create an employee."""
    with client.application.test_request_context():
        response = request(
            client.post, url_for('create_employee'),
            data={'login': 'Tester', 'password': 'test', 'name': 'Tester',
                  'firstname': 'Tester'})
        assert 'Tester Tester' in response.data
        response = request(
            client.post, url_for('create_employee'),
            data={'login': '', 'password': '', 'name': '', 'firstname': ''})
        assert 'This field is required' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_update_fields(client):
    """Check employee update fields"""
    with client.application.test_request_context():
        response = request(client.get, url_for('update_employee'))
        assert 'name="name"' in response.data
        assert 'name="firstname' in response.data
        assert 'name="company"' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_update_employee(client):
    """Update an employee."""
    with client.application.test_request_context():
        response = request(client.get, url_for('logout'))
        response = request(
            client.post, url_for('login_post'),
            data={'login': 'test_login', 'password': 'test_psswd'})
        response = request(
            client.post, url_for('update_employee', person_id=2),
            data={'firstname': 'Updated', 'name': 'Tester'})
        assert 'Updated Tester' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_delete_confirm(client):
    """Check the delete confimation."""
    with client.application.test_request_context():
        response = request(client.get, url_for('delete_employee', person_id=2))
        assert 'Do you really want to delete '
        '<strong>Tester Tester</strong>?' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_delete_employee(client):
    """Delete an employee."""
    with client.application.test_request_context():
        response = request(
            client.post, url_for('delete_employee', person_id=2))
        assert 'Tester Tester' not in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_employee_list(client):
    """Check the employee list."""
    with client.application.test_request_context():
        response = request(client.get, url_for('employees'))
        assert 'Tester Tester' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_employee_table(client):
    """Check the employee table."""
    with client.application.test_request_context():
        response = request(client.get, url_for('table_employees'))
        assert 'Tester Tester' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_company_create_fields(client):
    """Check company create fields."""
    with client.application.test_request_context():
        response = request(client.get, url_for('create_company'))
        assert 'name="name"' in response.data
        assert 'name="employees"' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_company_list(client):
    """Test the company list."""
    with client.application.test_request_context():
        response = request(client.get, url_for('companies'))
        assert 'Test Company 1' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_create_employee_in_company(client):
    """Create employee with company."""
    with client.application.test_request_context():
        response = request(
            client.post, url_for('create_employee'),
            data={'login': 'Tester', 'password': 'test', 'firstname': 'Hired',
                  'name': 'Tester2', 'company': '1'})
        assert 'Hired Tester2' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_check_company_have_employees(client):
    """Check company's employees."""
    with client.application.test_request_context():
        response = request(client.get, url_for('read_company', company_id=1))
        assert 'Hired Tester' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_check_employee_in_company(client):
    """Check employee's company."""
    with client.application.test_request_context():
        response = request(client.get, url_for('read_employee', person_id=3))
        assert 'Test Company 1' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_edit_template(client):
    """Test the edit template."""
    with client.application.test_request_context():
        response = request(
            client.get, url_for(
                'edit_employee_report', person_id=1))
        assert 'EMPLOYEE\'S IDENTITY' in response.data
        assert '{{ field.label.text }}' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_edit_template_post(client):
    """Test the edit template."""
    with client.application.test_request_context():
        response = request(
            client.post,
            url_for(
                'edit_employee_report', person_id=1,
                version='370fc6c4f1cf798e954791d7d9bbd169afabca71'),
            data={
                'document': 'new template',
                'message': 'Update new template',
                '_old_commit': ''})
        assert 'The document was saved.' in response.data
        assert 'Employee List' in response.data
        response = request(
            client.post,
            url_for(
                'edit_employee_report', person_id=1,
                version='370fc6c4f1cf798e954791d7d9bbd169afabca71'),
            data={
                'document': 'new template',
                'message': 'Update new template',
                '_old_commit': '370fc6c4f1cf798e954791d7d9bbd169afabca71'})
        assert 'A conflict happened.' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_archive_employee_report(client):
    with client.application.test_request_context():
        response = request(
            client.post, url_for('archive_employee_report', person_id=1),
            data={'document': 'new template',
                  'message': 'Update new template',
                  '_old_commit': ''})
        assert 'The report was sucessfully archived.' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_html_employee(client):
    """Test the HTML template."""
    with client.application.test_request_context():
        response = request(
            client.get, url_for('html_employee', person_id=1))
        assert 'EMPLOYEE\'S IDENTITY' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_archived_html_employee(client):
    """Test the HTML template archive."""
    with client.application.test_request_context():
        response = request(
            client.get, url_for('archived_html_employee', person_id=1))
        assert 'EMPLOYEE\'S IDENTITY' in response.data


@with_client
@with_setup(setup_func, teardown_func)
def test_pdf_employee(client):
    """Test the PDF generation."""
    with client.application.test_request_context():
        response = request(
            client.get, url_for('pdf_employee', person_id=1),
            content_type='application/pdf')
        assert '%PDF' in response.data[:4]


@with_client
@with_setup(setup_func, teardown_func)
def test_archived_pdf_employee(client):
    """Test the PDF generation archive."""
    with client.application.test_request_context():
        response = request(
            client.get, url_for('archived_pdf_employee', person_id=1),
            content_type='application/pdf')
        assert '%PDF' in response.data[:4]


@with_client
@with_setup(setup_func, teardown_func)
def test_pynuts_static(client):
    """Test the pynuts static route."""
    with client.application.test_request_context():
        request(client.get,
                url_for('_pynuts-static', filename='javascript/save.js'),
                content_type='application/x-javascript')


@with_client
@with_setup(setup_func, teardown_func)
def test_pynuts_resource(client):
    """Test the pynuts resource route."""
    with client.application.test_request_context():
        request(client.get,
                '/_pynuts/resource/EmployeeDoc/1'
                '/370fc6c4f1cf798e954791d7d9bbd169afabca71/logo.png',
                content_type='image/png')


@with_client
@raises(NoPermission)
@with_setup(setup_func, teardown_func)
def test_rights(client):
    """Test for rights."""
    with client.application.test_request_context():
        request(client.get, url_for('test_rights'))
        request(client.get, url_for('logout'))
        request(client.get, url_for('test_rights'))


@with_client
@with_setup(setup_func, teardown_func)
def test_update_content(client):
    """Test the update_content method."""
    with client.application.test_request_context():
        response = request(client.post, url_for('_pynuts-update_content'),
            data=json.dumps({
                    "data": [{
                        "part": "comments",
                        "document_type": "EmployeeDoc",
                        "document_id": "1",
                        "version": "",
                        "content": "comment test"
                    }, {
                        "part": "info",
                        "document_type": "EmployeeDoc",
                        "document_id": "1",
                        "version": "",
                        "content": "info test"}
                    ],
                    "message": None,
                    "author": None,
                    "author_email": None
                }), data_content_type='application/json',
                    content_type='application/json')
        assert "document" in response.data


@with_client
@raises(InvalidId)
@with_setup(setup_func, teardown_func)
def test_InvalidId(client):
    """Test InvalidId exception."""
    class EmployeeDoc(app.Document):
        document_id_template = '/'
    EmployeeDoc.create()