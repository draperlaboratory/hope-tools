import os
import errno
import shutil
import logging
import coloredlogs
import subprocess

from elftools.elf.elffile import ELFFile

# possible module outcomes
class retVals:
    NO_BIN = "No binary found to run"
    NO_POLICY = "No policy found"
    TAG_FAIL = "Tagging tools did not produce expected output"
    SUCCESS = "Simulator run successfully"
    FAILURE = "Simulator failed to run to completion"


elf_archs = {
    ("EM_RISCV", 32) : "rv32",
    ("EM_RISCV", 64) : "rv64",
}

supportedArchs = list(elf_archs.values())

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


def getPolicyFullName(policies, global_policies, debug):
    composed_policies = "-".join(sorted(policies))

    if global_policies:
        composed_global_policies = "-".join(sorted(global_policies))
        composed_policies = "-".join([composed_global_policies, composed_policies])

    if debug:
        return "-".join([composed_policies, "debug"])
    else:
        return composed_policies


def getPolicyModuleName(policy):
    return ".".join(["osv", policy, (policy + "Pol")])


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


def generateTagInfo(exe_path, run_dir, policy_dir, soc_cfg=None, arch=None):
    policy = os.path.basename(policy_dir).split("-debug")[0]
    exe_name = os.path.basename(exe_path)
    doMkDir(os.path.join(run_dir, "bininfo"))
    args = ["gen_tag_info",
            "-d", policy_dir,
            "-t", os.path.join(run_dir, "bininfo", exe_name + ".taginfo"),
            "-b", exe_path,
            "-e", os.path.join(policy_dir, "policy_entities.yml"),
            os.path.join(policy_dir, "composite_entities.yml"),
            os.path.join(run_dir, exe_name + ".entities.yml")]
    if soc_cfg is not None:
        args += ["-s", soc_cfg]
    if arch is not None:
        args += ["--arch", arch]

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
        return "Program exited with code:"

    return ""


def checkDependency(path, logger, repo=None):
    if not os.path.exists(path):
        if repo:
            logger.error('''
            Could not find the runtime dependency {} from the {} repository.
            If you have access to {}, re-install the dependency from this repo and try again.
            '''.format(path, repo, repo))
        else:
            logger.error('''
            Could not find the repository {}
            If you have access to {}, please clone it and try again
            '''.format(path, os.path.basename(path)))
        return False

    return True


def getArch(exe_path):
    exe = open(exe_path, "rb")
    elf_file = ELFFile(exe)

    elf_arch = (elf_file.header["e_machine"], elf_file.elfclass)

    if elf_arch in elf_archs:
        return elf_archs[elf_arch]

    return None
