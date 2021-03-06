#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8 tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# Copyright © Mike Dacre <mike.dacre@gmail.com>
#
# Distributed under terms of the MIT license
"""
#=======================================================================================#
#                                                                                       #
#          FILE: run_matlab (python 3)                                                  #
#        AUTHOR: Michael D Dacre, mike.dacre@gmail.com                                  #
#  ORGANIZATION: Stanford University                                                    #
#       LICENSE: MIT License, Property of Stanford, Use as you wish                     #
#       VERSION: 0.1                                                                    #
#       CREATED: 2014-08-22 16:26                                                       #
# Last modified: 2015-03-03 11:38
#                                                                                       #
#   DESCRIPTION: Create a bunch of temporary matlab scripts to call some other          #
#                matlab script and then submit to the cluster.                          #
#                                                                                       #
#                Requires that the matlab function be written to accept imput           #
#                variables.                                                             #
#                                                                                       #
#                Right now only works with torque jobs tools and requires               #
#                pbs_torque from                                                        #
#                https://github.com/MikeDacre/torque_queue_manager and logging          #
#                functions from http://j.mp/python_logme                                #
#                                                                                       #
#         USAGE: -p or --path allows the addition of multiple matlab paths              #
#                                                                                       #
#                <function> is a positional arg and is the name of the function to run  #
#                    Note, this function can have no return, you will need to           #
#                    write a specific wrapper function in matlab to call other          #
#                    functions you need.                                                #
#                                                                                       #
#                STDIN: Variable list for matlab                                        #
#                    This list must be space or newline separated. Each space separated #
#                    item will be run as a separate matlab job.                         #
#                    To provide multiple variables to the matlab function,              #
#                    comma separate the variables on a single line.                     #
#                                                                                       #
#          NOTE: Creates temp files in the location of your choice. Default is          #
#                cwd                                                                    #
#                                                                                       #
#                                                                                       #
#                Run as a script or import as a module.  See '-h' or 'help' for usage   #
#                                                                                       #
#=======================================================================================#
"""
# Set to true to get pointlessly verbose output
_debug=True

# Default walltime and other pbs flags
walltime=None

# Exactly as you would enter them on the command line (eg '-l nodes=1')
pbs_flags=None

def build_matlab_jobs(paths, variables, function, tempfile_path='.', walltime=walltime, cores=1, pbs_flags=pbs_flags, verbose=False, logfile=None):
    """ Take a list of paths, a list of lists of variables, and a single Function
        and submit one job for every list in the lists of variables (each item of
        the second dimension will be submitted as an additional argument to the
        matlab function."""
    import logme
    import pbs_torque

    # Build a job for each variable
    joblist = []
    count = 0
    for i in variables:
        count = count + 1
        tf = create_temp_file(paths, variables, function, count, tempfile_path)
        job = pbs_torque.job()
        job.command = 'matlab -nodisplay -nojvm -nosplash -nodesktop < ' + tf
        job.cores = cores
        if walltime:
            job.walltime = walltime
        if pbs_flags:
            job.flags = pbs_flags
        job.name = i + '_' + str(count)


def create_temp_file(paths, variables, function, count, file_path):
    """ Create a tempfile for a job"""
    from tempfile import mkstemp
    from os import path

    tf = mkstemp(suffix='_' + str(count) + '.m', prefix=variable + '_', text=True)[1]
    with open(tf, 'w') as outfile:
        for i in paths:
            print("addpath('" + path.abspath(i) + "')", file=outfile)
        print(function + '(' + ','.join(variables) + ')', file=outfile)

    return(tf)

def _get_args():
    """ Command Line Argument Parsing """
    import argparse

    parser = argparse.ArgumentParser(
                 description=__doc__,
                 formatter_class=argparse.RawDescriptionHelpFormatter)

    # Optional Arguments
    parser.add_argument('-p', '--path',
                        help="Comma separated list of matlab paths")
    parser.add_argument('--cores',
                        help="Number of cores to use for each job. Default: 1")
    parser.add_argument('--walltime',
                        help="PBS walltime")
    parser.add_argument('--pbs_flags',
                        help="Optional flags to pass to pbs")
    parser.add_argument('-t', '--tmp_path',
                        help="Where to store tempfiles, defaults to current working dir")
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose output")

    # Function name
    parser.add_argument('function',
                        help="Name of the matlab function to run")

    # Optional Files
    parser.add_argument('-l', '--logfile',
                        help="Log File, Default STDERR (append mode)")

    return parser

# Main function for direct running
def main():
    """ Run directly """
    from sys import stdin

    # Get commandline arguments
    parser = _get_args()
    args = parser.parse_args()

    # Get variable list from STDIN
    variables = [i.split(',') for i in stdin.read().rstrip().split('\n')]

    # Split paths
    paths = args.path.split(',')

    # Parse with defaults
    walltime  = args.walltime   if args.walltime  else walltime
    cores     = int(args.cores) if args.cores     else cores
    pbs_flags = args.pbs_flags  if args.pbs_flags else args.pbs_flags
    tp        = args.tmp_path   if args.tmp_path  else '.'

    if _debug:
        print(paths)
        print(args.function)
        print(variables)

    # Run the sucker
    jobs = build_matlab_jobs(paths=paths, variables=variables, function=function, tempfile_path=tp, walltime=walltime, cores=cores, pbs_flags=pbs_flags, verbose=args.verbose, logfile=args.logfile)
    queue = pbs_torque.submit_multiple(jobs)

# The end
if __name__ == '__main__':
    main()
