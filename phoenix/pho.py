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

import sys
from phoenix import fabfile, plogging
import argparse

def main(argv = sys.argv):
    parser = argparse.ArgumentParser(prog="phoenix",
        description='To actually run phoenix, use one of the subcommands listed below. To see more help for a given command, run "pho <cmd> -h"',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--verbosity', action='store', choices=('debug', 'info', 'quiet'), default='info',
        help='Running Phoenix in various modes: (if nothing is specified, the default is \'info\')\n' \
             'debug: resulting in more detailed logging shown for both Phoenix as well as echoing all shell commands sent to nodes\n' \
             'info: resulting in info level logging shown for Phoenix as well as standard out logging for shell commands sent to nodes\n' \
             'quiet: resulting in only warnings/errors logging shown for both Phoenix and shell commands sent to nodes')


    subparsers = parser.add_subparsers(title="Commands")

    for func_and_parser_func in fabfile.CLI_FUNCS.values():
        _, add_subparser_func = func_and_parser_func
        add_subparser_func(subparsers)


    # The first argument will be the script name, so strip that off
    args = parser.parse_args(argv[1:])

    plogging.set_logging_output(args.verbosity)

    # The arg parser gives us a list of tuples - we need to convert this to a map for dispatch
    # We also need to strip off the function name, and the debug flag as we have already handled that above
    args.func(**{pair[0]:pair[1] for pair in args._get_kwargs() if not pair[0] == 'func' and not pair[0] == 'verbosity'})


if __name__ == '__main__':
    sys.exit(main())