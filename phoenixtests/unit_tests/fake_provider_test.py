# Copyright 2012 ThoughtWorks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import unittest
from nose.tools import istest
import yaml
from phoenix.providers import FileBackedNodeProvider
from phoenix.service_definition import DynamicDictionary


NODE_DEFINITIONS = {
    'web_node': {'type': 'web_node'}
}


class GivenAValidConfigurationFile(unittest.TestCase):

    @istest
    def should_wire_up_an_node(self):
        node = FileBackedNodeProvider().start(NODE_DEFINITIONS['web_node'], 'dev', 'some_def')
        fake_env = self.load_fake_env()
        self.assertEqual(fake_env[node.id()]['env'], 'dev')

    @istest
    def should_wire_up_two_nodes(self):
        node1 = FileBackedNodeProvider().start(NODE_DEFINITIONS['web_node'], 'dev', 'some_def')
        node2 = FileBackedNodeProvider().start(NODE_DEFINITIONS['web_node'], 'dev', 'some_def')
        fake_env = self.load_fake_env()
        self.assertEqual(len(fake_env.values()), 2)

    def test_should_bootstrap_with_callback(self):
        node = FileBackedNodeProvider().start(NODE_DEFINITIONS['web_node'], 'dev', 'some_def')
        node.wait_for_ready(lambda : node.run_command('bootstrapped'), 15)
        fake_env = self.load_fake_env()
        assert fake_env[node.id()]['state'] == 'bootstrapped'

    def test_should_terminate_node(self):
        provider = FileBackedNodeProvider()
        node = provider.start(NODE_DEFINITIONS['web_node'], 'dev', 'some_def')
        provider.shutdown(node.id())
        fake_env = self.load_fake_env()
        assert fake_env[node.id()]['state'] == 'terminated'

    def test_should_list_created_nodes(self):
        fake_node_provider = FileBackedNodeProvider()
        node1 = fake_node_provider.start(NODE_DEFINITIONS['web_node'], 'dev', 'some_def')
        node2 = fake_node_provider.start(NODE_DEFINITIONS['web_node'], 'dev', 'some_def')
        self.assertIn(node1, fake_node_provider.list(None, lambda x: True))
        self.assertIn(node2, fake_node_provider.list(None, lambda x: True))

    def test_should_list_service_and_include_ports(self):
        fake_node_provider = FileBackedNodeProvider()
        node = fake_node_provider.start(NODE_DEFINITIONS['web_node'], 'dev', 'some_def')
        node.add_service_to_tags("test", [DynamicDictionary({'ports':[ 8080, 8081 ]})])
        fake_env = self.load_fake_env()
        self.assertDictEqual(fake_env[node.id()]['services']['test'], {8080:8080, 8081:8081})

    def load_fake_env(self):
        f = open('./fake_nodes/fake_env.yml', 'r')
        fake_env = yaml.load(f)
        return fake_env['nodes']

    def tearDown(self):
        file_path = './fake_nodes/fake_env.yml'
        if os.path.exists(file_path):
            os.remove(file_path)


