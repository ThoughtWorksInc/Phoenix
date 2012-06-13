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
from phoenix.configurators.puppet_service_configurator import PuppetServiceConfigurator
import yaml

class PuppetServiceConfiguratorTests(unittest.TestCase):

    def test_will_parse_puppet_service_configuration(self):
        single_service_yaml = """
            apache:
                puppet_module_directory : puppet
                puppet_manifest : apache.pp
            """

        puppetServiceConfigurator = PuppetServiceConfigurator()
        error_list = []
        valid = puppetServiceConfigurator.validate('apache', yaml.load(single_service_yaml)['apache'], os.path.abspath('samples'), error_list)
        self.assertTrue(valid)
        self.assertEqual(len(error_list), 0)

    def test_will_throw_exception_if_value_for_puppet_module_directory_is_not_fount(self):
        single_service_yaml = """
            apache:
                puppet_manifest : apache.pp
            """

        puppetServiceConfigurator = PuppetServiceConfigurator()
        error_list = []
        valid = puppetServiceConfigurator.validate('apache', yaml.load(single_service_yaml)['apache'], os.path.abspath('samples'), error_list)
        self.assertFalse(valid)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'puppet_module_directory' is not defined in services configuration of service: 'apache'", error_list[0])

    def test_will_throw_exception_if_value_for_puppet_manifest_is_not_fount(self):
        single_service_yaml = """
            apache:
                puppet_module_directory : puppet
            """

        puppetServiceConfigurator = PuppetServiceConfigurator()
        error_list = []
        valid = puppetServiceConfigurator.validate('apache', yaml.load(single_service_yaml)['apache'], os.path.abspath('samples'), error_list)
        self.assertFalse(valid)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Key 'puppet_manifest' is not defined in services configuration of service: 'apache'", error_list[0])

    def test_will_only_validate_yaml_if_config_path_found(self):
        single_service_yaml = """
            apache:
                aa : aa
            """

        puppetServiceConfigurator = PuppetServiceConfigurator()
        error_list = []
        wrong_path = os.path.abspath('wrong path')
        valid = puppetServiceConfigurator.validate('apache', yaml.load(single_service_yaml)['apache'], wrong_path, error_list)
        self.assertFalse(valid)
        self.assertEqual(len(error_list), 1)
        self.assertEqual("Config path '"+wrong_path+"' not found", error_list[0])

    def test_will_throw_exception_if_value_for_puppet_module_directory_is_not_fount(self):
        single_service_yaml = """
            apache1:
                puppet_module_directory : puppet
            apache2:
                puppet_manifest : apache.pp
            """

        puppetServiceConfigurator = PuppetServiceConfigurator()
        error_list = []
        valid = puppetServiceConfigurator.validate('apache1', yaml.load(single_service_yaml)['apache1'], os.path.abspath('samples'), error_list)
        self.assertFalse(valid)
        valid = puppetServiceConfigurator.validate('apache2', yaml.load(single_service_yaml)['apache2'], os.path.abspath('samples'), error_list)
        self.assertFalse(valid)

        self.assertEqual(len(error_list), 2)
        self.assertEqual("Key 'puppet_manifest' is not defined in services configuration of service: 'apache1'", error_list[0])
        self.assertEqual("Key 'puppet_module_directory' is not defined in services configuration of service: 'apache2'", error_list[1])
