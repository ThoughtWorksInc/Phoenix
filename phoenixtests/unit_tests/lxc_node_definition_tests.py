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

import unittest
from unittest.case import SkipTest
from phoenix import fabfile, node_config
import yaml
from phoenix.utilities.utility import get_class_from_fully_qualified_string

all_credentials = {
    'test' : fabfile.Credentials('test', {'private_key' : 'unit-test.pem'}, "/some/path")
}
class LXCNodeDefinitionTests(unittest.TestCase):

    def load_node_definition(self, aws_node_yaml):
        env_values = yaml.load(aws_node_yaml)
        node_definition = env_values['nodes'][0]
        node_type_class = node_definition['type']
        node_definition_object = get_class_from_fully_qualified_string(node_type_class)()
        return node_definition, node_definition_object

    def test_should_add_error_if_node_template_definition_is_missing(self):
        lxc_node_yaml = """
                  test:
                  nodes:
                    - invalid_template: ubuntu
                      services: [hello_world]
                      type: phoenix.providers.lxc_provider.LXCNodeDefinition

                  node_provider:
                    class_name: LXCNodeProvider
                    host_name: ec2-184-72-150-211.compute-1.amazonaws.com
                    admin_user: ubuntu
                    credentials: test
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(lxc_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'template' not set for LXC node definition number 1 in 'test' environment", error_list[0])
