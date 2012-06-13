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

from unittest import TestCase
from phoenix import fabfile
import phoenix
from phoenix.environment_definition import environment_definitions_from_yaml
from phoenix.service_definition import service_definitions_from_yaml

all_credentials = {
    'test' : fabfile.Credentials('test', {'private_key' : 'unit-test.pem'}, "/some/path")
}

services_yaml = """
hello_world:
  puppet_module_directory : puppet
  puppet_manifest : hello_world.pp
  service_configurator: phoenix.configurators.puppet_service_configurator.PuppetServiceConfigurator
  connectivity:
    - protocol: tcp
      ports: [ 8080, 8081 ]
      allowed: [ WORLD ]
mongo:
  puppet_module_directory : puppet
  puppet_manifest : mongo.pp
  service_configurator: phoenix.configurators.puppet_service_configurator.PuppetServiceConfigurator
  connectivity:
    - protocol: tcp
      ports: [ 27017 ]
      allowed: [ hello_world ]
"""

service_definitions = service_definitions_from_yaml(services_yaml, "samples/")

class TestNodeDefinitions(TestCase):
    def test_will_throw_exception_if_node_type_is_not_set(self):
        env_yaml = """
          dev:
            nodes:
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  services: [mongo, hello_world]
                  aws_key_name : test
                  invalid_type: phoenix.providers.aws_provider.AWSNodeDefinition
            node_provider:
                class_name: AWSNodeProvider
                public_api_key: AKIAIGBFGAGVPGKLVX4Q
                private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
        """
        with self.assertRaisesRegexp(Exception, "^Node type is missing for node number 1 in 'dev' environment$"):
            environment_definitions_from_yaml(env_yaml, service_definitions, 'test', all_credentials)

    def test_will_throw_exception_if_node_type_is_not_valid(self):
        env_yaml = """
          dev:
            nodes:
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  services: [mongo, hello_world]
                  type: phoenix.providers.aws_provider.InvalidAWSNodeDefinition
            node_provider:
                class_name: AWSNodeProvider
                public_api_key: AKIAIGBFGAGVPGKLVX4Q
                private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
        """
        with self.assertRaisesRegexp(Exception, "^Node type 'phoenix.providers.aws_provider.InvalidAWSNodeDefinition' is invalid for node number 1 in 'dev' environment$"):
            environment_definitions_from_yaml(env_yaml, service_definitions, 'dev', all_credentials)

    def test_will_throw_exception_if_node_type_is_not_valid_for_multiple_nodes(self):
        env_yaml = """
          dev:
            nodes:
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  services: [mongo, hello_world]
                  type: phoenix.providers.aws_provider.InvalidAWSNodeDefinition
                - ami_id: ami-4dad7424
                  size:   t1.micro
                  credentials_name: test
                  services: [mongo, hello_world]
                  type: phoenix.providers.aws_provider.InvalidAWSNodeDefinition
            node_provider:
                class_name: AWSNodeProvider
                public_api_key: AKIAIGBFGAGVPGKLVX4Q
                private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
        """
        with self.assertRaisesRegexp(Exception, """^Node type 'phoenix.providers.aws_provider.InvalidAWSNodeDefinition' is invalid for node number 1 in 'dev' environment,\nNode type 'phoenix.providers.aws_provider.InvalidAWSNodeDefinition' is invalid for node number 2 in 'dev' environment$"""):
            environment_definitions_from_yaml(env_yaml, service_definitions, 'test', all_credentials)

    def test_will_throw_exception_if_services_is_not_set_for_a_node(self):
        env_yaml = """
              dev:
                nodes:
                    - ami_id: ami-4dad7424
                      size:   t1.micro
                      credentials_name: test
                      invalid_services: [mongo, hello_world]
                      aws_key_name : test
                      type: phoenix.providers.aws_provider.AWSNodeDefinition
                node_provider:
                    class_name: AWSNodeProvider
                    public_api_key: AKIAIGBFGAGVPGKLVX4Q
                    private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
            """
        with self.assertRaisesRegexp(Exception, "^Key 'services' is not set for node number 1 in 'dev' environment$"):
            environment_definitions_from_yaml(env_yaml, service_definitions, 'dev', all_credentials)

    def test_will_throw_exception_if_service_is_missing_definitions(self):
        env_yaml = """
              dev:
                nodes:
                    - ami_id: ami-4dad7424
                      size:   t1.micro
                      credentials_name: test
                      services: [mongo, hello_world, test_service]
                      aws_key_name : test
                      type: phoenix.providers.aws_provider.AWSNodeDefinition
                node_provider:
                    class_name: AWSNodeProvider
                    public_api_key: AKIAIGBFGAGVPGKLVX4Q
                    private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
            """
        with self.assertRaisesRegexp(Exception, "^Service definitions is missing for 'test_service' in node number 1 for 'dev' environment$"):
            environment_definitions_from_yaml(env_yaml, service_definitions, 'dev', all_credentials)

    def test_will_throw_exception_if_AWS_node_fails_validation(self):
        aws_node_yaml = """
              dev:
                nodes:
                    - ami_id: ami-4dad7424
                      invalid_size:   t1.micro
                      credentials_name: test
                      aws_key_name : test
                      services: [mongo, hello_world]
                      type: phoenix.providers.aws_provider.AWSNodeDefinition
                node_provider:
                    class_name: AWSNodeProvider
                    public_api_key: AKIAIGBFGAGVPGKLVX4Q
                    private_api_key: NAOcwcX3an5hcyLCz3Y4xucwr4Fqxs9ijLn6biqk
            """
        with self.assertRaisesRegexp(Exception, "^Key 'size' not set for AWS node definition number 1 in 'dev' environment$"):
            environment_definitions_from_yaml(aws_node_yaml, service_definitions, 'dev', all_credentials)

    def test_will_throw_exception_if_LXC_node_fails_validation(self):
        single_service_yaml = """
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
        with self.assertRaisesRegexp(Exception, "^Key 'template' not set for LXC node definition number 1 in 'test' environment$"):
            environment_definitions_from_yaml(single_service_yaml, service_definitions, 'test', all_credentials)
            

