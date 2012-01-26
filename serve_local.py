# -*- coding: utf-8 -*-

import os, uuid, urlparse, simplejson, shutil, re, datetime, time, hashlib, urllib, shutil, subprocess, filecmp
import web
import Image

from putup import putup
from util import *

render = web.template.render('templates/')
if not os.path.exists('locks'):
    os.mkdir('locks')

urls=('/','index',
    '/images/(.*)', 'images', #this is where the image folder is located....
    '/docs/(.*)', 'docs', #this is where the image folder is located....
    '/move','move',
    '/delete','delete',
    '/up','up',
    '/play','play',
    '/clearlocks','clearlocks',
    '/aa','test',
    '/ren','rename',
    '/fixname','fixname',
)

target_defs={'mp3albums':'/media/I/mp3albums',
    'home':'/home/ernie',
    'mp3discography':'/media/I/mp3discography',
    'mp3spoken':'/media/I/mp3spoken',
    'mp3':'/media/I/mp3',
    'other':'/media/I/other',
    'gals':'/media/I/gals',
    'movie':'/media/twot/movie',
    'tv':'/media/twot/tv',
    'get':'/media/I/get',
    'funny':'/media/I/get/funny',
    'bg':'/media/I/get/bg',
    'g_know':'/home/ernie/file/pic/g_know',
    'know':'/home/ernie/file/pic/know',
    'fambly':'/home/ernie/file/pic/fambly',
    'dl':'/media/twot/dl',
    'myphoto':'/home/ernie/file/pic/myphoto',
    'ebook':'/home/ernie/ebook',
    'saved':'/media/I/saved',
    'doc':'/home/ernie/file/docs'
}

KEYBOARD_SHORTCUTS={}
KEYBOARD_OVERRIDES={'gals':'l',
    'mp3':'3',
    'mp3albums':'a',
    'movie':'m',
    'g_know':'w',
    'myphoto':'p',
    'fambly':'m',
    }
for k in target_defs.keys():
    if k in KEYBOARD_OVERRIDES:
        KEYBOARD_SHORTCUTS[k]=KEYBOARD_OVERRIDES[k]
    else:
        KEYBOARD_SHORTCUTS[k]=k[0]
    #=={'get':'g',...}

PLAYERS={'mp3':'rhythmbox', 'doc':'evince', 'movie':'vlc'}
DIRS=['/media/I/dl','/media/I/get','/home/ernie/file',]

LINUX=True
if os.path.exists('laptop'):
    LINUX=True

if not LINUX:
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

def mk_bold_name(txt):
    if txt in KEYBOARD_SHORTCUTS:
        return txt.replace(KEYBOARD_SHORTCUTS[txt],'<b>%s</b>'%KEYBOARD_SHORTCUTS[txt],1)
    return txt

TARGETS={}
for a,b in target_defs.items():
    t=Target(name=a, dest=b)
    t.bold_name=mk_bold_name(a)
    TARGETS[a]=t


IMAGE_EXTENSIONS=['jpg','png','gif','jpeg','svg','bmp',]
MP3_EXTENSIONS=['mp3','wav','m4a',]
MOVIE_EXTENSIONS=['avi','wmv','rm','mp4','avi','mkv','mpg','wmv']
DOC_EXTENSIONS='html doc mobi txt rtf epub pdf htm docx xlsx xls lit js'.split()

EXTENSIONS=[]
EXTENSIONS.extend(IMAGE_EXTENSIONS)
EXTENSIONS.extend(MP3_EXTENSIONS)
EXTENSIONS.extend(MOVIE_EXTENSIONS)
EXTENSIONS.extend(DOC_EXTENSIONS)

IMAGE_TARGETS=[(TARGETS[n], 'move') for n in 'get funny bg home other gals g_know know fambly myphoto'.split() if n in TARGETS]
MP3_TARGETS=[(TARGETS[n],'move') for n in 'mp3albums mp3discography mp3spoken mp3'.split() if n in TARGETS]
MOVIE_TARGETS=[(TARGETS[n],'move') for n in 'movie other'.split() if n in TARGETS]
OTHERDIR_TARGETS=[(TARGETS[n],'move') for n in 'movie other myphoto'.split() if n in TARGETS]
OTHERDIR_TARGETS.extend(MP3_TARGETS)
OTHERDIR_TARGETS.append((TARGETS['doc'],'move'))
DOC_TARGETS=[(TARGETS[n],'move') for n in 'ebook file home doc'.split() if n in TARGETS]

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('jinjaproj', 'jtemplates'))

try:
    import WindowsError
    windows=True
except:
    WindowsError=None
    windows=False

HEAD="<head></head><body>"
TAIL="</body>"

DIRS.extend(target_defs.values())
DIRS=list(set([d for d in DIRS if os.path.isdir(d)]))
DIRS.sort()

def has_movie(fp):
    files=os.listdir(fp)
    for f in files:
        if '.' not in f:
            continue
        ext=f.split('.')[-1]
        if ext.lower() in MOVIE_EXTENSIONS:
            return os.path.join(fp, f)

def has_mp3(fp):
    files=os.listdir(fp)
    for f in files:
        if '.' not in f:
            continue
        ext=f.split('.')[-1]
        if ext.lower() in MP3_EXTENSIONS:
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
    if ext.lower() in IMAGE_EXTENSIONS:
        return 'image'
    if ext.lower() in MP3_EXTENSIONS:
        return 'mp3'
    if ext.lower() in MOVIE_EXTENSIONS:
        return 'movie'
    if ext.lower() in DOC_EXTENSIONS:
        return 'doc'
    return False

def mkgolink(fp):
    """just go there."""
    res='<a href="/?dir=%s">%s</a>'%(urllib.quote(fp),fp)
    #res+=' <a href="/docs/%s">filelink</a>'%(urllib.quote(fp))
    return res

def mkfpbutton(fp, cmd, target=None):
    idd=str(uuid.uuid4()).replace('-','_')
    fpjs=fp.replace("\'","\\\'")
    template=env.get_template('fpbutton.html')
    vars={'idd':idd,'cmd':cmd,'fpjs':fpjs, 'target':target,}
    return template.render(vars)

def image(fp):
    filter=readqs('filter')
    im=Image.open(fp)
    sz=im.size
    if filter:
        try:
            if max(sz)>=1024:
                res='<img src="/images/%s"> %dx%d'%(fp, sz[0],sz[1])
            else:
                return None
        except Exception, e:
            res='<img src="/images/%s"> %s'%(fp, e)
    else:
        res='<img src="/images/%s"> '%(fp,)
    res+='<a style="target-new:tab;" target="_blank" href="/images/%s">%s</a><br>%dx%d'%(fp,fp.rsplit('/',1)[-1], sz[0],sz[1])
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
    res='DOC<br><a href="/docs/%s">%s</a>'%(urllib.quote(fp),fp)
    res+=' as <a href="/images/%s">img</a>'%(urllib.quote(fp))
    return res

def mp3dir(fp):
    return 'MP3dir<br>%s'%fp

def movie(fp):
    res='MOVIE<br>%s'%(fp)
    return res

def moviedir(fp):
    res='MOVIEdir<br>%s'%fp
    return res

def otherdir(fp):
    res='OTHERDIR<br>%s (%d)'%(fp,len(os.listdir(fp)))
    return res

def display(d, f):
    fp=os.path.join(d, f).replace('\\','/')
    res=None
    kind=getkind(fp)
    buttons=['<br>',]
    if kind =='image':
        res=image(fp)
        if res:
            for target, cmd in IMAGE_TARGETS:
                buttons.append(mkfpbutton(fp, cmd=cmd, target=target))
            res+=''.join(buttons)
            res+=mkfpbutton(fp, 'up')
        else:
            return None
    elif kind =='mp3':
        res=mp3(fp)
        for target,cmd in MP3_TARGETS:
            buttons.append(mkfpbutton(fp, cmd=cmd, target=target))
        res+=''.join(buttons)
        res+=mkfpbutton(fp, 'play')
    elif kind == 'movie':
        res=movie(fp)
        for target,cmd in MOVIE_TARGETS:
            buttons.append(mkfpbutton(fp, cmd=cmd, target=target))
        res+=''.join(buttons)
        res+=mkfpbutton(fp, 'play')
    elif kind=='moviedir':
        res=moviedir(fp)
        mm=has_movie(fp)
        for target,cmd in MOVIE_TARGETS:
            buttons.append(mkfpbutton(fp, cmd=cmd, target=target))
        res+=''.join(buttons)
        res+=mkfpbutton(mm, 'play')
        res+=mkgolink(fp)
    elif kind=='mp3dir':
        res=mp3dir(fp)
        for target,cmd in MP3_TARGETS:
            buttons.append(mkfpbutton(fp, cmd=cmd, target=target))
        res+=''.join(buttons)
        res+=mkfpbutton(fp, 'play')
        res+=mkgolink(fp)
    elif kind=='otherdir':
        res=otherdir(fp)
        for target,cmd in OTHERDIR_TARGETS:
            buttons.append(mkfpbutton(fp, cmd=cmd, target=target))
        res+=''.join(buttons)
        res+=mkgolink(fp)
    elif kind=='doc':
        res=doc(fp)
        for target,cmd in DOC_TARGETS:
            buttons.append(mkfpbutton(fp, cmd=cmd, target=target))
        res+=''.join(buttons)
        res+=mkfpbutton(fp, 'play')
        res+=mkgolink(fp)
    else:
        #empty dir.
        return res
    try:
        res+=mkfpbutton(fp, 'delete')
    except Exception, e:
        print e
    return res

class docs:
    def GET(self,name):
        ext = name.rsplit(".",1)[-1].lower()
        cType = {
            "png":"image/png",
            "jpg":"image/jpeg",
            "jpeg":"image/jpeg",
            "gif":"image/gif",
            "svg":"image/svg+xml",
            "txt":"text/plain",
            "htm":"text/html",
            "html":"text/html",
            "ico":"image/x-icon",
            "bmp":"image/bmp",
            'js':'text/plain',
        }
        if ext not in cType:
            print 'bad ext',ext
            return None
        web.header("Content-Type", cType[ext])
        return open('%s'%name,"rb").read()

class images:
    def GET(self,name):
        ext = name.rsplit(".",1)[-1].lower()
        cType = {
            "png":"image/png",
            "jpg":"image/jpeg",
            "jpeg":"image/jpeg",
            "gif":"image/gif",
            "svg":"image/svg+xml",
            "txt":"text/plain",
            "ico":"image/x-icon",
            "txt":"image/jpeg",
            "htm":"image/jpeg",
            "html":"image/jpeg",
            "bmp":"image/bmp",
        }
        if ext not in cType:
            print 'bad ext',ext
            return None
        web.header("Content-Type", cType[ext])
        return open('%s'%name,"rb").read()

class delete:
    def GET(self):
        try:
            fp=readfp()
            if not getlock(fp):return False
            print 'would remove %s'%fp
            print fp
            if os.path.exists(fp):
                log('removed'+fp)
                if os.path.isdir(fp):
                    shutil.rmtree(fp)
                else:
                    os.remove(fp)
                unlock(fp)
            res={'res':'success','fp':fp}
            res['hide']=True
            web.header("Content-Type", 'text/json')
            return simplejson.dumps(res)
        except Exception, e:
            print e
            import ipdb;ipdb.set_trace();print 'ipdb!'

class up:
    def GET(self):
        fp=readfp()
        web.header("Content-Type", 'text/json')
        res={}
        if not getlock(fp):
            res['res']='fail'
            return simplejson.dumps(res)
        fn=os.path.split(fp)[-1]
        mkupres=putup(fp)
        res.update(mkupres)
        #res['res']=mkupres
        res['url']='http://fuseki.net/putup/images/%s'%res['newfn']
        res['fp']=fp
        res['hide']=False
        unlock(fp)
        return simplejson.dumps(res)

def readfp():
    return readqs('fp')

def readqs(name):
    pts=urlparse.parse_qs(web.ctx.query[1:])
    #pairs=urlparse.parse_qs(web.ctx.query).split('?')
    try:
        res=pts[name][0].encode('raw_unicode_escape').replace('\x00','/000')
    except KeyError:
        res=None
    except Exception, e:
        print e
    return res


class play:
    def GET(self):
        fp=readfp()
        kind=getkind(fp)
        if not getlock(fp):return False
        prefix=''
        ext=fp.rsplit('.')[-1]
        if ext.lower() in PLAYERS:
            player=PLAYERS[ext]
        else:
            player=PLAYERS[kind]
        if LINUX:
            prefix=''
        else:
            if kind=='doc' and ext not in PLAYERS:
                prefix='file:///'
        cmd='%s "%s%s"'%(player, prefix, fp)
        print cmd
        if LINUX:
            cmdres=os.system(cmd)
        else:
            cmdres=subprocess.Popen(cmd)
        if cmdres:
            return simplejson.dumps(None)
        res={}
        res['res']='success'
        unlock(fp)
        web.header("Content-Type", 'text/json')
        res['hide']=False
        return simplejson.dumps(res)


class move:
    def GET(self):
        pts=urlparse.parse_qs(web.ctx.query[1:])
        fp=pts['fp'][0].encode('raw_unicode_escape').replace('\x00','/000')
        target=pts['target'][0].encode('raw_unicode_escape')
        print fp, target, pts
        slept=0
        if not getlock(fp):return False
        fn=os.path.split(fp)[-1].lower()
        targetdone=os.path.join(target, fn)
        res={'fp':fp,'target':target,}
        identical=False
        if os.path.exists(targetdone):
            if filecmp.cmp(targetdone,fp) or os.path.isdir(fp):
                identical=True
                res['res']='identical.'
                #return simplejson.dumps(res)
            else:
                fn=str(uuid.uuid4())+'___'+fn
                log('renamed to %s',fn)
        assert os.path.isdir(target)
        fulltarget=os.path.join(target,fn)
        try:
            shutil.move(fp, fulltarget)
            res['res']='success'
            log('moved '+fp+' ===> '+fulltarget)
        except Exception, e:
            print e
            log('failed move '+fp+'==>'+fulltarget)
            res['res']='fail.'
        unlock(fp)
        res['hide']=True
        web.header("Content-Type", 'text/json')
        return simplejson.dumps(res)

class rename:
    def GET(self):
        newname=uuid.uuid4()

class fixname:
    def GET(self):
        pass

class clearlocks:
    def GET(self):
        cmd='rm locks/*'
        cmdres=os.system(cmd)
        res={}
        res['res']=cmdres
        web.header("Content-Type", 'text/json')
        return simplejson.dumps(res)

class test:
    def GET(self):
        import ipdb;ipdb.set_trace();print 'ipdb!'

class index:
    def GET(self):
        d=readqs('dir')
        sizelimit=readqs('sizelimit')
        if not d:
            d='/media/I/dl'
        if not os.path.isdir(d):
            d='d:/dl'
        files=[]
        if os.path.isdir(d):
            files=sorted(os.listdir(d))
        files=[f for f in files if not f.startswith('.')]
        res=[]
        did=0
        page=readqs('page')
        if page:
            page=int(page)
        if not page:
            page=1
        chunk=50
        for f in files[(page-1)*chunk:page*chunk]:
            if f[0]=='.':continue
            print f
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
            if windows:
                try:
                    th=display(d, f)
                except WindowsError, e:
                    print 'windowserror!',d,f
                    print e
                    continue
                except Exception, e:
                    print e
                    continue
            else:
                try:
                    th=display(d, f)
                except Exception, e:
                    print e
                    continue
            if not th:
                continue
            did+=1
            res.append(th)
        okres=[]
        for r in res:
            try:
                ok=r.decode('utf8')
            except Exception, e:
                print e
                import ipdb;ipdb.set_trace()
            if not ok:
                continue
            okres.append(ok)
        if len(files)>page*chunk:
            qq=web.ctx.query.replace('page=%s'%page,'')
            dest='<a href="%s%s&page=%s">next page</a>'%(web.ctx.path, qq, str(int(page)+1))
            dest=dest.replace('&&','&')
            okres.append(dest)
            #~ okres.insert(0, dest)
        KEYBOARD_SHORTCUTS_DICT=[[a[0], a[1]] for a in KEYBOARD_SHORTCUTS.items()]
        return render.index(okres, d, DIRS, KEYBOARD_SHORTCUTS_DICT)

app=web.application(urls, globals(), autoreload=True)
if __name__=="__main__":
    app.run()