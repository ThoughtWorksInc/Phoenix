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

import commands
import logging
import unittest
import boto
from boto.regioninfo import RegionInfo
from fabric.context_managers import settings
import time
import twill
from phoenix.providers import node_predicates
from phoenix.fabfile import launch, env_conf_from_dir
from phoenix.plogging import logger

class GivenAValidConfigurationFile(unittest.TestCase):

    env_to_shut_down = {}

    def get_connection_for_region(self, region, public_api_key, private_api_key):
        reg = RegionInfo(
            name=region,
            endpoint='elasticloadbalancing.'+ region +'.amazonaws.com'
        )
        conn = boto.connect_elb(
            aws_access_key_id=public_api_key,
            aws_secret_access_key=private_api_key,
            region=reg
        )
        return conn

    def remove_existing_hello_world_elb(self, env_template, service_name):
        with env_conf_from_dir('samples', 'dummy_name', 'build_credentials/phoenix.ini') as env_def:
            env_vals = env_def[env_template]
            node_provider = env_vals.get_node_provider()
            region = env_vals.node_definitions[0].region
            conn = self.get_connection_for_region(region, node_provider.public_api_key, node_provider.private_api_key)
            hook_elb_name = env_vals.service_lifecycle_hooks[service_name][0].elb_name
            try:
                load_balancer = conn.get_all_load_balancers(load_balancer_names=[hook_elb_name])[0]
                load_balancer.delete()
            except:
                pass

    def test_should_have_a_functioning_hello_world(self):
        with settings(credentials_dir="credentials"):
            dynamic_env_name = "test_should_have_a_functioning_hello_world_"+str(int(round(time.time() * 1000)))
            env_template_name = "integration"
            self.env_to_shut_down.update({env_template_name: dynamic_env_name})
            environment_definition = launch(env_template=env_template_name, env_name=dynamic_env_name, config_dir="samples", property_file="build_credentials/phoenix.ini")

            node_provider = environment_definition.node_provider

            nodes = node_provider.list(environment_definition.all_credentials, lambda x: node_predicates.running_in_env(dynamic_env_name, env_template_name)(x))

            hello_world_node = [x for x in nodes if 'hello_world' in x.get_services()].pop()

            status, output = commands.getstatusoutput("curl -s %s:8081/healthcheck" % hello_world_node.address().dns_name)

            self.assertEqual(status, 0)
            self.assertEqual(output, "* Apache: OK\n* deadlocks: OK")

    def test_can_create_elb_for_a_service(self):
        with settings(credentials_dir="credentials"):
            self.remove_existing_hello_world_elb('elb_integration', 'hello_world')

            dynamic_env_name = "test_can_create_a_load_balancer_for_a_service"+str(int(round(time.time() * 1000)))
            env_template_name = "elb_integration"
            self.env_to_shut_down.update({env_template_name: dynamic_env_name})

            environment_definition = launch(env_template=env_template_name, env_name=dynamic_env_name, config_dir="samples", property_file="build_credentials/phoenix.ini")
            node_provider = environment_definition.node_provider
            nodes = node_provider.list(environment_definition.all_credentials, lambda x: node_predicates.running_in_env(dynamic_env_name, env_template_name)(x))
            node_provider = environment_definition.node_provider
            node = [x for x in nodes if 'hello_world' in x.get_services()].pop()

            conn = self.get_connection_for_region(node.region().name, node_provider.public_api_key, node_provider.private_api_key)

            hook_elb_name = environment_definition.service_lifecycle_hooks['hello_world'][0].elb_name
            load_balancer = conn.get_all_load_balancers(load_balancer_names=[hook_elb_name])[0]

#            self.assertEqual(load_balancer.dns_name, node.address().get_dns_name()) TODO: make sure the node address dns matches with the elb dns

            status, output = commands.getstatusoutput("curl -s %s:8081/healthcheck" % load_balancer.dns_name)

            self.assertEqual(status, 0)
            self.assertEqual(output, "* Apache: OK\n* deadlocks: OK")



    def get_running_node(self, environment_definition, env_def_name, environment_name, node_provider):
        nodes = node_provider.list(environment_definition.all_credentials,
            lambda x: node_predicates.running_in_env(environment_name, env_def_name)(x))
        self.assertEquals(len(nodes), 1)
        return nodes[0]

    def test_should_not_relaunch_nodes_if_not_needed(self):
        with settings(credentials_dir="credentials"):
            dynamic_env_name = "test_should_not_relaunch_nodes_if_not_needed_"+str(int(round(time.time() * 1000)))
            env_template_name = 'development'
            self.env_to_shut_down.update({env_template_name: dynamic_env_name})
            environment_definition = launch(env_template=env_template_name, env_name=dynamic_env_name, config_dir="samples", property_file="build_credentials/phoenix.ini")
            node_provider = environment_definition.node_provider

            original_node_id = self.get_running_node(environment_definition, env_template_name, dynamic_env_name, node_provider).id()

            launch(env_template=env_template_name, env_name=dynamic_env_name, config_dir="samples", property_file="build_credentials/phoenix.ini")

            self.assertEqual(original_node_id, self.get_running_node(environment_definition, env_template_name, dynamic_env_name, node_provider).id())

    def test_can_launch_single_apache_node(self):
        with settings(credentials_dir="credentials"):
            dynamic_env_name = "test_can_launch_single_apache_node_on_a_specific_az_"+str(int(round(time.time() * 1000)))
            env_template_name = "development"
            self.env_to_shut_down.update({env_template_name: dynamic_env_name})
            environment_definition = launch(env_template=env_template_name, env_name=dynamic_env_name, config_dir="samples", property_file="build_credentials/phoenix.ini")
            node_provider = environment_definition.node_provider

            launched_node = self.get_running_node(environment_definition, env_template_name, dynamic_env_name, node_provider)
            apache_address = launched_node.address().get_service_address('apache')

            b = twill.get_browser()
            b.go("http://%s/" % apache_address[0])

            logging.getLogger("phoenix").info("Got address %s" % apache_address)
            self.assertEqual(b.get_code(), 200)

    def tearDown(self):
        for env_template, env_name in self.env_to_shut_down.items() :
            logger.info("Terminating environment: template %s, name %s" % (env_template, env_name))
            logger.info(commands.getoutput("cd phoenix && ./pho terminate_environment --env_template %s --env_name %s --property_file %s" % (env_template, env_name, "../build_credentials/phoenix.ini")))
        self.env_to_shut_down.clear()

if __name__ == '__main__':
    unittest.main()