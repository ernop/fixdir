import os, hashlib, datetime, time

def log(*arggs):
    try:
        if arggs:
            if len(arggs)>1:
                res=arggs[0]%arggs[1:]
            else:
                res=arggs[0]
        print res
        moment=datetime.datetime.now()
        open('log.txt','a').write(str(moment)+': '+res+'\n')
    except:
        import traceback;traceback.print_exc()
        import ipdb;ipdb.set_trace();print 'ipdb!'
        print 'x'

def getlock(fp, source=None):
    lockfile='locks/%s'%(hashlib.md5(fp).hexdigest())
    slept=0
    while 1:
        if source:
            print 'source is:',source,
        if not os.path.exists(lockfile):
            os.system('touch %s'%lockfile)
            log('locked %s',fp)
            return True
        else:
            time.sleep(1)
            slept+=1
            print slept,'waiting for lock on',fp
        if slept>55:
            log('failed to lock %s',fp)
            return False

    return False

def unlock(fp):
    lockfile='locks/%s'%(hashlib.md5(fp).hexdigest())
    if os.path.exists(lockfile):
        os.remove(lockfile)
        log('unlocked %s',fp)
    else:
        import ipdb;ipdb.set_trace();print 'ipdb!'
        print 'missing lock.'
