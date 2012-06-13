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
from mockito import mock
from mockito.mockito import when
import yaml
from phoenix import fabfile
from phoenix.providers.aws_provider import AWSNodeProvider, AWSRunningNode, AWSNodeDefinition
from phoenix.environment_description import YamlEnvironmentDescriber

all_credentials = {
    'test' : fabfile.Credentials('test', {'private_key' : 'unit-test.pem'}, "/some/path")
}

class AWSRunningNodeTests(unittest.TestCase):

    def test_can_match_a_node_def_with_service_port_mappings(self):
        fake_boto_instance = mock()

        tags = {
            'services' : """
            apache :
              80: 80""",
            'env_name' : 'my_environment',
            'env_def_name' : 'Single-AZ Deployment',
            'credentials_name' : 'bob'
        }
        fake_boto_instance.tags = tags
        stub_region = mock()
        stub_region.name = 'eu-west'
        fake_boto_instance.region = stub_region
        fake_boto_instance.image_id = '1234'
        fake_boto_instance.instance_type = 'large'

        running_node = AWSRunningNode(fake_boto_instance, None)
        node_def = AWSNodeDefinition(ami_id='1234', size='large', credentials_name='bob', region='eu-west', services=['apache'])

        self.assertTrue(running_node.matches_definition(node_def))


class AWSNodeProviderTests(unittest.TestCase):

    def test_will_parse_AWS_node_environment_configuration(self):
        single_service_yaml = """
            prod:
                services:
                    hello_world: [ web_node, web_node ]
                    mongo: [ db_node ]

                node_provider:
                    class_name: AWSNodeProvider
                    public_api_key: AKIAIGBFGAGVPGKLVX4Q
                    private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
            """

        aws_node_provider = AWSNodeProvider()
        error_list = []
        aws_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 0)



    def test_should_add_error_if_public_api_key_not_found(self):
        single_service_yaml = """
                prod:
                  nodes:
                    - ami_id: ami-4dad7424
                      size:   t1.micro
                      credentials_name: test
                      services: [mongo, hello_world]
                      type: phoenix.providers.aws_provider.AWSNodeDefinition

                  node_provider:
                    class_name: AWSNodeProvider
                    invalid_public_api_key: AKIAIGBFGAGVPGKLVX4Q
                    private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
            """
        aws_node_provider = AWSNodeProvider()
        error_list = []
        aws_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'public_api_key' not found for AWS in 'prod' environment", error_list[0])

    def test_should_add_error_if_public_api_key_is_empty(self):
        single_service_yaml = """
                prod:
                  nodes:
                    - ami_id: ami-4dad7424
                      size:   t1.micro
                      credentials_name: test
                      services: [mongo, hello_world]
                      type: phoenix.providers.aws_provider.AWSNodeDefinition

                  node_provider:
                    class_name: AWSNodeProvider
                    public_api_key:
                    private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
            """
        aws_node_provider = AWSNodeProvider()
        error_list = []
        aws_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'public_api_key' not defined for AWS in 'prod' environment", error_list[0])

    def test_should_add_error_if_public_api_key_contains_only_spaces(self):
        single_service_yaml = """
                prod:
                  nodes:
                    - ami_id: ami-4dad7424
                      size:   t1.micro
                      credentials_name: test
                      services: [mongo, hello_world]
                      type: phoenix.providers.aws_provider.AWSNodeDefinition

                  node_provider:
                    class_name: AWSNodeProvider
                    public_api_key:
                    private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
            """
        aws_node_provider = AWSNodeProvider()
        error_list = []
        aws_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'public_api_key' not defined for AWS in 'prod' environment", error_list[0])

    def test_should_add_error_if_private_api_key_not_found(self):
        single_service_yaml = """
                prod:
                  nodes:
                    - ami_id: ami-4dad7424
                      size:   t1.micro
                      credentials_name: test
                      services: [mongo, hello_world]
                      type: phoenix.providers.aws_provider.AWSNodeDefinition

                  node_provider:
                    class_name: AWSNodeProvider
                    public_api_key: AKIAIGBFGAGVPGKLVX4Q
                    invalid_private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
                """
        aws_node_provider = AWSNodeProvider()
        error_list = []
        aws_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'private_api_key' not found for AWS in 'prod' environment", error_list[0])

    def test_should_add_error_if_private_api_key_is_empty(self):
        single_service_yaml = """
                prod:
                  nodes:
                    - ami_id: ami-4dad7424
                      size:   t1.micro
                      credentials_name: test
                      services: [mongo, hello_world]
                      type: phoenix.providers.aws_provider.AWSNodeDefinition

                  node_provider:
                    class_name: AWSNodeProvider
                    public_api_key: AKIAIGBFGAGVPGKLVX4Q
                    private_api_key:
                """
        aws_node_provider = AWSNodeProvider()
        error_list = []
        aws_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'private_api_key' not defined for AWS in 'prod' environment", error_list[0])

    def test_should_add_error_if_private_api_key_contains_only_spaces(self):
        single_service_yaml = """
                prod:
                  nodes:
                    - ami_id: ami-4dad7424
                      size:   t1.micro
                      credentials_name: test
                      services: [mongo, hello_world]
                      type: phoenix.providers.aws_provider.AWSNodeDefinition

                  node_provider:
                    class_name: AWSNodeProvider
                    public_api_key: AKIAIGBFGAGVPGKLVX4Q
                    private_api_key:
                """
        aws_node_provider = AWSNodeProvider()
        error_list = []
        aws_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'private_api_key' not defined for AWS in 'prod' environment", error_list[0])

    def test_should_return_empty_running_environment_if_nothing_is_running(self):
        fake_boto_instance = mock()

        tags = {
            'services' : """
                apache :
                80: 80""",
            'credentials_name': 'test',
            'env_name' : 'my_environment',
            'env_def_name' : 'Single-AZ Deployment',
            }
        fake_boto_instance.tags = tags
        stub_region = mock()
        stub_region.name = 'eu-west'
        fake_boto_instance.region = stub_region
        fake_boto_instance.image_id = '1234'
        fake_boto_instance.instance_type = 'large'

        mock_connection_provider = mock()
        when(mock_connection_provider).ec2_connection_for_region("eu-west", None, None).thenReturn(None)
        when(mock_connection_provider).get_all_boto_instances(None, None).thenReturn([fake_boto_instance])

        provider = AWSNodeProvider(None, None, mock_connection_provider)

        environment = provider.get_running_environment("test","test", all_credentials)
        self.assertIsNotNone(environment)
        self.assertEqual(0, len(environment.get_locations()))

    def test_should_return_a_node_from_a_running_environment(self):
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
        fake_boto_instance.id = 'id1234'
        fake_boto_instance.public_dns_name = 'test_dns'
        fake_boto_instance.instance_type = 'large'
        fake_boto_instance.state = 'running'
        fake_boto_instance.placement='us-east-1'

        mock_connection_provider = mock()
        when(mock_connection_provider).ec2_connection_for_region("eu-west", None, None).thenReturn(None)
        when(mock_connection_provider).get_all_boto_instances(None, None).thenReturn([fake_boto_instance])

        provider = AWSNodeProvider(None, None, mock_connection_provider)

        environment = provider.get_running_environment("test","Single-AZ Deployment", all_credentials)
        self.assertIsNotNone(environment)
        self.assertIsNotNone(environment.get_locations())
        self.assertIsNotNone(environment.get_locations()[0].get_nodes())
        self.assertEquals('eu-west', environment.get_locations()[0].get_name())
        node = environment.get_locations()[0].get_nodes()[0]

        self.assertIsNotNone(node.get_services())
        self.assertEquals({'apache' : {80 : 80}}, node.get_services())

        expected_yaml = """
        test:
          locations:
          - eu-west:
              nodes:
              - ami_id: '1234'
                availability_zone: 'us-east-1'
                dns_name: test_dns
                id: id1234
                services:
                  apache: {80: 80}
        """
        yamlWriter = YamlEnvironmentDescriber()
        actual_yaml = yamlWriter.describe(environment)

        self.assertEqual(yaml.load(expected_yaml), yaml.load(actual_yaml))

    def test_should_return_a_list_of_nodes_from_a_running_environment(self):
        fake_boto_instance1 = mock()

        tags = {
            'services' : """
                'apache' :
                     80: 80""",
            'credentials_name': 'test',
            'env_name' : 'test',
            'env_def_name' : 'Single-AZ Deployment',
            }
        fake_boto_instance1.tags = tags
        stub_region = mock()
        stub_region.name = 'eu-west'
        fake_boto_instance1.region = stub_region
        fake_boto_instance1.image_id = '1234'
        fake_boto_instance1.id = 'id1234'
        fake_boto_instance1.public_dns_name = 'test_dns'
        fake_boto_instance1.instance_type = 'large'
        fake_boto_instance1.state = 'running'
        fake_boto_instance1.placement='us-east-1'
        fake_boto_instance2 = mock()

        tags = {
            'services' : """
                'mongo' :
                     81: 81""",
            'credentials_name': 'test',
            'env_name' : 'test',
            'env_def_name' : 'Single-AZ Deployment',
            }
        fake_boto_instance2.tags = tags
        stub_region1 = mock()
        stub_region1.name = 'eu-west-1'
        fake_boto_instance2.region = stub_region1
        fake_boto_instance2.image_id = '1234'
        fake_boto_instance2.id = 'id1235'
        fake_boto_instance2.public_dns_name = 'test_dns'
        fake_boto_instance2.instance_type = 'large'
        fake_boto_instance2.state = 'running'
        fake_boto_instance2.placement='us-east-1'
        mock_connection_provider = mock()
        when(mock_connection_provider).ec2_connection_for_region("eu-west-1", None, None).thenReturn(None)
        when(mock_connection_provider).get_all_boto_instances(None, None).thenReturn([fake_boto_instance1, fake_boto_instance2])

        provider = AWSNodeProvider(None, None, mock_connection_provider)

        environment = provider.get_running_environment("test", "Single-AZ Deployment", all_credentials)

        self.assertIsNotNone(environment)
        self.assertEquals(2, len(environment.get_locations()))
        self.assertIsNotNone(environment.get_locations()[0].get_nodes())
        self.assertIsNotNone(environment.get_locations()[1].get_nodes())
        self.assertEquals('eu-west', environment.get_locations()[0].get_name())
        self.assertEquals('eu-west-1', environment.get_locations()[1].get_name())

        node1 = environment.get_locations()[0].get_nodes()[0]
        self.assertIsNotNone(node1.get_services())
        self.assertEquals({'apache' : {80 : 80}}, node1.get_services())

        node2 = environment.get_locations()[1].get_nodes()[0]
        self.assertIsNotNone(node2.get_services())
        self.assertEquals({'mongo' : {81 : 81}}, node2.get_services())

    def test_should_return_a_list_of_nodes_with_same_location_from_a_running_environment(self):
        fake_boto_instance1 = mock()

        tags = {
            'services' : """
                'apache' :
                     80: 80""",
            'credentials_name': 'test',
            'env_name' : 'test',
            'env_def_name' : 'Single-AZ Deployment',
            }
        fake_boto_instance1.tags = tags
        stub_region = mock()
        stub_region.name = 'eu-west'
        fake_boto_instance1.region = stub_region
        fake_boto_instance1.image_id = '1234'
        fake_boto_instance1.id = 'id1234'
        fake_boto_instance1.public_dns_name = 'test_dns'
        fake_boto_instance1.instance_type = 'large'
        fake_boto_instance1.state = 'running'
        fake_boto_instance1.placement='us-east-1'
        fake_boto_instance2 = mock()

        tags = {
            'services' : """
                'mongo' :
                     81: 81""",
            'credentials_name': 'test',
            'env_name' : 'test',
            'env_def_name' : 'Single-AZ Deployment',
            }
        fake_boto_instance2.tags = tags
        stub_region1 = mock()
        stub_region1.name = 'eu-west'
        fake_boto_instance2.region = stub_region1
        fake_boto_instance2.image_id = '1234'
        fake_boto_instance2.id = 'id1235'
        fake_boto_instance2.public_dns_name = 'test_dns'
        fake_boto_instance2.instance_type = 'large'
        fake_boto_instance2.state = 'running'
        fake_boto_instance2.placement='us-east-1'
        mock_connection_provider = mock()
        when(mock_connection_provider).ec2_connection_for_region("eu-west-1", None, None).thenReturn(None)
        when(mock_connection_provider).get_all_boto_instances(None, None).thenReturn([fake_boto_instance1, fake_boto_instance2])

        provider = AWSNodeProvider(None, None, mock_connection_provider)

        environment = provider.get_running_environment("test", "Single-AZ Deployment", all_credentials)

        self.assertIsNotNone(environment)
        self.assertEquals(1, len(environment.get_locations()))
        self.assertIsNotNone(environment.get_locations()[0].get_nodes())
        self.assertEquals('eu-west', environment.get_locations()[0].get_name())
        self.assertEquals(2, len(environment.get_locations()[0].get_nodes()))
        node1 = environment.get_locations()[0].get_nodes()[0]
        self.assertIsNotNone(node1.get_services())
        self.assertEquals({'apache' : {80 : 80}}, node1.get_services())

        node2 = environment.get_locations()[0].get_nodes()[1]
        self.assertIsNotNone(node2.get_services())
        self.assertEquals({'mongo' : {81 : 81}}, node2.get_services())

    def test_should_not_throw_exception_when_node_is_up_and_running(self):
        mock_connection_provider = mock()
        tags = {
            'services' : """
                'apache' :
                     80: 80""",
            'credentials_name': 'test',
            'env_name' : 'test',
            'env_def_name' : 'Single-AZ Deployment',
            }
        fake_boto_instance1 = mock()
        fake_boto_instance1.tags = tags
        stub_region = mock()
        stub_region.name = 'eu-west'
        fake_boto_instance1.region = stub_region
        fake_boto_instance1.image_id = '1234'
        fake_boto_instance1.id = 'id1234'
        fake_boto_instance1.public_dns_name = 'test_dns'
        fake_boto_instance1.ip_address = 'test_ip'
        fake_boto_instance1.state = 'running'
        fake_boto_instance1.placement='us-east-1'
        aws_node = AWSRunningNode(fake_boto_instance1, None, mock_connection_provider)

        when(mock_connection_provider).connected_to_node('test_ip', 22).thenReturn(True)

        aws_node.wait_for_ready(lambda : None, 15)

    def test_should_throw_exception_when_node_is_not_up_and_running(self):
        mock_connection_provider = mock()
        tags = {
            'services' : """
                'apache' :
                     80: 80""",
            'credentials_name': 'test',
            'env_name' : 'test',
            'env_def_name' : 'Single-AZ Deployment',
            }
        fake_boto_instance1 = mock()
        fake_boto_instance1.tags = tags
        stub_region = mock()
        stub_region.name = 'eu-west'
        fake_boto_instance1.region = stub_region
        fake_boto_instance1.id = 'id1234'
        fake_boto_instance1.ip_address = 'test_ip'
        fake_boto_instance1.state = 'running'
        fake_boto_instance1.placement='us-east-1'
        aws_node = AWSRunningNode(fake_boto_instance1, None, mock_connection_provider)

        when(mock_connection_provider).connected_to_node('test_ip', 22).thenReturn(False)

        with self.assertRaisesRegexp(Exception, "Node id1234 is not running"):
            aws_node.wait_for_ready(lambda : None, 5)