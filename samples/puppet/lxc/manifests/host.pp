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

class lxc::host {
  package {
    ['lxc', 'debootstrap', 'bridge-utils', 'dnsmasq']:
      ensure => 'present',
  }

  # Needs persisting
  exec {'bridge-add':
    command => '/sbin/brctl addbr br0',
    unless => '/sbin/brctl show | grep br0',
    require => Package['bridge-utils'],
  }

  # Needs persisting
  exec {'bridge-set-fd':
    command => '/sbin/brctl setfd br0 0',
    unless => "/sbin/brctl showstp br0 | grep 'forward delay' | awk '{print $3}' | grep '0\\.00'",
    require => [Exec['bridge-add'], Package['bridge-utils']],
  }

  # Needs persisting
  exec {'bridge-bring-up':
    command => '/sbin/ifconfig br0 192.168.3.1 up',
    unless => "/bin/sh -c '/sbin/ifconfig br0 | grep UP' && /bin/sh -c '/sbin/ifconfig br0 | grep 192\\.168\\.3\\.1'",
    require => Exec['bridge-add'],
  }

  # Needs persisting
  exec {'bridge-nat':
    command => '/sbin/iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE',
    unless => '/sbin/iptables -t nat -L POSTROUTING -v | grep eth0 | grep MASQUERADE',
  }

  # Needs persisting
  exec {'bridge-enable-fowarding':
    command => '/sbin/sysctl -w net.ipv4.ip_forward=1',
    unless => '/sbin/sysctl net.ipv4.ip_forward | grep 1',
  }

  file {'/etc/dnsmasq.d/lxc.bridge.conf':
    source => 'puppet:///modules/lxc/dnsmasq.conf',
    require => Package['dnsmasq'],
    notify => Service['dnsmasq'],
  }

  service {'dnsmasq':
    hasrestart => true,
    require => Package['dnsmasq'],
  }

  file {'/etc/dhcp/dhclient.conf':
    source => 'puppet:///modules/lxc/dhclient.conf',
  }

  # Needs persisting
  exec {'dhcp-configure':
    command => '/sbin/dhclient -e IF_METRIC=100 -pf /var/run/dhclient.eth0.pid -lf /var/lib/dhcp/dhclient.eth0.leases eth0',
    refreshonly => true,
    subscribe => File['/etc/dhcp/dhclient.conf'],
    notify => Service['dnsmasq'],
  }

  file {'/etc/default/lxc':
    source => 'puppet:///modules/lxc/lxc.default',
  }

  file {'/etc/lxc/lxc.conf':
    source => 'puppet:///modules/lxc/lxc.conf',
    require => Package['lxc'],
  }
}
