#!/usr/bin/perl -w
use strict;
##### pacbio_isoseq_cluster.pl #####
#
# Input: <isoseq full length fasta> 
#        <isoseq nonfull length fasta> 
#        <output base>
# Output: <output base>.consensus.fasta <output base>.summary.txt <output base>.report.txt
# Modifies: Creates temporary folder and deletes it

if(scalar(@ARGV) != 3) { die "<IsoSeqFLNC fasta> <IsoSeqNFL> <output base>\n"; }
my $flinfile = shift @ARGV;
my $nflinfile = shift @ARGV;
my $outbase = shift @ARGV;
my $rand = int(rand()*10000000);
my $tfolder = "/tmp/weirathe/t$rand";
unless(-d "/tmp/weirathe") {
  `mkdir /tmp/weirathe`;
}
unless(-d "$tfolder") {
  `mkdir $tfolder`;
}
print "$rand\n";
my $cmd1 = '. /Shared/Au/jason/Source/smrtanalysis/current/etc/setup.sh && '; 
$cmd1 .= '/Shared/Au/jason/Source/smrtanalysis/current/analysis/bin/pbtranscript.py cluster '; 
$cmd1 .= " -d $tfolder/tempdir ";
$cmd1 .= " --summary $tfolder/summary.txt ";
$cmd1 .= " --report $tfolder/report.txt ";
$cmd1 .= ' --nfl_fa '.$nflinfile.' ';
$cmd1 .= " $flinfile $tfolder/consensus.fasta ";
print "$cmd1\n"; 
open(STR,"$cmd1|") or die; 
while(my $ln = <STR>) {
  chomp($ln);
  print "$ln\n";
}
close STR;
`cp $tfolder/consensus.fasta $outbase.consensus.fasta`;
`cp $tfolder/summary.txt $outbase.summary.txt`;
`cp $tfolder/report.txt $outbase.report.txt`;
`rm -r $tfolder`; 
#`cp -r $tfolder testendisoseq.$rand/`;
