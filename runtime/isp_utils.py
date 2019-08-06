import os
import errno
import shutil
import logging

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


def getIspPrefix():
    isp_prefix = os.environ["HOME"] + "/.local/isp/"

    try:
        isp_prefix = os.environ["ISP_PREFIX"]
    except KeyError:
        pass

    return isp_prefix


def getPolicyFullName(policy, runtime="{}"):
    return "osv." + runtime + ".main." + policy


def setupLogger():
    logger = logging.getLogger()
    logging.basicConfig(format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s", datefmt="%H:%M:%S")

    return logger


def terminateMessage(runtime):
    if runtime == "frtos":
        return "Main task has completed with code:"
    if runtime == "sel4":
        return "Root task has completed with code:"
    elif runtime == "bare":
        return "Program has exited with code:"

    return ""
