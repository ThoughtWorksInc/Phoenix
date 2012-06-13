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

class FakeServiceConfigurator:

    def validate(self, service_name, service_definition, abs_path_to_conf, error_list):
        pass

    def config(self, node, service_definition, settings):
        def prepare_node():
            node.run_command('running')
            node.upload_file('settings-' + str(settings))

        node.wait_for_ready(prepare_node, 15)
