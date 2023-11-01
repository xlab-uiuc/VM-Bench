#!/usr/bin/env perl
######################################################################
#	Name:		benchRun.pl
#	By:		John Johnston (johnj@msu.edu)
#	Created:	September 20, 2011
#	Last Mod:	09-21-2011
#	Purpose:	Automated execution of bioinformatics
#			benchmark tests
#	Output:		Benchmarking results in bioBenchResults.csv
#			Misc. runtime output in benchResults.txt
#			Application-specific output in output subdir
#			of each individual application.
#
#	Run Time:	Total number of CPU seconds spent in kernel
#			and user modes (user and sys combined).
#
######################################################################
#
#			GENERAL INSTRUCTIONS
#
#	First run the auto-build script "buildBench.sh".  Assuming
#	there are no errors, run this script using:
#	perl ./runBench.pl, or set the executable bit on the file and
#	run as:  ./runBench.pl
#
#	Informational output annouces each test, resulting run times,
#	and replicate.
#
#	CSV output produced in bioBenchResults.csv.
#
#	MODIFY "$replicates" variable below to control the number of
#	test iterations (default = 3).
#
#####################################################################
##
## SET TEST ITERATION VALUE BELOW!!
##
$replicates = 1;
##
## SET OMP_NUM_THREADS TO CONTROL CPU USAGE FOR VELVET!!
##
$ENV{'OMP_NUM_THREADS'}=1;
##
$runStart = `date`;
open (MYFILE, '>>bioBenchResults.csv');
$hostName = `hostname`;
@memoryInfo = `free -m`;
@totalMemory = split /\s+/, $memoryInfo[1];
@sysInfo = `cat /proc/cpuinfo`;
@vendorID = split /\s+/, $sysInfo[1];
@cpuFamily = split /\s+/, $sysInfo[2];
@model = split /\s+/, $sysInfo[3];
@modelName = split /\s+/, $sysInfo[4];
$compilerInfo = `gcc -v 2>&1`;
chomp($compilerInfo);
@compilerParse = split("version",$compilerInfo);
@compiler = split /\s+/, $compilerParse[1];
$modelLength = scalar(@modelName) - 1;
@sliceModelName = @modelName[3..$modelLength];
@speed = split /\@/, $sysInfo[4];
@cache = split /\s+/, $sysInfo[8];
@cores = split /\s+/, $sysInfo[12];
$prettySpeed = trim($speed[1]);
$prettyModelName = $sliceModelName[0] . " " . $sliceModelName[1] . " " . $sliceModelName[2] . " " . $sliceModelName[3];
chomp($prettyModelName);
chomp($hostName);
$hwInfo =  "$vendorID[2],$cpuFamily[3],$model[2],$prettyModelName,$prettySpeed,$cache[3]KB,$cores[3],$totalMemory[1]MB,gcc-$compiler[1]";
print "\nBeginning Bio-Benchmarking:\n";
print MYFILE "Run Start: $runStart\n\n";
print MYFILE "host,test,replicate,runTime,cpuVendor,cpuFamily,cpuModel,procSpeed,cacheSize,numCores,totalMem,compiler\n";

for ($i=1; $i <= $replicates; $i++) {
##
##	MUMmer v. 3.0
##
print "\nRunning MUMmer, replicate # $i...\n\n";
# system("sleep 5");
@timeResults = `(time -p sh -c './MUMmer/mummer -b -c  ./MUMmer/input/hs_chrY.fa ./MUMmer/input/hs_chr17.fa  1> ./QuEST/output/results.txt 2>> benchResults.txt') 2>&1`;
chomp(@timeResults);
print "@timeResults\n";
@userTime = split /\s+/, $timeResults[1];
@sysTime = split /\s+/, $timeResults[2];
$totalTime = $userTime[1] + $sysTime[1];
print MYFILE "$hostName,mummer,$i,$totalTime,$hwInfo\n";
}  ## end replicate loop

print "DONE!\n";
print "Benchmarking results written to: bioBenchResults.csv\n";
print "Extraneous run output dumped to: benchResults.txt\n";
$runEnd = `date`;
print MYFILE "Run End: $runEnd\n";
close(MYFILE);

sub trim($)
{
	my $string = shift;
	$string =~ s/^\s+//;
	$string =~ s/\s+$//;
	return $string;
}
