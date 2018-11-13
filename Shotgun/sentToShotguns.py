import os
import maya.cmds as cmds
from Shotgun import mediaPublish
reload(mediaPublish)

def sendToShotgun():

    file_path = cmds.file(q=True, sn=True)

    if not file_path:
        return

    file_name = os.path.basename(file_path)
    fileName  = file_name.split('_')

    taskcode = fileName[0]
    project  = fileName[1]
    episode  = fileName[2]
    shotName = fileName[3].split('.')[0]

    shot_node_name = '%s_%s_%s_%s' % (taskcode,project,episode,shotName)

    local_path = os.getenv('USERPROFILE').replace('\\','/')
    play_path = '%s/LIVE/%s/%s/COMMON/MEDIA/%s.mov' % (local_path,project,episode,shot_node_name)

    if not os.path.exists(play_path):
        return

    else:
        version_name = '.'.join(file_name.split('.')[:-1])
        shot = mediaPublish.Shot(play_path, file_name)
        version_ent = shot.publish(comment='Publish from %s' % version_name)
        if version_ent:
            print 'update shotgun :' + version_name




