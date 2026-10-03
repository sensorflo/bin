#!/bin/perl -i

my $arwFilePath = $ARGV[0];

$arwFilePath =~ m/(.*)\.ARW.xmp/i;
my $dngFilePath = "$1.dng.xmp";

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

# copy rating value
#   xmp:Rating="2"
$arwContent =~ m/xmp:Rating="([^"]*)"/;
my $rating = $1;
$dngContent =~ s/xmp:Rating="([^"]*)"/xmp:Rating="$rating"/;

# copy all location related lines
#   exif:DateTimeOriginal="2024:07:29 19:10:13.179"
#   exif:GPSVersionID="2.2.0.0"
#   exif:GPSLongitude="18,26.157303E"
#   exif:GPSLatitude="46,46.389999N"
#   xmp:Rating="2"
$arwContent =~ m/exif:DateTimeOriginal=.*?\n(.*)\n\s*xmp:Rating=/s;
my $locationLines = $1;
$dngContent =~~ s/exif:DateTimeOriginal=(.*?\n).*(\n\s*xmp:Rating=)/$1$locationLines$2/;

if (($arwContent =~ m@<rdf:li>OnlyForOthers</rdf:li>@) && !($dngContent =~ m@<rdf:li>OnlyForOthers</rdf:li>@)) {
	$dngContent =~ s@<dc:subject>\n    <rdf:Bag>\n@<dc:subject>\n    <rdf:Bag>\n     <rdf:li>NotForPublic</rdf:li>\n     <rdf:li>OnlyForOthers</rdf:li>\n@;
	$dngContent =~ s@<lr:hierarchicalSubject>\n    <rdf:Bag>\n@<lr:hierarchicalSubject>\n    <rdf:Bag>\n     <rdf:li>NotForPublic|OnlyForOthers</rdf:li>\n@;	
}

# location, artist, onlyforme, 
# todo: copy location, also in the other direction script


   <dc:title>
    <rdf:Alt>
     <rdf:li xml:lang="x-default">Ozora 2024</rdf:li>
    </rdf:Alt>
   </dc:title>

if (open FH, ">:encoding(UTF-8)", $dngFilePath and -w $dngFilePath) {
  print FH $dngContent;
  close FH;
}