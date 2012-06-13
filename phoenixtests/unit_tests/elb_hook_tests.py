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
from phoenix.service_definition import service_definitions_from_yaml, DynamicDictionary
import unittest
from phoenix.environment_definition import environment_definitions_from_yaml
from phoenix import fabfile, service_definition
from phoenix.configurators.fake_service_configurator import FakeServiceConfigurator
from phoenixtests.unit_tests.node_definition_tests import services_yaml

class ELBHookTests(unittest.TestCase):

    all_credentials = {
        'test' : fabfile.Credentials('test', {'private_key' : 'unit-us-east-test.pem', 'login' : 'ubuntu'}, "/some/path")
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
    """
    service_definitions = service_definitions_from_yaml(services_yaml, "samples/")

    def test_should_return_correct_port_mappings(self):
        env_yaml_str = """
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
        env_definitions = environment_definitions_from_yaml(env_yaml_str,
            self.service_definitions, 'prod', self.all_credentials)
        elb_connectivity_mappings = env_definitions['prod'].service_lifecycle_hooks['hello_world'][0].get_elb_mappings(self.service_definitions['hello_world'].definitions['connectivity'])
        self.assertEqual(2, len(elb_connectivity_mappings))
        self.assertTrue((80, 8080, 'tcp') in elb_connectivity_mappings)
        self.assertTrue((81, 8081, 'tcp') in elb_connectivity_mappings)
