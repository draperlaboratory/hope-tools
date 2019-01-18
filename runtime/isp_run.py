import functools
import itertools
import operator
import subprocess
import os
import shutil
import time
import glob
import errno

from isp_utils import *
import isp_qemu
import isp_renode

# backend helper to run an ISP simulation with a binary & kernel
# TODO: runFPGA support

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

def runSim(exe_path, kernels_dir, run_dir, policy, sim, rule_cache, gdb):
    exe_name = os.path.basename(exe_path)

    if not os.path.isfile(exe_path):
        return retVals.NO_BIN

    policy_dir = os.path.join(kernels_dir, policy)
    if not os.path.isdir(policy_dir):
        return retVals.NO_POLICY

    doMkDir(run_dir)

    doValidatorCfg(policy_dir, run_dir, exe_name, rule_cache)
    doEntitiesFile(run_dir, exe_name)
    generateTagInfo(exe_path, run_dir, policy_dir)

    bininfo_base_path = os.path.join(run_dir, "bininfo", exe_name) + ".{}"
    if not os.path.isfile(bininfo_base_path.format("taginfo")) or \
       not os.path.isfile(bininfo_base_path.format("text"))    or \
       not os.path.isfile(bininfo_base_path.format("text.tagged")):
        return retVals.TAG_FAIL

    if sim == "qemu":
        isp_qemu.runOnQEMU(exe_path, run_dir, policy_dir, gdb)
    elif sim == "renode":
        isp_renode.runOnRenode(exe_path, run_dir, policy_dir, gdb)

    return retVals.SUCCESS


def generateTagInfo(exe_path, run_dir, policy_dir):
    policy = os.path.basename(policy_dir)
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


def doValidatorCfg(policy_dir, run_dir, exe_name, rule_cache):
    rule_cache_name = rule_cache[0]
    rule_cache_size = rule_cache[1]

    if "hifive" in policy_dir:
        soc_cfg = "hifive_e_cfg.yml"
    else:
        soc_cfg = "dover_cfg.yml"

    validatorCfg =  """\
---
   policy_dir: {policyDir}
   tags_file: {tagfile}
   soc_cfg_path: {soc_cfg}
""".format(policyDir=policy_dir,
           tagfile=os.path.join(run_dir, "bininfo", exe_name + ".taginfo"),
           soc_cfg=os.path.join(policy_dir, "soc_cfg", soc_cfg))

    if rule_cache_name != "":
        validatorCfg += """\
   rule_cache:
      name: {rule_cache_name}
      capacity: {rule_cache_size}
        """.format(rule_cache_name=rule_cache_name, rule_cache_size=rule_cache_size)

    with open(os.path.join(run_dir, "validator_cfg.yml"), 'w') as f:
        f.write(validatorCfg)
