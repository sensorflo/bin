

# find Git repositories where 'email' config variable is not set
find -xdev -type d -name .git -print0 |
  perl -0 -pe 'chomp; s@$@/config$/@' |
  xargs -0 grep -n email -L
