import itertools


class VlanMatchType:
    PERFECT_MATCH = 'PERFECT_MATCH'
    PARTIAL_MATCH = 'PARTIAL_MATCH'
    MISMATCH = 'MISMATCH'
    UNEXPECTED = 'UNEXPECTED'
    ERROR = 'ERROR'


class ProblematicIfcVersion:
    MLX = '5.4-1.0.3'


def to_ranges(iterable):
    iterable = sorted(set(iterable))
    for key, group in itertools.groupby(enumerate(iterable),
                                        lambda t: t[1] - t[0]):
        group = list(group)
        yield group[0][1], group[-1][1]


def lst_vlan_to_range(lst):
    ranges = list(to_ranges(lst))
    for i, vlan_range in enumerate(ranges):
        if vlan_range[0] == vlan_range[1]:
            ranges[i] = f'{vlan_range[0]}'
        else:
            ranges[i] = f'{vlan_range[0]}-{vlan_range[1]}'
    return ranges


def range_to_lst(vlan_ranges):
    res = []
    s_vlan_ranges = [vlan_range.strip() for vlan_range in vlan_ranges.split(',') if vlan_range.strip()]
    ss_vlan_ranges = [vlan_range.split('-') for vlan_range in s_vlan_ranges]
    for i, vlan_range in enumerate(ss_vlan_ranges):
        ss_vlan_ranges[i] = (vlan_range[0], vlan_range[1]) if len(vlan_range) > 1 else (vlan_range[0], vlan_range[0])
    for vlan_range in ss_vlan_ranges:
        res += list(range(int(vlan_range[0]), int(vlan_range[1]) + 1))
    return res


def vlan_match_type(expected_vlan_range, vlan_range):
    expected_vlan_range_lst = range_to_lst(expected_vlan_range)
    vlan_range_lst = range_to_lst(vlan_range)

    intersection_lst = set(expected_vlan_range_lst).intersection(set(vlan_range_lst))
    if set(expected_vlan_range_lst) == set(vlan_range_lst):
        return VlanMatchType.PERFECT_MATCH
    elif intersection_lst:
        return VlanMatchType.PARTIAL_MATCH
    else:
        return VlanMatchType.MISMATCH


def vlan_match(expected_vlan_range, vlan_range):
    mismatch_vlans_lst = []
    expected_vlan_range_match = {_range: {'range_lst': range_to_lst(_range), 'match': []} for _range in
                                 expected_vlan_range.split(',')}

    vlan_range_lst = range_to_lst(vlan_range)
    for vlan in vlan_range_lst:
        added = False
        for range_data in expected_vlan_range_match.values():
            if vlan in range_data['range_lst']:
                range_data['match'].append(vlan)
                added = True
                break
        if not added:
            mismatch_vlans_lst.append(vlan)

    for _range, range_data in expected_vlan_range_match.items():
        range_data['matchVlans'] = ','.join(lst_vlan_to_range(range_data['match']))
        range_data['result'] = vlan_match_type(expected_vlan_range=_range,
                                               vlan_range=range_data['matchVlans'])
        del range_data['match']
        del range_data['range_lst']

    if mismatch_vlans_lst:
        expected_vlan_range_match['-1'] = {'match': ','.join(lst_vlan_to_range(mismatch_vlans_lst)),
                                           'result': VlanMatchType.UNEXPECTED}

    return expected_vlan_range_match
