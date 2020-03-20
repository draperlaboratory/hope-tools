import shutil
import logging
import os
import isp_utils
import multiprocessing
import subprocess 

logger = logging.getLogger()
isp_prefix = isp_utils.getIspPrefix()

def copyPexKernelSources(source_dir, output_dir):
    logger.info("Copying pex-kernel sources")
    pex_kernel_output_dir = os.path.join(output_dir, "pex-kernel")

    try:
        shutil.copytree(source_dir, pex_kernel_output_dir)
    except Exception as e:
        logger.error("Copying pex-kernel sources failed with error: {}".format(str(e)))
        return False

    subprocess.call(["make", "clean"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                    cwd=pex_kernel_output_dir)

    return True


def copyPolicySources(policy_dir, output_dir, fpga):
    logger.debug("Copying policy source to pex kernel")
    policy_name = os.path.basename(policy_dir)
    pex_kernel_output_dir = os.path.join(output_dir, "pex-kernel")
    build_dir_name = "-".join([fpga, policy_name])
    gen_dir = os.path.join(pex_kernel_output_dir, "build", build_dir_name, "gen")

    try:
        shutil.copytree(policy_dir, gen_dir)
    except Exception as e:
        logger.error("Copying pex-kernel sources failed with error: {}".format(str(e)))
        return False

    return True


def buildPexKernel(policy_name, output_dir, fpga):
    logger.debug("Building PEX kernel")
    env = dict(os.environ)

    env["FPGA"] = fpga

    if policy_name.endswith("-debug"):
        policy_name = policy_name.replace("-debug", "")
        env["DEBUG"] = "1"

    env["POLICY_NAME"] = policy_name

    num_cores = str(multiprocessing.cpu_count())
    build_log_path = os.path.join(output_dir, "build.log")
    build_log = open(build_log_path, "w+")
    pex_kernel_output_dir = os.path.join(output_dir, "pex-kernel")

    result = subprocess.call(["make", "-j"+num_cores], stdout=build_log, stderr=subprocess.STDOUT,
                             cwd=pex_kernel_output_dir, env=env)
    build_log.close()

    if result != 0:
        logger.error("PEX kernel build failed. See {} for more info".format(build_log_path))
        return False

    return True


def movePexKernel(policy_name, output_dir, fpga):
    logger.debug("Moving PEX kernel to output dir")
    pex_kernel_output_dir = os.path.join(output_dir, "pex-kernel")

    build_dir_name = "-".join([fpga, policy_name])
    build_dir = os.path.join(pex_kernel_output_dir, "build", build_dir_name)

    pex_kernel_name = pexKernelName(policy_name, fpga)
    pex_kernel_path = os.path.join(build_dir, pex_kernel_name)
    pex_kernel_out_path = os.path.join(os.path.dirname(output_dir), pex_kernel_name)

    try:
        shutil.move(pex_kernel_path, pex_kernel_out_path)
        shutil.rmtree(output_dir)
    except Exception as e:
        logger.error("Moving PEX kernel to output dir failed with error: {}".format(e))
        return False

    return True


def pexKernelName(policy_name, fpga):
    return "-".join(["kernel", fpga, policy_name])
