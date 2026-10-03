import sys
import re

arwFilePath = sys.argv[1]

filenameMatch = re.match(r'(.*)\.ARW\.xmp', arwFilePath, re.IGNORECASE)
dngFilePath = f"{filenameMatch.group(1)}.dng.xmp"

with open(dngFilePath, 'r', encoding='utf-8') as fh:
    dngContent = fh.read()

with open(arwFilePath, 'r', encoding='utf-8') as fh:
    arwContent = fh.read()

# copy rating valuec
#   xmp:Rating="2"
ratingMatch = re.search(r'xmp:Rating="([^"]*)"', arwContent)
rating = ratingMatch.group(1) if ratingMatch else "0"
dngContent = re.sub(r'xmp:Rating="([^"]*)"', f'xmp:Rating="{rating}"', dngContent)

# copy all location related lines
#   exif:DateTimeOriginal="2024:07:29 19:10:13.179"
#   exif:GPSVersionID="2.2.0.0"
#   exif:GPSLongitude="18,26.157303E"
#   exif:GPSLatitude="46,46.389999N"
#   xmp:Rating="2"
location_match = re.search(r'exif:DateTimeOriginal=.*?\n(.*)\n\s*xmp:Rating=', arwContent, re.DOTALL)
location_lines = location_match.group(1) if location_match else ''
dngContent = re.sub(r'exif:DateTimeOriginal=(.*?\n).*(\n\s*xmp:Rating=)', r'\1' + location_lines + r'\2', dngContent, flags=re.DOTALL)

if (re.search(r'<rdf:li>OnlyForOthers</rdf:li>', arwContent) and 
    not re.search(r'<rdf:li>OnlyForOthers</rdf:li>', dngContent)):
    dngContent = re.sub(r'<dc:subject>\n    <rdf:Bag>\n', r'<dc:subject>\n    <rdf:Bag>\n     <rdf:li>NotForPublic</rdf:li>\n     <rdf:li>OnlyForOthers</rdf:li>\n', dngContent)
    dngContent = re.sub(r'<lr:hierarchicalSubject>\n    <rdf:Bag>\n', r'<lr:hierarchicalSubject>\n    <rdf:Bag>\n     <rdf:li>NotForPublic|OnlyForOthers</rdf:li>\n', dngContent)

# location, artist, onlyforme, 
# todo: copy location, also in the other direction script

#   <dc:title>
#    <rdf:Alt>
#     <rdf:li xml:lang="x-default">Ozora 2024</rdf:li>
#    </rdf:Alt>
#   </dc:title>

with open(dngFilePath, 'w', encoding='utf-8') as fh:
    fh.write(dngContent)

