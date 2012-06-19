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

import time
import re
import socket
from time import sleep
import boto
import boto.ec2
from boto.exception import EC2ResponseError
from fabric.context_managers import settings
from fabric.operations import run, put
import phoenix.environment_description
from phoenix.providers import node_predicates
import yaml
from node_predicates import all_nodes
from address import Address
from phoenix.plogging import logger
from phoenix.providers.node_predicates import running_nodes

class AWSNodeDefinition():

    def __init__(self, ami_id=None, size=None, credentials_name=None, region='us-east-1', services=None, security_groups=None, aws_key_name=None, availability_zone=None):

        """Supports the following launch parameters:
        ami_id          - AMI ID to Launch
        size            - Size of AWS instance to launch.
        admin_user      - The admin user to connect with
        admin_key_name  - The AWS key to install on the server

        For testing purposes, consider ami_id=ami-81c5fdf5,size=t1.micro to launch
        micro 64bit ubuntu instances. Note: This call does NOT block. You'll need to wait until the instance reports that it is running,
        and then wait for the SSH interface to be up, before you can log in and configure the instance."""
        if not services: services = []

        self.ami_id = ami_id
        self.size = size
        self.credentials_name = credentials_name
        self.region = region
        self.services = services
        self.security_groups = security_groups
        self.aws_key_name=aws_key_name
        self.admin_user=None
        self.path_to_private_key=None
        self.availability_zone = availability_zone

    def add_credentials(self, all_credentials):
        if not all_credentials[self.credentials_name] is None:
            self.admin_user = all_credentials[self.credentials_name].login
            self.path_to_private_key = all_credentials[self.credentials_name].path_to_private_key()


    def validate(self, error_list, node_number, env_name, node_definition, all_credentials):
        if not 'ami_id' in node_definition or node_definition['ami_id'] is None or node_definition['ami_id'].strip() == "":
            error_list.append("Key 'ami_id' not set for AWS node definition number %s in '%s' environment" % (node_number, env_name))
        if not 'aws_key_name' in node_definition or node_definition['aws_key_name'] is None or node_definition['aws_key_name'].strip() == "":
            error_list.append("Key 'aws_key_name' not set for AWS node definition number %s in '%s' environment" % (node_number, env_name))
        if not 'size' in node_definition or node_definition['size'] is None or node_definition['size'].strip() == "":
            error_list.append("Key 'size' not set for AWS node definition number %s in '%s' environment" % (node_number, env_name))
        if not 'credentials_name' in node_definition or node_definition['credentials_name'] is None or node_definition['credentials_name'].strip() == "":
            error_list.append("Key 'credentials_name' not set for AWS node definition number %s in '%s' environment" % (node_number, env_name))
        else:
            credentials_name = node_definition['credentials_name']
            if not credentials_name in all_credentials:
                error_list.append("Key 'credentials_name' does not contain a valid credential for AWS node definition number %s in '%s' environment" % (node_number, env_name))

    def __str__(self):
        return "AWSNodeDefinition for %s as %s" % (self.ami_id, self.size)

    def __repr__(self):
        return "AWSNodeDefinition AMI:'%s' Size:'%s' Credentials:'%s' Region:'%s' Services:'%s'" %\
               (self.ami_id, self.size, self.credentials_name, self.region, self.services)

class AWSRunningNode():
    def __init__(self, boto_instance, aws_security, connection_provider=None):
        self.boto_instance = boto_instance
        self.environment = self.boto_instance.tags['env_name']
        self.services = self.boto_instance.tags['services']
        self.aws_security = aws_security
        self.connection_provider = connection_provider
        if self.connection_provider is None :
            self.connection_provider = EC2ConnectionProvider()

    def __str__(self):
        return "AWS Running node. id:%s ami_id:%s size:%s credentials:%s region:%s services:%s" % \
               (self.boto_instance.id, self.boto_instance.image_id, self.boto_instance.instance_type, self._tag('credentials_name'), self.boto_instance.region, self.services)

    def __repr__(self):
        return "AWS Running node. id:%s ami_id:%s size:%s credentials:%s region:%s services:%s" % \
               (self.boto_instance.id, self.boto_instance.image_id, self.boto_instance.instance_type, self._tag('credentials_name'), self.boto_instance.region, self.services)

    def id(self):
        return self.boto_instance.id

    def ami_id(self):
        return self.boto_instance.image_id

    def state(self):
        return self.boto_instance.state

    def tags(self):
        return self.boto_instance.tags

    def region(self):
        return self.boto_instance.region

    def placement(self):
        return self.boto_instance.placement

    def _dns_name(self):
        return self.boto_instance.public_dns_name

    def _admin_user(self):
        return self._tag('admin_user')

    def _path_to_private_key(self):
        return self._tag('path_to_private_key')

    def address(self):
        services = self.get_services()

        # AWS services always run on the port that was requested, so we don't store
        # a mapping. But the address assumes we have this mapping in place...

        service_to_port_mapping = {}
        for service_name, port_list in services.items():
            service_to_port_mapping[service_name] = { p: p for p in port_list }

        return Address(self._dns_name(), service_to_port_mapping)

    def add_service_to_tags(self, service_name, connectivities):
        service_to_ports_dict = self.get_services()
        ports = reduce(lambda x,y: x + y.ports, connectivities, [])
        service_to_ports_dict[service_name] = ports
        self.boto_instance.add_tag('services', yaml.dump(service_to_ports_dict))
        for connectivity in connectivities:
            self.aws_security.open_ports(service_name, connectivity)

    def attributes(self):
        return {'id':self.id(),'ami_id':self.ami_id(),'dns_name':self._dns_name(),'services':self.address().get_service_mappings(), 'availability_zone':self.placement()}

    def get_services(self):
        service_tag_content = self.tags().get('services')
        return yaml.load(service_tag_content)

    def _running_node(self):
        if not self.state() == 'running':
            raise StandardError("Cannot run a command on a node which is in state %s" % self.state())

        if not self._dns_name():
            raise StandardError("Cannot run a command on a node without a DNS name")

        return settings(host_string=self._dns_name(), user=self._admin_user(), key_filename=self._path_to_private_key())

    def run_command(self, command, warn_only=False):
        with settings(warn_only = warn_only):
            with self._running_node():
                logger.debug("Running on node %s with user %s and key %s" % \
                                                  (self._dns_name(), self._admin_user(), self._path_to_private_key()))
                return run(command)

    def upload_file(self, file_name, destination='.'):
        with self._running_node():
            put(file_name, destination)


    def wait_for_ready(self, callback, start_up_timeout=90):
        logger.info("Waiting for node %s to be ready" % self.id())
        start = time.time()
        node_is_up = False
        while time.time() - start <= start_up_timeout :
            self.boto_instance.update()
            if self.state() == 'running' and self.boto_instance.ip_address is not None:
                node_is_up = self.connection_provider.connected_to_node(self.boto_instance.ip_address, 22)
                if node_is_up :
                    logger.info("*********Node %s is ready!********" % self.id())
                    break
            else:
                logger.debug("Waiting for 5 seconds for node %s" % self.id())
                sleep(5)

        if not node_is_up :
            raise Exception("Node %s is not running" % self.id())

        # For some reason, with the Ubuntu instances we use, if we try and install packages too quickly after the machine
        # boots, we don't get the transient dependencies - highly annoying.
        sleep(10)
        callback()

    def matches_definition(self, node_definition):
        logger.info("Matching %s against definition %s" % (self, node_definition))
        return self.boto_instance.image_id == node_definition.ami_id and \
        self.boto_instance.instance_type == node_definition.size and \
        self._tag('credentials_name') == node_definition.credentials_name and \
        self.boto_instance.region.name == node_definition.region and \
        self.get_services().keys() == node_definition.services

    def environment_definition_name(self):
        return self._tag('env_def_name')

    def environment_name(self):
        return self._tag('env_name')

    def _tag(self, tagname, default="Unknown"):
        if self.boto_instance.tags.has_key(tagname):
            return self.boto_instance.tags[tagname]

        logger.warn("Unable to retrieve tag %s for instance %s, returning %s instead" % (tagname, self.id(), default))
        return default

class AWSNodeProvider:

    def __init__(self, public_api_key=None, private_api_key=None, connection_provider = None, start_up_timeout = 90, **kwargs):
        self.public_api_key = public_api_key
        self.private_api_key = private_api_key
        self.connection_provider = connection_provider
        if self.connection_provider is None:
            self.connection_provider = EC2ConnectionProvider()
        self.start_up_timeout = start_up_timeout

    def __eq__(self, other):
        return self.private_api_key == other.private_api_key and self.public_api_key == other.public_api_key

    def __hash__(self):
        return hash(self.private_api_key + self.public_api_key)

    def __str__(self):
        return "AWS Node Provider using public key %s" % self.public_api_key

    def list(self, all_credentials, node_predicate = all_nodes):
        nodes = []

        for boto_instance in [i for i in self.connection_provider.get_all_boto_instances(self.public_api_key, self.private_api_key) if i.state == 'running']:
            if boto_instance.tags.has_key('env_def_name'):
                aws_security = AWSSecurity(self.connection_provider.ec2_connection_for_region(boto_instance.region.name, self.public_api_key, self.private_api_key),
                    self._security_group_name(boto_instance.tags['env_def_name'], boto_instance.tags['env_name']))

                aws_node = AWSRunningNode(boto_instance, aws_security)
                if node_predicate(aws_node):
                    nodes.append(aws_node)
            else:
                logger.warn(
                    "Unable to find env_def_name for %s:%s, will not be included in listing in state %s" % (boto_instance.id, boto_instance.region, boto_instance.state))

        return nodes

    def get_locations(self, region_nodes_map):
        locations = []
        for region, nodes in region_nodes_map.items() :
            locations.append(phoenix.environment_description.Location(region, nodes))
        return locations

    def get_running_environment(self, env_name, env_template_name, all_credentials):
        nodes = self.list(all_credentials, lambda x: node_predicates.running_in_env(env_name, env_template_name)(x))
        region_nodes_map = {}
        for node in nodes:
            if not node.region().name in region_nodes_map.keys():
                region_nodes_map.update({node.region().name:[node]})
            else:
                region_nodes_map[node.region().name].append(node)

        locations = self.get_locations(region_nodes_map)
        return phoenix.environment_description.EnvironmentDescription(env_name, locations)

    def _find_node(self, identity):
        nodes = [i for i in self.connection_provider.get_all_boto_instances(self.public_api_key, self.private_api_key) if i.id == identity.decode('utf-8')]
        if not len(nodes):
            raise StandardError("No node with ID %s found" % identity)

        return nodes.pop()

    def shutdown(self, identity):
        self._find_node(identity).terminate()

    def start(self, aws_node_definition, env_name, env_def_name):
        tags = { 'env_name' : env_name,
                 'env_def_name' : env_def_name,
                 'services' : {},
                 'credentials_name': aws_node_definition.credentials_name,
                 'admin_user' : aws_node_definition.admin_user,
                 'path_to_private_key' : aws_node_definition.path_to_private_key}

        conn = self.connection_provider.ec2_connection_for_region(aws_node_definition.region, self.public_api_key, self.private_api_key)
        ami = conn.get_image(aws_node_definition.ami_id)

        aws_security = AWSSecurity(conn, env_def_name + '/' + env_name)

        security_groups = [aws_security.create_security_group_if_it_does_not_exists(x) for x in aws_node_definition.services]

        security_groups = security_groups + aws_node_definition.security_groups if aws_node_definition.security_groups else security_groups

        reservation = ami.run(instance_type=aws_node_definition.size, key_name=aws_node_definition.aws_key_name,
            security_groups=security_groups, placement=aws_node_definition.availability_zone)

        boto_instance = reservation.instances[0]
        for name, value in tags.items():
            boto_instance.add_tag(name, value)

        return AWSRunningNode(boto_instance, aws_security)

    def _security_group_name(self, env_def_name, env_name):
        return env_def_name + '/' + env_name

    def validate(self, env_name, env_values, error_list, all_credentials):
        if not 'public_api_key' in env_values:
            error_list.append("Key 'public_api_key' not found for AWS in '%s' environment" % env_name)
        elif env_values['public_api_key'] is None or str(env_values['public_api_key']).strip() == "":
            error_list.append("Key 'public_api_key' not defined for AWS in '%s' environment" % env_name)
        if not 'private_api_key' in env_values:
            error_list.append("Key 'private_api_key' not found for AWS in '%s' environment" % env_name)
        elif env_values['private_api_key'] is None or str(env_values['private_api_key']).strip() == "":
            error_list.append("Key 'private_api_key' not defined for AWS in '%s' environment" % env_name)

    def get_env_definition_translator(self):
        return phoenix.environment_description.AWSEnvironmentDefinitionTranslator()

    def get_node_startup_timeout(self):
        return self.start_up_timeout

class AWSSecurity:
    def __init__(self, connection, env_name):
        self.connection = connection
        self.env_name = env_name

    def create_security_group_if_it_does_not_exists(self, service_name):
        """
        Creates a security group for the given service name if that service group does not already exist
        returns the fully qualified name of the security group
        """
        security_group_name = self._get_sec_group_name(service_name)

        sec_groups = self.connection.get_all_security_groups()
        if not len([x for x in sec_groups if x.name == security_group_name]):
            logger.info("Creating new Security Group %s" % security_group_name)
            self.connection.create_security_group(security_group_name, "dynamically created security group")
        else:
            logger.info("Security Group %s already exists" % security_group_name)

        return security_group_name

    def open_ports(self, service_name, connectivity):
        """
        Uses Amazon security groups to open ports either to the world or to other services security groups
        service_name: the name of the service that we want to open ports for
        connectivity: the connectivity information for the given service
            - ports: a list of ports that are needed for the service to work - expects either an integer [80, 81] or a range [ 50-59, 65-70 ]
            - allowed: a list of services that have access to this service Note: WORLD is a special case that allows everybody to access the port
            - protocol: one of 'tcp', 'udp' or 'icmp'

        Method assumes that the security groups will all exist before it is called
        """
        security_group_name = self._get_sec_group_name(service_name)
        cur_group = self._get_security_group(security_group_name)
        sources = []

        for allowed in connectivity.allowed:
            if allowed == 'WORLD':
                sources.append('0.0.0.0/0')
            elif re.search("^(\d{1,3}\.){3}\d{1,3}(/\d{1,3})?$", allowed): # allow direct ip access if you'd like
                sources.append(allowed)
            else:
                source_sec_group = self._get_security_group(self._get_sec_group_name(allowed))
                sources.append(source_sec_group)
        for port in connectivity.ports:
            if isinstance(port, basestring):
                from_port = port.split('-')[0] if '-' in port else port
                to_port = port.split('-')[1] if '-' in port else port
            else:
                from_port = port
                to_port = port
            for source in sources:
                try:
                    cur_group.authorize(connectivity.protocol, from_port, to_port, source) if isinstance(source, basestring)\
                        else cur_group.authorize(connectivity.protocol, from_port, to_port, src_group=source)
                except EC2ResponseError as (error): #TODO: don't re-authorize existing rules
                    logger.warn("An error has occurred during authorization %s\nThis may be expected if the rule has already been authorized" % error   )

    def _get_sec_group_name(self, service_name):
        return self.env_name + '/' + service_name

    def _get_security_group(self, security_group_name):
        sec_groups = self.connection.get_all_security_groups()
        cur_group = [x for x in sec_groups if x.name == security_group_name].pop()
        return cur_group


class EC2ConnectionProvider:

    def ec2_connection_for_region(self, region_name, public_api_key, private_api_key):
        return boto.ec2.connect_to_region(region_name, aws_access_key_id=public_api_key, aws_secret_access_key=private_api_key)

    def get_ec2_regions(self, public_api_key, private_api_key):
        return boto.ec2.regions(aws_access_key_id=public_api_key, aws_secret_access_key=private_api_key)

    def get_all_boto_instances(self, public_api_key, private_api_key):
        for region in self.get_ec2_regions(public_api_key, private_api_key):
            for reservation in self.ec2_connection_for_region(region.name, public_api_key, private_api_key).get_all_instances():
                for instance in reservation.instances:
                    yield instance

    def connected_to_node(self, ip_address, port):
        try:
            socket.create_connection((ip_address, port))
            return True
        except:
            return False
