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
from phoenix import   service_definition
from phoenix.configurators import FakeServiceConfigurator
from phoenix.providers import FileBackedNodeProvider

service_definition = service_definition.ServiceDefinition('apache', {'name': 'apache'}, FakeServiceConfigurator(), None)
node_definition =  {'type': 'web_node'}

class GivenAValidConfiguration(unittest.TestCase):
    def test_should_apply_settings_to_node(self):
        provider = FileBackedNodeProvider()
        node = provider.start(node_definition, 'dev', 'some_def')

        service_definition.apply_on(node, { 'settings' : { 'apache' : node.id() } })

        fake_env = self.load_fake_env()
        assert fake_env[node.id()]['settings'] == { 'apache' : node.id() }

    def load_fake_env(self):
        f = open('./fake_nodes/fake_env.yml', 'r')
        fake_env = yaml.load(f)
        return fake_env['nodes']

    def tearDown(self):
        file_path = './fake_nodes/fake_env.yml'
        if os.path.exists(file_path):
            os.remove(file_path)


