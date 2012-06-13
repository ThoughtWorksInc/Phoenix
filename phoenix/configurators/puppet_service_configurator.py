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

import os
from phoenix.plogging import logger

class PuppetServiceConfigurator:

    def validate(self, service_name, service_definition, abs_path_to_conf, error_list):

        if abs_path_to_conf is None:
            error_list.append("Path to config must be set")
            return False

        if not os.path.exists(abs_path_to_conf):
            error_list.append("Config path '%s' not found" % abs_path_to_conf)
            return False

        if not 'puppet_module_directory' in service_definition:
            error_list.append("Key 'puppet_module_directory' is not defined in services configuration of service: '%s'" % service_name)
            return False

        abs_path_to_puppet_module_directory = os.path.join(abs_path_to_conf, service_definition['puppet_module_directory'])
        if not os.path.exists(abs_path_to_puppet_module_directory):
            error_list.append("Puppet module directory '%s' not found" % abs_path_to_puppet_module_directory)
            return False

        if not 'puppet_manifest' in service_definition:
            error_list.append("Key 'puppet_manifest' is not defined in services configuration of service: '%s'" % service_name)
            return False

        abs_path_to_puppet_manifest = os.path.join(abs_path_to_puppet_module_directory, service_definition['puppet_manifest'])
        if not os.path.exists(abs_path_to_puppet_manifest):
            error_list.append("Puppet manifest '%s' not found" % abs_path_to_puppet_manifest)
            return False

        return True


    def config(self, node, service_definition, service_to_dns):
        ConfigureService(node, service_definition, service_to_dns).configure()

class ConfigureService():

    def __init__(self, node, service_definition, service_to_dns):
        self.node = node
        self.service_definition = service_definition
        self.service_to_dns = service_to_dns

    def configure(self):
        self._bootstrap_puppet()
        self._upload_artifacts()
        self._configure_service()

    def _bootstrap_puppet(self):
        puppet_status = self.node.run_command("dpkg-query -W -f='${Status} ${Version}\n' puppet", warn_only=True)

        if "installed" in puppet_status:
            logger.debug("Puppet already bootstrapped")
        else:
            logger.debug("Bootstrapping puppet")
            self.node.run_command('sudo apt-get update && sudo apt-get install puppet -y')

    def _upload_artifacts(self):
        logger.debug('Uploading artifacts')
        tar_file = self.service_definition.bundle("puppet_module_directory", "%s_puppet_bundle.tgz" % self.service_definition.name)
        self.node.upload_file(tar_file, "/tmp")
        remote_tarfile_path = "/tmp/%s" % os.path.basename(tar_file)
        self.node.run_command('tar xvfz %s' % remote_tarfile_path)

    def _configure_service(self):
        facter_settings = ""
        for service_name, node_addresses in self.service_to_dns['settings'].items():
            facter_settings += ("FACTER_%s=%s " % (service_name, ",".join(node_addresses)))

        puppet_manifest = os.path.join(self.service_definition.puppet_module_directory, self.service_definition.puppet_manifest)
        command_to_run = "sudo %s puppet apply --modulepath=puppet %s" % (facter_settings, puppet_manifest)
        print command_to_run
        self.node.run_command(command_to_run)
