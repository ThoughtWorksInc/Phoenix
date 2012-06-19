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

import logging
import fabric.state


phoenix_python_logging_level_map={'debug': logging.DEBUG, 'info': logging.INFO, 'quiet' : logging.WARN}

def set_logging_level(level):
    logging_level = logging.INFO
    if level in phoenix_python_logging_level_map.keys() :
        logging_level = phoenix_python_logging_level_map[level]
    logger.setLevel(logging_level)
    logging_level_name = logging.getLevelName(logger.level)
    logger.info("Logging level set to "+logging_level_name+". Log messages at "+ logging_level_name +" and above will be printed to console")
    logging.getLogger('boto').setLevel(logger.getEffectiveLevel())
    logging.getLogger('ssh.transport').setLevel(logger.getEffectiveLevel())

def set_fabric_level(level):
    # see http://docs.fabfile.org/en/1.4.1/usage/output_controls.html for more details
    if level == 'debug':
        fabric.state.output["debug"] = True
        fabric.state.output["running"] = True
        fabric.state.output["stdout"] = True
        fabric.state.output["stderr"] = True
        fabric.state.output["user"] = True
    if level == 'info':
        fabric.state.output["debug"] = False
        fabric.state.output["running"] = False
        fabric.state.output["stdout"] = True
        fabric.state.output["stderr"] = True
        fabric.state.output["user"] = True
    if level == 'quiet':
        fabric.state.output["debug"] = False
        fabric.state.output["running"] = False
        fabric.state.output["stdout"] = False
        fabric.state.output["stderr"] = True
        fabric.state.output["user"] = False

def set_logging_output(level):
    set_logging_level(level)
    set_fabric_level(level)

# Default logging
logger = logging.getLogger('phoenix')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s'))
logger.addHandler(handler)
logging.getLogger('boto').setLevel(logger.getEffectiveLevel())
logging.getLogger('ssh.transport').setLevel(logger.getEffectiveLevel())

set_fabric_level('info')


