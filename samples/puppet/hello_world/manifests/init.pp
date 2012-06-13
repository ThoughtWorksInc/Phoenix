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

class hello_world() {

package{'openjdk-6-jdk':
    ensure => true
   }

file {'/tmp/hello-world.yml':
    content => template('hello_world/hello-world.yml')
    }

exec { 'run helloworld':
    command => 'nohup java -jar puppet/my-project-0.0.1-SNAPSHOT.jar server /tmp/hello-world.yml &',
    path => ['/usr/bin'],
    require => [File['/tmp/hello-world.yml'],Package['openjdk-6-jdk']]
    }
}
