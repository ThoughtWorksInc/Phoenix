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
import tempfile
import unittest
import os.path
from fabric.context_managers import settings
from fabric.operations import run
import yaml
from phoenix.configurators import PuppetServiceConfigurator
from phoenix.fabfile import Credentials, launch
from phoenix.providers import LXCNodeProvider, node_predicates, LXCNodeDefinition
from phoenix.service_definition import ServiceDefinition, DynamicDictionary

service_definition = ServiceDefinition("apache", {"ports": [80], 'puppet_module_directory':"puppet", 'puppet_manifest': 'apache.pp'},
    PuppetServiceConfigurator, "samples/")

lxc_host_name = 'ec2-184-72-150-211.compute-1.amazonaws.com'

class LXCProviderTests(unittest.TestCase):

    def test_should_be_able_to_create_node(self):

        provider = get_provider()
        node1 = start_node(provider)
        node2 = start_node(provider)

        with settings(host_string=lxc_host_name, user='ubuntu', key_filename='credentials/us-east-test.pem'):
            output = yaml.load(run("sudo lxc-info -n %s" % node1.id()))

        self.assertEqual('RUNNING', output['state'])

        nodes = provider.list(None,None)
        self.assertIn(node1, nodes)
        self.assertIn(node2, nodes)

        provider.shutdown(node1.id())
        provider.shutdown(node2.id())

        with settings(host_string=lxc_host_name, user='ubuntu', key_filename='credentials/us-east-test.pem'):
            output = yaml.load(run("sudo lxc-info -n %s" % node1.id()).replace("'", ''))

        self.assertEqual('STOPPED', output['state'])

    def test_should_be_able_to_show_state(self):
        provider = get_provider()
        node = start_node(provider)

        self.assertEqual('running', node.state())
        node.add_service_to_tags('hello_world', [DynamicDictionary({ 'ports' : [80]})])
        node.add_service_to_tags('mongo', [DynamicDictionary({ 'ports' : [80]})])

        self.assertIn('hello_world', node.get_services())
        self.assertIn('mongo', node.get_services())
        provider.shutdown(node.id())

    def test_should_be_able_to_run_command(self):
        provider = get_provider()
        node = start_node(provider)
        output = node.run_command('ps')
        self.assertIn("upstart-socket-", output)
        provider.shutdown(node.id())

    def test_should_be_able_to_upload_file(self):
        provider = get_provider()
        node = start_node(provider)

        with tempfile.NamedTemporaryFile() as f:
            node.upload_file(f.name, "/tmp")
            file_name = f.name.split('/')[-1]

        self.assertEqual(file_name, node.run_command("ls /tmp").strip())
        provider.shutdown(node.id())

    def test_should_match_definition(self):
        provider = get_provider()
        node = start_node(provider)

        node.add_service_to_tags('hello_world', [DynamicDictionary({ 'ports' : [80]})])

        self.assertTrue(node.matches_definition(DynamicDictionary({'services': [ 'hello_world' ], 'template': 'ubuntu' })))

    def test_add_service_to_tags_should_map_a_single_port_to_another_port(self):
        provider = get_provider()
        node = start_node(provider)

        configurator = PuppetServiceConfigurator()
        configurator.config(node, service_definition, { 'settings' : {}})
        node.add_service_to_tags('apache', [DynamicDictionary({'ports':[ 80 ]})])

        address = node.address().get_service_address('apache')[0]
        status,output = commands.getstatusoutput("curl -s %s" % address)

        self.assertEqual(expected, output)
        provider.shutdown(node.id())

    def test_full_end_to_end_integration_test(self):
        with settings(credentials_dir="credentials"):
            environment_definition = launch(env_template="lxc_hello_world", env_name="auto", config_dir="samples")

            node_provider = environment_definition.node_provider

            nodes = node_provider.list(environment_definition.all_credentials, lambda x: node_predicates.running_in_env('auto','lxc_hello_world')(x))

            hello_world_node = [x for x in nodes if 'hello_world' in x.get_services()].pop()

            status, output = commands.getstatusoutput("curl -s %s/healthcheck" % hello_world_node.address().get_service_address('hello_world')[1])

            self.assertEqual(status, 0)
            self.assertEqual(output, "* Apache: OK\n* deadlocks: OK")

    def tearDown(self):
        get_provider()._terminate_all()

expected = """<html><body><h1>It works!</h1>
<p>This is the default web page for this server.</p>
<p>The web server software is running but no content has been added, yet.</p>
</body></html>"""

def get_provider():
    # This will only work when running from nose - really, we should just invoke the fab
    # command directly for these integration tests, and load the credentials from the
    # config directory
    current_dir = os.path.abspath(os.path.curdir)
    credentials = Credentials('test', {'private_key' : 'us-east-test.pem', 'login' : 'ubuntu'}, os.path.join(current_dir, "samples/"))
    provider = LXCNodeProvider(credentials, host_name=lxc_host_name)
    return provider

def start_node(provider):
    node = provider.start(LXCNodeDefinition('ubuntu'), 'env', 'unit_test')
    node.wait_for_ready(lambda : None, 15)
    return node

if __name__ == '__main__':
    unittest.main()
