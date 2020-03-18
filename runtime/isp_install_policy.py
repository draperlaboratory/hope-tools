#! /usr/bin/python3

import functools
import itertools
import operator
import subprocess
import os.path
import time
import glob
import shutil
import multiprocessing
import argparse
import sys
import isp_utils
import yaml
import logging

logger = logging.getLogger()
isp_prefix = isp_utils.getIspPrefix()
sys.path.append(os.path.join(isp_prefix, "runtime", "modules"))

def runPolicyTool(policies, policies_dir, entities_dir, output_dir, debug):
    policy_names = list(isp_utils.getPolicyModuleName(policy) for policy in policies)
    logger.info("Running policy tool")

    policy_tool_cmd = "policy-tool"
    policy_tool_args = ["-t", entities_dir, "-m", policies_dir, "-o", output_dir] + policy_names

    if debug is True:
        policy_tool_args.insert(0, "-d")

    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir)

    with open(os.path.join(output_dir, "policy_tool.log"), "w+") as ptlog:
        result = subprocess.call([policy_tool_cmd]+policy_tool_args, stdout=ptlog, stderr=subprocess.STDOUT)

    if result != 0:
        return False
    return True


def generateCompositeEntities(policies, entities_dir, output):
    entity_sources = []

    for policy in policies:
        entities_file = ".".join(["osv", policy, "entities", "yml"])
        entities_path = os.path.join(entities_dir, entities_file)

        if os.path.isfile(entities_path):
            entity_sources.append(entities_path)

    entities = []
    for source in entity_sources:
        stream = open(source, "r")
        for entity_list in yaml.load_all(stream, Loader=yaml.FullLoader):
            for entity in entity_list:
                entities.append(entity)
        stream.close()

    output_stream = open(output, "w")
    if entities:
        yaml.dump_all([entities], output_stream)
    output_stream.close()


def main():
    parser = argparse.ArgumentParser(description="Build and install ISP kernels with policies")
    parser.add_argument("-p", "--policies", nargs='+', required=True, help='''
    List of policies to compose and install, or path to a policy directory
    ''')
    parser.add_argument("-P", "--global-policies", nargs='+', help='''
    List of global policies to compose and install
    ''')
    parser.add_argument("-s", "--sim", type=str, help='''
    Simulator for which to build kernel/validator
    Currently supported: qemu
    If omitted, only the policy tool will run
    ''')
    parser.add_argument("-o", "--output", type=str, default=os.getcwd(), help='''
    Output directory for compiled kernel/validator
    Default is current working directory
    This option is redundant if -s/--sim is not specified
    ''')
    parser.add_argument("-O", "--policy-output", type=str, default=os.getcwd(), help='''
    Output directory for policy
    Default is current working directory
    ''')
    parser.add_argument("-d", "--debug", action="store_true", help='''
    Enable debug logging in this script
    ''')
    parser.add_argument("-D", "--policy-debug", action="store_true", help='''
    Build policy with debug logging
    ''')
    parser.add_argument("--disable-colors", action="store_true", help='''
    Disable colored logging
    ''')

    args = parser.parse_args()

    log_level = logging.INFO
    if args.debug is True:
        log_level = logging.DEBUG

    logger = isp_utils.setupLogger(log_level, (not args.disable_colors))

    policies_dir = os.path.join(isp_prefix, "sources", "policies")
    soc_cfg_path = os.path.join(isp_prefix, "soc_cfg")
    entities_dir = os.path.join(policies_dir, "entities")

    policy_name = ""
    policy_out_dir = ""

    # use existing policy directory if -p arg refers to path
    if (len(args.policies) == 1 and
        "/" in args.policies[0] and
        os.path.isdir(args.policies[0])):
        policy_out_dir = os.path.abspath(args.policies[0])
        policy_name = os.path.basename(policy_out_dir)
    else:
        policy_name = isp_utils.getPolicyFullName(args.policies, args.global_policies, args.policy_debug)
        policy_out_dir = os.path.join(args.policy_output, policy_name)
        policies = args.policies
        if args.global_policies:
            policies += args.global_policies

        if runPolicyTool(policies, policies_dir, entities_dir,
                         policy_out_dir, args.policy_debug) is False:
            logger.error('''
                         Policy tool failed to run to completion.
                         See {}/policy_tool.log for more info
                         '''.format(policy_out_dir))
            sys.exit(1)

        entity_output_path = os.path.join(policy_out_dir,
                                          ".".join(["composite_entities", "yml"]))
        logger.info("Generating composite policy entity file at {}".format(entity_output_path))
        generateCompositeEntities(policies, entities_dir, entity_output_path)

    logger.debug("Policy directory is {}".format(policy_out_dir))

    if args.sim:
        base_output_dir = args.output

        output_dir = os.path.abspath(os.path.join(base_output_dir, "-".join(["isp", "install", policy_name])))

        shutil.rmtree(output_dir, ignore_errors=True)
        isp_utils.doMkDir(output_dir)
        sim_module = __import__("isp_" + args.sim)
        sim_module.installPex(policy_out_dir, output_dir)


if __name__ == "__main__":
    main()
