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
from phoenix import environment_description, fabfile, environment_definition, service_definition
from mockito import *
from phoenix.providers.address import Address
import yaml
from phoenix.configurators.fake_service_configurator import FakeServiceConfigurator
from phoenix.environment_description import Environment, YamlEnvironmentDescriber, Location, AWSEnvironmentDefinitionTranslator, LXCEnvironmentDefinitionTranslator, Node
from phoenix.providers.aws_provider import AWSNodeProvider, AWSRunningNode, AWSSecurity

class RunningEnvironmentTests(unittest.TestCase):

    def test_should_output_empty_environment_in_yaml_if_no_locations_found(self):

        environment = Environment("test", None)


        yaml_formatter = YamlEnvironmentDescriber()

        expected_yaml="""
        test: {}"""

        expected_values = yaml.load(expected_yaml)
        actual_values = yaml.load(yaml_formatter.describe(environment))
        self.assertEquals(expected_values, actual_values)

    def test_should_output_environment_with_empty_location_in_yaml_if_no_nodes_found(self):

        locations = [Location("us-east-1", None)]

        environment = Environment("test", locations)


        yaml_formatter = YamlEnvironmentDescriber()

        expected_yaml="""
        test:
          locations:
          - us-east-1: {}"""

        expected_values = yaml.load(expected_yaml)
        actual_values = yaml.load(yaml_formatter.describe(environment))
        self.assertEquals(expected_values, actual_values)

    def test_should_output_environment_in_yaml(self):
        fake_boto_instance = mock()

        tags = {
            'services' : """
                'apache' :
                     80: 80""",
            'credentials_name': 'test',
            'env_name' : 'test',
            'env_def_name' : 'Single-AZ Deployment',
            }
        fake_boto_instance.tags = tags
        stub_region = mock()
        stub_region.name = 'eu-west'
        fake_boto_instance.region = stub_region
        fake_boto_instance.image_id = '1234'
        fake_boto_instance.instance_type = 'large'
        fake_boto_instance.state = 'running'
        fake_boto_instance.id = 'test_id'
        fake_boto_instance.public_dns_name = 'test_dns'
        fake_boto_instance.placement = 'us-east-1a'

        nodes = [Node({'dns_name':'test_dns', 'id':'test_id', 'ami_id':'1234', 'services':{'apache':{80:80}}})]

        locations = [Location("us-east-1", nodes)]

        environment = Environment("test", locations)


        yaml_formatter = YamlEnvironmentDescriber()

        expected_yaml="""
        test:
          locations:
          - us-east-1:
                nodes:
                - dns_name: test_dns
                  id: test_id
                  ami_id: '1234'
                  services:
                    apache: {80: 80}
                """

        expected_values = yaml.load(expected_yaml)
        actual_values = yaml.load(yaml_formatter.describe(environment))
        self.assertEquals(expected_values, actual_values)

class EnvironmentDefinitionTests(unittest.TestCase):
    service_definitions = {
        'apache': service_definition.ServiceDefinition('apache', {'name': 'apache', 'connectivity':{'protocol':'http','ports': [ 80 ], 'allowed':['WORLD']}}, FakeServiceConfigurator(), None),
        'my_app': service_definition.ServiceDefinition('my_app', {'name': 'my_app', 'connectivity':{'protocol':'http','ports': [ 8080, 8081], 'allowed':['WORLD']}}, FakeServiceConfigurator(), None)}

    all_credentials = {
        'test' : fabfile.Credentials('test', {'private_key' : 'unit-us-east-test.pem', 'login' : 'ubuntu'}, "/some/path")
    }
    def test_should_output_environment_definition_in_yaml_for_aws(self):
        env_yaml_string = """
        integration:
          nodes:
          - ami_id: ami-4dad7424
            size:   t1.micro
            credentials_name: test
            aws_key_name: test
            services: [apache, my_app]
            type: phoenix.providers.aws_provider.AWSNodeDefinition
            region: eu-west-1
            availability_zone: eu-west-1a

          node_provider:
            class_name: AWSNodeProvider
            public_api_key: AKIAIGBFGAGVPGKLVX4Q
            private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
        """
        env_definitions_from_yaml = environment_definition.environment_definitions_from_yaml(env_yaml_string, self.service_definitions, "test", self.all_credentials)

        translator = AWSEnvironmentDefinitionTranslator()

        environment = translator.translate(env_definitions_from_yaml, 'integration', self.service_definitions)

        yaml_formatter = YamlEnvironmentDescriber()
        expected_yaml="""
        test:
          locations:
          - eu-west-1:
                nodes:
                - ami_id: 'ami-4dad7424'
                  availability_zone: 'eu-west-1a'
                  services:
                    apache:
                        ports:
                            - 80
                        protocol: 'http'
                        allowed:
                            - WORLD
                    my_app:
                         ports:
                            - 8080
                            - 8081
                         protocol: 'http'
                         allowed:
                            - WORLD
                """


        expected_values = yaml.load(expected_yaml)
        actual_values = yaml.load(yaml_formatter.describe(environment))
        self.assertEquals(expected_values, actual_values)

    def test_should_output_environment_definition_in_yaml_for_lxc(self):
        env_yaml_string = """
        lxc_hello_world:
          nodes:
            - template: ubuntu
              services: [apache]
              type: phoenix.providers.lxc_provider.LXCNodeDefinition
            - template: ubuntu
              services: [my_app]
              type: phoenix.providers.lxc_provider.LXCNodeDefinition

          node_provider:
            class_name: LXCNodeProvider
            host_name: ec2-184-72-150-211.compute-1.amazonaws.com
            credentials: test
        """
        env_definitions_from_yaml = environment_definition.environment_definitions_from_yaml(env_yaml_string, self.service_definitions, "lxc_hello_world", self.all_credentials)

        translator = LXCEnvironmentDefinitionTranslator()

        environment = translator.translate(env_definitions_from_yaml, 'lxc_hello_world', self.service_definitions)

        yaml_formatter = YamlEnvironmentDescriber()
        expected_yaml="""
        lxc_hello_world:
          locations:
          - ec2-184-72-150-211.compute-1.amazonaws.com:
                nodes:
                - template: 'ubuntu'
                  services:
                    apache:
                        ports:
                            - 80
                        protocol: 'http'
                        allowed:
                            - WORLD
                - template: 'ubuntu'
                  services:
                    my_app:
                         ports:
                            - 8080
                            - 8081
                         protocol: 'http'
                         allowed:
                            - WORLD
                """


        expected_values = yaml.load(expected_yaml)
        actual_values = yaml.load(yaml_formatter.describe(environment))
        self.assertEquals(expected_values, actual_values)