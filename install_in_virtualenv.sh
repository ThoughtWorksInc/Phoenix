#!/bin/bash
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


if [ $# -ne 1 ]; then
  if [ -n "${GO_PIPELINE_LABEL:+x}" ]; then
    echo "Creating virtual_env for $GO_PIPELINE_LABEL"
    export virt_env_location=/tmp/$GO_PIPELINE_LABEL
  else
    echo "No label is given for the virtual environment to use, will default to a random name"
    export virt_env_location=/tmp/$RANDOM
  fi
else
  export virt_env_location=/tmp/$1
fi

echo "Installing Phoenix to $virt_env_location"

virtualenv --no-site-packages -p `which python2.7` $virt_env_location
source $virt_env_location/bin/activate
pip install dist/Phoenix-*.tar.gz
$virt_env_location/bin/pho -h
