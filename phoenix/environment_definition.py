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

from collections import defaultdict

import yaml
from phoenix.plogging import logger
from phoenix.node_config import node_definition_from_map
from phoenix.providers import node_predicates
from phoenix.providers.noop_provider import NoopNodeProvider
from phoenix.utilities.utility import get_class_from_fully_qualified_string
import providers as providers

def _provider(env_values, all_credentials):
    provider_definition = env_values['node_provider']

    class_name = getattr(providers, provider_definition['class_name'])
    provider_definition.pop(
        'class_name') # pop this off the config - we don't need this as a constructor arg for our providers

    # Convert a named set of Credentials to the actual object
    if provider_definition.has_key('credentials'):
        credentials_name = provider_definition['credentials']
        provider_definition['credentials'] = all_credentials[credentials_name]

    return class_name(**provider_definition)


def list_environments(yaml_string):
    definition_data = yaml.load(yaml_string)
    return definition_data.keys()


def _validate_node_definition(env_name, error_list, node_definition, node_number, all_credentials, service_definitions):
    if not 'services' in node_definition:
        error_list.append("Key 'services' is not set for node number %s in '%s' environment" % (node_number, env_name))
    else :
        for service_name in node_definition['services']:
            if not service_name in service_definitions.keys():
                error_list.append("Service definitions is missing for '%s' in node number %s for '%s' environment" % (service_name, node_number, env_name))

    if not 'type' in node_definition:
        error_list.append("Node type is missing for node number %s in '%s' environment" % (node_number, env_name))
    else:
        node_type_class = node_definition['type']

        try:
            node_definition_object = get_class_from_fully_qualified_string(node_type_class)()
            node_definition_object.validate(error_list, node_number, env_name, node_definition, all_credentials)
        except StandardError:
            error_list.append("Node type '%s' is invalid for node number %s in '%s' environment" % (
                node_type_class, node_number, env_name))


def _validate_environment_definitions(definition_data, error_list, all_credentials, service_definitions):
    for env_name, env_values in definition_data.items():
        if not 'nodes' in env_values:
            error_list.append("Key 'nodes' not found for environment '%s'" % env_name)
        else:
            node_number = 0
            for node_definition in env_values['nodes']:
                node_number = node_number + 1
                _validate_node_definition(env_name, error_list, node_definition, node_number, all_credentials, service_definitions)

        if not 'node_provider' in env_values:
            error_list.append("Key 'node_provider' not found for environment '%s'" % env_name)
            continue

        class_name = env_values['node_provider']['class_name']
        try:
            provider = getattr(providers, class_name)()
        except AttributeError:
            error_list.append(
                "Key 'node_provider' class_name '%s' is invalid for environment '%s'" % (class_name, env_name))
            continue

        provider.validate(env_name, env_values['node_provider'], error_list, all_credentials)

    if not len(error_list):
        return

    not_first_errors = False
    error_string = ""
    for error in error_list:
        if not_first_errors:
            error_string = error_string + ",\n"
        not_first_errors = True
        error_string = error_string + error

    raise Exception(error_string)

def environment_definitions_from_yaml(yaml_string, service_definitions=None, env_name=None, all_credentials=None, noop=False):
    definition_data = yaml.load(yaml_string)
    definition_map = {}

    error_list = []
    _validate_environment_definitions(definition_data, error_list, all_credentials, service_definitions)

    for env_template, env_values in definition_data.items():
        node_defs = []

        for node_def_as_map in env_values['nodes']:
            node_defs.append(node_definition_from_map(node_def_as_map, all_credentials))

        node_provider = _provider(env_values, all_credentials)
        if noop:
            node_provider = NoopNodeProvider(node_provider)

        service_hooks = get_service_lifecycle_hooks(env_values)
        definition_map[env_template] = EnvironmentDefinition(
            env_name, node_provider,
            service_definitions, node_defs, all_credentials, env_template, service_hooks)
    return definition_map

def get_service_lifecycle_hooks(env_values):
    service_lifecycle_hooks = {}
    if 'service_hooks' in env_values.keys():
        for service_name, hook_definitions in env_values['service_hooks'].items():
            hooks = []
            for hook_definition in hook_definitions :
                class_name = get_class_from_fully_qualified_string(hook_definition['class_name'])
                hook_definition.pop('class_name')
                hooks.append(class_name(**hook_definition))
            service_lifecycle_hooks.update({service_name: hooks})
    return service_lifecycle_hooks

class EnvironmentDefinition:
    def __init__(self, name, node_provider, service_definitions, node_definitions, all_credentials, env_def_name, service_lifecycle_hooks = {}):
        self.name = name
        self.node_provider = node_provider
        self.service_definitions = service_definitions
        self.all_credentials = all_credentials
        self.node_definitions = node_definitions
        self.env_def_name = env_def_name
        self.service_lifecycle_hooks = service_lifecycle_hooks

    def __repr__(self):
        return self.name.__repr__()

    def get_node_provider(self):
        return self.node_provider

    def _block_until_all_nodes_are_ready(self, provisioned_nodes):
        for node in provisioned_nodes:
            node.wait_for_ready(lambda: None, self.node_provider.get_node_startup_timeout())

    def build_environment_settings(self, service_to_nodes):
        env_settings = defaultdict(lambda: [])

        for service_name, running_nodes in service_to_nodes.items():
            for running_node in running_nodes:
                env_settings[service_name].append(running_node.address().dns_name)
                env_settings[service_name + '_port'].append(",".join(running_node.address().get_ports(service_name)))
        return dict(env_settings)

    def configure_services(self, service_to_nodes, env_settings):
        for service_name, running_nodes in service_to_nodes.items():
            for running_node in running_nodes:
                self.service_definitions[service_name].apply_on(running_node, {"settings": env_settings})
                self.fire_service_installed(service_name, running_node)

    def fire_service_installed(self, service_name, node):
        if service_name in self.service_lifecycle_hooks.keys():
            service_hooks = self.service_lifecycle_hooks[service_name]
            connectivities = self.service_definitions[service_name].definitions['connectivity']
            for hook in service_hooks:
                hook.service_installed(service_name, node, connectivities)

    def fire_service_terminated(self, service_name, node):
        if service_name in self.service_lifecycle_hooks.keys():
            service_hooks = self.service_lifecycle_hooks[service_name]
            if not service_hooks is None:
                for hook in service_hooks:
                    hook.service_terminated(service_name, node)

    def _provision_node(self, node_definition):
        return self.node_provider.start(node_definition, self.name, self.env_def_name)

    def _provision_nodes(self, node_defs, blocking=False):
        # Takes a list of node definitions, returning a map of service name -> node

        running_nodes = []
        service_to_nodes = defaultdict(lambda: [])

        for node_def in node_defs:
            running_node = self._provision_node(node_def)
            running_nodes.append(running_node)

            for service in node_def.services:
                service_to_nodes[service].append(running_node)

        if blocking:
            self._block_until_all_nodes_are_ready(running_nodes)

        return dict(service_to_nodes)

    def list_nodes(self):
        return self.node_provider.list(self.all_credentials, lambda x: node_predicates.running_in_env(self.name, self.env_def_name)(x))

    def delta_defs_with_running_nodes(self, node_definitions):
        # Given a list of node definitions, determines if a running node matches. If so,
        # that node is removed from the returned node definitons.
        # Returns a tuple of nodes still to provision, a mapping from service to running nodes for those
        # nodes that match, and list of nodes in the environment that are no longer needed
        pre_existing_nodes = defaultdict(lambda: set())
        node_defs_to_provision = []

        nodes_in_environment = self.node_provider.list(self.all_credentials, lambda x: node_predicates.running_in_env(self.name, self.env_def_name)(x))

        for node_def in node_definitions:
            matching_running_node = next((n for n in nodes_in_environment if n.matches_definition(node_def)), None)

            if matching_running_node:
                for service in node_def.services:
                    pre_existing_nodes[service].add(matching_running_node)

                # We don't want to match the same node again!
                nodes_in_environment.remove(matching_running_node)
            else:
                node_defs_to_provision.append(node_def)

        # At this point, if there are any nodes still in 'nodes_in_environment' then they haven't matched, and need
        # therefore to be terminated
        nodes_to_terminate = []
        nodes_to_terminate.extend(nodes_in_environment)

        return node_defs_to_provision, pre_existing_nodes, nodes_to_terminate

    def merge_service_to_nodes_dicts(self, services_to_already_launched_nodes, services_to_newly_launched_nodes):
        services_to_all_running_nodes = defaultdict(lambda: [])
        for service_name in self.service_definitions:
            services_to_all_running_nodes[service_name].extend(services_to_already_launched_nodes.get(service_name, []))
            services_to_all_running_nodes[service_name].extend(services_to_newly_launched_nodes.get(service_name, []))
        return services_to_all_running_nodes

    def launch(self):
        node_defs_to_provision, services_to_already_launched_nodes, running_nodes_to_terminate = self.delta_defs_with_running_nodes(
            self.node_definitions)

        # AWS Problems:
        #  1. Shutting down instances in a different environment
        #  2. Not matching existing instances
        # TODO - Should log gracefully during lifecycle events....
        logger.info("Shutting down instances %s" % [n.id() for n in running_nodes_to_terminate])
        logger.info("Launching new instances %s" % node_defs_to_provision)

        services_to_newly_launched_nodes = self._provision_nodes(node_defs_to_provision, blocking=True)
        map(lambda n: self.node_provider.shutdown(n.id()), running_nodes_to_terminate)

        services_to_all_running_nodes = self.merge_service_to_nodes_dicts(services_to_already_launched_nodes,
            services_to_newly_launched_nodes)

        self.tag_nodes_with_services(services_to_all_running_nodes)

        env_settings = self.build_environment_settings(services_to_all_running_nodes)
        logger.debug("settings: %s" % env_settings)
        self.configure_services(services_to_all_running_nodes, env_settings)

    def terminate_all(self):
        self.terminate_nodes([x for x in self.list_nodes()])

    def terminate_nodes(self, nodes_to_eliminate):
        for node in nodes_to_eliminate:
            self.node_provider.shutdown(node.id())
            for service_name in node.get_services().keys():
                self.fire_service_terminated(service_name,node)

    def tag_nodes_with_services(self, services_to_running_nodes):
        for service_name, running_nodes in services_to_running_nodes.items():
            map(lambda n: n.add_service_to_tags(service_name, self.service_definitions[service_name].connectivity),
                running_nodes)