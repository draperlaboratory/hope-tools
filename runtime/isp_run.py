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

# backend helper to run an ISP simulation with a binary & kernel

# possible module outcomes
class retVals:
    NO_BIN = "No binary found to run"
    NO_POLICY = "No policy found"
    TAG_FAIL  = "Tagging tools did not produce expected output"
    SUCCESS   = "Simulator run successfully"

# -- MAIN MODULE FUNCTIONALITY

# arguments:
#  test_dir - output directory produced by isp_build tool
#  kernels_dir - directory containing the kernel to be run
#  run_dir - output of this module. Directory to put supporting files, run
#    the simulation, and store the appropriate logs
#  template_dir - Directory containing ISP provided generic run simulation
#    scripts
#  runtime - Currently supported: frtos, hifive (bare metal)
#  policy - name of the policy to be run
#  sim - name of the simultator to use
#  rc - rule cache configuration tuple. (cache_name, size)

def run_sim(test_dir, kernels_dir, run_dir, template_dir, runtime, policy, sim, rc):

    if not os.path.isfile(os.path.join(test_dir, "build", "main")):
        return retVals.NO_BIN

    doMkDir(run_dir)

    # simulator-specific run options
    if "qemu" in sim:
        shutil.copy(os.path.join(template_dir, "runQEMU.py"), test_dir)
    elif "renode" in sim:
        shutil.copy(os.path.join(template_dir, "runRenode.py"), test_dir)
    else:
        shutil.copy(os.path.join(template_dir, "runFPGA.py"), test_dir)

    # policy-specific stuff

    # retrieve policy
    subprocess.Popen(["cp", "-r", os.path.join(kernels_dir, policy), run_dir], stdout=open(os.devnull, 'w'), stderr=subprocess.STDOUT).wait()
    if not os.path.isdir(os.path.join(run_dir, policy)):
        return retVals.NO_POLICY

    # test-run-level makefile. ie make inits & make qemu
    doMakefile(policy, run_dir)

    # script for renode config
    if sim == "renode":
        doReSc(policy, run_dir)

    doDebugScript(run_dir, sim)

    # config validator including rule cache
    doValidatorCfg(policy, run_dir, rc[0], rc[1])

    # run tagging tools
    doMkDir(os.path.join(run_dir, "bininfo"))
    make_entities_file(run_dir, "main")

    with open(os.path.join(run_dir, "inits.log"), "w+") as initlog:
        subprocess.Popen(["make", "-f", "Makefile.isprun", "inits"], stdout=initlog, stderr=subprocess.STDOUT, cwd=run_dir).wait()

    # Check for tag information
    if not os.path.isfile(os.path.join(run_dir, "bininfo", "main.taginfo")) or \
       not os.path.isfile(os.path.join(run_dir, "bininfo", "main.text"))    or \
       not os.path.isfile(os.path.join(run_dir, "bininfo", "main.text.tagged")):
        return retVals.TAG_FAIL

    # run test
    simlog = open(os.path.join(run_dir, "sim.log"), "w+")
    subprocess.Popen(["make", "-f", "Makefile.isprun", sim], stdout=simlog, stderr=subprocess.STDOUT, cwd=run_dir).wait()

    return retVals.SUCCESS

# Generate the makefile
def doMakefile(policy, dp):

    mf = sim_makefile(policy)

    with open(os.path.join(dp,'Makefile.isprun'), 'w') as f:
        f.write(mf)

def sim_makefile(policy):
    return """
PYTHON ?= python3

inits:
	gen_tag_info -d ./{p} -t bininfo/main.taginfo -b ../build/main -e ./{p}/{p}.entities.yml ../*.entities.yml

renode:
	$(PYTHON) ../runRenode.py

renode-console:
	renode main.resc

qemu:
	$(PYTHON) ../runQEMU.py {p}

qemu-console:
	$(PYTHON) ../runQEMU.py {p} -d

gdb:
	riscv32-unknown-elf-gdb -q -iex "set auto-load safe-path ./" ../build/main

clean:
	rm -rf *.o *.log bininfo/*
""".format(p=policy)

# Generate the resc script
def doReSc(policy, dp):

    rs = rescScript(dp, policy)

    with open(os.path.join(dp,'main.resc'), 'w') as f:
        f.write(rs)

# generate a debug script
def doDebugScript(dp, simulator):
    gs = gdbScriptQemu(dp) if simulator == "qemu" else gdbScript(dp)

    with open(os.path.join(dp,'.gdbinit'), 'w') as f:
        f.write(gs)

def rescScript(dir, policy):
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
sysbus.ap_core StartGdbServer 3333
logLevel 1 sysbus.ap_core
sysbus.ap_core StartStatusServer 3344
""".format(path = os.path.join(os.getcwd(), dir), policies=policy)

def gdbScript(dir):
    return """

define metadata
   help metadata
end

document metadata
Renode simulator commands:
   rstart   - renode start
   rquit    - renode quit
Metadata related commnads:
   pvm      - print violation message
   lre      - print last rule evaluation
   env-m    - get the env metadata
   reg-m n  - get register n metadata
   areg-m   - get all register metadata
   csr-m a  - get csr metadata at addr a
   mem-m a  - get mem metadata at addr a
Watchpoints halt simulation when metadata changes
   env-mw   - set watch on the env metadata
   reg-mw n - set watch on register n metadata
   csr-mw a - set watch on csr metadata at addr a
   mem-mw a - set watch on mem metadata at addr a
end

define pvm
   monitor sysbus.ap_core PolicyViolationMsg
end

document pvm
   Command to print last policy violation info
   Only captures the last violation info.
end

define lre
   monitor sysbus.ap_core RuleEvalLog
end

document lre
   Command to print last rule evaluation info
end

define rstart
   monitor start
end

define rquit
   monitor quit
end

define env-m
   monitor sysbus.ap_core EnvMetadata
end

document env-m
   get environment metadata
end

define reg-m
   monitor sysbus.ap_core RegMetadata $arg0
end

document reg-m
   get register metadata
end

define areg-m
   monitor sysbus.ap_core AllRegMetadata
end

document areg-m
   get all register metadata
end

define csr-m
   monitor sysbus.ap_core CsrMetadata $arg0
end
document csr-m
   get csr metadata at addr
end

define mem-m
   monitor sysbus.ap_core MemMetadata $arg0
end
document mem-m
   get mem metadata at addr
end

define env-mw
   monitor sysbus.ap_core EnvMetadataWatch true
end
document env-mw
   set watch on the env metadata
end

define reg-mw
   monitor sysbus.ap_core RegMetadataWatch $arg0
end
document reg-mw
   set watch on register metadata
end

define csr-mw
   monitor sysbus.ap_core CsrMetadataWatch $arg0
end
document csr-mw
   set watch on csr metadata at addr
end

define mem-mw
   monitor sysbus.ap_core MemMetadataWatch $arg0
end
document mem-mw
   set watch on mem metadata at addr
end



define hook-stop
   pvm
end

set confirm off
target remote :3333
break main
monitor start
continue
""".format(path = os.path.join(os.getcwd(), dir))


def gdbScriptQemu(dir):
    return """

define metadata
   help metadata
end

document metadata
Metadata related commnads:
   pvm      - print violation message
   env-m    - get the env metadata
   reg-m n  - get register n metadata
   csr-m a  - get csr metadata at addr a
   mem-m a  - get mem metadata at addr a
Watchpoints halt simulation when metadata changes
   env-mw   - set watch on the env metadata
   reg-mw n - set watch on register n metadata
   csr-mw a - set watch on csr metadata at addr a
   mem-mw a - set watch on mem metadata at addr a
end

define pvm
   monitor pvm
end

document pvm
   Command to print last policy violation info
   Only captures the last violation info.
end

define env-m
   monitor env-m
end

document env-m
   get environment metadata
end

define reg-m
   monitor reg-m
end

document reg-m
   get register metadata
end

define csr-m
   monitor csr-m $arg0
end
document csr-m
   get csr metadata at addr
end

define mem-m
   monitor mem-m $arg0
end
document mem-m
   get mem metadata at addr
end

define env-mw
   monitor env-mw
end
document env-mw
   set watch on the env metadata
end

define reg-mw
   monitor reg-mw $arg0
end
document reg-mw
   set watch on register metadata
end

define csr-mw
   monitor csr-mw $arg0
end
document csr-mw
   set watch on csr metadata at addr
end

define mem-mw
   monitor mem-mw $arg0
end
document mem-mw
   set watch on mem metadata at addr
end



define hook-stop
   pvm
end

set confirm off
target remote :3333
break main
continue
""".format(path = os.path.join(os.getcwd(), dir))

def doValidatorCfg(policy, dirPath, rule_cache, rule_cache_size):

    if "hifive" in policy:
        soc_cfg = "hifive_e_cfg.yml"
    else:
        soc_cfg = "dover_cfg.yml"

    validatorCfg =  """\
---
   policy_dir: {policyDir}
   tags_file: {tagfile}
   soc_cfg_path: {soc_cfg}
""".format(policyDir=os.path.join(os.getcwd(), dirPath, policy),
           tagfile=os.path.join(os.getcwd(), dirPath, "bininfo/main.taginfo"),
           soc_cfg=os.path.join(os.getcwd(), dirPath, policy, "soc_cfg", soc_cfg))

    if (rule_cache):
        validatorCfg += """\
   rule_cache:
      name: {rule_cache_name}
      capacity: {rule_cache_size}
        """.format(rule_cache_name=rule_cache, rule_cache_size=rule_cache_size)

    with open(os.path.join(dirPath,'validator_cfg.yml'), 'w') as f:
        f.write(validatorCfg)
