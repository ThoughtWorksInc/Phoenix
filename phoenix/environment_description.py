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
from texttable import Texttable


class EnvironmentDescription():
    def __init__(self, name, locations):
        self.name = name
        self.locations = locations

    def get_name(self):
        return self.name

    def get_locations(self):
        return self.locations

class Location():
    def __init__(self, name, nodes):
        self.name = name
        self.nodes = nodes

    def get_name(self):
        return self.name

    def get_nodes(self):
        return self.nodes

class Node():
    def __init__(self, attributes):
        self._attributes = attributes

    def attributes(self):
        return self._attributes

class Service():
    def __init__(self, name, port_mappings):
        self.name = name
        self.port_mappings = port_mappings


def service_descriptions(node_defn, service_definitions):
    services = []
    for service_name in node_defn.services:
        services.append(Service(service_name, service_definitions[service_name].definitions['connectivity']))
    return services

# TODO: This is butt ugly - nodes/environments should be self-describing
class AWSEnvironmentDefinitionTranslator(object):

    def translate(self, env_definitions_from_yaml, env_template, service_definitions):
        env_definition = env_definitions_from_yaml[env_template]
        name = env_definition.name

        node_region_map = {}
        for node_defn in env_definition.node_definitions:

            attribute_map = {'ami_id': node_defn.ami_id, 'size': node_defn.size,
                             'services': (service_descriptions(node_defn, service_definitions))}

            if not node_defn.availability_zone is None:
                attribute_map.update({'availability_zone': node_defn.availability_zone})

            node_to_append = Node(attribute_map)

            if not node_defn.region in node_region_map.keys() :
                node_region_map.update({node_defn.region : [node_to_append]})
            else :
                node_region_map[node_defn.region].append(node_to_append)

        return EnvironmentDescription(name, self.get_locations(node_region_map))

    def get_locations(self, node_region_map):
        locations = []
        for region, nodes in node_region_map.items() :
            locations.append(Location(region, nodes))
        return locations

class LXCEnvironmentDefinitionTranslator(object):


    def translate(self, env_definitions_from_yaml, env_template, service_definitions):
        env_definition = env_definitions_from_yaml[env_template]
        name = env_definition.name

        nodes = []
        for node_defn in env_definition.node_definitions:
            nodes.append(Node({'template': node_defn.template,'services': service_descriptions(node_defn, service_definitions)}))
        return EnvironmentDescription(name, [Location(env_definition.node_provider.host_name, nodes)])

class SimpleTextEnvironmentDescriber():
    def describe(self, environment):
        description = environment.get_name() + '\n'

        for location in environment.get_locations():
            description += '  ' + location.get_name() + '\n'

            for node in location.get_nodes():
                description += '    DNS: ' + node.attributes()['dns_name'] + ' Services:'
                services = node.attributes()['services']
                for service_name in services.keys():
                    description += ' ' + service_name
                description += '\n'

        return description

class TextTableEnvironmentDescriber():

    def describe(self, environment):
        description = "\nEnvironment: " + environment.get_name() + '\n'

        table = Texttable()
        table.set_cols_width([10, 50, 20, 15])
        rows = [["Location", "DNS", "Services", "ID"]]

        for location in environment.get_locations():

            for node in location.get_nodes():
                rows.append([location.get_name(), node.attributes()['dns_name'], node.attributes()['services'], node.attributes()['id']])

        table.add_rows(rows)
        description += table.draw()

        return description