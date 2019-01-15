def get_sub_lists(init_list):
    sub_lists = [[]]
    for i in range(len(init_list)):
        j = i+1
        while j <= len(init_list):
            sub = init_list[i:j]
            sub_lists.append(sub)
            j += 1

    return sub_lists


def get_policy_names(policies):
    policy_lists = get_sub_lists(policies)
    policy_names = []

    for policy_list in policy_lists:
        policy_names.append('-'.join(policy_list))

    return policy_names


policies = ['heap', 'rwx', 'stack', 'threeClass']
policy_names = get_policy_names(policies)

for policy_name in policy_names:
    if policy_name is not '':
        print policy_name
