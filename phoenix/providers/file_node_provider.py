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
import random
from node_predicates import all_nodes
from phoenix.providers.address import Address

class FileBackedNodeDefinition:
    def __init__(self, role=None, services=[]):
        self.role = role
        self.services = services

    def validate(self, error_list, node_number, env_name, node_definition, all_credentials):
        pass

class FileBackedNode:
    def __init__(self, node_id, state, env, services, env_def_name):
        self.node_id = node_id
        self.node_state = state
        self.env = env
        self.env_def_name = env_def_name
        self.services = services

    def __str__(self):
        return 'FileBackedNode: id: %s - %s' % (self.node_id, self.state)

    def __repr__(self):
        return "FileBackedNode with ID %s in environment %s" % (self.node_id, self.env)

    def __eq__(self, other):
        return other.id() == self.id()

    def __hash__(self):
        return hash(self.node_id)

    def id(self):
        return self.node_id

    def tags(self):
        pass

    def environment(self):
        return self.env

    def state(self):
        return self.node_state

    def address(self):
        return Address(self.node_id, self.services)

    def belongs_to_env(self, env_name):
        return env_name == self.env

    def get_services(self):
        return self.services

    def run_command(self, command):
        _change_state(self.id(), command)

    def add_service_to_tags(self, service_name, connectivity):
        file_string = './fake_nodes/fake_env.yml'
        with open(file_string, 'r') as f:
            nodes = yaml.load(f)

        ports = reduce(lambda x,y: x + y.ports, connectivity, [])

        nodes['nodes'][self.id()]['services'][service_name] = dict([(x,x) for x in ports])
        self.services = nodes['nodes'][self.id()]['services']

        with open(file_string, 'w') as f:
            yaml.dump(nodes, f)

    def upload_file(self, file, destination='.'):
        file_string = './fake_nodes/fake_env.yml'
        with open(file_string, 'r') as f:
            nodes = yaml.load(f)

        if file.startswith("settings"):
            nodes['nodes'][self.id()].update(yaml.load(file.split('-')[1]))

        with open(file_string, 'w') as f:
            yaml.dump(nodes, f)

    def matches_definition(self, node_type):
        return set(self.services) == set(node_type.services)

    def wait_for_ready(self, callback, start_up_timeout):
        callback()

    def environment_name(self):
        return self.env

    def environment_definition_name(self):
        return self.env_def_name

class FileBackedNodeProvider(object):
    def __init__(self, node_ids=None):
        if not node_ids: node_ids = []
        self.node_ids = node_ids

    def __eq__(self, other):
        return self.node_ids == other.node_ids

    def __hash__(self):
        return hash(reduce(lambda a, b: a+b, self.node_ids, ""))

    def __str__(self):
        return "FileBackedNodeProvider"

    def next_id(self):
        if not self.node_ids:
            return random.randint(1, 100000)
        else:
            return self.node_ids.pop()

    def list(self, all_credentials, node_predicate=all_nodes):
        file_string = './fake_nodes/fake_env.yml'
        if not os.path.exists(file_string):
            return []

        f = open(file_string, 'r')
        nodes = yaml.load(f)['nodes']
        return filter(node_predicate, [FileBackedNode(bob[0], bob[1]['state'], bob[1]['env'], bob[1]['services'], bob[1]['env_def_name'])
                                       for bob in nodes.items()])

    def shutdown(self, identity):
        _change_state(identity, 'terminated')

    def start(self, node_definition, env_name, env_def_name):
        contents = _get_content()
        node_id = self.next_id()
        state = 'running'
        with open(file_string, 'w') as file:
            contents['nodes'][node_id] = { 'state' : state, 'services' : {}, 'env' : env_name, 'env_def_name' : env_def_name }
            yaml.dump(contents, file)

        return FileBackedNode(node_id, state, env_name, [], env_def_name)


    def validate(self, env_name, env_values, error_list, all_credentials):
        pass

    def get_running_environment(self, env_name, all_credentials):
        pass

    def get_node_startup_timeout(self):
        pass

file_string = './fake_nodes/fake_env.yml'
def _get_content():
    dir_string = './fake_nodes'
    if not os.path.exists(dir_string):
        os.makedirs(dir_string)
    file_string = dir_string + '/fake_env.yml'
    contents = {'nodes': {}, 'security_groups': [] }
    if os.path.exists(file_string):
        with open(file_string, 'r') as file:
            contents = yaml.load(file)
    return contents

def _change_state(identity, state):
    file_string = './fake_nodes/fake_env.yml'
    with open(file_string, 'r') as file:
        obj = yaml.load(file)
    obj['nodes'][identity]['state'] = state
    with open(file_string, 'w') as file:
        yaml.dump(obj, file)
