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

import os.path as path
import phoenix


def copy_template(dest_dir, template_name):
    # This looks daft, but we want to allow for values to be templated via pystache or similar...
    with(open('%s/%s' % (path.dirname(phoenix.templates.__file__), template_name), 'r')) as env_template:
        filecontents = env_template.read()

        dest_filename = template_name.replace('_template', '')

        with(open(path.join(dest_dir, dest_filename), 'w')) as dest_file:
            dest_file.write(filecontents)