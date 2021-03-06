# -*-  coding: utf-8 -*-
"""
"""

# Copyright (C) 2015 ZetaOps Inc.
#
# This file is licensed under the GNU General Public License v3
# (GPLv3).  See LICENSE.txt for details.
from time import sleep

import pytest

from zengine.models import Role, Unit
from zengine.lib.exceptions import FormValidationError
from zengine.lib.test_utils import BaseTestCase, username

RESPONSES = {}


class TestCase(BaseTestCase):
    def test_sequential_cruds(self):
        """
        tests proper handling of sequential crudviews.
        if first view's form's "object_key" should not
        broke the latter form
        """
        self.prepare_client('/sequential_cruds/', username='super_user')
        resp = self.client.post()
        object_key = resp.json['forms']['model']['object_key']
        resp = self.client.post(object_id=object_key)
        assert resp.json['msgbox']['title'] == 'object_id:HjgPuHelltHC9USbj8wqd286vbS'
        assert resp.json['msgbox']['msg'] == 'test_ok'

    def test_form_validation(self):
        """
        tests form validation with addition of extra field.
        """
        self.prepare_client('/crud/', username='super_user')
        resp = self.client.post(model='User',
                                cmd='add_edit_form')
        with pytest.raises(FormValidationError):
            self.client.post(model='User',
                             form=dict(foo="bar"),
                             cmd='save::show')

    def test_list_search_add_delete_with_user_model(self):
        # setup workflow
        self.prepare_client('/crud/', username='super_user')

        # calling the crud view without any model should list available models
        # resp = self.client.post()
        # resp.raw()
        # assert resp.json['models'] == [[m.Meta.verbose_name_plural, m.__name__] for m in
        #                                model_registry.get_base_models()]
        model_name = 'User'
        # calling with just model name (without any cmd) equals to cmd="list"
        resp = self.client.post(model=model_name, filters={"username": {"values": [username]}})
        assert 'objects' in resp.json
        assert resp.json['objects'][1]['fields'][0] == username

        resp = self.client.post(model=model_name, cmd='list')
        # count number of records
        num_of_objects = len(resp.json['objects']) - 1

        # add a new employee record, then go to list view (do_list subcmd)
        self.client.post(model=model_name, cmd='add_edit_form')
        resp = self.client.post(model=model_name,
                                cmd='save::show',
                                form=dict(username="fake_user", password="123"))
        assert resp.json['object']['Username'] == 'fake_user'

        # we should have 1 more object relative to previous listing
        # assert num_of_objects + 1 == len(resp.json['objects']) - 1
        # since we are searching for a just created record, we have to wait
        # sleep(1)
        # resp = self.client.post(model=model_name, filters={"username": "fake_user"})

        # attempt to delete the first object, and cancel the confirmation
        obj_id = resp.json['object_key']
        self.client.post(model=model_name, cmd='confirm_deletion',
                         object_id=obj_id)
        resp = self.client.post(model=model_name, cmd='list')

        # after adding one user and cancelling the delete
        assert num_of_objects + 1 == len(resp.json['objects']) - 1

        # delete the first object then go to list view
        print("Delete this %s" % obj_id)
        self.client.post(model=model_name, cmd='confirm_deletion',
                         object_id=obj_id)
        self.client.post(model=model_name, cmd='delete', object_id=obj_id)
        # resp = self.client.post(model=model_name, cmd='list')
        # number of objects should be equal to starting point
        # sleep(1)
        resp = self.client.post(model=model_name, cmd='list')
        resp.raw()
        # perform delete
        assert num_of_objects == len(resp.json['objects']) - 1

    def test_make_list_header(self):
        """
        test headers of object lists
        """
        Role.Meta.list_fields = ['user.username', 'user.unit']
        self.prepare_client('/crud', username='super_user')
        resp = self.client.post(model="Role")
        assert Unit.Meta.verbose_name_plural in resp.json['objects'][0]
        assert "Username" in resp.json['objects'][0]
        assert len(resp.json['objects']) - 1 == Role.objects.count()

