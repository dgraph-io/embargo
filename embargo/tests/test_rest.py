#
#  Copyright (C) 2016 Dell, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from ..api.manager import EmbargoManager
from ..api.rest import app
from ..core import Embargo
from . import unittest

import json
import mock


class RestTests(unittest.TestCase):

    name = "EmbargoRestTests"
    headers = {'Content-Type': 'application/json'}

    def setUp(self):
        self.client = app.test_client()
        self.embargo = mock.MagicMock()

    def test_network_state_missing_state(self):
        data = '''
            {
                "wrong_key": "fast",
                "container_names": "c1"
            }
        '''
        with mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.post('/embargo/%s/network_state' % self.name,
                                      headers=self.headers,
                                      data=data)

            self.assertEqual(400, result.status_code)

    def test_network_state_missing_container_names(self):
        data = '''
            {
                "network_state": "fast",
                "wrong_key": "c1"
            }
        '''
        with mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.post('/embargo/%s/network_state' % self.name,
                                      headers=self.headers,
                                      data=data)

            self.assertEqual(400, result.status_code)

    def test_network_state(self):
        data = '''
            {
                "network_state": "fast",
                "container_names": ["c1"]
            }
        '''
        with mock.patch.object(EmbargoManager,
                               'get_embargo',
                               return_value=self.embargo), \
             mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.post('/embargo/%s/network_state' % self.name,
                                      headers=self.headers,
                                      data=data)

            self.assertEqual(204, result.status_code)
            self.assertEqual(1, self.embargo.fast.call_count)

    def test_action_missing_command(self):
        data = '''
            {
                "wrong_key": "start",
                "container_names": "c1"
            }
        '''
        with mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.post('/embargo/%s/action' % self.name,
                                      headers=self.headers,
                                      data=data)

            self.assertEqual(400, result.status_code)

    def test_action_missing_container_names(self):
        data = '''
            {
                "command": "start",
                "wrong_key": "c1"
            }
        '''
        with mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.post('/embargo/%s/action' % self.name,
                                      headers=self.headers,
                                      data=data)

            self.assertEqual(400, result.status_code)

    def test_action(self):
        data = '''
            {
                "command": "start",
                "container_names": ["c1"]
            }
        '''
        with mock.patch.object(EmbargoManager,
                               'get_embargo',
                               return_value=self.embargo), \
             mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.post('/embargo/%s/action' % self.name,
                                      headers=self.headers,
                                      data=data)

            self.assertEqual(204, result.status_code)
            self.assertEqual(1, self.embargo.start.call_count)

    def test_delete_partition(self):
        with mock.patch.object(EmbargoManager,
                               'get_embargo',
                               return_value=self.embargo), \
             mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.delete('/embargo/%s/partitions' % self.name,
                                        headers=self.headers)

            self.assertEqual(204, result.status_code)
            self.assertEqual(1, self.embargo.join.call_count)

    def test_random_partition(self):
        with mock.patch.object(EmbargoManager,
                               'get_embargo',
                               return_value=self.embargo), \
             mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.post('/embargo/%s/partitions' % self.name,
                                      headers=self.headers,
                                      query_string={'random': 'True'})

            self.assertEqual(204, result.status_code)
            self.assertEqual(1, self.embargo.random_partition.call_count)

    def test_partitions(self):
        data = '''
            {
                "partitions": [["c1"], ["c2"]]
            }
        '''
        with mock.patch.object(EmbargoManager,
                               'get_embargo',
                               return_value=self.embargo), \
             mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.post('/embargo/%s/partitions' % self.name,
                                      headers=self.headers,
                                      data=data)

            self.assertEqual(204, result.status_code)
            self.assertEqual(1, self.embargo.partition.call_count)


    def test_delete_embargo(self):
        with mock.patch.object(EmbargoManager,
                               'get_embargo',
                               return_value=self.embargo), \
             mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.delete('/embargo/%s' % self.name)

            self.assertEqual(204, result.status_code)
            self.assertEqual(1, self.embargo.destroy.call_count)

    def test_get_embargo(self):
        with mock.patch.object(EmbargoManager,
                               'get_embargo',
                               return_value=self.embargo), \
             mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.get('/embargo/%s' % self.name)

            result_data = json.loads(result.get_data(as_text=True))
            self.assertEqual(200, result.status_code)
            self.assertTrue('containers' in result_data)

    def test_get_all_embargos(self):
        embargos = {
            'embargo1': 'abc',
            'embargo2': 'def',
            'embargo3': 'xyz'
        }
        with mock.patch.object(EmbargoManager,
                               'get_all_embargo_names',
                               return_value=list(embargos.keys())):
            result = self.client.get('/embargo', headers=self.headers)
            result_data = json.loads(result.get_data(as_text=True))
            self.assertEqual(200, result.status_code)
            self.assertTrue('embargos' in result_data)
            for key in embargos.keys():
                self.assertTrue(key in result_data.get('embargos'))

    def test_create_embargo(self):
        data = '''
            {
                "containers": {
                    "c1": {
                        "image": "ubuntu:trusty",
                        "hostname": "c1",
                        "command": "/bin/sleep 300"
                    },
                    "c2": {
                        "image": "ubuntu:trusty",
                        "hostname": "c2",
                        "command": "/bin/sleep 300"
                    }
                }
            }
        '''
        with mock.patch.object(EmbargoManager,
                               'get_embargo',
                               return_value=self.embargo):

            result = self.client.post('/embargo/%s' % self.name,
                                      headers=self.headers,
                                      data=data)

            self.assertEqual(1, self.embargo.create.call_count)
            self.assertEqual(204, result.status_code)


    def test_add_docker_container(self):
        data = '''
            {
                "container_ids": ["docker_container_id"]
            }
        '''
        with mock.patch.object(EmbargoManager,
                               'get_embargo',
                               return_value=self.embargo), \
             mock.patch.object(EmbargoManager,
                               'embargo_exists',
                               return_value=True):

            result = self.client.put('/embargo/%s' % self.name,
                                     headers=self.headers,
                                     data=data)

            self.assertEqual(204, result.status_code)
            self.assertEqual(1, self.embargo.add_container.call_count)
