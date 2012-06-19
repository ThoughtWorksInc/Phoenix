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
import ConfigParser

from functools import partial
import os
import os.path as path
from contextlib import contextmanager

from fabric.utils import error
import pystache
from texttable import Texttable
import yaml

from environment_definition import environment_definitions_from_yaml
from environment_definition import list_environments
from phoenix.environment_description import SimpleTextEnvironmentDescriber, TextTableEnvironmentDescriber
from phoenix.plogging import logger
from phoenix.templates.templating import copy_template
from providers.aws_provider import AWSNodeProvider
import service_definition as service_definitions

CHOICES = 'choices'
REQUIRED = 'required'
ACTION = 'action'
DEFAULT = 'default'
HELP = 'help'

DEFAULT_ENVIRONMENT="../samples"

RUNNING_ENVIRONMENT_OPTION = ('--env_name', {HELP:'The name of the running environment', REQUIRED:True})

ENVIRONMENT_TEMPLATE_OPTION = ('--env_template', {HELP:'The name of the environment template', REQUIRED:True})

CONFIG_DIR_OPTION = ('--config_dir',
                         {DEFAULT: DEFAULT_ENVIRONMENT,
                          HELP: 'Runs Phoenix in debug mode, resulting in more detailed logging both from Phoenix as well as echoing all shell commands sent to nodes'})

PROPERTY_FILE_OPTION = ('--property_file',
    {DEFAULT: os.path.join(os.path.abspath("."), "phoenix.ini"),
     HELP: "Location of a properties file in INI format containing values to template in environment configuration. Useful for \
           externalising things like AWS public/private API keys. Defaults to 'phoenix.ini' in the current working directory"})


CLI_FUNCS = {}

class cliCall(object):

    def __init__(self, *args):
        self.args = args

    def __call__(self, f):

        def add_arguments(subparser):
            """Expects a subparser from argparse (e.g. result of calling
            subparsers = parser.add_subparsers()"""
            parser = subparser.add_parser(f.__name__, help=f.__doc__)

            for arg, options in self.args:
                if not options.has_key(ACTION):
                    options[ACTION] = 'store'

                parser.add_argument(arg, **options)

            parser.set_defaults(func=f)

        CLI_FUNCS[f.__name__] = (f, add_arguments)

        def wrapped_f(**args):
            return f(**args)

        return wrapped_f


@cliCall(("--dest_dir",{HELP: "Location where you want the generated template to be stored"}))
def generate_skeleton(dest_dir):
    """Generates an example skeleton environment"""
    if path.exists(dest_dir) and path.isdir(dest_dir):
        copy_template(dest_dir, 'environment_definitions_template.yaml')
        copy_template(dest_dir, 'credentials_template.yaml')
        copy_template(dest_dir, 'service_definitions_template.yaml')

    else:
        print("Directory %s must exist and be a valid directory" % dest_dir)


@cliCall(CONFIG_DIR_OPTION, ENVIRONMENT_TEMPLATE_OPTION, RUNNING_ENVIRONMENT_OPTION, PROPERTY_FILE_OPTION)
def list_nodes_in_environment(env_template=None, env_name=None, config_dir=DEFAULT_ENVIRONMENT, property_file=None):
    """Lists nodes in a named environment"""
    with env_conf_from_dir(config_dir, env_name, property_file) as env_defs:
        template_ = env_defs[env_template]
        _render_table(template_.list_nodes())


def describe_running_environment(config_dir, env_def, env_name, env_template, formatter):
    provider = env_def.get_node_provider()
    running_env = provider.get_running_environment(env_name, env_template, _credentials_from_path(config_dir))
    return formatter.describe(running_env)


def _describer_for_format(format):
    if format == 'txt':
        return SimpleTextEnvironmentDescriber()
    elif format == 'table':
        return TextTableEnvironmentDescriber()
    else:
        raise StandardError('Unsupported format %s' % format)


@cliCall(CONFIG_DIR_OPTION, ENVIRONMENT_TEMPLATE_OPTION, RUNNING_ENVIRONMENT_OPTION, PROPERTY_FILE_OPTION,
    ("--format", {HELP:"Which format do you want the description in. Defaults to YAML",
                  DEFAULT:"txt",
                  CHOICES:['yaml', 'txt', 'table']}))
def show_running_environment(env_template=None, env_name=None, config_dir=DEFAULT_ENVIRONMENT, format=None, property_file=None):
    """Show an environment with its running nodes"""
    with env_conf_from_dir(config_dir, env_template, property_file) as env_def:
        describer = _describer_for_format(format)

        if not env_def.has_key(env_template):
            raise StandardError("Cannot find template %s" % env_template)

        print describe_running_environment(config_dir, env_def[env_template], env_name, env_template, describer)


@cliCall(CONFIG_DIR_OPTION, ENVIRONMENT_TEMPLATE_OPTION, PROPERTY_FILE_OPTION,
    ("--format", {HELP:"Which format do you want the description in. Defaults to YAML",
                  DEFAULT:"yaml",
                  CHOICES:['yaml', 'txt']}))
def describe_definition(env_template=None, config_dir=DEFAULT_ENVIRONMENT, format=None, property_file=None):
    """Show an environment definition with all its nodes"""
    with env_conf_from_dir(config_dir, env_template, property_file) as env_def:
        provider = env_def[env_template].get_node_provider()
        translator = provider.get_env_definition_translator()
        environment = translator.translate(env_def, env_template, service_defs_from_dir(config_dir))
        describer = _describer_for_format(format)
        print describer.describe(environment)

def get_list_of_environment_definitions(config_dir, property_file=None):
    """List available environment definitions with all their nodes"""
    environment_definitions = []
    with env_conf_from_dir(config_dir, 'dummy_name', property_file) as env_defs:
        for env_template, env_vals in env_defs.items() :
            translator = env_vals.get_node_provider().get_env_definition_translator()
            environment = translator.translate(env_defs, env_template, service_defs_from_dir(config_dir))
            environment.name = env_template # resetting the name to env_template as we do not have an env name
            environment_definitions.append(environment)

        return environment_definitions


@cliCall(CONFIG_DIR_OPTION, PROPERTY_FILE_OPTION)
def list_definitions(config_dir=DEFAULT_ENVIRONMENT, property_file=None):
    formatter = TextTableEnvironmentDescriber()

    for env_def in get_list_of_environment_definitions(config_dir, property_file):
        print formatter.describe(env_def)

@cliCall(CONFIG_DIR_OPTION, ENVIRONMENT_TEMPLATE_OPTION, RUNNING_ENVIRONMENT_OPTION, PROPERTY_FILE_OPTION)
def terminate_environment(env_template=None, env_name=None, config_dir=DEFAULT_ENVIRONMENT, property_file=None):
    """Shuts down all nodes associated with a given environment"""
    with env_conf_from_dir(config_dir,  env_name, property_file) as env_defs:
        env_defs[env_template].terminate_all() # TODO: let's confirm this shall we?

@cliCall(CONFIG_DIR_OPTION, ENVIRONMENT_TEMPLATE_OPTION,
    RUNNING_ENVIRONMENT_OPTION, PROPERTY_FILE_OPTION,
    ('--noop', {REQUIRED:False, ACTION:'store_true', HELP:"If no-op is set, then the environment will not be launched or changed, rather Phoenix will report \
                      on what would be done"}))
def launch(env_template=None, env_name=None, config_dir=DEFAULT_ENVIRONMENT, noop=False, property_file=None):
    """Launches a new environment, or applies changes made to an existing environment"""
    with env_conf_from_dir(config_dir, env_name, property_file, noop=noop) as env_defs:
        if noop:
            logger.info("Running in NOOP mode - no changes will be made to your system")

        environment_definition = env_defs[env_template]
        environment_definition.launch()
        if noop:
            print environment_definition.node_provider.noop_actions_string()
        else:
            print describe_running_environment(config_dir, environment_definition, env_name, env_template, TextTableEnvironmentDescriber())

        return environment_definition

def _render_table(nodes):
    table = Texttable()
    rows = [["ID", "State", "Tags", "Environment", "Address"]]
    for node in nodes:
        environment_description = "%s\nDef: %s" % (node.environment_name(), node.environment_definition_name())
        rows.append([node.id(), node.state(), node.tags(), environment_description, node.address()])

    table.add_rows(rows)
    print(table.draw())

def _conf_file_from_dir(dir, filename):
    if not os.path.exists(dir):
        error("%s does not exist" % dir)

    if not os.path.isdir(dir):
        error("%s is not a directory" % dir)

    conf_path = os.path.join(dir, filename)

    if not os.path.exists(conf_path):
        error("Configuration file %s not found" % os.path.abspath(conf_path))

    return conf_path

@contextmanager
def env_conf_from_dir(directory, env_name, property_file, noop=False):
    logger.debug("Using property file %s" % property_file)
    if not env_name:
        raise StandardError("env_name is a required field")

    try:
        yield _definition_from_yaml(directory, "environment_definitions.yaml",
            partial(environment_definitions_from_yaml, service_definitions=service_defs_from_dir(directory),
                env_name=env_name, noop=noop, all_credentials=_credentials_from_path(directory)), property_file)
    finally:
        pass

def service_defs_from_dir(directory):
    return _definition_from_yaml(directory, "service_definitions.yaml", partial(service_definitions.service_definitions_from_yaml, abs_path_to_config=directory))

def _properties_from_file(property_file):
    if property_file:

        if not os.path.isfile(property_file):
            raise StandardError("property_file %s is not a valid file " % property_file)

        config = ConfigParser.RawConfigParser()
        config.read(property_file)
        return dict(config.items("properties"))
    else:
        return {}


def _definition_from_yaml(def_directory, filename, from_yaml_func, property_file=None):
    conf_path = _conf_file_from_dir(def_directory, filename)
    config_file = open(conf_path,'r')

    try:
        properties_from_file = _properties_from_file(property_file)
        logger.debug("Loading properties %s" % properties_from_file)
        templated_yaml = pystache.render(config_file.read(), properties_from_file)
        logger.debug("Post templated YAML %s" % templated_yaml)
        return from_yaml_func(templated_yaml)
    finally:
        config_file.close()

class Credentials:

    def __init__(self, name, data, abs_path_to_configuration_dir):
        self.name = name
        self.data = data
        self.abs_path_to_configuration_dir = abs_path_to_configuration_dir

    def __getattr__(self, attribute_name):
        return self.data[attribute_name]

    def __repr__(self):
        return "Credentials " + self.name.__repr__()

    def __str__(self):
        return "Credentials name: %s" % self.name

    def __eq__(self, other):
        return self.name == other.name and self.data == other.data and self.abs_path_to_configuration_dir == other.abs_path_to_configuration_dir

    def __hash__(self):
        return hash(self.name + str(self.data.items()) + self.abs_path_to_configuration_dir)

    def path_to_private_key(self):
        return os.path.join(self.abs_path_to_configuration_dir, self.data['private_key'])

def _credentials_from_path(directory):
    def _credentials_from_yaml(yaml_string, directory=None):
        yaml_data = yaml.load(yaml_string)
        credentials_dict = {}

        for credential_name, credential_data in yaml_data.items():
            credentials_dict[credential_name] = Credentials(credential_name, credential_data, os.path.abspath(directory))

        return credentials_dict

    return _definition_from_yaml(directory, "credentials.yaml", partial(_credentials_from_yaml, directory=directory))
