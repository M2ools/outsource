# --- memePlayblast Script ---

import playblastOptions
reload(playblastOptions)

mov_path = playblastOptions.run()
result = cmds.confirmDialog( title='Playblast', message='Finish.', button=['OK'])
if result:
    import subprocess
    subprocess.Popen('explorer /select,"%s"' %mov_path[0][0].replace('/','\\'))

# --- end ---