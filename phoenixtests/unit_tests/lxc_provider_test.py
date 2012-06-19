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
from mockito.mocking import mock
from mockito.mockito import when
from phoenix.providers.lxc_provider import LXCNodeProvider, LXCNode
import yaml
from phoenix import fabfile

all_credentials = {
    'test' : fabfile.Credentials('test', {'private_key' : 'unit-test.pem'}, "/some/path")
}
class LXCNodeProviderTests(unittest.TestCase):

    def test_will_parse_LXC_node_environment_configuration(self):
        single_service_yaml = """
                prod:
                    services:
                        hello_world: [ web_node, web_node ]
                        mongo: [ db_node ]

                    node_provider:
                        class_name: LXCNodeProvider
                        host_name: ec2-107-20-98-18.compute-1.amazonaws.com
                        admin_user: ubuntu
                        credentials: test
                """

        lxc_node_provider = LXCNodeProvider()
        error_list = []
        lxc_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 0)


    def test_should_add_error_if_no_host_name_found(self):
        single_service_yaml = """
                prod:
                    services:
                        hello_world: [ web_node, web_node ]
                        mongo: [ db_node ]

                    node_provider:
                        class_name: LXCNodeProvider
                        invalid_host_name: ec2-107-20-98-18.compute-1.amazonaws.com
                        admin_user: ubuntu
                        credentials: test
                """
        lxc_node_provider = LXCNodeProvider()
        error_list = []
        lxc_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'host_name' not found for LXC in 'prod' environment", error_list[0])

    def test_should_add_error_if_host_name_is_empty(self):
        single_service_yaml = """
                prod:
                    services:
                        hello_world: [ web_node, web_node ]
                        mongo: [ db_node ]

                    node_provider:
                        class_name: LXCNodeProvider
                        host_name:
                        admin_user: ubuntu
                        credentials: test
                """
        lxc_node_provider = LXCNodeProvider()
        error_list = []
        lxc_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'host_name' not defined for LXC in 'prod' environment", error_list[0])

    def test_should_add_error_if_host_name_contains_only_spaces(self):
        single_service_yaml = """
                prod:
                    services:
                        hello_world: [ web_node, web_node ]
                        mongo: [ db_node ]

                    node_provider:
                        class_name: LXCNodeProvider
                        host_name:
                        admin_user: ubuntu
                        credentials: test
                """
        lxc_node_provider = LXCNodeProvider()
        error_list = []
        lxc_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'host_name' not defined for LXC in 'prod' environment", error_list[0])

    def test_should_add_error_if_no_credentials_found(self):
        single_service_yaml = """
                prod:
                    services:
                        hello_world: [ web_node, web_node ]
                        mongo: [ db_node ]

                    node_provider:
                        class_name: LXCNodeProvider
                        host_name: ec2-107-20-98-18.compute-1.amazonaws.com
                        admin_user: ubuntu
                        invalid_credentials: test
                """
        lxc_node_provider = LXCNodeProvider()
        error_list = []
        lxc_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'credentials' not found for LXC in 'prod' environment", error_list[0])

    def test_should_add_error_if_credentials_is_empty(self):
        single_service_yaml = """
                prod:
                    services:
                        hello_world: [ web_node, web_node ]
                        mongo: [ db_node ]

                    node_provider:
                        class_name: LXCNodeProvider
                        host_name: ec2-107-20-98-18.compute-1.amazonaws.com
                        admin_user: ubuntu
                        credentials:
                """
        lxc_node_provider = LXCNodeProvider()
        error_list = []
        lxc_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'credentials' not defined for LXC in 'prod' environment", error_list[0])

    def test_should_add_error_if_credentials_contains_only_spaces(self):
        single_service_yaml = """
                prod:
                    services:
                        hello_world: [ web_node, web_node ]
                        mongo: [ db_node ]

                    node_provider:
                        class_name: LXCNodeProvider
                        host_name: ec2-107-20-98-18.compute-1.amazonaws.com
                        admin_user: ubuntu
                        credentials:
                """
        lxc_node_provider = LXCNodeProvider()
        error_list = []
        lxc_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'credentials' not defined for LXC in 'prod' environment", error_list[0])

    def test_should_add_error_if_credentials_invalid(self):
        single_service_yaml = """
                prod:
                    services:
                        hello_world: [ web_node, web_node ]
                        mongo: [ db_node ]

                    node_provider:
                        class_name: LXCNodeProvider
                        host_name: ec2-107-20-98-18.compute-1.amazonaws.com
                        admin_user: ubuntu
                        credentials: test1
                """
        lxc_node_provider = LXCNodeProvider()
        error_list = []
        lxc_node_provider.validate('prod', yaml.load(single_service_yaml)['prod']['node_provider'], error_list, all_credentials)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("'test1' is invalid for key 'credentials' in LXC for 'prod' environment", error_list[0])

    def test_should_return_empty_running_environment_if_nothing_is_running(self):
        mock_command_helper = mock()
        when(mock_command_helper).run_command("sudo lxc-ls -c1").thenReturn("")
        provider = LXCNodeProvider(None, None, mock_command_helper)
        environment = provider.get_running_environment("test", "test", all_credentials)
        self.assertIsNotNone(environment)
        self.assertEqual(0, len(environment.get_locations()))

    def test_should_return_a_list_of_nodes_from_a_running_environment(self):
        mock_command_helper = mock()
        tags1 = """
                'services' :
                     'apache': {80: 80}
                'credentials_name': 'test'
                'env_name' : 'test'
                'env_def_name' : 'Single-AZ Deployment'
                """
        tags2 = """
                'services' :
                     'mongo': {81: 82}
                'credentials_name': 'test'
                'env_name' : 'test'
                'env_def_name' : 'Single-AZ Deployment'
                """
        when(mock_command_helper).run_command("sudo lxc-ls -c1").thenReturn("123\n124")
        when(mock_command_helper).run_command("if sudo [ -f /var/lib/lxc/123/tags ]; then sudo cat /var/lib/lxc/123/tags; else echo '{}'; fi").thenReturn(tags1)
        when(mock_command_helper).run_command("if sudo [ -f /var/lib/lxc/124/tags ]; then sudo cat /var/lib/lxc/124/tags; else echo '{}'; fi").thenReturn(tags2)
        when(mock_command_helper).run_command("sudo lxc-info -n 123").thenReturn("state: RUNNING")
        when(mock_command_helper).run_command("sudo lxc-info -n 124").thenReturn("state: RUNNING")

        provider = LXCNodeProvider(all_credentials, 'test_host', mock_command_helper)
        environment = provider.get_running_environment("test", "Single-AZ Deployment", all_credentials)

        self.assertIsNotNone(environment)
        self.assertEquals(1, len(environment.get_locations()))
        self.assertIsNotNone(environment.get_locations()[0].get_nodes())
        self.assertEquals('test_host', environment.get_locations()[0].get_name())

        node1 = environment.get_locations()[0].get_nodes()[0]
        self.assertIsNotNone(node1.get_services())
        self.assertEquals({'apache' : {80 : 80}}, node1.get_services())

        node2 = environment.get_locations()[0].get_nodes()[1]
        self.assertIsNotNone(node2.get_services())
        self.assertEquals({'mongo' : {81 : 82}}, node2.get_services())

    def test_should_not_throw_exception_when_node_is_up_and_running(self):
        mock_command_helper = mock()
        mock_string_attr = mock()
        mock_string_attr.succeeded=True
        lxc_node = LXCNode("123", mock_command_helper, "test_host_name")

        when(mock_command_helper).run_command_silently("ping -c1 123").thenReturn(mock_string_attr)

        lxc_node.wait_for_ready(lambda : None, 15)

    def test_should_throw_exception_when_node_is_not_up_and_running(self):
        mock_command_helper = mock()
        mock_string_attr = mock()
        mock_string_attr.succeeded=False
        lxc_node = LXCNode("123", mock_command_helper, "test_host_name")

        when(mock_command_helper).run_command_silently("ping -c1 123").thenReturn(mock_string_attr)
        with self.assertRaisesRegexp(Exception, "Node 123 is not running"):
            lxc_node.wait_for_ready(lambda : None, 5)