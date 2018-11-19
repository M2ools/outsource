import maya.cmds as cmds

def setPlayblastViewport(camera, AO=True, viewport2=True, displayLight=True):

    if not camera:
        print "Error : Camera Not found. Please check shot camera in camera sequencer"
        return

    cam_panel     = controlPanels(camera)
    viewport_data,ao_data = collectViewportData(cam_panel)

    setShowViewport(cam_panel, isAO=AO, isViewport2=viewport2, isLight=displayLight)

    camShape = camera if 'Shape' in camera else cmds.listRelatives(camera, shapes=True)[0]

    try:
        cmds.setAttr(('%s.overscan' % camShape), 1.0)

    except RuntimeError:
        print 'Runtime Error: {0}'.format(RuntimeError)
        pass

    if displayLight:
        addLight(camera)

    return cam_panel,viewport_data,ao_data

def restorePlayblastViewoport(cam_panel, viewport_data=None, ao_data=None):
    playblastTmpLight_Grp = 'playblastTmpLight_Grp'
    if cmds.objExists(playblastTmpLight_Grp):
        cmds.delete(playblastTmpLight_Grp)



    for key, value in viewport_data.items():
        if 'modelEditor' in key:
            continue
        setView_value = 'cmds.modelEditor(cam_panel, edit = True,{attr} = {value})'.format(attr=key, value=value)

        try:
            eval(setView_value)
        except Exception as error:
            # print "Exception: {0}".format(error)
            pass

    for key,item in ao_data.items():
        cmds.setAttr(key,item)


def controlPanels(cameraName):
    panals = [ n for n in cmds.getPanel( type="modelPanel") if cmds.modelPanel( n, query=True, camera=True) == cameraName]
    panel_name = panals[0] if panals else 'modelPanel4'
    cmds.lookThru(cameraName)

    return panel_name

def collectViewportData(curr_panal):

    modelEditors        = cmds.modelEditor(curr_panal, q=True, sts=True)
    modelEditorList     = modelEditors.replace('  ', '').replace('\n', '').split('-')

    data = {}
    for i in modelEditorList:
        splits          = i.split(' ')
        data[splits[0]] = ' '.join(splits[1:])

    ao_data = {'hardwareRenderingGlobals.ssaoEnable': cmds.getAttr('hardwareRenderingGlobals.ssaoEnable'),
               'hardwareRenderingGlobals.multiSampleEnable': cmds.getAttr('hardwareRenderingGlobals.multiSampleEnable'),
               'hardwareRenderingGlobals.ssaoRadius':cmds.getAttr('hardwareRenderingGlobals.ssaoRadius'),
               'hardwareRenderingGlobals.ssaoFilterRadius':cmds.getAttr('hardwareRenderingGlobals.ssaoFilterRadius'),
               'hardwareRenderingGlobals.ssaoSamples':cmds.getAttr('hardwareRenderingGlobals.ssaoSamples')}

    return data, ao_data

def setShowViewport(cam_panel, isAO=True, isViewport2=True, isLight=True):

    lightOn         = 'all' if isLight else 'default'

    renderer_mode   = 'vp2Renderer' if isViewport2 else 'base_OpenGL_Renderer'
    if 'CROWD/CWD_' in cmds.file(q=True, sn=True):
        renderer_mode = 'base_OpenGL_Renderer'

    cmds.colorManagementPrefs(e=True, cmEnabled=True)
    cmds.modelEditor(cam_panel, edit = True, allObjects = False)
    cmds.modelEditor(cam_panel, edit = True, displayAppearance = 'smoothShaded',
                                           displayTextures  = True,
                                           displayLights    = lightOn,
                                           nurbsSurfaces    = True,
                                           polymeshes       = True,
                                           dynamics         = True,
                                           fluids           = True,
                                           rendererName     = renderer_mode,
                                           twoSidedLighting = True
                                           )
    if cmds.pluginInfo('gpuCache.mll',q=True,l=True):
        cmds.modelEditor(cam_panel, edit=True, pluginObjects = ('gpuCacheDisplayFilter', True))

    cmds.setAttr('hardwareRenderingGlobals.ssaoEnable',True)
    cmds.setAttr('hardwareRenderingGlobals.multiSampleEnable',True)

    if not isAO:
        cmds.setAttr('hardwareRenderingGlobals.ssaoEnable',False)
        cmds.setAttr('hardwareRenderingGlobals.multiSampleEnable',False)

    cmds.setAttr('hardwareRenderingGlobals.ssaoRadius',16)
    cmds.setAttr('hardwareRenderingGlobals.ssaoFilterRadius',16)
    cmds.setAttr('hardwareRenderingGlobals.ssaoSamples',16)

def addLight(camera, add=True):
    if not cmds.objExists(camera):
        print 'No camera exists', camera

    playLightGrp = 'playblastTmpLight_Grp'

    if cmds.objExists(playLightGrp):
        cmds.delete(playLightGrp)

    if add:
        if not cmds.objExists(playLightGrp):
            playLightGrp = cmds.group(empty=True, name=playLightGrp)

        direcLight_grpName  = createDirectlight()
        cmds.parent(direcLight_grpName, playLightGrp)
        ambLight_Name = createAmblight()
        cmds.parent(ambLight_Name, playLightGrp)

        if cmds.objExists(camera):
            cam_grp = cmds.listRelatives(camera,ap=True)
            if not cam_grp:
                cmds.parentConstraint(camera, direcLight_grpName, weight=1, maintainOffset=False)
            else:
                cmds.parentConstraint(cam_grp, direcLight_grpName, weight=1, maintainOffset=False)

def createDirectlight():

    direcLight_nameGrp = 'directLight_Grp'

    if cmds.objExists('directLight'):
        cmds.delete('directLight')

    if not cmds.objExists(direcLight_nameGrp):
        direcLight_nameGrp  = cmds.group(empty=True, name=direcLight_nameGrp)

    create_DirectLight      = cmds.CreateDirectionalLight()
    directLight_new_Name    = cmds.rename(create_DirectLight, 'directLight')
    directLight_Shape       = cmds.listRelatives(directLight_new_Name, shapes=True)
    direcLight_Parent       = cmds.listRelatives(directLight_Shape, parent=True)

    if not direcLight_Parent == direcLight_nameGrp:
        cmds.parent(direcLight_Parent, direcLight_nameGrp)

    cmds.setAttr(directLight_Shape[0] + '.shadowColor', 1, 1, 1, type='double3')
    cmds.setAttr(directLight_Shape[0] + '.intensity', 0.6)
    cmds.xform(directLight_new_Name, rotation=[30, -30, -90])

    return direcLight_nameGrp

def createAmblight():

    ambLight_Name   = 'amb_light'
    if cmds.objExists(ambLight_Name):
        cmds.delete(ambLight_Name)

    ambLight_Shape  = cmds.ambientLight(intensity=0.2, name=ambLight_Name)
    ambLight_Name   = cmds.listRelatives(ambLight_Shape, parent=True)

    return ambLight_Name

