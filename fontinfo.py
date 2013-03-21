#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from freetype import *
import os,re,sys

# http://www.microsoft.com/typography/SpecificationsOverview.mspx
# http://www.microsoft.com/typography/otspec/name.htm
class Name_Translator(object):
    # FIXME: convert from MacRoman to ASCII/ISO8895-1/whatever
    # (MacRoman is mostly like ISO8895-1 but there are differences)
    platform_string = ('Unicode', 'Macintosh', 'ISO (deprecated)', 'Microsoft', 'Custom')
    platform_encoding = (('utf_16_be', 'utf_16_be', 'utf_16_be', 'utf_32_be'),
                         ('mac_roman', 'shift_jis', 'big5', 'euc_kr', 'mac_arabic',
                          'mac_hebrew', 'mac_greek', 'mac_cyrillic', 'mac_symbol', 'Devanagari',
                          'Gurmukhi', 'Gujarati', 'Oriya', 'Bengali', 'Tamil',
                          'Telugu', 'Kannada', 'Malayalam', 'Sinhalese', 'Burmese',
                          'Khmer', 'Thai', 'Laotian', 'Georgian', 'Armenian',
                          'euc_cn', 'Tibetan', 'Mongolian', 'Geez', 'Slavic',
                          'Vietnamese', 'Sindhi', 'Uninterpreted'),
                         ('ascii', 'utf_16_be', 'latin_1'),
                         ('utf_16_be', 'utf_16_be', 'shift_jis', 'gbk', 'big5'))
    name_string = ('Copyright',
                   'Family',
                   'Subfamily',
                   'Unique ID',
                   'Full name',
                   'Version',
                   'PS name',
                   'Trademark',
                   'Manufacturer',
                   'Designer',
                   'Description',
                   'URL Vendor',
                   'URL Designer',
                   'License',
                   'License URL',
                   '(Reserved)',
                   'Preferred Family',
                   'Preferred Subfamily',
                   'Compatible Full Name',
                   'Sample text',
                   'PS CID findfont name',
                   'WWS Family Name',
                   'WWS Subfamily Name'
                   )
    
    def __init__(self, sfnt_name):
        self.__platform = Name_Translator.platform_string[sfnt_name.platform_id]
        self.__encoding = Name_Translator.platform_encoding[sfnt_name.platform_id][sfnt_name.encoding_id]

        self.__name = Name_Translator.name_string[sfnt_name.name_id]
        self.__property = sfnt_name.string.decode(self.__encoding, 'ignore')
        
    def property(self):
        return self.__name, self.__platform, self.__property

def gather_info(font_filepath):
    face = Face(font_filepath)
    info = [Name_Translator(face.get_sfnt_name(i)).property() for i in range(face.sfnt_name_count)]
    return info

def rename(font_filepath):
    if not os.path.splitext(font_filepath)[1] in ['.otf','.OTF','.ttf','.TTF','.ttc','.TTC']:
        return

    ps_name = ''
    family = ''
    version =''
    for i in gather_info(font_filepath.encode(sys.getfilesystemencoding())):
        if i[0] == 'PS name' and not ps_name:
            ps_name = i[2]
        elif i[0] == 'Family' and (i[1] == 'Microsoft' or not family):
            family = i[2]
        elif i[0] == 'Version' and not version:
            match = re.search('\d[.\d]*',i[2])
            if match:
                version = match.group(0)

    _,ext = os.path.splitext(font_filepath)
    font_dir,_ = os.path.split(font_filepath)
    
    new_fontpath = os.path.join(font_dir,'{}_{}_{}{}'.format(ps_name, family, version, ext))
    if font_filepath == new_fontpath:
        print os.path.split(font_filepath)[1]
    else:
        print os.path.split(font_filepath)[1] + '  ---->  ', os.path.split(new_fontpath)[1]
        os.rename(font_filepath, new_fontpath)

if __name__ == '__main__':
    args = [arg.decode(sys.getfilesystemencoding()) for arg in sys.argv]
    if args[1] == '--rename':
        path = args[2].decode(sys.getfilesystemencoding())
        if os.path.isdir(path):
            for root,dirs,files in os.walk(path):
                for f in files:
                    try:
                        rename(os.path.join(root, f))
                    except:
                        pass
        else:
            rename(os.path.abspath(path))
    else:
        path = args[1].decode(sys.getfilesystemencoding())
        for name,platform,prop in gather_info(path):
            print '{:36}{}'.format( '{} ({}):'.format(name,platform), prop )
