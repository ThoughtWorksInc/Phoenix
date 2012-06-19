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

import random
import string
from fabric.context_managers import settings, hide
from fabric.operations import run, put
from phoenix.providers import node_predicates
import time
import yaml
from node_predicates import all_nodes
import phoenix
from phoenix.environment_description import Location
from phoenix.plogging import logger
from phoenix.providers.address import Address

class LXCNodeDefinition:
    def __init__(self, template=None, services=None):
        if not services: services = []
        self.template = template
        self.services = services

    def validate(self, error_list, node_number, env_name, node_definition, all_credentials):
        if not 'template' in node_definition or node_definition['template'] is None or node_definition['template'].strip() == "":
            error_list.append("Key 'template' not set for LXC node definition number %s in '%s' environment" % (node_number, env_name))

    def __str__(self):
        return "LXCNodeDefinition for %s" % self.template

class LXCNode:
    def __init__(self, node_id, ssh_command_helper, lxc_host_name):
        self.node_id = node_id
        self.ssh_command_helper = ssh_command_helper
        self.lxc_host_name = lxc_host_name

    def __str__(self):
        return "LXC Node: %s running on %s" % (self.node_id, self.lxc_host_name)

    def __eq__(self, other):
        return self.id() == other.id()

    def id(self):
        return self.node_id

    def attributes(self):
        return {'template': self._tag('template'),'id':self.id(), 'dns_name': self.lxc_host_name, 'services':self.get_services()}

    def tags(self):
        tags = self.ssh_command_helper.run_command("if sudo [ -f /var/lib/lxc/%s/tags ]; then sudo cat /var/lib/lxc/%s/tags; else echo '{}'; fi" % (self.node_id, self.node_id))
        return yaml.load(tags)

    def state(self):
        # replace "'" with "" in order to allow yaml to parse the state
        return yaml.load(self.ssh_command_helper.run_command("sudo lxc-info -n %s" % self.node_id).replace("'", ''))['state'].lower()

    def address(self):
        return Address(self.lxc_host_name, self.get_services())

    def belongs_to_env(self, env_name):
        tokens = env_name.split(":")
        return self.environment_name() == tokens[1] and self.environment_definition_name() == tokens[0]

    def get_services(self):
        return self._tag('services')

    def run_command(self, command, warn_only=False):
        with settings(warn_only = warn_only):
            logger.info("Running on node %s" % str(self))
            return self.ssh_command_helper.run_command("sudo ssh -i /root/.ssh/id_rsa -oStrictHostKeyChecking=no root@%s '%s'" % (self.node_id, command))

    def _get_next_port_number_to_map(self):
        # need to start somewhere... 50000
        # TODO: fix this via configuration
        used_ports = [int(x) for x in self.ssh_command_helper.run_command("sudo iptables -t nat -L PREROUTING | cut -c 86-90").splitlines() if x.isdigit()]
        if not used_ports:
            return 50000
        return sorted(used_ports)[-1] + 1

    def add_service_to_tags(self, service_name, connectivity):
        """
            Add a service to the tag
            This is where we do the port forwarding for LXC Containers
            connectivity is expected to be a list of connectivity objects each with a list of ports
        """
        ports = reduce(lambda x, y: x + y.ports, connectivity, [])

        if service_name in self._tag('services'):
            return

        next_port_number = self._get_next_port_number_to_map()
        node_ip = self.ssh_command_helper.run_command("host %s | sed 's/^.*address //'" % self.node_id)

        mapped_ports = {}
        for port in ports:
            mapped_ports[port] = next_port_number
            host_ip = self.ssh_command_helper.run_command("ifconfig eth0 | grep 'inet addr' | awk '{print $2}' | sed -e 's/.*://'")
            commands = []
            # Allow the world to see the port we are mapping to
            commands.append("sudo iptables -t nat -A PREROUTING -p tcp -i eth0 -d %s --dport %s --sport 1024:65535 -j DNAT --to %s:%s" % (host_ip, next_port_number, node_ip, port))
            # Allow the other nodes to see th port we are mapping to
            commands.append("sudo iptables -t nat -A PREROUTING -p tcp -i br0 -d %s --dport %s --sport 1024:65535 -j DNAT --to %s:%s" % (host_ip, next_port_number, node_ip, port))
            # Allow the host to see the port we are mapping to
            commands.append("sudo iptables -t nat -A OUTPUT -p tcp -d %s --dport %s -j DNAT --to-destination %s:%s" % (host_ip, next_port_number, node_ip, port))
            self.ssh_command_helper.run_commands(commands)
            next_port_number += 1

        cur_tags = self.tags()
        cur_tags['services'][service_name] = mapped_ports
        self.ssh_command_helper.run_command("sudo sh -c \"echo '%s' > /var/lib/lxc/%s/tags\"" % (yaml.dump(cur_tags).strip(), self.node_id)) # write tags

    def upload_file(self, file, destination='.'):
            file_name = file.split("/")[-1]
            self.ssh_command_helper.put_file(file, "/tmp")
            self.ssh_command_helper.run_command("sudo scp -i /root/.ssh/id_rsa -oStrictHostKeyChecking=no /tmp/%s root@%s:%s" % (file_name, self.node_id, destination))

    def matches_definition(self, node_definition):
        return self.get_services().keys() == node_definition.services and self.tags()['template'] == node_definition.template

    def wait_for_ready(self, callback, start_up_timeout=45):
        logger.info("Waiting for node %s to be ready" % self.id())
        start = time.time()
        succeeded = False
        while time.time() - start <= start_up_timeout:
            try:
                succeeded = self.ssh_command_helper.run_command_silently("ping -c1 %s" % self.node_id).succeeded
            except:
                pass
            if succeeded :
                logger.info("*********Node %s is ready!*********" % self.id())
                break
            else:
                logger.info("Node %s not yet ready, checking again in 3 seconds" % self.id())
                time.sleep(3)
        if not succeeded :
            raise Exception("Node %s is not running" % self.node_id)
        callback()

    def environment_name(self):
        return self._tag('env_name')

    def environment_definition_name(self):
        return self._tag('env_def_name')

    def _tag(self, tagname, default=None):
        tags = self.tags()

        if tags.has_key(tagname):
            return tags[tagname]

        logger.warn("Unable to retrieve tag %s for instance %s, returning %s instead" % (tagname, self.id(), default))
        return default


class LXCNodeProvider(object):

    def __init__(self, credentials=None, host_name=None, ssh_command_helper=None, start_up_timeout=45):
        self.credentials = credentials
        self.host_name = host_name
        self.ssh_command_helper = ssh_command_helper
        self.start_up_timeout = start_up_timeout
        if ssh_command_helper is None and not credentials is None:
            self.ssh_command_helper = SSHCommandHelper(host_name, credentials.login, credentials.path_to_private_key())

    def __eq__(self, other):
        return isinstance(other, LXCNodeProvider) and self.credentials == other.credentials

    def __hash__(self):
        return hash(self.credentials)

    def __str__(self):
        return "LXCNodeProvider"

    def validate(self, env_name, env_values, error_list, all_credentials):
        if not 'host_name' in env_values:
            error_list.append("Key 'host_name' not found for LXC in '%s' environment" % env_name)
        elif env_values['host_name'] is None or env_values['host_name'].strip() == "":
            error_list.append("Key 'host_name' not defined for LXC in '%s' environment" % env_name)
        if not 'credentials' in env_values:
            error_list.append("Key 'credentials' not found for LXC in '%s' environment" % env_name)
            return
        elif env_values['credentials'] is None or env_values['credentials'].strip() == "":
            error_list.append("Key 'credentials' not defined for LXC in '%s' environment" % env_name)
            return

        credential_name = env_values['credentials']
        if not credential_name in all_credentials:
            error_list.append("'%s' is invalid for key 'credentials' in LXC for '%s' environment" % (credential_name, env_name))

    def list(self, ignored_credentials = None, node_predicate = all_nodes):
        nodes = list(set(self.ssh_command_helper.run_command("sudo lxc-ls -c1").splitlines()))
        return filter(node_predicate, [LXCNode(x, self.ssh_command_helper, self.host_name) for x in nodes])

    def get_running_environment(self, env_name, env_template_name, all_credentials):
        nodes = self.list(all_credentials, lambda x: node_predicates.running_in_env(env_name, env_template_name)(x))
        locations = []
        if not nodes is None and len(nodes) != 0:
            locations.append(Location(self.host_name, nodes))
        return phoenix.environment_description.EnvironmentDescription(env_name, locations)


    def shutdown(self, identity):
        self.ssh_command_helper.run_command("sudo lxc-stop -n %s && sudo lxc-destroy -n %s" % (identity, identity))

    def _terminate_all(self):
        [self.shutdown(x.id()) for x in self.list()]

    def start(self, lxc_node_definition, env_name, env_def_name):
        node_id = "i-" + "".join( [random.choice(string.digits + string.letters) for _ in xrange(8)])
        tags = { 'env_name': env_name, 'env_def_name' : env_def_name, 'services' : {}, 'template' : lxc_node_definition.template }

        commands = []
        # TODO: this could be simply executing a bootstrap bash script instead of manually executing each line...
        # this would allow lxc hosts to have differing configuration - or us puppet
        commands.append("sudo lxc-create --name %s --config /etc/lxc/lxc.conf --template %s" % (node_id, lxc_node_definition.template))
        commands.append("sudo lxc-start --name %s --daemon" % (node_id))
        commands.append("sudo sh -c \"echo '%s' > /var/lib/lxc/%s/tags\"" % (yaml.dump(tags).strip(), node_id)) # write tags
        commands.append("sudo mkdir -p /var/lib/lxc/%s/rootfs/root/.ssh" % node_id)
        # technically this should be done as part of the original bootstrap
        commands.append("if sudo [ ! -f /root/.ssh/id_rsa ]; then sudo ssh-keygen -t rsa -f /root/.ssh/id_rsa -P ''; fi")
        commands.append("sudo cp /root/.ssh/id_rsa.pub /var/lib/lxc/%s/rootfs/root/.ssh/authorized_keys" % node_id)

        self.ssh_command_helper.run_commands(commands)
        return LXCNode(node_id, self.ssh_command_helper, self.host_name)

    def get_env_definition_translator(self):
        return phoenix.environment_description.LXCEnvironmentDefinitionTranslator()

    def get_node_startup_timeout(self):
        return self.start_up_timeout

class SSHCommandHelper():
    def __init__(self, host_name, admin_user, path_to_private_key):
        self.host_name = host_name
        self.admin_user = admin_user
        self.path_to_private_key = path_to_private_key

    def _ssh_credentials_context(self):
        return settings(host_string=self.host_name, user=self.admin_user, key_filename=self.path_to_private_key)

    def run_commands(self, commands):
        with self._ssh_credentials_context():
            for command in commands :
                run(command)

    def run_command(self, command):
        with self._ssh_credentials_context():
            return run(command)

    def run_command_silently(self, command):
        with self._ssh_credentials_context():
            with hide('running', 'stdout', 'stderr', 'status', 'aborts'):
                return run(command)

    def put_file(self, local_file, remote_path):
        with self._ssh_credentials_context():
            return put(local_file, remote_path)
