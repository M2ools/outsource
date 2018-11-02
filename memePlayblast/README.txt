# --- memePlayblast Script ---

import sys
sys.path.insert(0,' -------- Input memePlayblast script path -------- ')
# memePlayblast script path Example : 'C:\Users\~UserName~\Documents\maya\2016\scripts\memePlayblast' 

import playblastOptions
reload(playblastOptions)

mov_path = playblastOptions.run()
result = cmds.confirmDialog( title='Playblast', message='Finish.', button=['OK'])
if result:
    import subprocess
    subprocess.Popen('explorer /select,"%s"' %mov_path[0][0].replace('/','\\'))

# --- end ---