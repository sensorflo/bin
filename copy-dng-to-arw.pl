#!/bin/perl -i

my $dngFilePath = $ARGV[0];

$dngFilePath =~ m/(.*)\.dng.xmp/i;
my $arwFilePath = "$1.ARW.xmp";

my $dngContent = do {
    open my $fh, '<:encoding(UTF-8)', $dngFilePath or die "Cannot open $dngFilePath";
    local $/;
    <$fh>;
};

my $arwContent = do {
    open my $fh, '<:encoding(UTF-8)', $arwFilePath or die "Cannot open $arwFilePath";
    local $/;
    <$fh>;
};

$dngContent =~ m/\bxmp:Rating="([^"]*)"/;
my $rating = $1;
$arwContent =~ s/\bxmp:Rating="([^"]*)"/xmp:Rating="$rating"/;


#      <rdf:li>NotForPublic</rdf:li>
#     <rdf:li>OnlyForOthers</rdf:li>
if (($dngContent =~ m@<rdf:li>OnlyForOthers</rdf:li>@) && !($arwContent =~ m@<rdf:li>OnlyForOthers</rdf:li>@)) {
	$arwContent =~ s@<dc:subject>\n    <rdf:Bag>\n@<dc:subject>\n    <rdf:Bag>\n     <rdf:li>NotForPublic</rdf:li>\n     <rdf:li>OnlyForOthers</rdf:li>\n@;
	$arwContent =~ s@<lr:hierarchicalSubject>\n    <rdf:Bag>\n@<lr:hierarchicalSubject>\n    <rdf:Bag>\n     <rdf:li>NotForPublic|OnlyForOthers</rdf:li>\n@;	
}


if (open FH, ">:encoding(UTF-8)", $arwFilePath and -w $arwFilePath) {
  print FH $arwContent;
  close FH;
}