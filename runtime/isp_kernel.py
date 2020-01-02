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

def copyEngineSources(engine_dir, output_dir):
    engine_output_dir = os.path.join(output_dir, "engine")
    isp_utils.doMkDir(engine_output_dir)

    shutil.copytree(os.path.join(engine_dir, "validator"), os.path.join(engine_output_dir, "validator"))
    shutil.copytree(os.path.join(engine_dir, "tagging_tools"), os.path.join(engine_output_dir, "tagging_tools"))
    shutil.copy(os.path.join(engine_dir, "Makefile.isp"), engine_output_dir)
    shutil.copy(os.path.join(engine_dir, "CMakeLists.txt"), engine_output_dir)

    shutil.copytree(os.path.join(engine_dir, "soc_cfg"), os.path.join(output_dir, "soc_cfg"))


def copyPolicyYaml(policy, policies_dir, entities_dir, output_dir):

    policy_files = []
    for p in policies_dir:
        policy_files += [os.path.abspath(os.path.join(p,f)) for f in os.listdir(p)]

    for policy_file in policy_files:
        if "yml" in policy_file or "log" in policy_file:
            shutil.copy(policy_file, output_dir)

    # look for exact entity file match for policy
    entities_sources = []
    for e in entities_dir:
        ef = os.path.join(e, policy + ".entities.yml")
        if os.path.isfile(ef):
            shutil.copy(ef, output_dir)
            policy_entities_found = True

    entities_dest = os.path.join(output_dir, policy + ".entities.yml")

    # special handling for composite policies
    # TODO: better way to determine composite policy?
    policy_parts = policy.split(".")[-1].split("-")
    policy_prefix = policy.rsplit(".", 1)[0] + "."

    policy_entities_found = False

    # build composite entities for composite policy w.o existing entities
    if len(policy_parts) != 1 and not policy_entities_found:

        ents = []
        with open(entities_dest, 'w') as comp_ents:
            for p in policy_parts:

                policy_entities_file = policy_prefix + p + ".entities.yml"

                if os.path.isfile(os.path.join(entities_dir, policy_entities_file)):
                    f = os.path.join(entities_dir, policy_entities_file)
                    with open(f, "r") as instream:
                        for el in yaml.load_all(instream, Loader=yaml.FullLoader):
                            for e in el:
                                ents.append(e)

            if ents:
                yaml.dump_all([ents], comp_ents)

    # look for empty entities file.
    if not os.path.isfile(entities_dest):
        for e in entities_dir:
            for ee in [os.path.abspath(os.path.join(e,f)) for f in os.listdir(e)]:
                if "empty.entities.yml" in ee:
                    shutil.copyfile(ee, entities_dest)

    if not os.path.isfile(entities_dest):
        return False

    return True


        
def runPolicyTool(policy, policies_dir, entities_dir, output_dir, debug):
    policy_output_dir = os.path.join(output_dir, "engine", "policy")
    policy_tool_cmd = "policy-tool"

    policy_tool_args = []
    for e in entities_dir:
        policy_tool_args += ["-t", e]
    for p in policies_dir:
        policy_tool_args += ["-m", p]
    policy_tool_args += ["-o", policy_output_dir, policy]

    if debug is True:
        policy_tool_args.insert(0, "-d")

    shutil.rmtree(policy_output_dir, ignore_errors=True)
    os.makedirs(policy_output_dir)

    with open(os.path.join(output_dir, "policy_tool.log"), "w+") as ptlog:
        subprocess.Popen([policy_tool_cmd]+policy_tool_args, stdout=ptlog, stderr=subprocess.STDOUT, cwd=output_dir).wait()

    if not os.path.isdir(policy_output_dir):
        return False
    
    for policy_yaml in glob.glob(r"{}/policy_*.yml".format(policy_output_dir)):
        shutil.copy(policy_yaml, output_dir)
    
    return True

def buildPolicyKernel(policy, policies_dir, entities_dir, output_dir):
    engine_output_dir = os.path.join(output_dir, "engine")

    num_cores = str(multiprocessing.cpu_count())
    with open(os.path.join(output_dir, "build.log"), "w+") as buildlog:
        subprocess.Popen(["make", "-j"+num_cores, "-f", "Makefile.isp"], stdout=buildlog, stderr=subprocess.STDOUT, cwd=engine_output_dir).wait()

    validator_path = os.path.join(engine_output_dir, "build", "librv32-renode-validator.so")
    if not os.path.isfile(validator_path):
        return False

    shutil.move(validator_path, output_dir)
    shutil.rmtree(engine_output_dir)

    return True


def main():
    parser = argparse.ArgumentParser(description="Build and install ISP kernels with policies")
    parser.add_argument("policy", type=str, help='''
    The name of the policy to compile and install
    ''')
    parser.add_argument("-o", "--output", type=str, default="", help='''
    Directory where the compiled pex kernel is stored
    Default is ISP_PREFIX/kernels or current working directory if ISP_PREFIX is not set
    ''')
    parser.add_argument("-d", "--debug", action="store_true", help='''
    Enable debug logging
    ''')
    parser.add_argument("-s", "--source", type=lambda s: s.split(','), help='''
    List directories to search for policy sources (absolute paths, comma separated).
    The list will implicitly include ISP_PREFIX/sources/policies.
    ''')

    args = parser.parse_args()

    isp_prefix = isp_utils.getIspPrefix()

    engine_dir = os.path.join(isp_prefix, "sources", "policy-engine")
    policy_out_dir = os.path.join(engine_dir, "policy")
    soc_cfg_path = os.path.join(engine_dir, "soc_cfg")

    policies_dir = [os.path.join(isp_prefix, "sources", "policies")]
    if args.source != None:
        policies_dir = [os.path.abspath(s) for s in args.source] + policies_dir

    entities_dir = []
    for p in policies_dir:
        entities_dir = entities_dir + [os.path.join(p, "entities")]

    base_output_dir = os.getcwd()

    if args.output == "":
        kernels_dir = os.path.join(isp_utils.getIspPrefix(), "kernels")
        if os.path.isdir(kernels_dir):
            base_output_dir = kernels_dir
    else:
        base_output_dir = args.output

    output_dir = os.path.abspath(os.path.join(base_output_dir, args.policy))
    if args.debug is True:
        output_dir = output_dir + "-debug"

    shutil.rmtree(output_dir, ignore_errors=True)
    isp_utils.doMkDir(output_dir)

    copyEngineSources(engine_dir, output_dir)

    if copyPolicyYaml(args.policy, policies_dir, entities_dir, output_dir) is False:
        print("Faild to locate or generate appropriate entities file")
        sys.exit(1)

    if runPolicyTool(args.policy, policies_dir, entities_dir, output_dir, args.debug) is False:
        print("Failed to run policy tool")
        sys.exit(1)

    if buildPolicyKernel(args.policy, policies_dir, entities_dir, output_dir) is False:
        print("Failed to build policy kernel")
        sys.exit(1)


if __name__ == "__main__":
    main()
