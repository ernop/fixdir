import os, uuid, urlparse, simplejson, shutil, re

import web

render = web.template.render('templates/')
urls=('/','index',
    '/images/(.*)', 'images', #this is where the image folder is located....
    '/move','move',
    '/delete','delete',
)

target_defs={'mp3albums':'/media/I/mp3albums',
    'home':'/home/ernie',
    'mp3discography':'/media/I/mp3discography',
    'mp3spoken':'/media/I/mp3spoken',
    'mp3':'/media/I/mp3',
    'other':'/media/I/other',
    'movie':'/media/twot/movie',
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

IMAGE_EXTENSIONS=['jpg','png','gif','jpeg',]
MP3_EXTENSIONS=['mp3',]
MOVIE_EXTENSIONS=['avi','wmv','rm',]
IMAGE_TARGETS=[TARGETS[n] for n in 'get home other'.split()]
MP3_TARGETS=[TARGETS[n] for n in 'mp3albums mp3discography mp3spoken mp3'.split()]
MOVIE_TARGETS=[TARGETS[n] for n in 'movie other'.split()]

def has_movie(fp):
    files=os.listdir(fp)
    for f in files:
        if '.' not in f:
            continue
        ext=f.split('.')[-1]
        if ext in MOVIE_EXTENSIONS:
            return True

def getkind(fp):
    fp=fp.lower()
    if os.path.isdir(fp):
        if has_movie(fp):
            return 'moviedir'
        else:
            return 'otherdir'
    if '.' not in fp:
        return False
    ext=fp.split('.')[-1]
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
        for target in TARGETS:
            buttons.append(mkmvbutton(target, fp))
    elif kind=='otherdir':
        for target in TARGETS:
            buttons.append(mkmvbutton(target, fp))
    return ''.join(buttons)

def mkdelbutton(fp):
    idd=str(uuid.uuid4()).replace('-','_')
    res='<div class="button" id="%s">%s</div>'%(idd, 'delete')
    res+='''<script>
    (function(){
        var data={'fp':'%s'};
        $("#%s").click(function(){
            $("#%s").parent().append($('<div class="busy">Busy...</div>'));
            $.ajax({
                url:"/delete",
                data:data,
                success:function(dat){
                    $("#%s").parent().css('border','red').slideUp();
                    }
                });
            });
        }
    )()
    </script>'''%(fp, idd, idd, idd)
    return res
    
def mkmvbutton(target, fp):
    idd=str(uuid.uuid4()).replace('-','_')
    res='<div class="button" id="%s">%s</div>'%(idd, target.name)
    res+='''<script>
    (function(){
        var data={'target':'%s','fp':'%s'};
        $("#%s").click(function(){
            $("#%s").parent().append($('<div class="busy">Busy...</div>'));
            $.ajax({
                url:"/move",
                data:data,
                success:function(dat){
                    $("#%s").parent().slideUp();
                    }
                });
            });
        }
    )()
    </script>'''%(target.dest, fp, idd, idd, idd)
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
    if kind =='image':
        res=image(fp)
        res+=buttons('image',fp)
    elif kind =='mp3':
        res=mp3(fp)
        res+=buttons('mp3',fp)
    elif kind == 'movie':
        res=movie(fp)
        res+=buttons('movie',fp)
    elif kind=='moviedir':
        res=moviedir(fp)
        res+=buttons('moviedir',fp)
    elif kind=='otherdir':
        res=otherdir(fp)
        res+=buttons('otherdir',fp)
    res+=mkdelbutton(fp)
        
    return res

class images:
    def GET(self,name):
        ext = name.split(".")[-1].lower() # Gather extension
        cType = {
            "png":"image/png",
            "jpg":"image/jpeg",
            "gif":"image/gif",
            "ico":"image/x-icon"           }

        web.header("Content-Type", cType[ext]) # Set the Header
        return open('/%s'%name,"rb").read() # Notice 'rb' for reading images

class delete:
    def GET(self):
        pts=urlparse.parse_qs(web.ctx.query)
        fp=pts['?fp'][0]
        print 'would remove %s'%fp
        print fp
        if os.path.exists(fp):
            log('removed',fp)
            os.remove(fp)

def log(arggs):
    return
    try:
        if arggs:
            if len(arggs)>1:
                res=arggs[0]%args[1:]
            else:
                res=arggs[0]
        moment=datetime.datetime.now()
        open('log.txt','a').write(moment+': '+res+'\n')
    except:
        import ipdb;ipdb.set_trace();print 'ipdb!'
        print 'x'

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)
    
class move:
    def GET(self):
        pts=urlparse.parse_qs(web.ctx.query)
        fp=pts['fp'][0]
        target=pts['?target'][0]
        web.header("Content-Type", 'text/json')
        print fp, target, pts
        fn=os.path.split(fp)[-1]
        targetdone=os.path.join(target, fn)
        res={'fp':fp,'target':target,}
        if os.path.exists(targetdone):
            res={'res':'existed.'}
        else:
            try:
                shutil.move(fp, target)
                res['res']='moved it.'
                log('moved'+fp+'to'+target)
            except:
                import traceback;traceback.print_exc()
                import ipdb;ipdb.set_trace();print 'ipdb!'
                log('failed move '+fp+'to'+target)
                res['res']='fail.'
        return simplejson.dumps(res)

HEAD="<head></head><body>"
TAIL="</body>"
EXTENSIONS='jpg jpeg gif png avi'.split()

class index:
    def GET(self):
        d='/media/I/dl'
        files=os.listdir(d)
        res=[HEAD]
        did=0
        for f in files:
            if did>100:break
            if '.' not in f:
                continue
            fn, ext=f.lower().rsplit('.',1)
            if ext not in EXTENSIONS:
                continue
            th=display(d, f)
            if not th:
                continue
            did+=1
            res.append(th)
        res.append(TAIL)
        okres=[]
        for r in res:
            okres.append(r.decode('utf8'))
        return render.index(okres)

app=web.application(urls, globals(), autoreload=True)
if __name__=="__main__":
    app.run()