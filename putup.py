import urllib2, os
STATUSURL='http://fuseki.net/putup/head'
STATUSPATH='head'
LIVE_BASE='/home/ernop/fuseki.net/public/putup/img'

def log(a):
    print a
    return

def dlstatus():
    cmd='scp ernop@fuseki.net:/home/ernop/fuseki.net/public/putup/head .'
    res=os.system(cmd)
    if res:
        import ipdb;ipdb.set_trace();print 'ipdb!'
        print 'problem dling.'

def getstatus():
    dlstatus()
    res=open(STATUSPATH,'r').readlines()
    status={}
    for l in res:
        l=l.strip()
        if l.startswith('#'):continue
        a,b=l.split('=')
        status[a]=b
    log(str(status))
    return status

def putstatus(status):
    writestatus(status)
    cmd='rsync -av head ernop@fuseki.net:/home/ernop/fuseki.net/public/putup/head'
    log(cmd)
    os.system(cmd)
    
def writestatus(status):
    out=[]
    for k,v in status.items():
        out.append('%s=%s\n'%(str(k),str(v)))
    outfp=open('head','w')
    for o in out:
        outfp.write(o)
    outfp.close()

def putup(fp):
    """find the current HEAD.  add 1.  upload the image to that dir."""
    status=getstatus()
    
    head, fn = os.path.split(fp)
    fb, ext=os.path.splitext(fn)
    headplusone=int(status['head'])+1
    status['head']=str(headplusone)
    newfn=str(headplusone)+ext
    src=fp
    dest=os.path.join(LIVE_BASE, newfn)
    rsync_dest='ernop@fuseki.net:'+dest
    cmd='rsync -av %s %s'%(src, rsync_dest)
    log(cmd)
    res={}
    cmdres=os.system(cmd)
    if not cmdres:
        res['res']='success'
    else:
        res['res']=cmdres
    putstatus(status)
    return res