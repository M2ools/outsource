import os
import json
import sys
import shiboken
import platform
import maya.OpenMayaUI as mui
import maya.cmds as cmds

from PySide import QtGui as QtGui
from PySide import QtCore

#Import GUI
from Qt import QtCompat

op_sys = platform.system()

modulePath = sys.modules[__name__].__file__
moduleDir  = os.path.dirname(modulePath)

if not moduleDir in sys.path:
    sys.path.append(moduleDir)

def getMayaWindow():

    ptr = mui.MQtUtil.mainWindow()
    if ptr is not None:
        return shiboken.wrapInstance(long(ptr),QtGui.QMainWindow)

class setImporter(QtGui.QMainWindow):
    def __init__(self,parent=None):
        if cmds.window('memeGetURLWindow', exists = True) :
            cmds.deleteUI('memeGetURLWindow')

        self.parent= parent
        passsiveLive = self.getInfo()

        if not os.path.exists(passsiveLive):
            self.launchUI()
            self.initConnect()
        else:
            self.appendSetData(passsiveLive)

    def launchUI(self):
        self.ui = QtCompat.loadUi(moduleDir + '/loadSet.ui')
        self.ui.show()

    def initConnect(self):
        self.ui.convertPushButton.clicked.connect(self.appendSetData)

    def appendSetData(self, refFile=None):
        currentShow = self.getCurrentShow()

        if not currentShow:
            return

        if not refFile:
            refFile = self.ui.textureLineEdit.text().replace('\\', '/')
            if cmds.tabLayout('memeTabsUITabLayout', q=True, st=True) == 'memeAssetsFormLayout':
                currentAssetType = cmds.iconTextScrollList('memeAssetTypeList', q=True, si=True)
                currentAsset = cmds.iconTextScrollList('memeAssetList', q=True, si=True)
                currentVariant = cmds.iconTextScrollList('memeAssetVariantList', q=True, si=True)
                if currentAssetType[0] == 'SET':
                    if currentAsset:
                        refFile = 'L:/%s/SET/%s/ASSEMBLY/ASM_%s_SET_%s' % (currentAsset[0], currentShow, currentAsset[0])
                        if currentVariant:
                            refFile = '%s__%s.json' % (refFile, currentVariant)
                            if not os.path.exists(refFile):
                                return
                        else:
                            refFile = '%s.json' % refFile
                            if not os.path.exists(refFile):
                                return
                    else:
                        return
                else:
                    return
            else:
                return

        nameSpaceCounter = {}

        for each in cmds.file(q=True, r=True):
            if 'GPU/GPU_' not in each and 'RSPROXY/PRX_' not in each:
                continue
            namespace = None
            sdFile = None
            try:
                namespace = cmds.referenceQuery(each, ns=True)[1:]
                sdFile = cmds.referenceQuery(each, f=True, wcn=True)
                if 'RSPROXY/PRX_' in sdFile:
                    sdFile = sdFile.replace('RSPROXY/PRX_', 'GPU/GPU_')
            except:
                continue
            xfData = cmds.xform('%s:Rig_Grp' % namespace, q=1, m=1, ws=True)
            GNS = sdFile.split('/')[-1].split('.')[0].split('_%s_' % currentShow)[-1]
            if not GNS in nameSpaceCounter.keys():
                nameSpaceCounter[GNS] = {'.xform': [], 'PATH': sdFile}
            nameSpaceCounter[GNS]['.xform'].append(xfData)

        with open(refFile, 'r') as reader:
            additionalData = json.load(reader)
        reader.close()

        for key in additionalData.keys():
            if key not in nameSpaceCounter.keys():
                nameSpaceCounter[key] = additionalData[key]
            else:
                for v in additionalData[key]['.xform']:
                    if v in nameSpaceCounter[key]['.xform']:
                        continue
                    else:
                        nameSpaceCounter[key]['.xform'].append(v)

        allReferences = cmds.file(q=True, r=True)
        for e in allReferences:
            if '/GPU/GPU_' in e:
                cmds.file(e, rr=True)

        for key, item in nameSpaceCounter.items():
            if item.has_key('.xform'):
                for x in range(len(item['.xform'])):
                    namespaceName = '%s_%03d' % (key, x)
                    fpath = item['PATH']
                    fpath = fpath.replace('/RSPROXY/PRX_', '/GPU/GPU_')
                    if not os.path.exists(fpath):
                        fpath = item['PATH']
                    if cmds.objExists('%s:Rig_Grp' % namespaceName):
                        cmds.xform('%s:Rig_Grp' % namespaceName, m=item['.xform'][x])
                    elif cmds.objExists('%s:Geo_Grp' % namespaceName):
                        cmds.xform('%s:Geo_Grp' % namespaceName, m=item['.xform'][x])
                    else:
                        cmds.file(fpath, ns=namespaceName, r=True)
                        if cmds.objExists('%s:Rig_Grp' % namespaceName):
                            cmds.xform('%s:Rig_Grp' % namespaceName, m=item['.xform'][x])
                        elif cmds.objExists('%s:Geo_Grp' % namespaceName):
                            cmds.xform('%s:Geo_Grp' % namespaceName, m=item['.xform'][x])


    def getCurrentShow(self):
        currentShow = cmds.file(q=True, sn=True)
        if currentShow:
            currentShow = currentShow.split('/')
            if len(currentShow) > 5:
                currentShow = currentShow[-5]
            else:
                return None
        else:
            return None
        return currentShow

    def getInfo(self):

        file_path   = cmds.file(q=True, sn=True)
        split_path  = os.path.basename(file_path).split('_')
        task_code   = split_path[0]
        prj         = split_path[1]
        ep          = split_path[2]
        shot        = split_path[3].split('.')[0]

        passive_Name    = 'PAS_%s_%s_%s' % (prj, ep, shot)
        setdress_Name   = 'SDRS_%s_%s_%s' % (prj, ep, shot)

        passiveLIVE = 'L:/%s/%s/%s/PASSIVE/%s.json' % (prj, ep, shot,passive_Name)

        return passiveLIVE