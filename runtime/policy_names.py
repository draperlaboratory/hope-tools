import itertools

def get_sub_lists(init_list):
    sub_lists = []
    for i in range(len(init_list)):
        combinations = itertools.combinations(init_list, i)
        for c in combinations:
            sub = []
            for name in c:
                sub.append(name)
            sub_lists.append(sub)

    return sub_lists

def get_policy_names(policies):
    policy_lists = get_sub_lists(policies)
    policy_names = []

    for policy_list in policy_lists:
        policy_names.append('-'.join(policy_list))

    return policy_names


policies = ['heap', 'rwx', 'stack', 'threeClass']
policy_names = get_policy_names(policies)

print 'none'
for policy_name in policy_names:
    if policy_name is not '':
        print policy_name
