#!/usr/bin/perl

open F, "</proc/modules" or die "/proc/modules";
while (<F>) {
  $m{$1}=1 if /^(\S+)\s/;
}
close F;

open F, "<.config" or die ".config";
while (<F>) {
  $c{$1}=$2 if /^([A-Z0-9_]+)=([nmy])/;
}
close F;

for $f (split /\s+/,`find . -name Makefile`) {
#print STDERR "Reading $f...\n";
  open F, "<$f" or die "$f";
  while (<F>) {
    if (/^\s*obj-\$\(([A-Z0-9_]+)\)\s*[+:]?=\s*(.*?\.o)\s*$/) {
      $c=$1;
      $m=$2;
      $m =~ s/\S*\/([^\s.]+\.o)/$1/g;
      $m =~ s/\.o\b\s*/ /g;
#print STDERR "Option $c: $m\n";
      $cd{$c} .= " $m";
      for $d (split / /,$m) {
        $md{$d} = $c;
      }
    } else {
      while (/\b(CONFIG_[A-Z0-9_]+)\b/g) {
#print STDERR "Non-Option $1\n";
        $ca{$1}="";
      }
    }
  }
  close F;
}

for $k (sort keys %c) {
  if (! defined $cd{$k} && ! defined $ca{$k}) {
#    print STDERR "Warning: .config option $k not found in Makefiles\n";
    next;
  }
  for $n (split /\s+/, $cd{$k}) {
    ($t=$n) =~ s/-/_/g;
    if (defined $m{$n} || defined $m{$t}) {
      if ($c{$k} eq "m" || $c{$k} eq "M") {
        $c{$k} = "M";
        $m{$n} = 2 if defined $m{$n};
        $m{$t} = 2 if defined $m{$t};
      }
    }
  }
}

for $k (sort keys %m) {
  print STDERR "Warning: no config found for module $k: ".$m{$k}."\n" if $m{$k} == 1;
}
open F, "<.config" or die ".config (2)";
while (<F>) {
  if (/^([A-Z0-9_]+)=m/ && $c{$1} ne "M") {
#    print "# $_";
    print "$1=n\n";
  } else {
    print
  }
}
close F;
