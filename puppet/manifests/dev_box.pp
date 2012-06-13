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

package { 'fabric':
  ensure          => '1.4.1',
  provider        => 'pip',
}

package { 'nose':
        ensure => '1.1.2',
        provider => 'pip',
}

package { 'NoseXUnit':
        ensure => '0.3.3',
        provider => 'pip',
}

package { 'pystache':
         ensure => '0.5.2',
         provider => 'pip',
}

package { 'pyyaml':
        ensure => '3.08',
        provider => 'pip',
}

package { 'boto':
        ensure => '2.3.0',
        provider => 'pip',
}

package { 'texttable':
        ensure => '0.8.1',
        provider => 'pip',
}

package { 'pylint':
        ensure => '0.25.1',
        provider => 'pip',
}

package { 'mechanize':
        ensure => '0.2.5',
        provider => 'pip',
}

package { 'twill':
        ensure => '0.9',
        provider => 'pip',
}

package { 'mockito':
        ensure => '0.5.1',
        provider => 'pip',
}

package { 'ssh':
        ensure => '1.7.12',
        provider => 'pip',
}

package { 'virtualenv':
    ensure => '1.7.1.2',
    provider => 'pip',
}

package { 'virtualenvwrapper':
    ensure => '3.4',
    provider => 'pip',
}

group { 'puppet':
      ensure => present,
}