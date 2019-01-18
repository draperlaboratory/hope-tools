import os
import errno
import shutil

def doMkDir(dir):
    try:
        if not os.path.isdir(dir):
            os.makedirs(dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def removeIfExists(filename):
    if os.path.exists(filename):
        if os.path.isdir(filename):
            shutil.rmtree(filename)
        else:
            os.remove(filename)

def getTemplatesDir():
    isp_prefix = os.environ["ISP_PREFIX"]
    return os.path.join(isp_prefix, "sources",
                                    "policies",
                                    "policy_tests",
                                    "template")

def getKernelsDir():
    isp_prefix = os.environ["ISP_PREFIX"]
    return os.path.join(isp_prefix, "kernels")

def getPolicyFullName(policy, runtime):
    return "osv." + runtime + ".main." + policy
