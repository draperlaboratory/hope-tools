import os
import errno
import shutil
import logging
import coloredlogs
import subprocess

# possible module outcomes
class retVals:
    NO_BIN = "No binary found to run"
    NO_POLICY = "No policy found"
    TAG_FAIL = "Tagging tools did not produce expected output"
    SUCCESS = "Simulator run successfully"
    FAILURE = "Simulator failed to run to completion"


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


def setupLogger(level, colors=True):
    logger = logging.getLogger()
    logging.basicConfig(format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s", datefmt="%H:%M:%S")

    logger.setLevel(level)

    level_string = "INFO"
    if level is logging.DEBUG:
        level_string = "DEBUG"
    if colors is True:
        coloredlogs.install(level=level_string, logger=logger)

    return logger


def generateTagInfo(exe_path, run_dir, policy_dir, arch="rv32", soc_cfg=None):
    policy = os.path.basename(policy_dir).split("-debug")[0]
    exe_name = os.path.basename(exe_path)
    doMkDir(os.path.join(run_dir, "bininfo"))
    args = ["gen_tag_info",
            "-d", policy_dir,
            "-t", os.path.join(run_dir, "bininfo", exe_name + ".taginfo"),
            "-b", exe_path,
            "--arch", arch,
            "-e", os.path.join(policy_dir, policy + ".entities.yml"),
            os.path.join(run_dir, exe_name + ".entities.yml")]
    if soc_cfg is not None:
        args += ["-s", soc_cfg]

    with open(os.path.join(run_dir, "inits.log"), "w+") as initlog:
        subprocess.Popen(args, stdout=initlog,
                         stderr=subprocess.STDOUT, cwd=run_dir).wait()

    bininfo_base_path = os.path.join(run_dir, "bininfo", exe_name) + ".{}"

    if not os.path.isfile(bininfo_base_path.format("taginfo")) or \
       not os.path.isfile(bininfo_base_path.format("text"))    or \
       not os.path.isfile(bininfo_base_path.format("text.tagged")):
        return False

    return True


def processExtraArgs(extra):
    print("Extra: {}".format(extra))
    extra_stripped = []
    for e in extra:
        extra_stripped.append(e.strip())

    return extra_stripped


def terminateMessage(runtime):
    if runtime == "frtos":
        return "Main task has completed with code:"
    if runtime == "sel4":
        return "seL4 root server abort()ed"
    elif runtime == "bare":
        return "Program has exited with code:"

    return ""
