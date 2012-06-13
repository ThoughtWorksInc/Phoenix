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
import tempfile
import os.path
import tarfile
from mockito.inorder import verify
from mockito.mocking import mock
from mockito.mockito import when
from phoenix.service_definition import service_definitions_from_yaml
from phoenix.providers.address import Address

class ServiceDefinitionTests(unittest.TestCase):
    def test_can_load_single_service_definition(self):
        single_service_yaml = """
            apache:
                puppet_module_directory : puppet
                puppet_manifest : apache.pp
                service_configurator: phoenix.configurators.puppet_service_configurator.PuppetServiceConfigurator
                connectivity:
                    - protocol: tcp
                      ports: [ 80 ]
                      allowed: [ WORLD ]
        """

        service_definitions = service_definitions_from_yaml(single_service_yaml,
            os.path.abspath('samples'))
        self.assertEquals(service_definitions['apache'].name, 'apache')
        self.assertEquals(service_definitions['apache'].puppet_module_directory, 'puppet')
        self.assertEquals(service_definitions['apache'].puppet_manifest, 'apache.pp')

    def test_can_load_multiple_service_definitions(self):
        multiple_service_yaml = """
          apache:
                puppet_module_directory : puppet
                puppet_manifest : apache.pp
                service_configurator: phoenix.configurators.puppet_service_configurator.PuppetServiceConfigurator
          mongo:
                puppet_module_directory : puppet
                puppet_manifest : mongo.pp
                service_configurator: phoenix.configurators.puppet_service_configurator.PuppetServiceConfigurator
        """

        service_definitions = service_definitions_from_yaml(multiple_service_yaml,
            os.path.abspath('samples'))
        self.assertEquals(service_definitions['apache'].name, 'apache')
        self.assertEquals(service_definitions['apache'].puppet_manifest, 'apache.pp')
        self.assertEquals(service_definitions['mongo'].name, 'mongo')
        self.assertEquals(service_definitions['mongo'].puppet_manifest, 'mongo.pp')

    def test_can_bundle_directory(self):
        abs_temp_dir = tempfile.mkdtemp()
        temp_rel_dir = tempfile.mkdtemp(dir=abs_temp_dir)
        fakefile = tempfile.mkstemp(dir=temp_rel_dir)

        yaml = """
            apache:
                port : 80
                puppet_module_dir : %s
                service_configurator: phoenix.configurators.fake_service_configurator.FakeServiceConfigurator
                """ % os.path.relpath(temp_rel_dir, abs_temp_dir)

        service_definitions = service_definitions_from_yaml(yaml, abs_temp_dir)
        path_to_bundle = service_definitions['apache'].bundle('puppet_module_dir', 'testbundle.tgz')

        tar = tarfile.open(path_to_bundle)
        # Inside the tarball, the file path will be relative to the fake relative directory we created
        expected_rel_path_to_file = os.path.relpath(fakefile[1], abs_temp_dir)

        self.assertTrue(expected_rel_path_to_file in [entry.path for entry in tar.getmembers()])

    def test_will_throw_exception_if_service_definition_dont_have_a_service_configurator_key(self):
        single_service_yaml = """
            apache:
                miss_spelled_service_configurator: phoenix.configurators.fake_service_configurator.FakeServiceConfigurator
            """

        with self.assertRaisesRegexp(Exception,
            "Key 'service_configurator' is not found in services configuration of service: 'apache'"):
            service_definitions_from_yaml(single_service_yaml, None)


    def test_will_throw_exception_if_service_configurator_key_dont_name_a_existing_service_configurator(self):
        single_service_yaml = """
            apache:
                service_configurator: NonExistingServiceConfigurator
            """

        with self.assertRaisesRegexp(Exception,
            "Invalid Service Configurator: 'NonExistingServiceConfigurator' in services configuration of service: 'apache'"):
            service_definitions_from_yaml(single_service_yaml, None)


    def test_will_throw_exception_if_service_definition_dont_have_a_puppet_manifest_key(self):
        single_service_yaml = """
            apache:
                puppet_module_directory : puppet
                service_configurator: phoenix.configurators.puppet_service_configurator.PuppetServiceConfigurator
            """

        with self.assertRaisesRegexp(Exception,
            "Key 'puppet_manifest' is not defined in services configuration of service: 'apache'"):
            service_definitions_from_yaml(single_service_yaml, os.path.abspath('samples'))

    def test_finds_all_problems_when_loading_multiple_service_definitions(self):
        multiple_service_yaml = """
          apache:
                puppet_manifest : apache.pp
                service_configurator: phoenix.configurators.puppet_service_configurator.PuppetServiceConfigurator
          mongo:
                puppet_module_directory : puppet
                service_configurator: phoenix.configurators.puppet_service_configurator.PuppetServiceConfigurator
        """

        with self.assertRaisesRegexp(Exception,
            "Key 'puppet_module_directory' is not defined in services configuration of service: 'apache',\nKey 'puppet_manifest' is not defined in services configuration of service: 'mongo'"):
            service_definitions_from_yaml(multiple_service_yaml, os.path.abspath('samples'))
