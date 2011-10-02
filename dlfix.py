import os, uuid, urlparse, simplejson, shutil, re, datetime, time, hashlib

import web

from putup import putup
from util import *

render = web.template.render('templates/')

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
}


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
MOVIE_EXTENSIONS=['avi','wmv','rm','mp3','mp4','avi','mkv','mpg','wmv']
EXTENSIONS=[]
EXTENSIONS.extend(IMAGE_EXTENSIONS)
EXTENSIONS.extend(MP3_EXTENSIONS)
EXTENSIONS.extend(MOVIE_EXTENSIONS)
IMAGE_TARGETS=[TARGETS[n] for n in 'get home other'.split()]
MP3_TARGETS=[TARGETS[n] for n in 'mp3albums mp3discography mp3spoken mp3'.split()]
MOVIE_TARGETS=[TARGETS[n] for n in 'movie other tv'.split()]
MOVIEDIR_TARGETS=MOVIE_TARGETS[:]
OTHERDIR_TARGETS=[TARGETS[n] for n in 'movie other tv'.split()]
OTHERDIR_TARGETS.extend(MP3_TARGETS)

def has_movie(fp):
    files=os.listdir(fp)
    for f in files:
        if '.' not in f:
            continue
        ext=f.split('.')[-1]
        if ext in MOVIE_EXTENSIONS:
            return True

def getkind(fp):

    if os.path.isdir(fp):
        if has_movie(fp):
            return 'moviedir'
        else:
            return 'otherdir'
    if '.' not in fp:
        return False
    ext=fp.split('.')[-1].lower()
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    if ext in MP3_EXTENSIONS:
        return 'mp3'
    if ext in MOVIE_EXTENSIONS:
        return 'movie'
    return False

def buttons(kind, fp):
    buttons=[]
    if kind=='image':
        for target in IMAGE_TARGETS:
            buttons.append(mkmvbutton(target, fp))
    elif kind=='movie':
        for target in MOVIE_TARGETS:
            buttons.append(mkmvbutton(target, fp))
    elif kind=='mp3':
        for target in MP3_TARGETS:
            buttons.append(mkmvbutton(target, fp))
    elif kind=='moviedir':
        for target in MOVIEDIR_TARGETS:
            buttons.append(mkmvbutton(target, fp))
    elif kind=='otherdir':
        for target in OTHERDIR_TARGETS:
            buttons.append(mkmvbutton(target, fp))
    return ''.join(buttons)

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
                success:function(dat){
                    if (dat['res']!='success'){
                        $("#%s").parent().append($('<div class="fail">Fail: '+dat['res']+'</div>')).find('.busy').remove();
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
    res='<img src="/images%s"">'%(fp)
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

def movie(fp):
    res='MOVIE<br>%s'%(fp)
    return res

def moviedir(fp):
    res='MOVIEDIR<br>%s'%fp
    return res

def otherdir(fp):
    res='OTHERDIR<br>%s'%fp
    return res

def display(d, f):
    fp=os.path.join(d, f)
    res=None
    kind=getkind(fp)
    import ipdb;ipdb.set_trace();print 'in ipdb!'
    if kind =='image':
        res=image(fp)
        res+=buttons('image',fp)
        res+=mkfpbutton(fp, 'up')
    elif kind =='mp3':
        res=mp3(fp)
        res+=buttons('mp3',fp)
    elif kind == 'movie':
        res=movie(fp)
        res+=buttons('movie',fp)
        res+=mkfpbutton(fp, 'play')
    elif kind=='moviedir':
        res=moviedir(fp)
        res+=buttons('moviedir',fp)
    elif kind=='otherdir':
        res=otherdir(fp)
        res+=buttons('otherdir',fp)
    try:
        res+=mkfpbutton(fp, 'delete')
    except:
        import traceback;traceback.print_exc()
        import ipdb;ipdb.set_trace();print 'ipdb!'
    return res


class images:
    def GET(self,name):
        ext = name.split(".")[-1].lower() # Gather extension
        cType = {
            "png":"image/png",
            "jpg":"image/jpeg",
            "gif":"image/gif",
            "svg":"image/svg+xml",
            "ico":"image/x-icon"           }

        web.header("Content-Type", cType[ext]) # Set the Header
        return open('/%s'%name,"rb").read() # Notice 'rb' for reading images

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

class up:
    def GET(self):
        fp=readfp()
        if not getlock(fp):return False
        web.header("Content-Type", 'text/json')
        fn=os.path.split(fp)[-1]
        res={}
        mkupres=putup(fp)
        res['res']=mkupres
        unlock(fp)
        return simplejson.dumps(res)


def readfp():
    return readqs('fp')

def readqs(name):

    pts=urlparse.parse_qs(web.ctx.query[1:])
    try:
        res=pts[name][0].encode('raw_unicode_escape')
    except KeyError:
        res=''
    return res


class play:
    def GET(self):
        fp=readfp()
        if not getlock(fp):return False
        cmd='vlc "%s"'%fp
        cmdres=os.system(cmd)
        res={}
        res['res']=cmdres
        return simplejson.dumps(res)


class move:
    def GET(self):
        pts=urlparse.parse_qs(web.ctx.query[1:])
        fp=pts['fp'][0].encode('raw_unicode_escape')
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

DIRS=['/media/I/dl','/media/I/get','/home/ernie/file',]

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
        for f in files:
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
            except:
                import traceback;traceback.print_exc()
                import ipdb;ipdb.set_trace();print 'ipdb!'
                print 'x'
            if not th:
                continue
            did+=1
            res.append(th)
        okres=[]
        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        for r in res:
            ok=r.decode('utf8')
            if not ok:
                continue
            okres.append(ok)
        return render.index(okres, d, DIRS)

app=web.application(urls, globals(), autoreload=True)
if __name__=="__main__":
    app.run()