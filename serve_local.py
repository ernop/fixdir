import os, uuid, urlparse, simplejson, shutil, re, datetime, time, hashlib
import subprocess
import web

from putup import putup
from util import *

render = web.template.render('templates/')
if not os.path.exists('locks'):
    os.mkdir('locks')

urls=('/','index',
    '/images/(.*)', 'images', #this is where the image folder is located....
    '/move','move',
    '/delete','delete',
    '/up','up',
    '/play','play',
    '/clearlocks','clearlocks',
)


target_defs={'mp3albums':'/media/I/mp3albums',
    'home':'/home/ernie',
    'mp3discography':'/media/I/mp3discography',
    'mp3spoken':'/media/I/mp3spoken',
    'mp3':'/media/I/mp3',
    'other':'/media/I/other',
    'movie':'/media/twot/movie',
    'tv':'/media/twot/tv',
    'get':'/media/I/get',
    'know':'/home/ernie/file/g_know',
    'fambly':'/home/ernie/file/fambly',
    'dl':'/media/twot/dl',
}
PLAYERS={'mp3':'rhythmbox', 'doc':'netscape', 'movie':'vlc'}
DIRS=['/media/I/dl','/media/I/get','/home/ernie/file',]

if os.path.exists('laptop'):
    target_defs={'mp3albums':'d:/mp3albums',
        'other':'d:/other',
        'mp3':'d:/mp3',
        'home':'d:/file',
        'get':'d:/get',
        'know':'d:/file/g_know',
        'fambly':'d:/file/fambly',
        'myphoto':'d:/file/myphoto',
        'ebook':'d:/ebook',
        'dl':'d:/dl',
    }
    PLAYERS['mp3']=r'"c:\program files\winamp\winamp.exe" /ADD'
    PLAYERS['doc']=r'"c:\program files\mozilla firefox\firefox.exe"'
    DIRS=['d:/dl','d:/file','d:/get','d:/','c:/','d:/saved',]
    PLAYERS['txt']=r'"c:\notepad2\notepad2.exe"'
    PLAYERS['pdf']=r'"c:\program files\foxit software\foxit reader\foxit reader.exe"'

PLAYERS['mp3dir']=PLAYERS['mp3']

class Target:
    def __init__(self, name, dest):
        self.name=name
        self.dest=dest

TARGETS={}
for a,b in target_defs.items():
    t=Target(name=a, dest=b)
    TARGETS[a]=t


IMAGE_EXTENSIONS=['jpg','png','gif','jpeg','svg',]
MP3_EXTENSIONS=['mp3',]
MOVIE_EXTENSIONS=['avi','wmv','rm','mp4','avi','mkv','mpg','wmv']
DOC_EXTENSIONS='html doc mobi txt rtf epub pdf htm'.split()

EXTENSIONS=[]
EXTENSIONS.extend(IMAGE_EXTENSIONS)
EXTENSIONS.extend(MP3_EXTENSIONS)
EXTENSIONS.extend(MOVIE_EXTENSIONS)
EXTENSIONS.extend(DOC_EXTENSIONS)

IMAGE_TARGETS=[TARGETS[n] for n in 'get home other know fambly myphoto'.split() if n in TARGETS]
MP3_TARGETS=[TARGETS[n] for n in 'mp3albums mp3discography mp3spoken mp3'.split() if n in TARGETS]
MOVIE_TARGETS=[TARGETS[n] for n in 'movie other'.split() if n in TARGETS]
OTHERDIR_TARGETS=[TARGETS[n] for n in 'movie other myphoto'.split() if n in TARGETS]
OTHERDIR_TARGETS.extend(MP3_TARGETS)
DOC_TARGETS=[TARGETS[n] for n in 'ebook file home'.split() if n in TARGETS]

def has_movie(fp):
    files=os.listdir(fp)
    for f in files:
        if '.' not in f:
            continue
        ext=f.split('.')[-1]
        if ext in MOVIE_EXTENSIONS:
            return True

def has_mp3(fp):
    files=os.listdir(fp)
    for f in files:
        if '.' not in f:
            continue
        ext=f.split('.')[-1]
        if ext in MP3_EXTENSIONS:
            return True

def getkind(fp):
    if os.path.isdir(fp):
        if has_movie(fp):
            return 'moviedir'
        elif has_mp3(fp):
            return 'mp3dir'
        else:
            if os.listdir(fp):
                #it has files in it at least.
                return 'otherdir'
            return False
    if '.' not in fp:
        return False
    ext=fp.split('.')[-1].lower()
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    if ext in MP3_EXTENSIONS:
        return 'mp3'
    if ext in MOVIE_EXTENSIONS:
        return 'movie'
    if ext in DOC_EXTENSIONS:
        return 'doc'
    return False

def buttons(kind, fp):
    buttons=['<br>',]
    if kind=='image':
        for target in IMAGE_TARGETS:
            buttons.append(mkmvbutton(target, fp))
    elif kind in ['movie','moviedir']:
        for target in MOVIE_TARGETS:
            buttons.append(mkmvbutton(target, fp))
    elif kind in ['mp3','mp3dir']:
        for target in MP3_TARGETS:
            buttons.append(mkmvbutton(target, fp))
    elif kind=='otherdir':
        for target in OTHERDIR_TARGETS:
            buttons.append(mkmvbutton(target, fp))
    elif kind=='doc':
        for target in DOC_TARGETS:
            buttons.append(mkmvbutton(target, fp))
    return ''.join(buttons)

def mkgolink(fp):
    """just go there."""
    res='<a href="/?dir=%s">%s</a>'%(fp,fp)
    return res

def mkmvbutton(target, fp):
    idd=str(uuid.uuid4()).replace('-','_')
    res='<div class="button" id="%s">%s</div>'%(idd, target.name)
    fpjs=fp.replace("\'","\\\'")
    res+='''<script>
    (function(){
        var data={'target':'%s','fp':"%s"};
        $("#%s").click(function(){
            $("#%s").parent().append($('<div class="busy">Busy...</div>'));
            $.ajax({
                url:"/move",
                data:data,
                success:function(dat){
                    if (dat['res']!='success'){
                        $("#%s").parent().append($('<div class="existed">Fail: '+dat['res']+'</div>')).find('.busy').remove();
                    }
                    else{
                        $("#%s").parent().slideUp();
                    }
                    }
                });
            });
        }
    )()
    </script>'''%(target.dest, fpjs, idd, idd, idd, idd)
    return res

def mkfpbutton(fp, cmd):
    idd=str(uuid.uuid4()).replace('-','_')
    res='<div class="button" id="%s">%s</div>'%(idd, cmd)
    fpjs=fp.replace("\'","\\\'")
    res+='''<script>
    (function(){
        var data={'fp':"%s"};
        $("#%s").click(function(){
            $("#%s").parent().append($('<div class="busy">Busy...</div>'));
            $.ajax({
                url:"/%s",
                data:data,
                success:function(ddata){
                    if (ddata['res']!='success'){
                        $("#%s").parent().append($('<div class="fail">Fail: '+ddata['res']+'</div>')).find('.busy').remove();
                    }
                    else{
                        $("#%s").parent().slideUp();
                    }
                    }
                });
            });
        }
    )()
    </script>'''%(fpjs, idd, idd, cmd, idd, idd)
    return res


def image(fp):
    res='<img src="/images/%s"">'%(fp)
    return res

def mp3(fp):
    res='MP3<br>%s'%fp
    return res

def moviedir(fp):
    res='MOVIEDIR<br>'
    files=os.listdir(fp)
    for f in files:
        if '.' not in f:continue
        ext=f.split('.')[-1]
        if ext.lower() in IMAGE_EXTENSIONS:
            pass

def doc(fp):
    return 'DOC<br>%s'%fp

def mp3dir(fp):
    return 'MP3dir<br>%s'%fp

def movie(fp):
    res='MOVIE<br>%s'%(fp)
    return res

def moviedir(fp):
    res='MOVIEdir<br>%s'%fp
    return res

def otherdir(fp):
    res='OTHERDIR<br>%s'%fp
    return res

def display(d, f):
    fp=os.path.join(d, f).replace('\\','/')
    res=None
    kind=getkind(fp)
    if kind =='image':
        res=image(fp)
        res+=buttons('image',fp)
        res+=mkfpbutton(fp, 'up')
    elif kind =='mp3':
        res=mp3(fp)
        res+=buttons('mp3',fp)
        res+=mkfpbutton(fp, 'play')
    elif kind == 'movie':
        res=movie(fp)
        res+=buttons('movie',fp)
        res+=mkfpbutton(fp, 'play')
    elif kind=='moviedir':
        res=moviedir(fp)
        res+=buttons('moviedir',fp)
        res+=mkgolink(fp)
    elif kind=='mp3dir':
        res=mp3dir(fp)
        res+=buttons('mp3dir',fp)
        res+=mkfpbutton(fp, 'play')
        res+=mkgolink(fp)
    elif kind=='otherdir':
        res=otherdir(fp)
        res+=buttons('otherdir',fp)
        res+=mkgolink(fp)
    elif kind=='doc':
        res=doc(fp)
        res+=buttons('doc',fp)
        res+=mkfpbutton(fp, 'play')
    else:
        #empty dir.
        return res
    try:
        res+=mkfpbutton(fp, 'delete')
    except:
        import traceback;traceback.print_exc()
        import ipdb;ipdb.set_trace();print 'ipdb!'
    return res


class images:
    def GET(self,name):
        ext = name.rsplit(".",1)[-1].lower()
        cType = {
            "png":"image/png",
            "jpg":"image/jpeg",
            "gif":"image/gif",
            "svg":"image/svg+xml",
            "ico":"image/x-icon",}
        if ext not in cType:
            print 'bad ext',ext
            return None
        web.header("Content-Type", cType[ext])
        return open('%s'%name,"rb").read()

class delete:
    def GET(self):
        fp=readfp()
        if not getlock(fp):return False
        print 'would remove %s'%fp
        print fp
        if os.path.exists(fp):
            log('removed'+fp)
            os.remove(fp)
            unlock(fp)
        res={'res':'success','fp':fp}
        return simplejson.dumps(res)

class up:
    def GET(self):
        fp=readfp()
        if not getlock(fp):return False
        web.header("Content-Type", 'text/json')
        fn=os.path.split(fp)[-1]
        res={}
        mkupres=putup(fp)
        res['res']=mkupres
        res['fp']=fp
        unlock(fp)
        return simplejson.dumps(res)


def readfp():
    return readqs('fp')

def readqs(name):
    pts=urlparse.parse_qs(web.ctx.query[1:])
    try:
        res=pts[name][0].encode('raw_unicode_escape').replace('\x00','/000')
    except KeyError:
        res=''
    return res


class play:
    def GET(self):
        fp=readfp()
        kind=getkind(fp)
        if not getlock(fp):return False
        prefix=''
        ext=fp.rsplit('.')[-1]
        if ext in PLAYERS:
            player=PLAYERS[ext]
        else:
            player=PLAYERS[kind]
        if kind=='doc' and ext not in PLAYERS:
            prefix='file:///'
        cmd='%s "%s%s"'%(player, prefix, fp)
        print cmd
        subprocess.Popen(cmd)
        res={}
        res['res']='success'
        unlock(fp)
        return simplejson.dumps(res)


class move:
    def GET(self):
        pts=urlparse.parse_qs(web.ctx.query[1:])
        fp=pts['fp'][0].encode('raw_unicode_escape').replace('\x00','/000')
        target=pts['target'][0].encode('raw_unicode_escape')
        web.header("Content-Type", 'text/json')
        print fp, target, pts
        slept=0
        if not getlock(fp):return False
        fn=os.path.split(fp)[-1]
        targetdone=os.path.join(target, fn)
        res={'fp':fp,'target':target,}
        if os.path.exists(targetdone):
            res={'res':'existed.'}
        else:
            try:
                shutil.move(fp, target)
                res['res']='success'
                log('moved'+fp+'to'+target)
            except:
                import traceback;traceback.print_exc()
                import ipdb;ipdb.set_trace();print 'ipdb!'
                log('failed move '+fp+'to'+target)
                res['res']='fail.'
        unlock(fp)
        return simplejson.dumps(res)

HEAD="<head></head><body>"
TAIL="</body>"

DIRS.extend(target_defs.values())
DIRS=list(set([d for d in DIRS if os.path.isdir(d)]))

class clearlocks:
    def GET(self):
        cmd='rm locks/*'
        cmdres=os.system(cmd)
        res={}
        res['res']=cmdres
        web.header("Content-Type", 'text/json')
        return simplejson.dumps(res)

class index:
    def GET(self):
        d=readqs('dir')
        if not d:
            d='/media/I/dl'
        if not os.path.isdir(d):
            d='d:/dl'
        files=[]
        if os.path.isdir(d):
            files=os.listdir(d)
        res=[]
        did=0
        for f in files[:40]:
            fp=os.path.join(d, f)
            if os.path.isdir(fp):
                pass
            else:
                if '.' not in f:
                    print 'bad f.',f
                    continue
                fn, ext=f.lower().rsplit('.',1)
                if ext not in EXTENSIONS:
                    continue
            try:
                th=display(d, f)
            except WindowsError:
                print 'windowserror!',d,f
                continue
            except:

                import traceback;traceback.print_exc()
                import ipdb;ipdb.set_trace();print 'ipdb!'
                print 'x'
            if not th:
                continue
            did+=1
            res.append(th)
        okres=[]
        for r in res:
            ok=r.decode('utf8')
            if not ok:
                continue
            okres.append(ok)
        return render.index(okres, d, DIRS)

app=web.application(urls, globals(), autoreload=True)
if __name__=="__main__":
    app.run()