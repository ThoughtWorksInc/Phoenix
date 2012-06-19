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
import shutil

from fabric.api import local, task, execute
import os.path
from fabric.utils import abort

@task(default=True)
def full_build(test_output="", noseflags=""):
    """Default task - this runs pylint, all tests, and finally creates a distributable package"""
    execute(clean)
    execute(pylint_for_build)
    execute(fast_tests, test_output=test_output, noseflags=noseflags)
    execute(package)

@task
def clean():
    shutil.rmtree('dist', ignore_errors=True)
    shutil.rmtree('test_results', ignore_errors=True)

    def rm_manifest(dirname, names):
      if 'MANIFEST' in names:
        os.remove(os.path.join(dirname, 'MANIFEST'))
        print("Removed MANIFEST from %s" % dirname)

    os.path.walk(".", lambda arg, dirname, names: rm_manifest(dirname, names), 'x')

@task
def package():
    """Creates a local pip package"""
    local("cd phoenix && python2.7 setup.py sdist --dist-dir=../dist")
    local("cd phoenixtests && python2.7 setup.py sdist --dist-dir=../dist")

    print('=================')
    print('| Package built |')
    print('=================')
    print("Do `sudo pip install dist/Phoenix-x.y.z.tar.gz` to install")

@task
def pylint_for_build():
    """Runs pylint, but only fails if errors are found"""
    local('pylint --rcfile="pylint.config" --output-format=colorized --include-ids=y --reports=n phoenix -E')

@task
def pylint():
    """Runs a detailed pylint report, including all levels of messages"""
    local('pylint --rcfile="pylint.config" --include-ids=y --reports=n phoenix')

@task
def tests(noseflags=""):
    """Runs all tests. You can pass flags to nose using noseflags=... For example -s is useful to ensure
    that stdout is not captured"""
    local('nosetests %s phoenixtests' % noseflags)

@task
def fast_tests(noseflags="", test_output='txt'):
    """Runs fasts tests.
    You can pass flags to nose using noseflags=... For example -s is useful to ensure
    that stdout is not captured. To produce test output in JUNit-style XML, use test_output=xml"""

    if test_output == 'xml':
        noseflags = noseflags + ' --with-nosexunit --core-target=test_results'

    local('nosetests %s phoenixtests -e "integration"' % noseflags)

def running_under_go():
    return os.environ.has_key('GO_PIPELINE_LABEL')

def check_for_phoenix_ini():
    if not os.path.isdir("build_credentials"):
        if running_under_go():
            local("git clone git@github-tech-lab:ThoughtWorksInc/EU-Techlab-Credentials.git build_credentials")
        else:
            local("git clone git@github.com:ThoughtWorksInc/EU-Techlab-Credentials.git build_credentials")
    else:
        local("cd build_credentials && git pull")

    if not os.path.isdir("build_credentials"):
        abort(
            "Build credentials directory - make sure you create a phoenix.ini file in a directory called build_credentials to run these tests'")
    elif not os.path.isfile(os.path.join(os.path.abspath("build_credentials"), "phoenix.ini")):
        abort(
            "phoenix.ini not found - make sure you create a phoenix.ini file in a directory called build_credentials to run these tests'")


@task
def aws_integration_tests(noseflags="", test_output='txt'):
    """Runs all AWS integration tests. You can pass flags to nose using noseflags=... For example -s is useful to ensure
    that stdout is not captured"""
    check_for_phoenix_ini()

    if test_output == 'xml':
        noseflags = noseflags + ' --with-nosexunit --core-target=test_results'

    local('nosetests %s phoenixtests -e "integration_lxc_tests" -e "unit_tests"' % noseflags)

@task
def lxc_integration_tests(noseflags="", test_output='txt'):
    """Runs all LXC integration tests. You can pass flags to nose using noseflags=... For example -s is useful to ensure
    that stdout is not captured"""
    check_for_phoenix_ini()

    if test_output == 'xml':
        noseflags = noseflags + ' --with-nosexunit --core-target=test_results'

    local('nosetests %s phoenixtests-e "integration_aws_tests" -e "unit_tests"' % noseflags)

@task
def run_web():
    local("cd phoenix && sh phoweb")
