import isp_utils
import os
import argparse
import logging
import multiprocessing
import pexpect
import shutil
import subprocess
import sys
import time

sys.path.append(os.path.join(isp_utils.getIspPrefix(), "runtime"))
import isp_load_image
import isp_pex_kernel

logger = logging.getLogger()

isp_prefix = isp_utils.getIspPrefix()

fpga = "gfe-sim"
debug_suffix = "-debug"

#################################
# Build/Install PEX kernel
# Invoked by isp_install_policy
#################################

def defaultPexPath(policy_name, arch, extra):
    extra_args = parseExtra(extra)
    return os.path.join(isp_prefix, "pex-kernel", isp_pex_kernel.pexKernelName(policy_name, fpga, extra_args.processor))


def installTagMemHexdump(policy_name, output_dir, processor):
    logger.debug("Building tag_mem_hexdump utility for VCS")

    if not os.path.isdir(os.path.join(output_dir, "pex-kernel")) and \
       not isp_pex_kernel.copyPexKernelSources(os.path.join(isp_prefix, "sources", "pex-kernel"), output_dir):
        return False

    env = dict(os.environ)

    env["FPGA"] = "gfe-sim"
    env["PROCESSOR"] = processor

    if policy_name.endswith(debug_suffix):
        policy_name = policy_name.replace(debug_suffix, "")
        env["DEBUG"] = "1"

    env["POLICY_NAME"] = policy_name

    build_log_path = os.path.join(output_dir, "build.log")
    build_log = open(build_log_path, "w+")
    pex_kernel_output_dir = os.path.join(output_dir, "pex-kernel")
    result = subprocess.call(["make", "tag_mem_hexdump"], stdout=build_log, stderr=subprocess.STDOUT,
                             cwd=pex_kernel_output_dir, env=env)
    shutil.copy(os.path.join(pex_kernel_output_dir, "tag_mem_hexdump", "tag_mem_hexdump-{}".format(policy_name)),
                output_dir)
    shutil.rmtree(pex_kernel_output_dir)

    if result != 0:
        logger.error("Failed to install tag_mem_hexdump")
        return False

    return True


def installPex(policy_dir, output_dir, arch, extra):
    logger.info("Installing pex kernel for VCS")
    pex_kernel_source_dir = os.path.join(isp_prefix, "sources", "pex-kernel")
    pex_firmware_source_dir = os.path.join(isp_prefix, "sources", "pex-firmware")
    policy_name = os.path.basename(policy_dir)

    extra_args = parseExtra(extra)

    if not isp_utils.checkDependency(pex_kernel_source_dir, logger):
        return False

    if not isp_pex_kernel.copyPexKernelSources(pex_kernel_source_dir, output_dir):
        return False

    if not isp_pex_kernel.copyPolicySources(policy_dir, output_dir, fpga, extra_args.processor):
        return False

    if not isp_pex_kernel.buildPexKernel(policy_name, output_dir, fpga, extra_args.processor):
        return False

    if not isp_pex_kernel.movePexKernel(policy_name, output_dir, fpga, extra_args.processor):
        return False

    return True


#################################
# Run VCU118
# Invoked by isp_run_app
#################################

def parseExtra(extra):
    parser = argparse.ArgumentParser(prog="isp_run_app ... -s vcs -e")

    parser.add_argument("--config", default="P1SimCGConfig", help="Simulation configuration")
    parser.add_argument("--debug", action="store_true", help="Enable debug tracing")
    parser.add_argument("--timeout", type=int, default=0, help="Simulator timeout (in seconds)")
    parser.add_argument("--max-cycles", type=int, default=300000000, help="Maxmimum number of cycles to simulate")
    parser.add_argument("--processor", type=str, default="P1", help="GFE processor configuration (P1/P2/P3)")

    if extra is not None:
        extra_dashed = []
        for e in extra:
            if e.startswith("+"):
                extra_dashed.append("--" + e[1:])
            else:
                extra_dashed.append(e)

        return parser.parse_args(extra_dashed)
    return parser.parse_args([])

def generateTagMemHexdump(run_dir, tag_file_path, policy):
    policy = policy if not policy.endswith(debug_suffix) else policy[:-len(debug_suffix)]
    output_path = tag_file_path + ".hex"
    hexdump = f"tag_mem_hexdump-{policy}" if (shutil.which(f"tag_mem_hexdump-{policy}")) else os.path.join(run_dir, f"tag_mem_hexdump-{policy}")
    subprocess.call([hexdump, tag_file_path, output_path])
    return output_path

# sanity check the file name lengths; currently, the verilog code
# assumes file name lengths <= 256 characters
def validateFileName (fileName):
    if len(fileName) > 256:
        logger.debug(f"Filename path ({fileName}) needs to be less then 256 characters.")
        return False
    else:
        return True

def waitForError(run_dir, pex_uart_log):
    pex_uart_log_path = os.path.join(run_dir, pex_uart_log)
    while not os.path.exists(pex_uart_log_path):
        pass
    child = pexpect.spawn("tail", ["-f", pex_uart_log_path])
    child.expect("Unrecoverable failure", timeout=None)

def runVcsSim(exe_path, ap_hex_dump_path, pex_hex_dump_path, tag_mem_hexdump_path, config, debug, timeout, max_cycles,
              ap_uart_log, pex_uart_log):
    sim_path = os.path.join(isp_prefix, "vcs", f"simv-galois.system-{config}")
    if debug is True:
        sim_path += "-debug"

    if not isp_utils.checkDependency(sim_path, logger, "hope-gfe"):
        return False

    run_dir = os.path.dirname(ap_hex_dump_path)
    vpd_path = os.path.join(run_dir, "bininfo", (os.path.basename(exe_path) + ".vpd"))
    connector_trace_path = os.path.join(run_dir, "connector-trace.log")
    ap_trace_path = os.path.join(run_dir, "ap-trace.log")

    ap_uart_log_path = os.path.join(run_dir, ap_uart_log)
    pex_uart_log_path = os.path.join(run_dir, pex_uart_log)

    if validateFileName(ap_hex_dump_path) is False or \
       validateFileName(pex_hex_dump_path) is False or \
       validateFileName(tag_mem_hexdump_path) is False or \
       validateFileName(pex_uart_log_path) is False or \
       validateFileName(ap_uart_log_path) is False:
        return False
    
    sim_args = [sim_path,
                "+permissive",
                "-reportstats",
                "-q",
                "+ntb_random_seed_automatic",
                "+permissive-off",
                "+permissive",
                "+verbose",
                "+max-cycles=" + str(max_cycles),
                "+cg_taginfo_file=" + ap_hex_dump_path,
                "+cg_mem_file=" + pex_hex_dump_path,
                "+tags_preload_file=" + tag_mem_hexdump_path,
                "+pex_uart=" + pex_uart_log_path,
                "+ap_uart=" + ap_uart_log_path]

    if debug is True and validateFileName(vpd_path) is True:
        sim_args.append("+vcdplusfile=" + vpd_path)

    sim_args.append("+permissive-off")

    sim_args.append(exe_path)

    connector_trace = open(connector_trace_path, "w")
    ap_trace = open(ap_trace_path, "w")

    proc = subprocess.Popen(sim_args, stdout=connector_trace, stderr=ap_trace, cwd=run_dir)
    tail = multiprocessing.Process(target=waitForError, args=(run_dir, pex_uart_log))
    sleep = multiprocessing.Process(target=time.sleep, args=(timeout,))
    tail.start()
    if timeout != 0:
        sleep.start()
    while proc.poll() is None and tail.is_alive() and (timeout == 0 or sleep.is_alive()):
        pass
    proc.kill()
    tail.terminate()
    if timeout != 0:
        sleep.terminate()

    connector_trace.close()
    ap_trace.close()

    return True


def runSim(exe_path, run_dir, policy_dir, pex_path, runtime, rule_cache,
           gdb_port, tagfile, soc_cfg, arch, extra, use_validator=False, tag_only=False):
    extra_args = parseExtra(extra)
    ap_log_file = os.path.join(run_dir, "uart.log")
    pex_log_file = os.path.join(run_dir, "pex.log")
    tag_file_path = os.path.join(run_dir, "bininfo", os.path.basename(exe_path) + ".taginfo")
    ap_load_image_path = os.path.join(run_dir, os.path.basename(exe_path) + ".load_image")
    pex_load_image_path = os.path.join(run_dir, "pex.load_image")
    ap_hex_dump_path = os.path.join(run_dir, os.path.basename(ap_load_image_path) + ".hex")
    pex_hex_dump_path = os.path.join(run_dir, os.path.basename(pex_load_image_path) + ".hex")
    policy_name = os.path.basename(policy_dir)

    if not soc_cfg:
        soc_cfg = os.path.join(isp_prefix, "soc_cfg", "gfe-vcu118.yml")

    if isp_utils.generateTagInfo(exe_path, run_dir, policy_dir, soc_cfg=soc_cfg, arch=arch) is False:
        return isp_utils.retVals.TAG_FAIL

    policy = policy_name.replace(debug_suffix, "") if policy_name.endswith(debug_suffix) else policy_name
    if not shutil.which(f"tag_mem_hexdump-{policy}") and \
       not installTagMemHexdump(policy_name, run_dir, extra_args.processor):
        return False
    logger.info("Generating hex files")
    tag_mem_hexdump_path = generateTagMemHexdump(run_dir, tag_file_path, policy_name)

    isp_load_image.generate_load_image(exe_path, ap_load_image_path, tag_file_path)
    isp_load_image.generate_load_image(pex_path, pex_load_image_path)
    isp_load_image.generate_hex_dump(ap_load_image_path, ap_hex_dump_path, 64)
    isp_load_image.generate_hex_dump(pex_load_image_path, pex_hex_dump_path, 64)

    if tag_only is True:
        return isp_utils.retVals.SUCCESS

    # XXX: use default logfile names for now, update for parallel sim runs
    runVcsSim(exe_path, ap_hex_dump_path, pex_hex_dump_path, tag_mem_hexdump_path,
              extra_args.config, extra_args.debug, extra_args.timeout, extra_args.max_cycles,
              "uart.log", "pex.log")

    return isp_utils.retVals.SUCCESS
