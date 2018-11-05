import os
import shutil
import getpass
import glob
import subprocess
import sys
from os.path import basename, join, expanduser

if not 'M:/SCRIPTS/MEME/memeXplorer' in sys.path:
    sys.path.append('M:/SCRIPTS/MEME/memeXplorer')
import memeFTP
import util


_deadline_command = r'C:\Program Files\Thinkbox\Deadline9\bin\deadlinecommand.exe'


if __name__ == '__main__':

    src = r'C:/Users/joey/zip/*.ma'
    comment = 'SEVEN, Anim block, Upload 8'

    meme = memeFTP.memeFiles()
    processCodes = util.getProcessCode()


    passive_cmd = []
    for each in glob.glob(src):
        src_name = os.path.basename(each)
        dst_name = src_name
        for rename in ['BLK']:
            dst_name = dst_name.replace(rename, 'ANM')
        process, PRJ, EP, SH = os.path.splitext(dst_name)[0].split('_')[:4]
        local_dir = 'C:/Users/{}/WORK/{}/{}/{}/{}'.format(
            getpass.getuser(), PRJ, EP, SH, processCodes[process])
        if local_dir is None:
            continue

        local_file = '{}/{}'.format(local_dir, dst_name)
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        shutil.copyfile(each, local_file)


        meme.checkIn(local_file, comment)

        w_file = 'W:' + (local_dir + '/' + basename(local_file)).split('/WORK')[1]
        passive_cmd.append(w_file)

    command_for_deadline = []
    for each in passive_cmd:
        cmd = '"C:/Program Files/Autodesk/Maya2016/bin/mayapy.exe" '\
              '"M:/SCRIPTS/MEME/memeXplorer/makePassiveScene.py" -p '
        cmd += each
        command_for_deadline.append(cmd)
        # print cmd

    doc_path = join(expanduser('~'), 'Documents')
    job_file = join(doc_path, 'job.txt')
    plugin_file = join(doc_path, 'plugin.txt')
    command_file = join(doc_path, 'command.txt')
    info = 'Plugin=CommandScript\n' \
           'Pool=all\n' \
           'Group=cpu\n' \
           'ChunkSize=1\n' \
           'Frames=0-{}\n'.format(len(passive_cmd)-1)
    info += 'Name=Make Passive, {}\n'.format(comment)
    with open(join(doc_path, 'job.txt'), 'w') as f:
        f.write(info)
    with open(join(doc_path, 'plugin.txt'), 'w') as f:
        f.write('')
    with open(join(doc_path, 'command.txt'), 'w') as f:
        f.write('\n'.join(command_for_deadline))
    subprocess.call([_deadline_command, job_file, plugin_file, command_file])

