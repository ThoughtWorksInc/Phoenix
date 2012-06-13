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

import unittest
from boto.sts import credentials
from mockito.mocking import mock
from mockito.mockito import verifyZeroInteractions, when
from phoenix.providers import node_predicates
from phoenix.providers.noop_provider import NoopNodeProvider
from phoenix.service_definition import DynamicDictionary


class NoopProviderTests(unittest.TestCase):
    def setUp(self):
        self.inner_provider = mock()
        self.node_definition = mock()
        self.sut = NoopNodeProvider(self.inner_provider)

    def test_should_not_call_inner_provider_on_state_changing_events(self):
        self.sut.start(None, None, None)
        self.sut.shutdown(None)
        verifyZeroInteractions(self.inner_provider)

    def test_should_add_actions_to_noop_list_for_state_changing_events(self):
        self.sut.start(self.node_definition, "env_name", "env_def_name")
        self.sut.shutdown("node_id")
        self.assertEqual(2, len(self.sut.actions))

    def test_should_capture_actions_on_returned_nodes_from_start(self):
        new_node = self.sut.start(self.node_definition, "env_name", "env_def_name")
        new_node.run_command("do something")
        new_node.upload_file("file", "destination")
        new_node.add_service_to_tags("service_name", [DynamicDictionary({'ports':[80]})])
        self.assertEqual(4, len(self.sut.actions))


    def test_should_capture_actions_on_returned_nodes_from_list(self):
        node = create_node()
        when(self.inner_provider).list('cred', node_predicates.all_nodes).thenReturn([node])

        new_node = self.sut.list('cred')[0]
        new_node.run_command("do something")
        new_node.upload_file("file", "destination")
        new_node.add_service_to_tags("service_name", [DynamicDictionary({'ports' : [80]})])
        self.assertEqual(3, len(self.sut.actions))

    def test_should_return_new_nodes_in_list_function(self):
        existing_node = create_node()
        when(self.inner_provider).list('cred', node_predicates.all_nodes).thenReturn([existing_node])
        new_node = self.sut.start(None,None,None)
        nodes = self.sut.list('cred')
        self.assertIn(new_node, nodes)

    def test_should_not_return_terminated_nodes(self):
        existing_node = create_node()
        when(self.inner_provider).list('cred', node_predicates.all_nodes).thenReturn([existing_node])
        self.sut.shutdown("id")
        nodes = self.sut.list('cred')
        self.assertEqual(0, len(nodes))


def create_node():
    node = mock()
    when(node).id().thenReturn("id")
    when(node).tags().thenReturn({})
    when(node).state().thenReturn('running')
    when(node).address().thenReturn(DynamicDictionary({'dns_name': 'dns_name'}))
    return node
