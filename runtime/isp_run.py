import functools
import itertools
import operator
import subprocess
import os
import shutil
import time
import glob
import errno
import logging

from isp_utils import *

# backend helper to run an ISP simulation with a binary & kernel
# TODO: runFPGA support

logger = logging.getLogger()

# possible module outcomes
class retVals:
    NO_BIN = "No binary found to run"
    NO_POLICY = "No policy found"
    TAG_FAIL  = "Tagging tools did not produce expected output"
    SUCCESS   = "Simulator run successfully"

# -- MAIN MODULE FUNCTIONALITY

# arguments:
#  exe_path - path to executable to be run
#  kernels_dir - directory containing PEX kernels
#  run_dir - output of this module. Directory to put supporting files, run
#    the simulation, and store the appropriate logs
#  policy - name of the policy to be run
#  sim - name of the simultator to use
#  rule_cache - rule cache configuration tuple. (cache_name, size)
#  gdb - debug port for gdbserver mode (optional)
#  tag_only - run the tagging tools without running the simulator
#  extra - extra command line arguments to the simulator

def runSim(exe_path, policy_dir, run_dir, sim, runtime, rule_cache, gdb, tag_only, soc_cfg, extra):
    exe_name = os.path.basename(exe_path)

    if not os.path.isfile(exe_path):
        return retVals.NO_BIN

    if not os.path.isdir(policy_dir):
        if compileMissingPolicy(policy_dir) is False:
            return retVals.NO_POLICY

    doMkDir(run_dir)

    doValidatorCfg(policy_dir, run_dir, exe_name, rule_cache, soc_cfg)
    doEntitiesFile(run_dir, exe_name)
    generateTagInfo(exe_path, run_dir, policy_dir)

    bininfo_base_path = os.path.join(run_dir, "bininfo", exe_name) + ".{}"
    if not os.path.isfile(bininfo_base_path.format("taginfo")) or \
       not os.path.isfile(bininfo_base_path.format("text"))    or \
       not os.path.isfile(bininfo_base_path.format("text.tagged")):
        return retVals.TAG_FAIL

    if tag_only is True:
        return retVals.SUCCESS

    sim_module = __import__("isp_" + sim)
    sim_module.runSim(exe_path, run_dir, policy_dir, runtime, gdb, extra)

    return retVals.SUCCESS


def compileMissingPolicy(policy_dir):
    isp_kernel_args = [os.path.basename(policy_dir), "-o",
            os.path.dirname(policy_dir)]

    logger.info("Attempting to compile missing policy")
    subprocess.Popen(["isp_kernel"] + isp_kernel_args).wait()

    if not os.path.isdir(policy_dir):
        logger.error("Failed to compile missing policy")
        return False

    logger.info("Successfully compiled missing policy")
    return True


def generateTagInfo(exe_path, run_dir, policy_dir):
    policy = os.path.basename(policy_dir).split("-debug")[0]
    exe_name = os.path.basename(exe_path)
    doMkDir(os.path.join(run_dir, "bininfo"))
    with open(os.path.join(run_dir, "inits.log"), "w+") as initlog:
        subprocess.Popen(["gen_tag_info",
                          "-d", policy_dir,
                          "-t", os.path.join(run_dir, "bininfo", exe_name + ".taginfo"),
                          "-b", exe_path,
                          "-e", os.path.join(policy_dir, policy + ".entities.yml"),
                          os.path.join(run_dir, exe_name + ".entities.yml")],
                          stdout=initlog, stderr=subprocess.STDOUT, cwd=run_dir).wait()


def doEntitiesFile(run_dir, name):
    filename = os.path.join(run_dir, (name + ".entities.yml"))
    if os.path.exists(filename) is False:
        open(filename, "a").close()


def doValidatorCfg(policy_dir, run_dir, exe_name, rule_cache, soc_cfg):
    rule_cache_name = rule_cache[0]
    rule_cache_size = rule_cache[1]

    logger.info("Using soc_cfg file: {}".format(soc_cfg))

    validatorCfg =  """\
---
   policy_dir: {policyDir}
   tags_file: {tagfile}
   soc_cfg_path: {soc_cfg}
""".format(policyDir=policy_dir,
           tagfile=os.path.join(run_dir, "bininfo", exe_name + ".taginfo"),
           soc_cfg=soc_cfg)

    if rule_cache_name != "":
        validatorCfg += """\
   rule_cache:
      name: {rule_cache_name}
      capacity: {rule_cache_size}
        """.format(rule_cache_name=rule_cache_name, rule_cache_size=rule_cache_size)

    with open(os.path.join(run_dir, "validator_cfg.yml"), 'w') as f:
        f.write(validatorCfg)
