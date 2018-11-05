# -*- coding: utf-8 -*-
import shutil
import sys
from os import listdir, devnull, makedirs
from os.path import isdir, isfile, exists, basename, splitext, dirname
from fnmatch import fnmatch
import zipfile
from archiveAsset import archive

def getProcessCode():
    return {'ANM': 'ANIMATION',
            'LAY': 'LAYOUT',
            'TIC': 'ANIMATICS',
            'AUD': 'AUDIO',
            'LIT': 'LIGHTING',
            'EFX': 'EFFECTS',
            'CMP': 'COMPOSITING'}

def getAssetCode():
    return {'ANML': 'ANIMAL',
            'CHAR': 'CHARACTER',
            'XTRA': 'EXTRA',
            'FNTR': 'FURNITURE',
            'NATR': 'NATURE',
            'PROP': 'PROPS',
            'STRC': 'STRUCTURE',
            'VECL': 'VEHICLE',
            'MATT': 'MATTE',
            'CAMERA': 'CAMERA'}


def collectAssetInfo():
    asset_code = getAssetCode()
    asset = {}
    for short, full in asset_code.items():
        base_dir = 'L:/F18/{}'.format(full)
        if isdir(base_dir):
            for each in listdir(base_dir):
                asset[each] = short
    return asset

def splitFilename(filename):
    filename = splitext(basename(filename))[0]
    variant = ''
    if '__' in filename:
        filename, variant = filename.split('__')
    tokens = filename.split('_')
    if len(tokens) > 3:
        tokens = tokens[1:]
    show = tokens[0]
    assetTypeCode = tokens[1]
    asset = tokens[2]
    return show, assetTypeCode, asset, variant


def getAssetBaseDir(asset_name, asset_info):
    return 'L:/F18/{}/{}'.format(asset_info[asset_name], asset_name)


def extractAssetFromMaya(ma_file):
    if not isfile(ma_file):
        print('{} does not exist'.format(ma_file))
        return
    print('Reading ref from: {}'.format(ma_file))
    refs = []
    with open(ma_file, 'r') as reader:
        data = reader.readlines()
    reader.close()
    for l in data:
        if ('requires' in l or 'applyMetadata' in l
                or '".mSceneName"' in l):
            continue
        if fnmatch(l, '*"*:/*/*.*"*'):
            r = l.split('"')[-2]
            if not exists(r):
                print('{} : Not exists'.format(r))
            else:
                refs.append(r)
    return refs


def extractAssetNameFromMaya(scenes):
    """ scenes must be a list"""
    result = []  # [ nane, variant=None ]
    fullnames = []
    for s in scenes:
        if not isfile(s):
            continue
        data = extractAssetFromMaya(s)
        for each in data:
            # skip none asset (camera, wav)
            if 'camera' in each.lower() or '.wav' in each.lower() \
                    or 'p:/' in each.lower():
                continue
            else:
                fullnames.append(each)
    for each in fullnames:
        variant = None
        if '.abc' in each:
            tmp = splitext(basename(each))[0].split('__')
            base = tmp[1]
            if len(tmp) > 2:
                variant = tmp[2]
        else:
            base = splitext(basename(each))[0]
            if '__' in base:
                tmp = base.split('__')
                base = tmp[-2]
                variant = tmp[-1]
        tmp = base.split('_')
        if len(tmp) < 4:
            continue
        cat, name = tmp[2:]
        if [cat, name, variant] not in result:
            result.append([cat, name, variant])
    return result

def doZip(src, dst_base, zipname=None):
    found = False
    for drive in ['L:', 'M:', 'W:']:
        if drive in src:
            found = True
            path_in_zip = src.replace(drive, '')
            if zipname:
                zipname = dst_base + '/' + zipname + '.zip'
            else:
                show, assetTypeCode, asset, variant = splitFilename(src)
                variant = '__' + variant if variant else ''
                zipname = '{}/{}_{}_{}{}.zip'.format(
                                            dst_base,show, asset, asset,variant)
            with zipfile.ZipFile(zipname,
                                 'w',
                                 zipfile.ZIP_DEFLATED,
                                 allowZip64=True) as zip:
                zip.write(src, path_in_zip)
    if not found:
        print('Drive letter not found in: {}'.format(src))

def doNuZip(show, destination, assetType, assetTypeCode, asset, variant, mode):
    archive(show=show,
            destination=destination,
            assetType=assetType,
            assetTypeCode=assetTypeCode,
            asset=asset,
            variant=variant,
            mode=mode)

# Disable
def blockPrint():
    sys.stdout = open(devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = sys.__stdout__
