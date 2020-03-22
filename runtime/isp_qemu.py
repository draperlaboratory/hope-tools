import socket
import select
import threading
import time
import sys
import subprocess
import os
import logging
import isp_utils

# set timeout seconds
timeout_seconds = 3600

uart_log_file = "uart.log"
status_log_file = "pex.log"
sim_log_file = "sim.log"

process_exit = False
qemu_cmd = "qemu-system-riscv32"

logger = logging.getLogger()

def qemuOptions(exe_path, run_dir, extra, runtime, use_validator=True, gdb_port=0):
    # Base options for any runtime
    opts = [ "-nographic",
             "-kernel", exe_path,
             "-serial", "file:{}".format(os.path.join(run_dir, uart_log_file)),
             "-D", os.path.join(run_dir, status_log_file),
             "-d", "nochain"]

    # ISP validator specific flags
    if use_validator:
        opts += ["-singlestep", #need to instrument every target instruction
                 "--policy-validator-cfg",
                 "yaml-cfg={}".format(os.path.join(run_dir, "validator_cfg.yml"))]

    # Machine selection
    if "sel4" in runtime:
        opts += ["-machine", "virt"]
    else:
        opts += ["-machine", "sifive_e"]

    # Runtime specific options
    if "sel4" in runtime:
        opts += ["-m", "size=2000M"]

    if gdb_port is not 0:
        opts += ["-S", "-gdb", "tcp::{}".format(gdb_port)]

    if extra is not None:
        opts += isp_utils.processExtraArgs(extra) #[0].split(" ")

    return opts


def qemuEnv(use_validator, policy_dir):
    env = {"PATH": os.environ["PATH"]}

    if use_validator:
        env["LD_LIBRARY_PATH"] = policy_dir

    return env


def doValidatorCfg(policy_dir, run_dir, exe_path, rule_cache, soc_cfg, tagfile):
    exe_name = os.path.basename(exe_path)
    rule_cache_name = rule_cache[0]
    rule_cache_size = rule_cache[1]

    if tagfile == None:
        tagfile = os.path.join(run_dir, "bininfo", exe_name + ".taginfo")

    validatorCfg =  """\
---
   policy_dir: {policyDir}
   tags_file: {tagfile}
   soc_cfg_path: {soc_cfg}
""".format(policyDir=policy_dir,
           tagfile=os.path.abspath(tagfile),
           soc_cfg=soc_cfg)

    if rule_cache_name != "":
        validatorCfg += """\
   rule_cache:
      name: {rule_cache_name}
      capacity: {rule_cache_size}
        """.format(rule_cache_name=rule_cache_name, rule_cache_size=rule_cache_size)

    with open(os.path.join(run_dir, "validator_cfg.yml"), 'w') as f:
        f.write(validatorCfg)


def watchdog():
    global process_exit
    for i in range(timeout_seconds * 10):
        if not process_exit:
            time.sleep(0.5)
        else:
            return
    logger.warn("Watchdog timeout")
    process_exit = True


def launchQEMU(exe_path, run_dir, policy_dir, runtime, extra, use_validator=True):
    global process_exit
    terminate_msg = isp_utils.terminateMessage(runtime)
    sim_log = open(os.path.join(run_dir, sim_log_file), "w+")

    opts = qemuOptions(exe_path, run_dir, extra, runtime, use_validator, gdb_port=0)

    env = qemuEnv(use_validator, policy_dir)

    try:
        logger.debug("Running qemu cmd:{}\n".format(str([run_cmd] + opts)))
        rc = subprocess.Popen([run_cmd] + opts, env=env, stdout=sim_log,
                              stderr=subprocess.STDOUT)
        while rc.poll() is None:
            time.sleep(1)
            try:
                if terminate_msg in open(os.path.join(run_dir, uart_log_file), 'r').read() or process_exit:
                    rc.terminate()
                    process_exit = True
                    return
                if "Policy Violation:" in open(os.path.join(run_dir, status_log_file), 'r').read() or process_exit:
                    rc.terminate()
                    process_exit = True
                    logger.warn("Process exited due to policy violation")
                    return
            except IOError:
                #keep trying if fail to open uart log
                pass
            except UnicodeDecodeError:
                # TODO: is this really what we want to do on this exception?
                rc.terminate()
                process_exit = True
                return;
        if rc.returncode != 0:
            raise Exception("exited with return code " + str(rc.returncode))
        process_exit = True
    except Exception as e:
        logger.error("QEMU run failed for exception {}.\n".format(e))
        raise


def launchQEMUDebug(exe_path, run_dir, policy_dir, gdb_port, extra, runtime, use_validator):
    sim_log = open(os.path.join(run_dir, sim_log_file), "w+")
    opts = qemuOptions(exe_path, run_dir, extra, runtime, use_validator, gdb_port)
    logger.debug("Running qemu cmd:{}\n".format(str([run_cmd] + opts)))

    env = qemuEnv(use_validator, policy_dir)
    rc = subprocess.Popen([run_cmd] + opts, env=env, stdout=sim_log)
    rc.wait()


def runSim(exe_path, run_dir, policy_dir, runtime, rule_cache,
           gdb_port, tagfile, soc_cfg, extra, use_validator=True):
    global run_cmd
    global uart_log_file
    global status_log_file
    global sim_log_file

    if soc_cfg is None:
        soc_cfg = os.path.join(policy_dir, "soc_cfg", "hifive_e_cfg.yml")
    else:
        soc_cfg = os.path.realpath(soc_cfg)
    logger.debug("Using SOC config {}".format(soc_cfg))

    if use_validator == False:
        run_cmd = os.path.join(os.environ['ISP_PREFIX'],'stock-tools','bin','qemu-system-riscv32')
    else:
        run_cmd = os.path.join(os.environ['ISP_PREFIX'],'bin','qemu-system-riscv32')

        doValidatorCfg(policy_dir, run_dir, exe_path, rule_cache, soc_cfg, tagfile)

        if tagfile is None:
            if isp_utils.generateTagInfo(exe_path, run_dir, policy_dir) is False:
                return isp_utils.retVals.TAG_FAIL

    try:
        logger.debug("Begin QEMU test... (timeout: {})".format(timeout_seconds))
        if gdb_port is not 0:
            launchQEMUDebug(exe_path, run_dir, policy_dir, gdb_port, extra,
                            runtime, use_validator)
        else:
            wd = threading.Thread(target=watchdog)
            wd.start()
            qemu = threading.Thread(target=launchQEMU, args=(exe_path, run_dir,
                                                             policy_dir, runtime,
                                                             extra, use_validator))
            qemu.start()
            wd.join()
            qemu.join()
    finally:
        pass

    return isp_utils.retVals.SUCCESS
