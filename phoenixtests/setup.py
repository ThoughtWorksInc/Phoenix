#!/usr/bin/env python
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

from distutils.core import setup
import os

if os.environ.has_key('GO_PIPELINE_LABEL'):
    version = os.environ['GO_PIPELINE_LABEL']
else:
    version = '0.0.1-SNAPSHOT'

setup(
    name='Phoenix-Tests',
    version=version,
    author='ThoughtWorks',
    author_email='snewman@thoughtworks.com',
    package_dir={'phoenixtests': ''},
    packages=['phoenixtests', "phoenixtests.integration_aws_tests", "phoenixtests.integration_lxc_tests"],
    url='http://thoughtworks.com/',
    install_requires=[
        "twill >= 0.9",
        "mechanize >= 0.2.5",
        "mockito >= 0.5.1",
        "pystache >= 0.5.2",
    ],
)
