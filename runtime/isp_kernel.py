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
import isp_utils

# -- MAIN MODULE FUNCTIONALITY
# arguments:
#   policy: the name of the policy to compile
#   policies_dir: root directory of policy definition. Example:
#     Directory structure: /{x}/policies/osv/hifive/main.dpl
#     policy name: osv.hifive.main
#     policies_dir argument: /{x}/policies
#   entities_dir: The location of the entities files for policies
#   engine_dir: The policy engine repo path
#   policy_out_dir: where should the compiled pex kernel be stored?
#   debug: run policy tool with debug output

def build_policy_kernel(policy, policies_dir, entities_dir,
                        engine_dir, policy_out_dir, debug):
    policy_tool_cmd = "policy-tool"
    policy_tool_args = ["-t", entities_dir, "-m", policies_dir, "-o", policy_out_dir] + [policy]

    if debug is True:
        policy_tool_args.insert(0, "-d")

    shutil.rmtree(policy_out_dir, ignore_errors=True)
    os.makedirs(policy_out_dir)

    # faster if we trust cmake & don't clean, but that can leave you with stale .so file
    fnull = open(os.devnull, 'w')
    policy_engine_build_dir = os.path.join(engine_dir, "build")
    subprocess.Popen(["make", "clean"], stdout=fnull, stderr=subprocess.STDOUT, cwd=policy_engine_build_dir).wait()

    with open(os.path.join(policy_out_dir, "policy_tool.log"), "w+") as ptlog:
        subprocess.Popen([policy_tool_cmd]+policy_tool_args, stdout=ptlog, stderr=subprocess.STDOUT, cwd=policy_out_dir).wait()

    num_cores = str(multiprocessing.cpu_count())
    with open(os.path.join(policy_out_dir, "build.log"), "w+") as buildlog:
        subprocess.Popen(["make", "-j"+num_cores], stdout=buildlog, stderr=subprocess.STDOUT, cwd=policy_engine_build_dir).wait()


def install_policy(policy, out_dir, policies_dir, entities_dir, validator_path, soc_cfg_path):
    shutil.rmtree(out_dir, ignore_errors=True)
    isp_utils.doMkDir(out_dir)

    shutil.copy(validator_path, out_dir)

    shutil.copytree(soc_cfg_path, os.path.join(out_dir, "soc_cfg"))

    f_names = os.listdir(policies_dir)
    for fn in f_names:
        if "yml" in fn or "log" in fn:
            shutil.copy(os.path.join(policies_dir, fn), out_dir)

    entFile = os.path.join(entities_dir, policy + ".entities.yml")
    destEnt = os.path.join(out_dir, policy + ".entities.yml")

    # special handling for composite policies
    # TODO: better way to determine composite policy?
    policy_parts = policy.split(".")[-1].split("-")
    policy_prefix = policy.rsplit(".", 1)[0] + "."

    if os.path.isfile(entFile):
        shutil.copy(entFile, out_dir)

    # build composite entities for composite policy w.o existing entities
    elif (len(policy_parts) != 1):
        shutil.copyfile(os.path.join(entities_dir, "empty.entities.yml"), destEnt)
        with open(destEnt, 'wb') as comp_ents:
            for p in policy_parts:
                polEntFile = policy_prefix + p + ".entities.yml"
                if os.path.isfile(os.path.join(entities_dir, polEntFile)):
                    with open(os.path.join(entities_dir, polEntFile), 'rb') as fd:
                        shutil.copyfileobj(fd, comp_ents);
    else:
        shutil.copyfile(os.path.join(entities_dir, "empty.entities.yml"), destEnt)


def main():
    parser = argparse.ArgumentParser(description="Build and install ISP kernels with policies")
    parser.add_argument("policy", type=str, help='''
    The name of the policy to compile and install
    ''')
    parser.add_argument("output_dir", type=str, help='''
    Directory where the compiled pex kernel is stored
    ''')
    parser.add_argument("-d", "--debug", action="store_true", help='''
    Enable debug logging
    ''')

    args = parser.parse_args()

    isp_prefix = os.environ["ISP_PREFIX"]
    policies_dir = os.path.join(isp_prefix, "sources", "policies")

    engine_dir = os.path.join(isp_prefix, "sources", "policy-engine")
    policy_out_dir = os.path.join(engine_dir, "policy")
    validator = "librv32-renode-validator.so"
    validator_path = os.path.join(engine_dir, "build", validator)
    soc_cfg_path = os.path.join(engine_dir, "soc_cfg")

    entities_dir = os.path.join(policies_dir, "entities")

    output_dir = os.path.join(args.output_dir, args.policy)

    build_policy_kernel(args.policy,
                        policies_dir,
                        entities_dir,
                        engine_dir,
                        policy_out_dir,
                        args.debug)

    install_policy(args.policy,
                   output_dir,
                   policy_out_dir,
                   entities_dir,
                   validator_path,
                   soc_cfg_path)


if __name__ == "__main__":
    main()
