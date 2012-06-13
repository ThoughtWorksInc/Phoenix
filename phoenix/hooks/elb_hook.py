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
import boto

from boto.ec2.elb.healthcheck import HealthCheck
from boto.regioninfo import RegionInfo
from phoenix.plogging import logger


class ELBHook():
    def __init__(self, elb_name, public_api_key, private_api_key, app_to_elb_ports, app_healthcheck_target):
        self.elb_name = elb_name
        self.public_api_key = public_api_key
        self.private_api_key = private_api_key
        self.app_to_elb_ports = app_to_elb_ports
        self.app_healthcheck_target = app_healthcheck_target

    def get_elb_mappings(self, connectivities):
        elb_ports = []
        for connectivity in connectivities:
            protocol = connectivity['protocol']
            ports = connectivity['ports']
            for port in ports:
                elb_port = self.app_to_elb_ports[port]
                elb_ports.append((elb_port, port, protocol))
        return elb_ports

    def get_connection_for_region(self, region):
        reg = RegionInfo(
            name=region,
            endpoint='elasticloadbalancing.'+region+'.amazonaws.com'
        )
        conn = boto.connect_elb(
            aws_access_key_id=self.public_api_key,
            aws_secret_access_key=self.private_api_key,
            region=reg
        )
        return conn

    def service_installed(self, service_name, node, connectivities):
        conn = self.get_connection_for_region(node.region().name)
        try:
            load_balancer = conn.get_all_load_balancers(load_balancer_names=[self.elb_name])[0]
            logger.info('Existing load balancer found with name %s' %self.elb_name)
        except:
            load_balancer = None

        if load_balancer is None:
            logger.info('Creating a new load balancer: '+ self.elb_name)
            elb_ports = self.get_elb_mappings(connectivities)
            load_balancer = conn.create_load_balancer(self.elb_name, str(node.placement()), elb_ports)

        health_check_address = self.app_healthcheck_target
        hc = HealthCheck(
            interval=20,
            healthy_threshold=3,
            unhealthy_threshold=5,
            target=health_check_address
        )
        load_balancer.configure_health_check(hc)
        logger.info('Registering node id %s for availability zone %s' %(node.id(), node.placement()))
        load_balancer.enable_zones([node.placement()])
        load_balancer.register_instances([node.id()])

    def service_terminated(self, service_name, node):
        conn = self.get_connection_for_region(node.region().name)
        try:
            load_balancer = conn.get_all_load_balancers(load_balancer_names=[self.elb_name])[0]
            logger.info('Existing load balancer found with name %s' %self.elb_name)
            load_balancer.degregister_instances([node.id()])
        except:
            pass


