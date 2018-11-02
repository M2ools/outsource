import sys
import os
import subprocess

currentFolderPath = (os.path.dirname(os.path.abspath(__file__)))
if not currentFolderPath in sys.path[0]:
    sys.path.insert(0, currentFolderPath)

import maya.cmds as cmds
import playblastControl
reload(playblastControl)

def run(pre_roll=0, ao=True):

    movpaths = []
    shot_selected = cmds.ls(sl=True, type='shot')

    shot_list = shot_selected if shot_selected else cmds.sequenceManager(listShots=True)

    for shot_node in shot_list:
        start = cmds.getAttr(shot_node + '.sequenceStartFrame') - pre_roll
        end   = cmds.getAttr(shot_node + '.sequenceEndFrame') + (1 if pre_roll else 0)
        camera = cmds.shot(shot_node, q=True, currentCamera=True)

        print shot_node, start, end, camera, ao
        cmds.currentTime(start, e=True)
        movie_path,version_file = playblastControl.setPlayblast(shot_node, start, end, camera, AOswitch=ao)

        if os.path.exists(movie_path):
            movpaths.append([movie_path,version_file])

    return movpaths

