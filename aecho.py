#!/usr/bin/python
# 
# NAME
#   aecho - Displays arguments explicitely
# 
#
# SYNOPSYS
#   aecho [ARGUMENTS]...
# 
#
# DESCRIPTION
#   All arguments are printed explicitely. In contrast to vanilla echo, that
#   makes it easier to see what the content of each individual argument is.
#   Argument 0 is the program's command name, argument 1 is the first argument.
#
#
# ENVIRONMENT VARIABLES
#   AET
#     aecho template. Printed for each argument. %i is replaced by argument's
#     number, %a is replaced by the argument itself, %% is replaced by %, any
#     other character following an % is reserved for future use and results in
#     an error.
#
#   AES
#     aecho separator. Printed between argument templates. 
#
#   AED
#     aecho delimiter. Printed after the last argument template.
#
#
# EXAMPLES
#   The following assumes a POSIX shell.
# 
#   aecho lorem "ipsum dolor"
#     prints:
#       arg 0: '/usr/bin/aecho'
#       arg 1: 'lorem'
#       arg 2: 'ipsum dolor'
# 
# 
#   AET="|%a| is arg %i" AES=", " AED="$" aecho hello world
#     prints:
#       |/usr/bin/aecho| is arg 0, |hello| is arg 1, |world| is arg 2$


import sys, re, os

# AE = aecho
template = os.getenv("AET", "arg %i: '%a'")
separator = os.getenv("AES", "\n")
delimiter = os.getenv("AED", "\n")

format_regexp = re.compile('%(.)')

for (argno,arg) in enumerate(sys.argv):
    is_first_iter = (argno == 0)
    if (not is_first_iter):
        sys.stdout.write(separator)

    # note that inserted text neither is itself searched for occurences of
    # % format sequences, nor can the inserted text at its two boundaries create
    # a new % format sequence which would then wrongly be substituted.
    template_start_pos = 0
    for match in format_regexp.finditer(template):
        sys.stdout.write(template[template_start_pos:match.start()])
        template_start_pos = match.end() # skip '%' and the char following it

        ch = match.group(1)
        if ch=='i'  : format_val = str(argno)
        elif ch=='a': format_val = arg
        elif ch=='%': format_val = '%'
        else        : sys.exit("Invalid template. '{}' at pos {} is not a valid "
                               "argument to %.".format(ch, match.start(1)))
        sys.stdout.write(format_val)

    sys.stdout.write(template[template_start_pos:])

sys.stdout.write(delimiter)
