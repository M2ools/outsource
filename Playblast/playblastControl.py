import os
import json
import maya.cmds as cmds
import hudDisplay
import viewportDisplay
reload(hudDisplay)
reload(viewportDisplay)

PROCESSCODE_TO_TASK = {'LAY': 'layout',
                       'ANM': 'animation',
                       'BLK': 'blocking',
                       'A2D': 'anim2D',
                       'LGT': 'light',
                       'REN': 'render',
                       'CMP': 'comp',
                       'EDT': 'edit',
                       'GRD': 'grading',
                       'EFX': 'effects',
                       'CWD': 'crowd'}

def getFileName(shot_node_name=None, task_code=None):

    file_path = cmds.file(q=True, sn=True)
    file_name = os.path.basename(file_path)
    fileName  = file_name.split('_')

    if not shot_node_name:
        shot_node_name = '_'.join(file_name.split('.')[0].split('_')[1:])

    if not task_code:
        task_code = fileName[0]

    if not file_name:
        return

    project  = fileName[1]
    episode  = fileName[2]

    local_drive  = os.getenv('USERPROFILE').replace('\\','/')
    live_drive   = 'L:'

    play_path    = '%s/LIVE/%s/%s/COMMON/MEDIA/%s_%s.mov' % (local_drive,project,episode,task_code,shot_node_name)
    audio_path   = '%s/%s/%s/COMMON/MEDIA/AUD_%s.wav' % (live_drive,project,episode,shot_node_name)

    return play_path, audio_path, task_code, file_path

def doPlayblast(play_path,audio_path,start,end,resolution=(1920,1080)):
    print '-- making playblast'
    if not os.path.exists(os.path.dirname(play_path)):
        os.makedirs(os.path.dirname(play_path))

    resultPath = cmds.playblast(format			= 'avi',
                                sound			= os.path.basename(audio_path.split('.')[0]),
                                filename		= os.path.splitext(play_path)[0],
                                startTime		= start,
                                endTime			= end,
                                forceOverwrite	= True,
                                clearCache		= 1,
                                viewer			= 0,
                                showOrnaments	= 1,
                                framePadding	= 4,
                                widthHeight		= [1920 ,1080],
                                percent			= 100,
                                compression		= 'none',
                                offScreen		= 1,
                                quality			= 70
                                )
    return resultPath

def convertFile(source, destination):
    import subprocess
    print '-- converting --'

    currentFolderPath = (os.path.dirname(os.path.abspath(__file__)))
    PROG_FFMPEG = '%s/ffmpeg/bin/ffmpeg.exe' % (currentFolderPath.replace('\\','/'))
    source = source + '.avi'

    args = [ PROG_FFMPEG, '-y', '-i', '%s' % source, '-r',
             '24' , '-vcodec', 'libx264', '-x264-params', 'b-pyramid=0', '-vprofile', 'baseline',
             '-crf', '22', '-threads', '2', '-pix_fmt', 'yuv420p', '-max_muxing_queue_size', '1024', '-f', 'mov', '%s' % destination]

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    p = subprocess.Popen(args, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    if os.path.exists(destination):
        os.remove(source)

def setPlayblast(shot_node, start, end, camera, AOswitch=True, showHUD=True, addLight=True, convert=True):

    play_path, audio_path, task_code, file_path = getFileName(shot_node_name=shot_node)
    cam_panel,viewport_data,ao_data = viewportDisplay.setPlayblastViewport(camera, AO=AOswitch, displayLight=addLight)

    if showHUD:
        hud = hudDisplay.hudDisplay(shot_node, start, end, camera, task_name=PROCESSCODE_TO_TASK[task_code])

    resultPath = doPlayblast(play_path,audio_path,start,end)

    if convert:
        # convert AVI to MOV
        convertFile(resultPath, play_path)

    viewportDisplay.restorePlayblastViewoport(cam_panel,viewport_data,ao_data)

    if showHUD:
        hud.removeAllHUD()
        return play_path, hud.version_name

    return play_path, '.'.join(play_version.split('.')[:-1])


"""
Example Path
destPath = 'C:/Users/bel.chanathan/WORK/F18/TVS1901/SH0270/ANIMATION/ANM_F18_TVS1901_SH0270.ma'
setPlayblast(destPath, quickPlay = False, AOswitch = True, convert = True, publish = False, showHUD = True, addLight = True)
"""
