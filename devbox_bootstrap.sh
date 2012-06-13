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

PUPPET_CMD="puppet apply puppet/manifests/dev_box.pp --modulepath=puppet/manifests"
RVM_INSTALLED=`which rvm 2> /dev/null`
if [ $? -eq 0 ]; then
  PUPPET_CMD="rvm default do $PUPPET_CMD"
fi

$PUPPET_CMD

