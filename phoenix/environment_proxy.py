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

from phoenix.environment_description import Location

class AWSRunningEnvironmentProxy():
    def __init__(self, aws_node_provider):
        self.aws_node_provider = aws_node_provider

    def get_nodes(self):
        return self.aws_node_provider.list()

    def get_locations(self):
        return {'us-east-1': Location(self.get_nodes())}
