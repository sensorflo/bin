#!/usr/bin/python

"""
splitr - splits a file into multiple files using a regex
"""

import re, sys

def getopts():
    from optparse import OptionParser
    op = OptionParser(
        usage="usage: %prog [options] file",
        version="%prog 0.1")
    op.add_option(
        "-r", "--regex",
        default=r"~ *<(?P<fn>.*)> *~ *",
        help="Regex separating files, group fn = filename", metavar="REGEX")
    op.add_option(
        "-n", "--name-pattern",
        default="",
        help="Pattern to create out filenames", metavar="PAT")
    op.add_option(
        "-d", "--dont-touch",
        action="store_true",
        help="Dont't touch a file if it's shall-be-new content is equal to it's current content")
    (opts,file_names) = op.parse_args()
    return (opts,file_names)


def splitr_file(file_name,regexobj):
    infile=open(file_name,'r')
    outfile=None
    for line in infile:
        mo = regexobj.match( line )
        if mo:
            nexts_file_name = mo.group( 'fn' )
            if nexts_file_name == None:
                sys.exit( file_name + " line '" + line + "' has no regex group named fn" )
            elif nexts_file_name == file_name:
                sys.exit( file_name + ": partfile is the sumfile itself" )
            outfile=open( nexts_file_name, 'w' )
        else:
            if outfile == None:
                sys.exit( file_name + " does not start with a separtor" )
            outfile.write(line)
            
def main():
    (opts,file_names) = getopts()
    regexobj = re.compile(opts.regex);
    for fn in file_names:
        splitr_file(fn,regexobj)
    
if __name__ == '__main__':
    main()
