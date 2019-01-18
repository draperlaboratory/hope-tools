# test script for running unit test
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

# backend helper to run an ISP simulation with a binary & kernel

# possible module outcomes
class retVals:
    NO_BIN = "No binary found to run"
    NO_POLICY = "No policy found"
    TAG_FAIL  = "Tagging tools did not produce expected output"
    SUCCESS   = "Simulator run successfully"

# -- MAIN MODULE FUNCTIONALITY

# arguments:
#  exe_path - path to executable to be run
#  kernels_dir - directory containing the kernel to be run
#  run_dir - output of this module. Directory to put supporting files, run
#    the simulation, and store the appropriate logs
#  policy - name of the policy to be run
#  sim - name of the simultator to use
#  rule_cache - rule cache configuration tuple. (cache_name, size)
#  gdb - debug port for gdbserver mode (optional)

def runSim(exe_path, kernels_dir, run_dir, policy, sim, rule_cache, gdb):

    if not os.path.isfile(exe_path):
        return retVals.NO_BIN

    exe_name = os.path.basename(exe_path)

    doMkDir(run_dir)

    # TODO: replace runRenode.py and runFPGA.py

    policy_dir = os.path.join(kernels_dir, policy)
    if not os.path.isdir(policy_dir):
        return retVals.NO_POLICY

    if sim == "renode":
        doRenodeScript(policy, run_dir)

    doValidatorCfg(policy_dir, run_dir, exe_name, rule_cache)

    doMkDir(os.path.join(run_dir, "bininfo"))
    makeEntitiesFile(run_dir, exe_name)

    with open(os.path.join(run_dir, "inits.log"), "w+") as initlog:
        subprocess.Popen(["gen_tag_info",
                          "-d", policy_dir,
                          "-t", os.path.join(run_dir, "bininfo", exe_name + ".taginfo"),
                          "-b", exe_path,
                          "-e", os.path.join(policy_dir, policy + ".entities.yml"),
                          os.path.join(run_dir, exe_name + ".entities.yml")],
                          stdout=initlog, stderr=subprocess.STDOUT, cwd=run_dir).wait()

    if not os.path.isfile(os.path.join(run_dir, "bininfo", exe_name + ".taginfo")) or \
       not os.path.isfile(os.path.join(run_dir, "bininfo", exe_name + ".text"))    or \
       not os.path.isfile(os.path.join(run_dir, "bininfo", exe_name + ".text.tagged")):
        return retVals.TAG_FAIL

    isp_qemu.runOnQEMU(exe_path, run_dir, policy_dir, gdb)

    return retVals.SUCCESS

# Generate the resc script for Renode
def doRenodeScript(policy, dp):

    rs = rescScript(dp, policy)

    with open(os.path.join(dp,'main.resc'), 'w') as f:
        f.write(rs)

def rescScript(dir, policy, gdb):
    gdb_command = ""

    if gdb is not 0:
        gdb_command = "sysbus.ap_core StartGdbServer {}".format(gdb)

    return """
mach create
machine LoadPlatformDescription @platforms/boards/dover-riscv-board.repl
sysbus.ap_core MaximumBlockSize 1
emulation CreateServerSocketTerminal 4444 "uart-socket"
connector Connect sysbus.uart1 uart-socket
#showAnalyzer sysbus.uart Antmicro.Renode.UI.ConsoleWindowBackendAnalyzer
#emulation CreateUartPtyTerminal "uart-pty" "/tmp/uart-pty"
#connector Connect sysbus.uart uart-pty
sysbus LoadELF @{path}/../build/main
sysbus.ap_core SetExternalValidator @{path}/{policies}/librv32-renode-validator.so @{path}/validator_cfg.yml
{gdb_command}
logLevel 1 sysbus.ap_core
sysbus.ap_core StartStatusServer 3344
""".format(path = os.path.join(os.getcwd(), dir), policies=policy, gdb_command=gdb_command)

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
