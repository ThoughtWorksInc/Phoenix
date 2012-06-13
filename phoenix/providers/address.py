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

class Address: # TODO: is there a better name for this object?
    def __init__(self, dns_name, services):
        """
        dns_name: dns_name where the services reside
        services: dictionary of services installed on the node and their ports
        ie: { 'apache': {80: 80, 81:81} }
        """
        self.dns_name = dns_name
        self.service_mappings = services

    def get_ports(self, service_name):
        if not isinstance(self.service_mappings, dict):
            return None
        return [str(x) for x in self.service_mappings[service_name].values()]

    def get_service_address(self, service_name):
        return ["%s:%s" % (self.dns_name, port) for port in self.get_ports(service_name)]

    def get_service_mappings(self):
        return self.service_mappings

    def __str__(self):
        return "dns: %s\nports: %s" % (self.dns_name, [self.get_ports(x) for x in self.service_mappings])

    def get_dns_name(self):
        return self.dns_name

