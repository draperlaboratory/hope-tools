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
run_cmd = "qemu-system-riscv32"

logger = logging.getLogger()

def qemuOptions(exe_path, run_dir, extra, gdb_port=0, use_val=True):

    opts = [ "-nographic",
             "-machine", "sifive_e",
             "-kernel", exe_path,
             "-serial", "file:{}".format(os.path.join(run_dir, uart_log_file)),
             "-D", os.path.join(run_dir, status_log_file),
             "-singlestep", #need to instrument every target instruction
             "-d", "nochain"]
    if use_val:
        opts+= ["--policy-validator-cfg",
                "yaml-cfg={}".format(os.path.join(run_dir, "validator_cfg.yml"))]

    if gdb_port is not 0:
        opts += ["-S", "-gdb", "tcp::{}".format(gdb_port)]

    if extra is not None:
        opts += extra.split()

    return opts


def watchdog():
    global process_exit
    for i in range(timeout_seconds * 10):
        if not process_exit:
            time.sleep(0.5)
        else:
            return
    logger.warn("Watchdog timeout")
    process_exit = True

def launchQEMU(exe_path, run_dir, policy_dir, runtime, extra, use_val=True):
    global process_exit
    terminate_msg = isp_utils.terminateMessage(runtime)
    sim_log = open(os.path.join(run_dir, sim_log_file), "w+")
    opts = qemuOptions(exe_path, run_dir, extra, 0, use_val)

    try:
        logger.debug("Running qemu cmd:{}\n".format(str([run_cmd] + opts)))
        rc = subprocess.Popen([run_cmd] + opts,
                              env={"LD_LIBRARY_PATH": policy_dir,
                                   "PATH": os.environ["PATH"]}, stdout=sim_log, stderr=subprocess.STDOUT)
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

def launchQEMUDebug(exe_path, run_dir, policy_dir, gdb_port, extra, use_val=True):
    sim_log = open(os.path.join(run_dir, sim_log_file), "w+")
    opts = qemuOptions(exe_path, run_dir, extra, gdb_port, use_val)
    logger.debug("Running qemu cmd:{}\n", str([run_cmd] + opts))
    rc = subprocess.Popen([run_cmd] + opts,
                          env={"LD_LIBRARY_PATH": policy_dir,
                               "PATH": os.environ["PATH"]}, stdout=sim_log)
    rc.wait()

def runSim(exe_path, run_dir, policy_dir, runtime, gdb_port, extra, use_val=True):
    global run_cmd
    global uart_log_file
    global status_log_file
    global sim_log_file

    if not use_val:
        run_cmd = os.path.join(os.environ['ISP_PREFIX'],"stock-tools/bin/qemu-system-riscv32")
        uart_log_file = "uart_noval.log"
        status_log_file = "pex_noval.log"
        sim_log_file = "sim_noval.log"

    try:
        logger.debug("Begin QEMU test... (timeout: {})".format(timeout_seconds))
        if gdb_port is not 0:
            launchQEMUDebug(exe_path, run_dir, policy_dir, gdb_port, extra, use_val)
        else:
            wd = threading.Thread(target=watchdog)
            wd.start()
            qemu = threading.Thread(target=launchQEMU, args=(exe_path, run_dir, policy_dir, runtime, extra, use_val))
            qemu.start()
            wd.join()
            qemu.join()
    finally:
        pass
