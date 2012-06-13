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
class AWSNodeDefinitionTests(unittest.TestCase):

    def load_node_definition(self, aws_node_yaml):
        env_values = yaml.load(aws_node_yaml)
        node_definition = env_values['nodes'][0]
        node_type_class = node_definition['type']
        node_definition.pop('type')
        node_definition_object = get_class_from_fully_qualified_string(node_type_class)(**node_definition)
        return node_definition, node_definition_object

    def test_should_add_error_if_node_size_definition_is_missing(self):
        aws_node_yaml = """
                  nodes:
                  - ami_id: ami-4dad7424
                    aws_key_name: test
                    credentials_name: test
                    services: [mongo, hello_world]
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'size' not set for AWS node definition number 1 in 'test' environment", error_list[0])

    def test_should_add_error_if_node_size_definition_is_empty(self):
        aws_node_yaml = """
                  nodes:
                  - ami_id: ami-4dad7424
                    size:
                    aws_key_name: test
                    credentials_name: test
                    services: [mongo, hello_world]
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'size' not set for AWS node definition number 1 in 'test' environment", error_list[0])

    def test_should_add_error_if_node_size_definition_contains_only_spaces(self):
        aws_node_yaml = """
                  nodes:
                  - ami_id: ami-4dad7424
                    size:
                    aws_key_name: test
                    credentials_name: test
                    services: [mongo, hello_world]
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'size' not set for AWS node definition number 1 in 'test' environment", error_list[0])


    def test_should_add_error_if_node_ami_id_definition_is_missing(self):
        aws_node_yaml = """
                nodes:
                  - aws_key_name: test
                    size:   t1.micro
                    credentials_name: test
                    services: [mongo, hello_world]
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'ami_id' not set for AWS node definition number 1 in 'test' environment", error_list[0])

    def test_should_add_error_if_node_ami_id_definition_is_empty(self):
        aws_node_yaml = """
                nodes:
                  - aws_key_name: test
                    ami_id:
                    size:   t1.micro
                    credentials_name: test
                    services: [mongo, hello_world]
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'ami_id' not set for AWS node definition number 1 in 'test' environment", error_list[0])

    def test_should_add_error_if_node_ami_id_definition_contains_only_spaces(self):
        aws_node_yaml = """
                nodes:
                  - aws_key_name: test
                    ami_id:
                    size:   t1.micro
                    credentials_name: test
                    services: [mongo, hello_world]
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'ami_id' not set for AWS node definition number 1 in 'test' environment", error_list[0])


    def test_should_add_error_if_aws_key_name_definition_is_missing(self):
        aws_node_yaml = """
                nodes:
                  - ami_id: ami-4dad7424
                    size:   t1.micro
                    credentials_name: test
                    services: [mongo, hello_world]
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'aws_key_name' not set for AWS node definition number 1 in 'test' environment", error_list[0])

    def test_should_add_error_if_aws_key_name_definition_is_empty(self):
        aws_node_yaml = """
                nodes:
                  - ami_id: ami-4dad7424
                    size:   t1.micro
                    credentials_name: test
                    aws_key_name:
                    services: [mongo, hello_world]
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'aws_key_name' not set for AWS node definition number 1 in 'test' environment", error_list[0])

    def test_should_add_error_if_aws_key_name_definition_contains_only_spaces(self):
        aws_node_yaml = """
                nodes:
                  - ami_id: ami-4dad7424
                    size:   t1.micro
                    credentials_name: test
                    services: [mongo, hello_world]
                    aws_key_name:
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'aws_key_name' not set for AWS node definition number 1 in 'test' environment", error_list[0])


    def test_should_add_error_if_credentials_name_is_missing(self):
        aws_node_yaml = """
                nodes:
                  - ami_id: ami-4dad7424
                    aws_key_name: test
                    size:   t1.micro
                    services: [mongo, hello_world]
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'credentials_name' not set for AWS node definition number 1 in 'test' environment", error_list[0])

    def test_should_add_error_if_credentials_name_is_empty(self):
        aws_node_yaml = """
                nodes:
                  - ami_id: ami-4dad7424
                    aws_key_name: test
                    size:   t1.micro
                    services: [mongo, hello_world]
                    credentials_name:
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'credentials_name' not set for AWS node definition number 1 in 'test' environment", error_list[0])

    def test_should_add_error_if_credentials_name_contains_only_spaces(self):
        aws_node_yaml = """
                nodes:
                  - ami_id: ami-4dad7424
                    aws_key_name: test
                    size:   t1.micro
                    services: [mongo, hello_world]
                    credentials_name:
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'credentials_name' not set for AWS node definition number 1 in 'test' environment", error_list[0])

    def test_should_add_error_if_credentials_name_is_not_valid(self):
        aws_node_yaml = """
                nodes:
                  - ami_id: ami-4dad7424
                    aws_key_name: test
                    size:   t1.micro
                    credentials_name: test_invalid
                    services: [mongo, hello_world]
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'credentials_name' does not contain a valid credential for AWS node definition number 1 in 'test' environment", error_list[0])

    def test_should_load_optional_availability_zones_if_one_is_specified(self):
        aws_node_yaml = """
                nodes:
                  - ami_id: ami-4dad7424
                    aws_key_name: test
                    size:   t1.micro
                    credentials_name: test_invalid
                    services: [mongo, hello_world]
                    availability_zone: test_zone1
                    type: phoenix.providers.aws_provider.AWSNodeDefinition
                """
        error_list = []
        node_definition, node_definition_object = self.load_node_definition(aws_node_yaml)

        self.assertEquals('test_zone1', node_definition_object.availability_zone)

        node_definition_object.validate(error_list, 1, "test", node_definition, all_credentials)

