import socket
import select
import threading
import time
import sys
import subprocess
import os
import logging
import isp_utils
import shutil
import multiprocessing

# set timeout seconds
timeout_seconds = 3600

uart_log_file = "uart.log"
status_log_file = "pex.log"

process_exit = False
qemu_base_cmd = "qemu-system-riscv"

logger = logging.getLogger()

isp_prefix = isp_utils.getIspPrefix()

#################################
# Build/Install validator
# Invoked by isp_install_policy
#################################

def copyEngineSources(engine_dir, output_dir):
    logger.info("Copying policy-engine sources")
    engine_output_dir = os.path.join(output_dir, "engine")
    isp_utils.doMkDir(engine_output_dir)

    try:
        shutil.copytree(os.path.join(engine_dir, "validator"), os.path.join(engine_output_dir, "validator"))
        shutil.copytree(os.path.join(engine_dir, "tagging_tools"), os.path.join(engine_output_dir, "tagging_tools"))
        shutil.copy(os.path.join(engine_dir, "Makefile.isp"), engine_output_dir)
        shutil.copy(os.path.join(engine_dir, "CMakeLists.txt"), engine_output_dir)

    except Exception as e:
        logger.error("Copying engine sources failed with error: {}".format(str(e)))
        return False

    result = subprocess.call(["make", "-f", "Makefile.isp", "clean"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=engine_output_dir)
    if result != 0:
        logger.error("Failed to clean engine directory")
        return False

    return True


def copyPolicySources(policy_dir, output_dir):
    engine_output_dir = os.path.join(output_dir, "engine", "policy")
    try:
        shutil.copytree(policy_dir, engine_output_dir)
    except Exception as e:
        logger.error("Copying policy sources failed with error: {}".format(str(e)))
        return False

    return True


def buildValidator(policy_name, output_dir):
    logger.info("Building validator library")
    engine_output_dir = os.path.join(output_dir, "engine")

    num_cores = str(multiprocessing.cpu_count())
    build_log_path = os.path.join(output_dir, "build.log")
    build_log = open(build_log_path, "w+")

    result = subprocess.call(["make", "-j"+num_cores, "-f", "Makefile.isp"], stdout=build_log, stderr=subprocess.STDOUT, cwd=engine_output_dir)
    build_log.close()

    if result != 0:
        logger.error("Policy engine build failed. See {} for more info".format(build_log_path))
        return False

    return True


def moveValidator(policy_name, output_dir, arch):
    engine_output_dir = os.path.join(output_dir, "engine")
    validator_path = os.path.join(engine_output_dir, "build", "lib{}-sim-validator.so".format(arch))

    try:
        validator_out_name = validatorName(policy_name, arch)
        validator_out_path = os.path.join(os.path.dirname(output_dir), validator_out_name) 
        shutil.move(validator_path, validator_out_path)
        shutil.rmtree(output_dir)
    except Exception as e:
        logger.error("Moving validator to output dir failed with error: {}".format(e))
        return False

    return True


def validatorName(policy_name, arch):
    return "-".join([arch, policy_name, "validator"]) + ".so"


def defaultPexPath(policy_name, arch, extra):
    return os.path.join(isp_prefix, "validator", validatorName(policy_name, arch))


def installPex(policy_dir, output_dir, arch, extra):
    logger.info("Installing policy validator for QEMU")
    engine_dir = os.path.join(isp_prefix, "sources", "policy-engine")
    policy_name = os.path.basename(policy_dir)
    
    if not copyEngineSources(engine_dir, output_dir):
        logger.error("Failed to copy policy engine sources")
        return False

    if not copyPolicySources(policy_dir, output_dir):
        logger.error("Failed to copy policy engine sources")

    if not buildValidator(policy_name, output_dir):
        logger.error("Failed to build validator")
        return False

    if not moveValidator(policy_name, output_dir, arch):
        logger.error("Failed to move validator")
        return False

    return True


#################################
# Run QEMU
# Invoked by isp_run_app
#################################
def qemuCommand(run_cmd, env, options):
    args = " ".join([run_cmd] + options)
    return "LD_LIBRARY_PATH={} {}".format(env["LD_LIBRARY_PATH"], args)

def qemuOptions(exe_path, run_dir, extra, runtime, use_validator=True, gdb_port=0):
    # Base options for any runtime
    opts = [ "-nographic",
             "-kernel", exe_path,
             "-d", "nochain"]

    # ISP validator specific flags
    if use_validator:
        opts += ["-singlestep", #need to instrument every target instruction
                 "--policy-validator-cfg",
                 "yaml-cfg={}".format(os.path.join(run_dir, "validator_cfg.yml"))]

    # Machine selection
    if "sel4" in runtime:
        opts += ["-machine", "sifive_u"]
        opts += ["-serial", "tcp::4445,server,nodelay"]
        timeout_seconds = 36000
    else:
        opts += ["-machine", "sifive_e"]

    opts += ["-serial", "file:{}".format(os.path.join(run_dir, uart_log_file))]
    # Runtime specific options
    if "sel4" in runtime:
        opts += ["-m", "size=2000M"]

    if gdb_port is not 0:
        opts += ["-S", "-gdb", "tcp::{}".format(gdb_port)]

    if extra is not None:
        opts += isp_utils.processExtraArgs(extra)

    return opts


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


def qemuSetupValidatorEnvironment(pex_path, run_dir, arch):
    os.symlink(pex_path, os.path.join(run_dir, "lib{}-sim-validator.so".format(arch)))
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = run_dir

    return env


def launchQEMU(run_dir, runtime, env, options):
    global process_exit
    terminate_msg = isp_utils.terminateMessage(runtime)
    status_log = open(os.path.join(run_dir, status_log_file), "w+")

    try:
        logger.debug("Running qemu cmd: {}\n".format(qemuCommand(run_cmd, env, options)))
        rc = subprocess.Popen([run_cmd] + options, env=env, stdout=status_log,
                              stderr=subprocess.STDOUT)
        while rc.poll() is None and not process_exit:
            time.sleep(1)
            try:
                uart_log = open(os.path.join(run_dir, uart_log_file), 'r')
                uart_output = uart_log.read()
                uart_log.close()
                if terminate_msg in uart_output:
                    rc.terminate()
                    process_exit = True
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
    except Exception as e:
        logger.error("QEMU run failed for exception {}.\n".format(e))
    finally:
        process_exit = True
        rc.terminate()

        # using grep because the pex log can get large when debug is on
        grep_cmd = ["grep", "Policy Violation\\|TMT miss", os.path.join(run_dir, status_log_file)]
        grep_results = subprocess.run(grep_cmd, env=env, stdout=subprocess.PIPE);
        if "Policy Violation" in str(grep_results.stdout):
            logger.warn("Process exited due to policy violation")
        if "TMT miss" in str(grep_results.stdout):
            logger.warn("Process exited due to TMT miss")


def launchQEMUDebug(run_dir, env, options):
    status_log = open(os.path.join(run_dir, status_log_file), "w+")
    logger.debug("Running qemu cmd: {}\n".format(qemuCommand(run_cmd, env, options)))

    rc = subprocess.Popen([run_cmd] + options, env=env, stdout=status_log)
    rc.wait()


def runSim(exe_path, run_dir, policy_dir, pex_path, runtime, rule_cache,
           gdb_port, tagfile, soc_cfg, arch, extra, use_validator=True, tag_only=False):
    global run_cmd
    global uart_log_file
    global status_log_file

    if soc_cfg is None:
        soc_cfg = os.path.join(isp_prefix, "soc_cfg", "hifive_e_cfg.yml")
    else:
        soc_cfg = os.path.realpath(soc_cfg)
    logger.debug("Using SOC config {}".format(soc_cfg))

    qemu_cmd = qemu_base_cmd + '32'
    if arch == 'rv64':
        qemu_cmd = qemu_base_cmd + '64'

    env = dict(os.environ)

    if use_validator == False:
        run_cmd = os.path.join(os.environ['ISP_PREFIX'],'stock-tools','bin', qemu_cmd)
    else:
        run_cmd = os.path.join(os.environ['ISP_PREFIX'],'bin', qemu_cmd)
        env = qemuSetupValidatorEnvironment(pex_path, run_dir, arch)

        doValidatorCfg(policy_dir, run_dir, exe_path, rule_cache, soc_cfg, tagfile)

        if tagfile is None:
            if isp_utils.generateTagInfo(exe_path, run_dir, policy_dir, arch=arch) is False:
                return isp_utils.retVals.TAG_FAIL

    if tag_only is True:
        return isp_utils.retVals.SUCCESS

    options = qemuOptions(exe_path, run_dir, extra, runtime, use_validator, gdb_port)

    try:
        logger.debug("Begin QEMU test... (timeout: {})".format(timeout_seconds))
        if gdb_port is not 0:
            launchQEMUDebug(run_dir, env, options)
        else:
            wd = threading.Thread(target=watchdog)
            wd.start()
            qemu = threading.Thread(target=launchQEMU, args=(run_dir, runtime, env, options))
            qemu.start()
            wd.join()
            qemu.join()
    finally:
        pass

    return isp_utils.retVals.SUCCESS
