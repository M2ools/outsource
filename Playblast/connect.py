import sys
import getpass
import os

from Shotgun import shotgun_api3

domain_link = 'https://m2a.shotgunstudio.com'
login       = 'seveneleven'
password    = 'outsourceStudio711'

sg = shotgun_api3.Shotgun(domain_link,login = login, password = password)

def getTagList(projectName, shot):
    shot_ent = sg.find_one('Shot', [['project.Project.sg_meme_name', 'is', projectName], ['code', 'is', shot]], ['code', 'tags', 'sg_time_of_day'])
    return shot_ent

def getProjectConfig(projectName):
    prj_ent = sg.find_one('Project',[['sg_meme_name','is',projectName]],['sg_fps','sg_resolution'])
    return prj_ent

def getHudShotgun(project_name,shot_name):
    TIME_dict = {'Dawn'     : 'DAWN',
                 'Morning'  : 'MORNING',
                 'Afternoon': 'AFTERNOON',
                 'Evening'  : 'EVENING',
                 'Dusk'     : 'DUSK',
                 'Night'    : 'NIGHT',
                 'Cloudy'   : 'CLOUDY'}

    CAMFX_dict = {'cmpShake'    : 'CAMERA SHAKE',
                  'cmpHHeld'    : 'HAND HELD CAMERA',
                  'cmpZoomIn'   : 'CAMERA ZOOM IN',
                  'cmpZoomOut'  : 'CAMERA ZOOM OUT',
                  'cmpPZoomIn'  : 'CAMERA PUNCH ZOOM IN',
                  'cmpPZoomOut' : 'CAMERA PUNCH ZOOM OUT',
                  'cmpPanLR'    : 'CAMERA PAN LEFT TO RIGHT',
                  'cmpPanRL'    : 'CAMERA PAN RIGHT TO LEFT',
                  'cmpTiltUD'   : 'CAMERA TILT UP TO DOWN',
                  'cmpTiltDU'   : 'CAMERA TILT DOWN TO UP',
                  'cmpDutchLR'  : 'CAMERA DUTCH LEFT TO RIGHT',
                  'cmpDutchRL'  : 'CAMERA DUTCH RIGHT TO LEFT'}
    comp_cam = ''
    time_of_day = ''
    shot_ent = getTagList(project_name, shot_name)

    if shot_ent['tags']:
        for tag in shot_ent['tags']:
            if tag['name'] in CAMFX_dict.keys():
                comp_cam = CAMFX_dict[tag['name']]
                break

    if shot_ent['sg_time_of_day'] and shot_ent['sg_time_of_day'] in TIME_dict.keys():
        time_of_day = TIME_dict[shot_ent['sg_time_of_day']]

    return comp_cam, time_of_day

def getCutDuration(shotName):
    cut_Dut = sg.find_one('Shot', [['code', 'is', shotName]], ['code', 'id', 'sg_cut_duration'])
    return cut_Dut
