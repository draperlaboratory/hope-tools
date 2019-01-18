import socket
import select
import threading
import time
import sys
import subprocess
import os
import logging

# this script relys on either the AP or Pex printing this to end the test
terminate_msg = "Progam has exited with code:"

# print fpga io to stdout
printIO = True

# set timeout seconds
timeoutSec = 3600

uart_log_file = "uart.log"
status_log_file = "pex.log"
sim_log_file = "sim.log"

test_done = False
run_cmd = "qemu-system-riscv32"

logger = logging.getLogger()

def qemuOptions(exe_path, run_dir, debug=0):
    opts = [ "-nographic",
             "-machine", "sifive_e",
             "-kernel", exe_path,
             "-serial", "file:{}".format(os.path.join(run_dir, uart_log_file)),
             "-D", os.path.join(run_dir, status_log_file),
             "-singlestep", #need to instrument every target instruction
             "-d", "nochain",
             "--policy-validator-cfg",
             "yaml-cfg={}".format(os.path.join(run_dir, "validator_cfg.yml"))]
    if debug is not 0:
        opts += ["-S", "-gdb", "tcp::{}".format(debug)]

    return opts


def watchdog():
    global test_done
    for i in range(timeoutSec * 10):
        if not test_done:
            time.sleep(0.5)
        else:
            return
    logger.warn("Watchdog timeout")
    test_done = True

def launchQEMU(exe_path, run_dir, policy_dir):
    global test_done
    sim_log = open(os.path.join(run_dir, sim_log_file), "w+")
    opts = qemuOptions(exe_path, run_dir)
    try:
        logger.debug("Running qemu cmd:{}\n".format(str([run_cmd] + opts)))
        rc = subprocess.Popen([run_cmd] + opts,
                              env={"LD_LIBRARY_PATH": policy_dir,
                                   "PATH": os.environ["PATH"]}, stdout=sim_log)
        while rc.poll() is None:
            time.sleep(1)
            try:
                if terminate_msg in open(os.path.join(run_dir, uart_log_file), 'r').read() or test_done:
                    rc.terminate()
                    test_done = True
                    return
                if terminate_msg in open(os.path.join(run_dir, status_log_file), 'r').read() or test_done:
                    rc.terminate()
                    test_done = True
                    return
            except IOError:
                #keep trying if fail to open uart log
                pass
            except UnicodeDecodeError:
                # TODO: is this really what we want to do on this exception?
                rc.terminate()
                test_done = True
                return;
        if rc.returncode != 0:
            raise Exception("exited with return code " + str(rc.returncode))
        test_done = True
    except Exception as e:
        logger.error("QEMU run failed for exception {}.\n".format(e))
        raise

def launchQEMUDebug(exe_path, run_dir, policy_dir, debug):
    sim_log = open(os.path.join(run_dir, sim_log_file), "w+")
    opts = qemuOptions(exe_path, run_dir, debug)
    logger.debug("Running qemu cmd:{}\n", str([run_cmd] + opts))
    rc = subprocess.Popen([run_cmd] + opts,
                          env={"LD_LIBRARY_PATH": policy_dir,
                               "PATH": os.environ["PATH"]}, stdout=sim_log)
    rc.wait()

def runOnQEMU(exe_path, run_dir, policy_dir, debug):
    try:
        logger.debug("Begin QEMU test... (timeout: {})".format(timeoutSec))
        if debug is not 0:
            launchQEMUDebug(exe_path, run_dir, policy_dir, debug)
        else:
            wd = threading.Thread(target=watchdog)
            wd.start()
            qemu = threading.Thread(target=launchQEMU, args=(exe_path, run_dir, policy_dir))
            qemu.start()
            wd.join()
            qemu.join()
            logger.debug("Test Completed")
    finally:
        pass
