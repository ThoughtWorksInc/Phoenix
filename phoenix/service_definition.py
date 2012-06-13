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

import yaml
from fabric.operations import local

import phoenix.configurators as configurators
from phoenix.utilities.utility import get_class_from_fully_qualified_string

def _validate_service_definitions(definition_data, abs_path_to_config):
    error_list = []
    for service_name, definitions in definition_data.items():
        if not 'service_configurator' in definitions:
            raise Exception(
                "Key 'service_configurator' is not found in services configuration of service: '%s'" % (service_name))

        configurator_name = definitions['service_configurator']
        try:
            service_configurator = get_class_from_fully_qualified_string(configurator_name)()
        except StandardError as e:
            error_list.append("Invalid Service Configurator: '%s' in services configuration of service: '%s'. Underlying error %s" % (
            configurator_name, service_name, e))
            continue

        service_configurator.validate(service_name, definitions, abs_path_to_config, error_list)

    if not len(error_list):
        return

    not_first_errors = False
    error_string = ""
    for error in error_list:
        if not_first_errors:
            error_string += ",\n"
        not_first_errors = True
        error_string = error_string + error

    raise Exception(error_string)


def service_definitions_from_yaml(yaml_string, abs_path_to_config):
    definition_data = yaml.load(yaml_string)

    _validate_service_definitions(definition_data, abs_path_to_config)

    definition_map = {}
    for service_name, definitions in definition_data.items():
        configurator_name = definitions['service_configurator']
        service_configurator = get_class_from_fully_qualified_string(configurator_name)()
        definition_map[service_name] = ServiceDefinition(service_name, definitions, service_configurator, abs_path_to_config)

    return definition_map

class ServiceDefinition:
    def __init__(self, name, definitions, service_configurator, abs_config_path):
        """
        name: name of the service to install
        definitions: settings for the given service
        service_configurator: what to use to set up this service
        abs_config_path: where to find the configuration in an absolute sense
        """
        self.name = name
        self.definitions = definitions
        self.service_configurator = service_configurator
        self.abs_config_path = abs_config_path

    def __repr__(self):
        return self.name.__repr__()

    def __getattr__(self, attribute_name):
        obj = self.definitions[attribute_name]
        if isinstance(obj, dict):
            return DynamicDictionary(obj)
        elif isinstance(obj, list):
            if isinstance(obj[0], dict):
                return map(lambda x:DynamicDictionary(x), obj)

        return obj

    def get_abs_config_path(self):
        return self.abs_config_path

    def apply_on(self, node, service_to_dns):
        self.service_configurator.config(node, self, service_to_dns)

    def bundle(self, attribute, bundle_name):
        local("cd %s && tar cfz /tmp/%s %s" % (self.abs_config_path, bundle_name, self.definitions[attribute]))
        return os.path.join("/tmp/%s" % bundle_name)

class DynamicDictionary(object):
    def __init__(self, dict): self.dict = dict
    def __getattr__(self, attribute_name):
        obj = self.dict[attribute_name]
        return obj if not isinstance(obj, dict) else DynamicDictionary(obj)
    def __str__(self):
        return str(self.dict)
