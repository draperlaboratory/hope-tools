import os
import errno
import shutil

def doMkDir(dir):
    try:
        if not os.path.isdir(dir):
            os.makedirs(dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def remove_if_exists(filename):
    if os.path.exists(filename):
        if os.path.isdir(filename):
            shutil.rmtree(filename)
        else:
            os.remove(filename)

def make_entities_file(run_dir, name):
    filename = os.path.join(run_dir, "..", (name + ".entities.yml"))
    if os.path.exists(filename) is False:
        print(filename)
        open(filename, "a").close()

def get_templates_dir():
    isp_prefix = os.environ["ISP_PREFIX"]
    return os.path.join(isp_prefix, "sources",
                                    "policies",
                                    "policy_tests",
                                    "template")

def get_kernels_dir():
    isp_prefix = os.environ["ISP_PREFIX"]
    return os.path.join(isp_prefix, "kernels")

def get_policy_full_name(policy, runtime):
    return "osv." + runtime + ".main." + policy
