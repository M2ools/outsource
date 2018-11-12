import maya.cmds as cmds
import os

def loadLooks(type='DPL', refNode=None):
    # print 'Cleaning Looks'
    sharedR = cmds.ls('sharedReferenceNode*')
    if cmds.objExists('setupTimeRange'):
        cmds.delete('setupTimeRange')
    if '/LIGHTING/' in cmds.file(q=True, sn=True):
        try:
            cmds.editRenderLayerGlobals(currentRenderLayer='defaultRenderLayer')
        except:
            print 'Failed updating shaders'
            return
    if sharedR:
        cmds.delete(sharedR)

    # --- if refNode is not passed, just take all references in the scene
    refs = []
    if not refNode:
        refs = cmds.file(q=True,r=True)
    else:
        refs = [cmds.referenceQuery(refNode, f=True)]

    # --- filter out invalid references...
    filteredRefs = []
    for each in refs:
        if '/LOOKS/' in each:
            if '{' in each:
                try:
                    cmds.file(each,rr=True)
                except Exception as e:
                    print e
            '''
            else:
                #cmds.file(each,rr=True)
                try:
                    rfn = cmds.referenceQuery(each,rfn=True)
                    cmds.file(ur=rfn)
                    cmds.referenceEdit(rfn,r=True)
                    cmds.file(lr=rfn)

                except Exception as e:
                    print e
            '''
            continue

        # skip sound references
        if '.wav' in each:
            continue

        # skip references without use of namespace
        try:
            cmds.referenceQuery(each, namespace=True)
        except Exception as e:
            print each
            print e
            continue

        filteredRefs.append(each)

    # print 'Cleaned Looks'

    # --- looping each filter reference paths...
    for each in filteredRefs:
        shadingSets = []
        isCrowd = False
        nameSpace = cmds.referenceQuery(each,namespace=True)[1:]

        # --- reference looks, collect shading sets...
        # crowd case
        if '__CROWD.abc' in each:
            print 'Applying looks to crowd: %s' %each
            lookName = each.replace('.abc', '.ma')
            lookBase = lookName.split('/')[-1].split('.')[0]
            if lookName not in cmds.file(q=True,r=True):
                lookName = cmds.file(lookName, ns=lookBase, sharedReferenceFile=False, r=True)
            lookBase = cmds.referenceQuery(lookName, namespace=True)[1:]
            shadingSets = cmds.ls('%s:*' % lookBase, type='shadingEngine')
            isCrowd = True

        # normal case
        elif '/SETUP/STP_' in each or '/PASSIVE/PAS_' in each or '/GEO/GEO_' in each or '/RENDER/PAS_' in each:
            # if this is a passive asset, look for setup path in memeName attribute on Geo_Grp
            if '/PASSIVE/PAS_' in each or '/RENDER/PAS_' in each:
                if cmds.objExists('%s:Geo_Grp.memeName'%nameSpace):
                    each = cmds.getAttr('%s:Geo_Grp.memeName'%nameSpace)
                else:
                    continue
            lookName = None
            lookBase = None
            if '/SETUP/STP_' in each:
                lookName = each.replace('.mb', '.ma')
                lookName = lookName.replace('/SETUP/', '/LOOKS/')
                lookBase = lookName.split('/')[-1].split('.')[0].replace('STP_', '%s_' %type)
                lookParts = lookName.split('/STP_')[0]
                lookName = '%s/%s/%s.ma' % (lookParts, lookBase, lookBase)
            elif '/GEO/GEO_' in each:
                lookName = each.replace('/GEO/', '/LOOKS/')
                lookBase = lookName.split('/')[-1].split('.')[0].replace('GEO_', '%s_' %type)
                lookParts = lookName.split('/GEO_')[0]
                lookName = '%s/%s/%s.ma' % (lookParts, lookBase, lookBase)

            if lookName:
                if not os.path.exists(lookName):
                    print 'Look path does not exists: %s' %lookName
                    continue
            # --- figure out if adding new reference is needed
            addNewRef = True
            # if already have the reference 
            if lookName in cmds.file(q=True,r=True):
                lookBase = cmds.referenceQuery(lookName, ns=True)[1:]
                shadingSets = cmds.ls('%s:*' % lookBase, type='shadingEngine')
                sgWithMemeConnect = [s for s in shadingSets if cmds.objExists('%s.memeConnect' %s) or cmds.objExists('%s.ptConnect' %s)]
                # if none of the SGs has ptConnect/memeConnect, reuse the look
                if not sgWithMemeConnect: 
                    addNewRef = False
            if not lookName:
                addNewRef = False

            # need to add new reference for the look
            if addNewRef:
                referedPath = cmds.file(lookName, ns=lookBase,sharedReferenceFile=False, r=True)
                lookBase = cmds.referenceQuery(referedPath, ns=True)[1:]

            # list all shading engines within the namespace
            shadingSets = cmds.ls('%s:*' % lookBase, type='shadingEngine')

            # also list RedshiftMeshParameters
            if type == 'LUK':
                shadingSets.extend(cmds.ls('%s:*'%lookBase, type='RedshiftMeshParameters'))
            
            # assign lambert1 to all of geoGrp first
            geoGrpChildren = cmds.listRelatives('%s:Geo_Grp' %nameSpace, ad=True, type='transform', f=True)
            if shadingSets and geoGrpChildren:
                geos = []
                for tr in geoGrpChildren:
                    shapes = cmds.listRelatives(tr, shapes=True, type='mesh', f=True, ni=True)
                    if not shapes:
                        continue
                    shp = shapes[0]
                    geos.append(shp)
                    # get rid of connections to reference node placeHolderList (failed connectAttr edits)
                    refConnections = cmds.listConnections(shp, d=True, s=False, p=True, c=True, type='reference')
                    if refConnections:
                        for s, d in zip(refConnections[0::2], refConnections[1::2]):
                            if '.placeHolderList' in d:
                                try:
                                    cmds.disconnectAttr(s, d)
                                except Exception, e:
                                    print e
                                    print 'Cannot disconnect %s from placeHolderList' %shp
                    
                cmds.sets(geos, e=True, fe='initialShadingGroup', nw=True)

        # ---------------------------------------------------------------------------------
        # looping each shadingSets
        for eachShader in shadingSets:
            setType = cmds.nodeType(eachShader)
            # assign/add to sets
            asignAttr = None
            if cmds.objExists('%s.memeAssign' % eachShader):
                asignAttr = '%s.memeAssign' % eachShader
            elif cmds.objExists('%s.ptAssign' % eachShader):
                asignAttr = '%s.ptAssign' % eachShader
            if asignAttr:
                objects = cmds.getAttr(asignAttr)
                for obj in objects.split('#'):
                    extingObj = None
                    if cmds.objExists('%s:%s' % (nameSpace, obj)):
                        extingObj = '%s:%s' % (nameSpace, obj)
                    elif cmds.objExists('%s:%sDeformed' % (nameSpace, obj)):
                        extingObj = '%s:%sDeformed' % (nameSpace, obj)
                    elif '.f[' in obj:
                        splits = obj.split('.')
                        objName = '%s:%sDeformed.%s' %(nameSpace, splits[0], splits[1])
                        if cmds.objExists(objName):
                            extingObj = objName
                    elif cmds.objExists('%s:%sShapeDeformed' % (nameSpace, obj)):
                        extingObj = '%s:%sShapeDeformed' % (nameSpace, obj)

                    objToAssign = None
                    fSplit = ''
                    if extingObj:
                        if not isCrowd:
                            # split .f
                            if '.f[' in extingObj:
                                objSplits = extingObj.split('.f[')
                                extingObj = objSplits[0]
                                fSplit = objSplits[1]

                            objTyp = cmds.nodeType(extingObj)
                            if objTyp == 'transform':
                                # get the shape
                                shapes = cmds.listRelatives(extingObj, s=True, ni=True, pa=True, type='mesh')
                                if shapes:
                                    objToAssign = shapes[0]
                                else:
                                    objToAssign = extingObj
                            elif objTyp == 'mesh':
                                # get the transform first
                                trs = cmds.listRelatives(extingObj, p=True)
                                if trs:
                                    # then get the most available shape
                                    shapes = cmds.listRelatives(trs[0], s=True, ni=True, pa=True, type='mesh')
                                    if shapes:
                                        objToAssign = shapes[0]
                        else: # if it's a crowd asset just take the name from strings
                            objToAssign = extingObj

                        if objToAssign:
                            if fSplit:
                                objToAssign = '%s.f[%s' %(objToAssign, fSplit)
                            if setType == 'shadingEngine':
                                try:
                                    # print 'assigning %s with %s' %(objToAssign, eachShader)
                                    cmds.sets(objToAssign, e=True, fe=eachShader, nw=True)
                                except Exception as e:
                                    pass
                                    # print e

                            elif setType == 'RedshiftMeshParameters':
                                try:
                                    # print 'RS %s with %s' %(objToAssign, eachShader)
                                    cmds.sets(objToAssign, e=True, add=eachShader, nw=True)
                                except Exception as e:
                                    pass
                                    # print e

            # connect rig to shaders
            conAttr = None
            if cmds.objExists('%s.memeConnect' % eachShader):
                conAttr = '%s.memeConnect' % eachShader
            elif cmds.objExists('%s.ptConnect' % eachShader):
                conAttr = '%s.ptConnect' % eachShader
            if conAttr:
                conStr = cmds.getAttr(conAttr)
                conPairs = conStr.split('#')
                for pairStr in conPairs:
                    src, des = pairStr.split(',')
                    src = '%s:%s' % (nameSpace, src)
                    des = '%s:%s' % (lookBase, des)
                    
                    if cmds.objExists(src) and cmds.objExists(des) and not cmds.isConnected(src, des):
                        #print 'Connected: %s to %s' % (src, des)
                        try:
                            cmds.connectAttr(src, des, f=True)
                        except Exception as e:
                            pass
                            # print e

    # remove unused looks
    toRem = []
    for ref in [r for r in cmds.file(q=True, r=True) if '/LOOKS/' in r]:
        ns = cmds.referenceQuery(ref, ns=True)[1:]
        sgs = cmds.ls('%s:*' %ns, type='shadingEngine')
        for sg in sgs:
            if cmds.sets(sg, q=True):
                break
        else:
            toRem.append(ref)
    for ref in toRem:
        try:
            cmds.file(ref, rr=True)
        except Exception as e:
            print e


    print "Shader update sucessful"


def applyAssetLooks(fileName,type):
    removeItem = 'LUK'
    if type == 'LUK':
        removeItem = 'DPL'
    base = fileName.split('/')[-1].split('.')[0]
    host = '%s/WORK/'%fileName.split('/WORK/')[0]
    prefix = base.split('_')[0]
    b = base.replace(prefix,type)
    base = 'LOOKS/%s/%s.ma'%(b,b)
    references = cmds.file(q=True,r=True)
    namespaces = []
    lookNamespaces = []
    for each in references:
        if '/LOOKS/' in each:
            lookNamespaces.append(cmds.referenceQuery(each,ns=True)[1:])
        if '/MEDIA/' in each:
            continue
        try:
            cmds.referenceQuery(each,namespace=True)
        except:
            continue
        namespaces.append(cmds.referenceQuery(each,ns=True)[1:])


    lookFileName = ''
    if '/SETUP/' in fileName:
        fparts = fileName.split('/SETUP/')
        lookFileName = '%s/%s'%(fparts[0],base)

    if '/MODEL/' in fileName:
        fparts = fileName.split('/MODEL/')
        lookFileName = '%s/%s'%(fparts[0],base)

    lookFileName=lookFileName.replace('/','/')

    lookFileName = lookFileName.replace(host,'L:')
    lookFileName = lookFileName.replace('W:/', 'L:/')
    removeLookFileName = lookFileName.replace('%s_'%type,'%s_'%removeItem)
    references = cmds.file(q=True,r=True)
    lookBase = None
    if removeLookFileName in references:
        cmds.file(removeLookFileName,rr=True)
    if lookFileName not in references:
        cmds.file(lookFileName, ns=b, r=True)
        lookBase = b
    else:
        lookBase = cmds.referenceQuery(lookFileName, ns=True)[1:]
    # edits = cmds.referenceQuery(lookFileName, es=True, scs=True)
    for eachShader in cmds.ls('%s:*' % lookBase, type='shadingEngine'):
        if cmds.objExists('%s.ptAssign' % eachShader):
            objects = cmds.getAttr('%s.ptAssign' % eachShader)
            objects = objects.split('#')
            for obj in objects:
                if cmds.objExists(obj):
                    cmds.select(obj)
                    cmds.sets(e=True, fe=eachShader)
                else:
                    for r in namespaces:
                        if cmds.objExists('%s:%sShapeDeformed' % (r, obj)):
                            cmds.select('%s:%sShapeDeformed' % (r, obj))
                            cmds.sets(e=True, fe=eachShader)
                        elif cmds.objExists('%s:%sDeformed'%(r,obj)):
                            cmds.select('%s:%sDeformed' % (r, obj))
                            cmds.sets(e=True, fe=eachShader)
                        elif cmds.objExists('%s:%s'%(r,obj)):
                            cmds.select('%s:%s'%(r,obj))
                            cmds.sets(e=True, fe=eachShader)

        if cmds.objExists('%s.ptConnect' % eachShader):
            conStr = cmds.getAttr('%s.ptConnect' % eachShader)
            conPairs = conStr.split('#')
            for pairStr in conPairs:
                src, des = pairStr.split(',')
                des = '%s:%s'%(lookBase, des)
                if cmds.objExists(des):
                    if cmds.objExists(src):
                        cmds.connectAttr(src, des, f=True)
                    else:
                        for r in namespaces:
                            srcNs = '%s:%s'%(r, src)
                            if cmds.objExists(srcNs):
                                print 'Connected: %s to %s' %(srcNs, des)
                                cmds.connectAttr(srcNs, des, f=True)