import subprocess
import sys
import os
import shutil
import getpass
import glob
from os.path import isfile, join, expanduser
import util
if not 'M:/SCRIPTS/MEME/memeXplorer' in sys.path:
    sys.path.append('M:/SCRIPTS/MEME/memeXplorer')
if not 'M:/SCRIPTS/MEME/memeBots/shotgun' in sys.path:
    sys.path.append('M:/SCRIPTS/MEME/memeBots/shotgun')
import memeFTP


_deadline_command = r'C:\Program Files\Thinkbox\Deadline9\bin\deadlinecommand.exe'


if __name__ == '__main__':
    src = 'C:/Users/joey/zip/*.mov'
    comment = 'SEVEN, Anim block, Upload 8'
    
    # task = 'ANM'
    meme = memeFTP.memeFiles()
    processCodes = util.getProcessCode()

    # rename and put to local
    cmd = []
    for each in glob.glob(src):
        src_name = os.path.basename(each)
        dst_name = src_name
        for rename in ['BLK']:
            dst_name = dst_name.replace(rename, 'ANM')
        process, PRJ, EP, SH = os.path.splitext(dst_name)[0].split('_')[:4]
        local_dir = 'C:/Users/{}/LIVE/{}/{}/COMMON/MEDIA'.format(
            getpass.getuser(), PRJ, EP)
        if local_dir is None:
            continue

        local_file = '{}/{}'.format(local_dir, dst_name)
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        shutil.copyfile(each, local_file)

        print 'Publishing ', local_file
        meme.publishLive(local_file, comment)

        # Publish
        live_file = 'L:/{}/{}/COMMON/MEDIA/{}'.format(
                    PRJ, EP, dst_name)
        if not isfile(live_file):
            print 'LIVE file not exists', live_file
            # continue
        cmd.append(live_file)



    # for each in cmd:
    #
    #     print 'M:/SCRIPTS/PACKAGES/python27/python.exe ' \
    #           'M:/SCRIPTS/MEME/memeBots/shotgun/mediaPublish.py -f '
    #     each

    command_for_deadline = []
    for each in cmd:
        tmp = 'M:/SCRIPTS/PACKAGES/python27/python.exe ' \
              'M:/SCRIPTS/MEME/memeBots/shotgun/mediaPublish.py -f '
        tmp += each
        command_for_deadline.append(tmp)
        # print tmp

    doc_path = join(expanduser('~'), 'Documents')
    job_file = join(doc_path, 'job.txt')
    plugin_file = join(doc_path, 'plugin.txt')
    command_file = join(doc_path, 'command.txt')
    info = 'Plugin=CommandScript\n' \
           'Pool=all\n' \
           'Group=cpu\n' \
           'ChunkSize=1\n' \
           'Frames=0-{}\n'.format(len(cmd)-1)
    info += 'Name=Playblast to Shotgun, {}\n'.format(comment)
    with open(join(doc_path, 'job.txt'), 'w') as f:
        f.write(info)
    with open(join(doc_path, 'plugin.txt'), 'w') as f:
        f.write('')
    with open(join(doc_path, 'command.txt'), 'w') as f:
        f.write('\n'.join(command_for_deadline))
    subprocess.call(
            [_deadline_command, job_file, plugin_file, command_file])
