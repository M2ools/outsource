import os
import argparse
import json
import getpass

domain_link = 'https://m2a.shotgunstudio.com'
login       = 'seveneleven'
password    = 'outsourceStudio711'

PROCESSCODE_TO_TASK = {'LAY': 'layout',
                       'ANM': 'animation',
                       'LIT': 'lighting',
                       'REN': 'render',
                       'CWD': 'crowd',
                       'CMP': 'compositing',
                       'EDT': 'edit',
                       'GRD': 'grading',
                       'EFX': 'effects',
                       'ANI': 'animation',
                       'COM': 'compositing',
                       'CST': 'construct'}

default_thumb_path = '%s/icons/XPLORER.png' % (os.path.dirname(os.path.abspath(__file__)).replace('\\','/'))

def connect():
    from Shotgun import shotgun_api3
    return shotgun_api3.Shotgun(domain_link,login = login, password = password)

def setup_parser(arguments, title):
    parser = argparse.ArgumentParser(description=title, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    for key, value in arguments.items():
        parser.add_argument('-%s' % key, dest=value['dest'], type=type(value["default"]), help=value["help"],
                            default=value["default"])
    return parser

def parse(arguments=None, title=None):
    if arguments is None:
        return None
    if type(arguments) is not type({}):
        if arguments.endswith('.json'):
            with open(arguments) as data_file:
                arguments = json.load(data_file)
    parser = setup_parser(arguments, title)
    return parser

class PublishError(Exception): pass

"""
movie_path   = L:/F18/TVS1901/COMMON/MEDIA/LAY_F18_TVS1901_SH0430.mov
version_name = LAY_F18_TVS1901_SH0430.V001.R001
user = 
"""
class Shot(object):

    PADDING = 3
    def __init__(self, movie_path, version_name, user=None, task_name='', meme_task=''):
        self.SG = connect()

        print '='*10
        print 'publish',version_name
        self.task_name = task_name
        self.task_ent = None
        self.prj_ent  = None
        self.epi_ent  = None
        self.shot_ent = None
        self.seq_ent  = None
        self.movie_file   = movie_path
        self.path_frames  = None
        self.version_name = version_name
        self.user = 'studio.seveneleven'
        self.user_ent = self.SG.find_one('HumanUser', filters = [['id', 'is', 895]], fields = ['name', 'email', 'id', 'sg_localuser'])

        self.getShotgunInfo(meme_task)

    def getShotgunInfo(self,meme_task=''):

        prj_dict       = {'F18' : 'Lego_frd'}
        file_name      = os.path.basename(self.movie_file)
        task_code      = file_name.split('_')[0]
        prj_name       = file_name.split('_')[1]
        type_name      = file_name.split('_')[2]
        asset_name     = file_name.split('_')[3].split('.')[0]

        asset_fullName = '{0}_{1}_{2}'.format(prj_name, type_name, asset_name)

        if not self.task_name:
            self.task_name  = PROCESSCODE_TO_TASK[str(task_code)]

        self.prj_ent  = self.SG.find_one('Project', [['name', 'is', prj_dict[prj_name]]], ['code', 'id'])

        self.epi_ent  = self.SG.find_one('Scene', [['project', 'is', self.prj_ent], ['code', 'is', type_name]],
                                        ['code', 'id'])

        self.shot_ent = self.SG.find_one('Shot', [['project', 'is', self.prj_ent],
                                                  ['code', 'is', asset_fullName]],
                                         ['code', 'id', 'sg_sequence'])
        try:
            if self.shot_ent.has_key('sg_sequence') and self.shot_ent['sg_sequence']:
                self.seq_ent  = {'type':'Sequence','id': self.shot_ent['sg_sequence']['id'] }

        except Exception as e :
            pass

        task_filters = [ ['project', 'is', self.prj_ent],
                         ['entity', 'is', self.shot_ent],
                         {  'filter_operator':'any',
                            'filters': [ ['content','is',self.task_name] ]
                         }
                        ]
        if meme_task:
            task_filters[-1]['filters'].append(['sg_meme_task','is',meme_task])
        self.task_ent = self.SG.find_one('Task', task_filters, ['id', 'content'])

    def createTask(self,thumb_path=default_thumb_path):

        TASK_STEPID = {'layout':13,'animation':5,'comp':8,'effects': 55}

        data = { 'project' : self.prj_ent,
                 'step' :{'type':'Step', 'id':TASK_STEPID[self.task_name]},
                 'entity' : self.shot_ent,
                 'content' : self.task_name}

        self.task_ent = self.SG.create('Task', data)
        self.SG.upload_thumbnail('Task', self.task_ent['id'], thumb_path)

    def createVersion(self, version_name, status='daily', description='', movieFile='', thumbnailPath='', framePaths=''):
        print 'Create Version'

        if not description:
            description = 'Publish %s'%self.version_name

        data = {'project': self.prj_ent,
                'code': version_name,
                'entity': self.shot_ent,
                'sg_task': self.task_ent,
                'sg_status_list': status,
                'description': description}

        if self.user_ent:
            data['user'] = self.user_ent

        if movieFile:
            data['sg_path_to_movie'] = movieFile.replace('/','\\\\')

        if framePaths:
            data['sg_path_to_frames'] = framePaths.replace('/','\\\\')

        versionEnt = self.SG.create('Version', data)

        if thumbnailPath:
            # upload thumbnail picture
            self.SG.upload_thumbnail('Version', versionEnt['id'], thumbnailPath)
        if movieFile:
            # upload thumbnail video
            print 'Upload Thumbnail'
            self.SG.upload('Version', versionEnt['id'], movieFile, 'sg_uploaded_movie')

        print 'version created : {0}'.format(version_name)
        return versionEnt

    def removeVersionFail(self,versionEnt):
        self.SG.delete('Version',versionEnt['id'])

    def publish(self, thumb_path=default_thumb_path, status='noaprv', comment='', path_frames=''):
        import time

        def correctErrorData(m, time, level = 'ERROR',):
            import datetime
            import socket
            import getpass

            log_dir = 'O:/studioTools/logs/memePublish/mediaPublish'
            if not os.path.exists(log_dir):
                return

            log_name = str(datetime.datetime.now().strftime("%m-%y")) + '.log'
            log_path = "%s/%s" % (log_dir, log_name)

            datetime = datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S")
            _message = "\n{datetime} - {machine}:{user} - {level} - {time:.02f} - {message}"
            _message = _message.format(datetime=datetime,
                                       machine=socket.gethostname(),
                                       user=getpass.getuser(),
                                       level = level,
                                       time = float(time),
                                       message=m)
            with open(log_path, 'a') as f:
                f.write(_message)

        start = time.time()
        end = time.time()
        version_ent = None
        try:
            if not self.task_ent:
                print 'No task exists', self.task_name
                return None

            if path_frames:
                self.path_frames = path_frames

            if not comment:
                comment = 'publish from %s' %self.version_name

            time.sleep(15)
            if not os.path.exists(thumb_path):
                print '{0} NOT EXISTS'.format(thumb_path)
            version_ent = self.createVersion(self.version_name,status=status, description=comment,
                        movieFile=self.movie_file, thumbnailPath=thumb_path, framePaths=self.path_frames)

            if self.task_name == 'layout':
                data = {'sg_status_list': status }
                sequence_task = self.SG.find_one('Task', [['project', 'is', self.prj_ent], ['entity', 'is', self.seq_ent],
                                                          ['content', 'is', self.task_name]], ['code', 'id'])
                try:
                    self.SG.update('Task', sequence_task['id'], data)
                except:
                    print 'Unable to publish'

            end = time.time()
            correctErrorData(m= "Publish complete : %s"%self.movie_file, level= 'INFO', time = str(end - start))
            return version_ent

        except Exception as e :
            import traceback
            import deadline.exception as exception

            # Delete version can't publish complete
            if version_ent:
                self.removeVersionFail(versionEnt=version_ent)

            _m = traceback.format_exc(e)
            _m += '\n\nMovie file : {file}\n'.format(file = self.movie_file)
            exception.sendEmail( msg = _m, errorname = 'Media Publish error', level = 'ERROR', subject = '[MEMEPublish]')
            end = time.time()
            correctErrorData(m = str(e) + " : %s"%self.movie_file, time = str(end - start))
            raise PublishError("Media Publish Error : Please publish again...")

if __name__ == "__main__":
    # movie_path, version_name, user=None, comment='', status='noaprv'
    arguments = {'f': {'dest': 'mediaLive', 'help': 'Media Live Path', 'default': ''},
                 'v': {'dest': 'version', 'help': 'Version Name', 'default': ''},
                 'user': {'dest': 'userName', 'help': 'Comment', 'default': ''},
                 'cm': {'dest': 'comment', 'help': 'Comment', 'default': ''},
                 's': {'dest': 'status', 'help': 'Status Code (Check on shotgun)', 'default': 'noaprv'},
                 'ft':{'dest': 'footage', 'help': 'get footage path', 'default': False},
                 'ff':{'dest': 'fileFormat', 'help': 'get file format', 'default': '.ma'}}
    parser = parse(arguments, 'Meme File Activity')
    params = parser.parse_args()

    if params.mediaLive == '':
        print('use -p Media Live Path')
    else:
        _versionEnt = None
        _movieFile = params.mediaLive.replace('\\', '/')
        _comment  = params.comment
        _version  = params.version
        _status   = params.status
        _username = params.userName
        _variant  = _movieFile.split('__')[-1].split('.')[0] if len(_movieFile.split('__')) == 2 else ''
        _footage  = params.footage

        _taskName, _memeTask, _framesPath = None,None,None
        _format = params.fileFormat

        # L:/F18/TVS1909/COMMON/MEDIA/CMP_F18_TVS1909_SH1950.mov

        if _variant:
            _taskName = _movieFile.split('/')[-1].split('_')[0].lower() + _variant.title()

        if not _version:
            if _footage:
                _version, _taskName, _memeTask, _framesPath = getVersionName(_movieFile)
                shot = Shot(_movieFile, _version, user=_username, task_name=_taskName, meme_task=_memeTask)
                _versionEnt = shot.publish(status=_status, comment=_comment, path_frames=_framesPath)
            if not _footage:
                _version, _taskName, _memeTask, _framesPath = getVersionName(_movieFile, get_footage=_footage,file_format=_format)
                shot = Shot(_movieFile, _version, user=_username, task_name=_taskName, meme_task=_memeTask)
                _versionEnt = shot.publish(status=_status, comment=_comment)
            # print 'as',_version, _taskName, _memeTask, _framesPath
        if not _versionEnt:
            print 'Shotgun Publish Error.'

