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

from phoenix.utilities.utility import get_class_from_fully_qualified_string

def node_definition_from_map(node_definition, all_credentials):
    node_class_name = node_definition['type']
    fq_class = get_class_from_fully_qualified_string(node_class_name)

    #We don't need the 'type' in the definition map...
    node_definition.pop('type')
    node_def_object = fq_class(**node_definition)

    if 'credentials_name' in node_definition.keys():
        node_def_object.add_credentials(all_credentials)
    return node_def_object
