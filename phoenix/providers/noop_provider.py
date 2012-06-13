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
from operator import eq
import random
from phoenix.providers.address import Address
from phoenix.providers.node_predicates import all_nodes

class StartAction(object):
    def __init__(self, node_definition, env_name, env_def_name, id):
        self.node_definition = node_definition
        self.env_def_name = env_def_name
        self.env_name = env_name
        self.node_id = id

    def __str__(self):
        return "Starting Node %s: %s on %s,%s with Credentials: %s" % (self.node_id, self.node_definition, self.env_name,self.env_def_name, self.node_definition.credentials_name)

class ShutdownAction(object):
    def __init__(self, node_id):
        self.node_id = node_id

    def __str__(self):
        return "Shutting Down Node %s" % self.node_id

class RunCommandAction(object):
    def __init__(self, command, warn_only, node_id):
        self.command = command.replace('\n','')
        self.warn_only = warn_only
        self.node_id = node_id

    def __str__(self):
        return "Command '%s' (warn only - %s) on %s" % (self.command, self.warn_only, self.node_id)

class UploadFileAction(object):
    def __init__(self, file, destination, node_id):
        self.file = file
        self.destination = destination
        self.node_id = node_id

    def __str__(self):
        return "Upload file '%s' (destination - %s) on %s" % (self.file, self.destination, self.node_id)

class AddServiceToTagAction(object):
    def __init__(self, service_name, connectivity, node_id):
        self.service_name = service_name
        self.connectivity = connectivity
        self.node_id = node_id

    def __str__(self):
        return "Adding service %s with connectivity %s to %s" % (self.service_name, [str(x) for x in self.connectivity], self.node_id)

class Actions(object):
    def __init__(self):
        self.actions = defaultdict(lambda : [])

    def add_action(self, node_id, action):
        self.actions[node_id].append(action)

    def __len__(self):
        return reduce(lambda x,y : x + len(y), self.actions.values(), 0)

    def __str__(self):
        output = ""
        for node_id, actions in dict(self.actions).items():
            output += "Actions on node %s:\n" % node_id
            for action in actions:
                output += "\t" + str(action) + "\n"
        return output

class NoopNodeProvider(object):
    def __init__(self, inner_provider):
        self.inner_provider = inner_provider
        self.actions = Actions()
        self.new_nodes = []
        self.shutdown_node_ids = []

    def __eq__(self, other):
        return self.inner_provider == other

    def __hash__(self):
        hash(self.inner_provider)

    def __str__(self):
        return str(self.inner_provider)

    def list(self, all_credentials, node_predicate=all_nodes):
        existing_nodes = [create_existing_noop_node(self.actions, node)
                          for node in self.inner_provider.list(all_credentials, node_predicate)
                          if node.id() not in self.shutdown_node_ids]

        return existing_nodes + self.new_nodes

    def shutdown(self, identity):
        action = ShutdownAction(identity)
        self.actions.add_action(identity, action)
        self.shutdown_node_ids.append(identity)

    def start(self, node_definition, env_name, env_def_name):
        id = "NewNode" + str(random.randint(1,10000))

        action = StartAction(node_definition, env_name, env_def_name, id)
        new_node = create_new_noop_node(self.actions, env_name, env_def_name, id)

        self.actions.add_action(id, action)
        self.new_nodes.append(new_node)
        return new_node

    def validate(self, env_name, env_values, error_list, all_credentials):
        self.inner_provider.validate(env_name, env_values, error_list, all_credentials)

    def get_running_environment(self, env_name, all_credentials):
        self.inner_provider.get_running_environment(env_name, all_credentials)

    def noop_actions_string(self):
        return str(self.actions)

    def get_node_startup_timeout(self):
        return 0

def create_new_noop_node(actions, env_name, env_def_name, id):
    tags = { 'env_name' : env_name,
             'env_def_name' : env_def_name,
             'services' : {} }
    state = "running"
    return NewNoopNode(actions, id, tags, state, id)

def create_existing_noop_node(actions, node):
    return ExistingNoopNode(actions, node)

class NewNoopNode(object):
    def __init__(self, actions, id, tags, state, dns_name):
        self._actions = actions
        self._id = id
        self._tags = tags
        self._state = state
        self._dns_name = dns_name

    def __str__(self):
        return "Noop Node: %s Current Tags: %s"

    def __eq__(self, other):
        return self._id == other.id()

    def id(self):
        return self._id

    def tags(self):
        return self._tags

    def state(self):
        return self._state

    def address(self):
        service_to_port_mapping = {}
        for service_name, port_list in self.tags()['services'].items():
            service_to_port_mapping[service_name] = { p: p for p in port_list }

        return Address(self._dns_name, service_to_port_mapping)

    def get_services(self):
        return self.tags()['services']

    def run_command(self, command, warn_only=False):
        self._actions.add_action(self._id, RunCommandAction(command, warn_only, self._id))
        return "fake_output"

    def add_service_to_tags(self, service_name, connectivity):
        self._actions.add_action(self._id, AddServiceToTagAction(service_name, connectivity, self._id))
        ports = reduce(lambda x,y: x + y.ports, connectivity, [])
        self.tags()['services'][service_name] = ports

    def upload_file(self, file, destination='.'):
        self._actions.add_action(self._id, UploadFileAction(file, destination, self._id))

    def matches_definition(self, node_definition):
        # This method is not currently used for new Nodes
        return False

    def wait_for_ready(self, callback, start_up_timeout):
        callback()

    def environment_name(self):
        return self.tags()['env_name']

    def environment_definition_name(self):
        return self.tags()['env_def_name']

class ExistingNoopNode(object):
    def __init__(self, actions, inner_node=None):
        self.actions = actions
        self.inner_node = inner_node
        self.additional_services = {}

    def __str__(self):
        return str(self.inner_node)

    def __eq__(self, other):
        return eq(other, self.inner_node)

    def id(self):
        return self.inner_node.id()

    def tags(self):
        return self.inner_node.tags()

    def state(self):
        return self.inner_node.state()

    def address(self):
        address = self.inner_node.address()
        service_to_port_mapping = {}
        for service_name, port_list in self.additional_services.items():
            service_to_port_mapping[service_name] = { p: p for p in port_list }
        address.service_mappings = dict(address.service_mappings.items() + service_to_port_mapping.items())
        return address

    def get_services(self):
        return self.inner_node.get_services()

    def run_command(self, command, warn_only=False):
        self.actions.add_action(self.id(), RunCommandAction(command, warn_only,self.id()))
        return "fake_output"

    def add_service_to_tags(self, service_name, connectivity):
        self.actions.add_action(self.id(),AddServiceToTagAction(service_name, connectivity, self.id()))
        ports = reduce(lambda x,y: x + y.ports, connectivity, [])
        self.additional_services[service_name] = ports

    def upload_file(self, file, destination='.'):
        self.actions.add_action(self.id(), UploadFileAction(file, destination, self.id()))

    def matches_definition(self, node_definition):
        return self.inner_node.matches_definition(node_definition)

    def wait_for_ready(self, callback, start_up_timeout):
        self.inner_node.wait_for_ready(callback, start_up_timeout)

    def environment_name(self):
        return self.inner_node.environment_name()

    def environment_definition_name(self):
        return self.inner_node.environment_definition_name()