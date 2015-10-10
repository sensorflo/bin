#!/bin/bash
# 
# NAME
#   aecho - Displays arguments explicitely
# 
# SYNOPSYS
#   aecho [ARGUMENTS]...
# 
# DESCRIPTION
#   All arguments are printed explicitely. In contrast to vanilla echo, that
#   makes it easier to see where what the contents of the independent arguments
#   are. Argument 0 is the program's command name, argument 1 is the first
#   argument.
#
# EXAMPLE
#   The following 
# 
#     aecho lorem "ipsum dolor"
# 
#   prints
#
#     arg 0: '/usr/bin/aecho'
#     arg 1: 'lorem'
#     arg 2: 'ipsum dolor'
# 

N=0
for a in "$0" "$@"; do
  echo "arg $N: '$a'"
  N=$((N+1))
done
