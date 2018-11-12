import re
from datetime import datetime
import maya.cmds as cmds
import os

HUD_POSITION = [(5, 3), (7, 3), (9, 3),
                (5, 2), (7, 2), (9, 2),
                (5, 1), (7, 1), (9, 1)]

class hudDisplay(object):
    def __init__(self, shot_node='', start_frame='', end_frame='', camera_name='', task_name=''):

        self.shot_node   = shot_node
        self.camera_name = camera_name
        self.start_frame = start_frame
        self.end_frame   = end_frame
        self.task_name   = task_name

        file_name = cmds.file(q=True,sn=True)

        if file_name:
            self.project_name = file_name.split('/')[-1].split('_')[1]

            if not self.task_name:
                self.task_name = file_name.split('/')[-2]

            self.version_name = self.getFileVersionName(file_name)

        hud_set = 'all'
        print 'hud_set: {0}'.format(hud_set)

        self.removeAllHUD()

        if shot_node:
            hudNameDict = self.getHudData(self.camera_name, hud_set)
            self.showHeadsUpDisplay(hudNameDict)

    def getHudData(self, curr_cam, hud_setting='all'):

        class objStr(object):

            def __init__(self, parent = None, **kwargs):
                super(objStr, self).__init__()
                self.parent = parent
                self.my_comp_cam, self.my_time_of_day = self.parent.hudShotgun(self.parent.project_name, self.parent.shot_node)
                self.my_curr_cam = kwargs.get('curr_cam', '')
                self.my_user_name = os.getenv('USERPROFILE').replace('\\','/').split('/')[-1]

            def curr_cam(self):
                return self.my_curr_cam

            def shot_name(self,shot_name):
                return '_'.join(self.parent.shot_node.split('_')[2:])

            def user_name(self):
                return self.my_user_name.upper()

            def comp_cam(self):
                return self.my_comp_cam

            def time_of_day(self):
                return self.my_time_of_day

            def task_name(self):
                return self.parent.task_name.upper()

            def version_name(self):
                return self.parent.version_name

        myObjStr = objStr(parent = self, curr_cam = curr_cam)

        if hud_setting == 'all':
            hudNameDict = [['ArtistHud',myObjStr.user_name], ['FocalLengthHud', lambda  : self.hudFocalLength(curr_cam)], ['TaskNameHud',myObjStr.task_name],
                           ['DateTimeHud',self.hudDateTime], ['CamCompFxHud',myObjStr.comp_cam], ['FrameHud',self.hudShotFrame],
                           ['FileNameHud',myObjStr.version_name], ['CameraNameHud',myObjStr.curr_cam], ['TimeOfDayHud',myObjStr.time_of_day]]

        return hud_setting,hudNameDict


    def removeAllHUD(self):
        for hud in cmds.headsUpDisplay(listHeadsUpDisplays=True):
            if cmds.headsUpDisplay(hud, exists=True):
                cmds.headsUpDisplay(hud, edit=True, visible=False)

        for column, row in HUD_POSITION:
            cmds.headsUpDisplay(removePosition=(column, row))


    def showHeadsUpDisplay(self, hud_data):

        if 'quick' in hud_data[0]:
            dataFontSize = 'large'
            labelFontSize = 'large'
            labelWidth = 130

        else:
            dataFontSize = 'large'
            labelFontSize = 'large'
            labelWidth = 130

        hud_data = (hud_data)[1]
        for i, hud in enumerate(hud_data):
            if not hud:
                continue
            re_hud      = re.findall('[A-Z][^A-Z]*', hud[0].split('Hud')[0])
            hud_display = ' '.join(re_hud+[': '])
            hud_name    = hud[0]
            hud_command = hud[1]
            section     = HUD_POSITION[i][0]
            block       = HUD_POSITION[i][1]
            #
            cmds.headsUpDisplay(hud_name,
                              section           = section,
                              block             = block,
                              label             = hud_display.upper(),
                              blockAlignment    = 'left',
                              labelWidth        = labelWidth,
                              dataFontSize      = dataFontSize,
                              labelFontSize     = labelFontSize,
                              attachToRefresh   = True,
                              command           = hud_command)


    def hudShotgun(self,project_name,shot_name):
        try:
            import connect
            reload(connect)

            comp_cam, time_of_day = connect.getHudShotgun(project_name,shot_name)
            return comp_cam, time_of_day

        except ImportError as E:
            return ' ', ' '
            pass

    def hudShotFrame(self) :
        # FRAME : 0001/0047
        current = (cmds.currentTime(q=True) + 1) - self.start_frame if cmds.currentTime(q=True) else 0
        overall = (self.end_frame + 1) - self.start_frame
        return '%04d/%04d' %(current, overall)

    def hudDateTime(self):
        return datetime.now().strftime('%y-%m-%d %H:%M:%S')

    def hudFocalLength(self, curr_cam):
        return '%.2f' %cmds.getAttr( curr_cam+'.focalLength')

    def getFileVersionName(self, file_name, publish=False):
        return os.path.basename(file_name)
