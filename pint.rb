#!/usr/bin/env ruby
#
# Copyright 2007-2008 David Shakaryan <omp@gentoo.org>
# Distributed under the terms of the GNU General Public License v2.
#
# pint.rb [version 0.10]
#
# Parse a Paludis log file and output install times of one or more packages,
# defaulting to all packages if none are specified.

require 'getoptlong'
require 'Paludis'

# Parse options and store them in a hash.
getopt = GetoptLong.new(
  ['--date',       '-d', GetoptLong::NO_ARGUMENT],
  ['--mean',       '-m', GetoptLong::NO_ARGUMENT],
  ['--regexp' ,    '-e', GetoptLong::NO_ARGUMENT],
  ['--repository', '-r', GetoptLong::REQUIRED_ARGUMENT],
  ['--current',    '-c', GetoptLong::NO_ARGUMENT],
  ['--no-colour',  '-C', GetoptLong::NO_ARGUMENT],
  ['--file',       '-f', GetoptLong::REQUIRED_ARGUMENT],
  ['--version',    '-v', GetoptLong::NO_ARGUMENT],
  ['--help',       '-h', GetoptLong::NO_ARGUMENT])
$opts = Hash['file' => '/var/log/paludis.log', 'repository' => '\S+']
getopt.each do |opt, arg| $opts[opt.sub('--', '')] = arg end

# Define colours.
if $opts.has_key?('no-colour')
  def colour_name(str); return str; end
  def colour_date(str); return str; end
  def colour_time(str); return str; end
else
  $env = Paludis::EnvironmentFactory.instance.create ''
  def colour_name(str)
    depspec = Paludis::parse_user_package_dep_spec('=' + str, $env, Array.new)

    name = depspec.package
    version = depspec.version_requirements.first[:spec]
    repository = depspec.in_repository

    return "\e[1;34m#{name}\e[0m-#{version}::#{repository}"
  end
  def colour_date(str); return "\e[33m#{str}\e[0m"; end
  def colour_time(str); return "\e[32m#{str}\e[0m"; end
end

# Format time from seconds to a readable string.
def format_time(s)
  # Calculate hours, minutes and seconds.
  h, s = s.divmod(3600)
  m, s = s.divmod(60)

  # Convert numbers to a string.
  str = ''
  unless h.zero?
    str += h.to_s + ' hours'
    str.chop! if h == 1
  end
  unless m.zero?
    str += ', ' unless str.empty?
    str += m.to_s + ' minutes'
    str.chop! if m == 1
  end
  unless s.zero?
    str += ', ' unless str.empty?
    str += s.to_s + ' seconds'
    str.chop! if s == 1
  end
  str = '0 seconds' if str.empty?

  return colour_time(str)
end

# Format package name and, optionally, date.
def format_name(name, start)
  str = '* ' + colour_name(name)
  str += ' ' + colour_date(Time.at(start).utc.to_s) if $opts.has_key?('date')

  return str
end

# Program help.
if $opts.has_key?('help')
  puts 'Usage: pint.rb [options] [packages]'
  puts
  puts 'Options:'
  puts '  --date        -d  Display install start dates'
  puts '  --mean        -m  Calculate arithmetic mean of all matches'
  puts '  --regexp      -e  Allow use of Ruby regular expressions in package' +
    ' names'
  puts '  --repository  -r  Display packages from comma-separated list of' +
    ' repositories'
  puts '  --current     -c  Display running time of current install'
  puts '  --no-colour   -C  Disable use of colour in program output'
  puts '  --file        -f  Specify path to a log file'
  puts '  --version     -v  Display program version'
  puts '  --help        -h  Display program help'
  exit
end

# Program version.
if $opts.has_key?('version')
  puts 'pint.rb 0.10'
  exit
end

# Read the log file.
log = File.read($opts['file'])

if $opts.has_key?('current')
  # Check whether the last line of log is the start of an install.
  if log =~ /^(\d+): starting install of package (\S*) \(\d+ of \d+\)\Z/
    # Store data in variables.
    name = $2
    start = $1.to_i
    time = Time.now.to_i - start

    puts format_name(name, start)
    puts '  ' + format_time(time)
  else
    puts 'No packages are currently being installed.'
  end

  exit
end

# Define a regular expression to match successful installs.
regexp = ARGV
regexp = regexp.map {|arg| Regexp.escape(arg)} unless $opts.has_key?('regexp')
regexp = /
        ^(\d+):\s starting (?# start of install)
            (\s install \s of \s package 
             \s (\S*(?:#{regexp.join('|')})\S*::#{$opts['repository'].gsub(',', '|')})
            \s \(\d+ \s of \s \d+\)\n)
        (?: (?# this stuff only happens when we're replacing an existing package)
         \d+: \s starting (\s clean \s of \s package \s
          (\S*(?:#{regexp.join('|')})\S*::installed)
          \s \(\d+ \s of \s \d+\)\n)
         \d+: \s finished \4
        )?
        (\d+): \s finished \2 (?# finish of install)
        /x

if $opts.has_key?('mean')
  sec = 0
  num = 0
end

while log =~ regexp
  # Store data in variables.
  name = $3
  start = $1.to_i
  finish = $+.to_i
  time = finish - start

  puts format_name(name, start)

  if $opts.has_key?('mean')
    sec += time
    num += 1
  else
    puts '  ' + format_time(time)
  end

  # Set log to string right of last match.
  log = $'
end

puts '  ' + format_time(sec/num) if $opts.has_key?('mean')
