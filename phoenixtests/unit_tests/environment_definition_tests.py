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
import shutil
import unittest
from itertools import chain
from mockito.mocking import mock
from mockito.mockito import when, verify
from phoenix.providers.address import Address
import yaml
from phoenix import service_definition, fabfile, node_config
from phoenix.environment_definition import environment_definitions_from_yaml, EnvironmentDefinition
from phoenix.configurators.fake_service_configurator import FakeServiceConfigurator
from phoenix.providers import FileBackedNodeProvider
from phoenix.service_definition import DynamicDictionary
from phoenix.hooks.elb_hook import ELBHook

service_definitions = {
    'apache': service_definition.ServiceDefinition('apache', {'name': 'apache', 'connectivity': [ DynamicDictionary( {'ports' : [ 80 ]} ) ] }, FakeServiceConfigurator(), None),
    'my_app': service_definition.ServiceDefinition('my_app', {'name': 'my_app', 'connectivity': [ DynamicDictionary( {'ports' : [ 8080, 8081 ]}  )] }, FakeServiceConfigurator(), None),
    'hello_world': service_definition.ServiceDefinition('hello_world', {'name': 'hello_world', 'connectivity': [ DynamicDictionary( {'ports' : [ 8080, 8081 ]}  )] }, FakeServiceConfigurator(), None)}

all_credentials = {
    'test' : fabfile.Credentials('test', {'private_key' : 'unit-us-east-test.pem', 'login' : 'ubuntu'}, "/some/path")
}

class SimpleNodeDefinition:
    def __init__(self, services=None):
        if not services: services = []
        self.role = "WhyDoWeNeedThis?"
        self.services = services

class EnvironmentDefinitionTests(unittest.TestCase):

    def setUp(self):
        self.tearDown()

    def nodes(self):
        return self.fake_env()['nodes'].values()

    def fake_env(self):
        f = open('./fake_nodes/fake_env.yml', 'r')
        fake_env = yaml.load(f)
        return fake_env

    def tearDown(self):
        path = './fake_nodes'
        if os.path.exists(path):
            shutil.rmtree(path)

    def test_can_load_environment_from_yaml(self):
        single_service_yaml = """
          dev:
            nodes:
              - role: test
                type: phoenix.providers.file_node_provider.FileBackedNodeDefinition
                services: [apache]
            node_provider:
              class_name : FileBackedNodeProvider
        """

        environment_definitions = environment_definitions_from_yaml(
            single_service_yaml, service_definitions, 'dev', all_credentials)
        environment_definitions['dev'].launch()

        assert os.path.exists('./fake_nodes/fake_env.yml')

    def test_can_list_running_nodes_for_specified_env(self):
        provider = FileBackedNodeProvider()
        provider.start(None, 'dev', 'some_def')
        node_to_terminate = provider.start(None, 'dev', 'some_def')
        provider.shutdown(node_to_terminate.id())
        provider.start(None, 'prod', 'some_def')

        dev_env = EnvironmentDefinition('dev', provider, service_definitions,
            None, all_credentials, 'some_def')

        nodes = dev_env.list_nodes()

        self.assertEqual(nodes.__len__(), 1)


    def test_can_launch_full_environment(self):
        environment_definition = self.EnvironmentBuilder().with_nodes(
            SimpleNodeDefinition(services=['apache']),
            SimpleNodeDefinition(services=['apache'])).build()

        environment_definition.launch()

        f = open('./fake_nodes/fake_env.yml', 'r')
        fake_env = yaml.load(f)
        self.assertEquals(fake_env['nodes'].values().__len__(), 2)

    def test_can_pass_settings_to_each_node(self):
        self.environment_definition = EnvironmentDefinition('dev',
            FileBackedNodeProvider(node_ids=[1, 2]), service_definitions, [SimpleNodeDefinition(services=['my_app']), SimpleNodeDefinition(services=['apache'])], all_credentials, 'some_def')

        self.environment_definition.launch()

        f = open('./fake_nodes/fake_env.yml', 'r')
        fake_env = yaml.load(f)['nodes']
        self.assertEquals(len(fake_env.values()), 2)
        self.assertIn('apache', fake_env.values()[0]['services'])
        self.assertIn('my_app', fake_env.values()[1]['services'])
        environment_settings = {"apache": [1], "my_app": [2], "apache_port": ['80'], "my_app_port" : ['8080,8081']}
        self.assertEquals(fake_env[1]["settings"].keys(), ["apache", "my_app", "apache_port", "my_app_port"])
        self.assertEquals(fake_env[1]["settings"], environment_settings)
        self.assertEquals(fake_env[2]["settings"], environment_settings)

    def test_can_skip_launching_node_if_node_already_has_service_running(self):
        environment_definition = self.EnvironmentBuilder().with_nodes(
            SimpleNodeDefinition(services=["apache"]),
            SimpleNodeDefinition(services=["my_app"])).build()

        environment_definition.launch()
        environment_definition.launch()

        f = open('./fake_nodes/fake_env.yml', 'r')
        fake_env = yaml.load(f)['nodes']
        nodes = fake_env.values()
        self.assertEqual(len(nodes), 2)

        launched_services = list(chain.from_iterable([n['services'] for n in nodes]))

        self.assertEqual(len(launched_services), 2)
        self.assertIn('my_app', launched_services)
        self.assertIn('apache', launched_services)

    def test_can_launch_new_node_if_not_enough_nodes(self):
        environment_definition = self.EnvironmentBuilder().with_nodes(
            SimpleNodeDefinition(services=["apache"])).build()

        environment_definition.launch()

        environment_definition = self.EnvironmentBuilder().with_nodes(
            SimpleNodeDefinition(services=["apache"]),
            SimpleNodeDefinition(services=["apache"])).build()

        environment_definition.launch()

        self.assertEqual(len(self.running_nodes()), 2)

    def running_nodes(self):
        return filter(lambda node: node["state"] == "running", self.nodes())

    def terminated_nodes(self):
        return filter(lambda node: node["state"] == "terminated", self.nodes())

    def test_can_delete_node_if_not_required(self):
        environment_definition = self.EnvironmentBuilder().with_nodes(
            SimpleNodeDefinition(services=['apache']),
            SimpleNodeDefinition(services=['apache'])
        ).build()

        environment_definition.launch()

        self.assertEqual(len(self.terminated_nodes()), 0)

        environment_definition = self.EnvironmentBuilder().with_nodes(
            SimpleNodeDefinition(services=['apache'])
        ).build()

        environment_definition.launch()

        self.assertEqual(len(self.terminated_nodes()), 1)

    def test_should_add_credentials_details_for_aws_node_definitions(self):
        single_service_yaml = """
            dev:
              nodes:
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  aws_key_name: test
                  services: [mongo, hello_world]
                  type: phoenix.providers.aws_provider.AWSNodeDefinition

              node_provider:
                class_name: AWSNodeProvider
                public_api_key: AKIAIGBFGAGVPGKLVX4Q
                private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
        """
        node_def_map = yaml.load(single_service_yaml)
        node_def = node_config.node_definition_from_map(node_def_map['dev']['nodes'][0], all_credentials)
        self.assertEqual('ubuntu', node_def.admin_user)
        self.assertEqual('/some/path/unit-us-east-test.pem', node_def.path_to_private_key)

    def test_should_not_add_credentials_details_for_lxc_node_definitions(self):
        single_service_yaml = """
            lxc_hello_world:
              nodes:
                - template: ubuntu
                  services: [hello_world]
                  type: phoenix.providers.lxc_provider.LXCNodeDefinition

              node_provider:
                class_name: LXCNodeProvider
                host_name: ec2-184-72-150-211.compute-1.amazonaws.com
                credentials: us-east-ssh
                start_up_timeout: 60
        """
        node_def_map = yaml.load(single_service_yaml)
        node_def = node_config.node_definition_from_map(node_def_map['lxc_hello_world']['nodes'][0], all_credentials)
        self.assertFalse(hasattr(node_def, 'admin_user'))
        self.assertFalse(hasattr(node_def, 'path_to_private_key'))


        # TODO: Get this test working. Should implement listeners for logging (terminate, start) etc to
    # make this work?
#    def test_will_only_remove_nodes_from_environmnet_being_changed(self):
#        first_environment = self.EnvironmentBuilder().with_nodes(
#            SimpleNodeDefinition(services=['apache'])
#        ).with_name("first").build()
#
#        second_environment = self.EnvironmentBuilder().with_nodes(
#            SimpleNodeDefinition(services=['apache'])
#        ).with_name("second").build()
#
#        first_environment.launch()
#        second_environment.launch()

    def test_blow_away_and_start_new_node_if_service_is_removed(self):
        environment_definition = self.EnvironmentBuilder().with_nodes(
            SimpleNodeDefinition(services=['apache', 'my_app'])
        ).build()

        environment_definition.launch()

        environment_definition = self.EnvironmentBuilder().with_nodes(
            SimpleNodeDefinition(services=['apache'])
        ).build()

        environment_definition.launch()

        self.assertEqual(len(self.running_nodes()), 1)
        self.assertEqual(len(self.terminated_nodes()), 1)

    class EnvironmentBuilder():
        def __init__(self):
            self.environment_name = 'dev'
            self.environment_def_name = 'some_def'
            self.node_provider = FileBackedNodeProvider()
            self.service_definitons = service_definitions
            self.node_definitions = []
            self.credentials = all_credentials

        def with_nodes(self, *node):
            self.node_definitions.extend(node)
            return self

        def with_name(self, name):
            self.environment_name = name
            return self

        def build(self):
            return EnvironmentDefinition(self.environment_name, self.node_provider, self.service_definitons, self.node_definitions, self.credentials, self.environment_def_name)

    def test_will_throw_exception_if_nodes_key_not_defined_for_environment(self):
        single_service_yaml = """
            dev:
              invalid_nodes:
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  aws_key_name: test
                  services: [mongo, hello_world]
                  type: phoenix.providers.aws_provider.AWSNodeDefinition

              node_provider:
                class_name: AWSNodeProvider
                public_api_key: AKIAIGBFGAGVPGKLVX4Q
                private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
        """
        with self.assertRaisesRegexp(Exception, "Key 'nodes' not found for environment 'dev'"):
                    environment_definitions_from_yaml(single_service_yaml, service_definitions, 'dev', all_credentials)

    def test_will_throw_exception_if_node_provider_key_not_defined_for_environment(self):
        single_service_yaml = """
          dev:
              nodes:
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  aws_key_name: test
                  services: [mongo, hello_world]
                  type: phoenix.providers.aws_provider.AWSNodeDefinition

              invalid_node_provider:
                class_name: AWSNodeProvider
                public_api_key: AKIAIGBFGAGVPGKLVX4Q
                private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
        """
        with self.assertRaisesRegexp(Exception, "Key 'node_provider' not found for environment 'dev'"):
            environment_definitions_from_yaml(single_service_yaml, service_definitions, 'dev', all_credentials)

    def test_will_throw_exception_if_node_provider_key_class_not_valid_for_environment(self):
        single_service_yaml = """
          dev:
              nodes:
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  aws_key_name: test
                  services: [mongo, hello_world]
                  type: phoenix.providers.aws_provider.AWSNodeDefinition

              node_provider:
                class_name: InvalidAWSNodeProvider
        """
        with self.assertRaisesRegexp(Exception, "Key 'node_provider' class_name 'InvalidAWSNodeProvider' is invalid for environment 'dev'"):
            environment_definitions_from_yaml(single_service_yaml, service_definitions, 'dev', all_credentials)


    def test_will_find_errors_in_all_environment(self):
        single_service_yaml = """
          dev1:
              nodes:
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  aws_key_name: test
                  services: [apache, my_app]
                  type: phoenix.providers.aws_provider.AWSNodeDefinition

              invalid_node_provider:
                class_name: InvalidAWSNodeProvider
          dev2:
              invalid_nodes:
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  services: [apache, my_app]
                  type: phoenix.providers.aws_provider.AWSNodeDefinition

              node_provider:
                class_name: FileBackedNodeProvider
        """
        with self.assertRaisesRegexp(Exception, "Key 'nodes' not found for environment 'dev2',\nKey 'node_provider' not found for environment 'dev1'"):
            environment_definitions_from_yaml(single_service_yaml, service_definitions, 'test', all_credentials)

    def test_will_throw_exception_if_AWS_node_provider_is_not_setup_correctly(self):
        single_service_yaml = """
          dev:
            nodes:
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  aws_key_name: test
                  services: [apache, my_app]
                  type: phoenix.providers.aws_provider.AWSNodeDefinition
            node_provider:
                class_name: AWSNodeProvider
                public_api_key: AKIAIGBFGAGVPGKLVX4Q
                private_api_key_WRONG: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
        """
        with self.assertRaisesRegexp(Exception, "Key 'private_api_key' not found for AWS in 'dev' environment"):
            environment_definitions_from_yaml(single_service_yaml, service_definitions, 'test', all_credentials)


    def test_should_add_service_lifecycle_hook_from_definition(self):
        yaml_string = """
        prod:
          service_hooks:
              hello_world:
                - class_name: phoenix.hooks.elb_hook.ELBHook
                  elb_name: hello_world_us_east_1_elb
                  public_api_key: AKIAIGBFGAGVPGKLVX4Q
                  private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
                  app_to_elb_ports: { 8080 : 80, 8081 : 81 }
                  app_healthcheck_target: 'HTTP:8081/healthcheck'
          nodes:
          - ami_id: ami-4dad7424
            size:   t1.micro
            credentials_name: test
            aws_key_name : test
            services: [hello_world]
            security_groups: [ spicy-beef ]
            availability_zone: us-east-1a
            type: phoenix.providers.aws_provider.AWSNodeDefinition

          node_provider:
            class_name: AWSNodeProvider
            public_api_key: 123
            private_api_key: 1234
        """

        env_definitions = environment_definitions_from_yaml(yaml_string,
            service_definitions, 'prod', all_credentials)

        self.assertEqual(1, len(env_definitions['prod'].service_lifecycle_hooks))
        self.assertTrue(isinstance(env_definitions['prod'].service_lifecycle_hooks['hello_world'][0], ELBHook))
