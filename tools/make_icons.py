#!/usr/bin/env python3
"""Favicon exports from the original MMG vector logo. Requires Pillow and Inkscape."""
from copy import deepcopy
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'src'/'assets'
S=2048
BLUE='#153f9e'

# Keep every path and the original horizontal proportions of Manuel's MMG logo.
# Only the white square canvas and small-size stroke widths are adapted.
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
original=ET.parse(DEST/'logo.svg').getroot()
favicon=ET.Element(f'{{{NS}}}svg',{'viewBox':'0 0 1210 1210','fill':'none'})
ET.SubElement(favicon,f'{{{NS}}}title').text='MMGestoria'
ET.SubElement(favicon,f'{{{NS}}}rect',{'width':'1210','height':'1210','fill':'#fff'})
mark=ET.SubElement(favicon,f'{{{NS}}}g',{'transform':'translate(0 430)'})
for child in original:
    if child.tag==f'{{{NS}}}title':
        continue
    copy=deepcopy(child)
    for element in copy.iter():
        if 'stroke-width' in element.attrib:
            element.set('stroke-width','24')
    mark.append(copy)
ET.indent(favicon,space='  ')
favicon_path=DEST/'favicon.svg'
ET.ElementTree(favicon).write(favicon_path,encoding='unicode')
with tempfile.TemporaryDirectory(prefix='mmg-icons-') as tmp:
    raster=Path(tmp)/'favicon.png'
    subprocess.run(['inkscape',str(favicon_path),'--export-type=png',
                    f'--export-width={S}',f'--export-height={S}',
                    f'--export-filename={raster}'],check=True,capture_output=True)
    im=Image.open(raster).convert('RGBA')
for size,name in [(180,'apple-touch-icon.png'),(192,'icon-192.png'),(512,'icon-512.png')]:
    im.resize((size,size),Image.Resampling.LANCZOS).save(DEST/name,optimize=True)
im.resize((256,256),Image.Resampling.LANCZOS).save(DEST/'favicon.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])

# Branded share image, rendered from exact text and native vector geometry.
social=Image.new('RGB',(1200,630),'#101f40');sd=ImageDraw.Draw(social)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
sd.text((75,58),'MMGestoria',font=ImageFont.truetype(bold,35),fill='white')
sd.text((77,118),'GESTIÓN INTEGRAL',font=ImageFont.truetype(font,15),fill='#afbddb')
sd.line((77,176,1123,176),fill='#354562',width=1)
sd.text((72,220),'Gestión integral.',font=ImageFont.truetype(font,64),fill='white')
sd.text((72,306),'Atención cercana.',font=ImageFont.truetype(font,64),fill='#a6bdff')
sd.text((77,445),'Autónomos · Pymes · Empresas · Particulares',font=ImageFont.truetype(font,23),fill='#ced7e8')
sd.text((77,538),'Régimen común · Navarra · País Vasco',font=ImageFont.truetype(font,17),fill='#afbddb')
for radius in [110,140,170]:
    sd.ellipse((1160-radius,510-radius,1160+radius,510+radius),outline='#354562',width=1)
social.save(DEST/'social-card.png',optimize=True)
print('Generated favicon.ico, Apple touch icon, 192/512 icons and social image.')
