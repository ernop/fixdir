import urllib2, os, shutil
STATUSURL='http://fuseki.net/putup/head'
STATUSPATH='head'
LIVE_BASE='/home/ernop/fuseki.net/public/putup/images'
from util import *

def dlstatus():
    cmd='rsync -av ernop@fuseki.net:/home/ernop/fuseki.net/public/putup/head .'
    res=os.system(cmd)
    if res:
        import ipdb;ipdb.set_trace();print 'ipdb!'
        print 'problem dling.'
        return False
    return True

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
    if not getlock('head','putup %s'%fp):return False
    status=getstatus()
    if not status:
        res['res']='failed to get status.'
        return res
    head, fn = os.path.split(fp)
    fb, ext=os.path.splitext(fn)
    headplusone=int(status['head'])+1
    status['head']=str(headplusone)
    newfn=str(headplusone)+ext
    newfn=newfn.lower()
    src=fp
    local_dest=os.path.join('images',newfn)
    shutil.copy(src, local_dest)
    cmd='chmod 644 %s'%local_dest
    os.system(cmd)
    src=local_dest
    dest=os.path.join(LIVE_BASE, newfn)
    rsync_dest='ernop@fuseki.net:'+dest
    cmd='rsync -av "%s" "%s"'%(src, rsync_dest)
    log(cmd)
    res={}
    cmdres=os.system(cmd)
    if not cmdres:
        res['res']='success'
    else:
        res['res']=cmdres
    res['newfn']=newfn
    putstatus(status)
    unlock('head')
    return res