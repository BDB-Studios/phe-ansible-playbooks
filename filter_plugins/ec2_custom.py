from ansible import errors


def get_zone_id(zone_data, zone_name):
    # print "{}".format(zone_data.get('HostedZones'))
    for x in zone_data.get('HostedZones'):
        if zone_name in x.get('Name'):
            zid = x.get('Id').split('/')
            return zid[2]
    return None


def validate_ruleset(ports, proto):
    '''
    check for emtpy values
    :param ports: should be list
    :param proto: should be list
    :raise: ansible error on failure
    '''
    if proto is None or len(proto) < 0:
        raise errors.AnsibleFilterError('proto is empty or missing')
    if ports is None or len(ports) < 0:
        raise errors.AnsibleFilterError('ports is empty or missing')


def rules_from_dict(rules, src_list=None):
    '''
    rules:
      - ports: '22'
          proto: tcp
          src: (optional)

     ec2_group:
       rules: "{{ rules | rules_from_dict() }}"

    :param rules: list of rule
    :param src_list: src group/cidr list
    :return: list of rules
    '''

    if isinstance(rules, list):
        rule_list = []
        if len(rules) > 0:
            for rule in rules:
                if 'src' in rule.keys():
                    src_list = rule.get('src')
                if isinstance(src_list, list) and len(src_list) > 0:
                    rule_list += make_rules(src_list, rule['ports'], rule['proto'], ('sg' in src_list[0]))
                else:
                    raise errors.AnsibleFilterError('src host or security group list empty or not a list')
            return rule_list
        else:
            raise errors.AnsibleFilterError('Rules list is empty')
    else:
        raise errors.AnsibleFilterError('Rules data must be a list')


def make_rules(hosts, ports, proto, group=False):
    '''
    inspiration: https://gist.github.com/viesti/1febe79938c09cc29501

    :param hosts: list
    :param ports: comma separated string
    :param proto: string
    :param group: bool default false
    :return: rules as list of dicts
    '''
    if isinstance(hosts, list) and len(hosts) > 0:
        validate_ruleset(ports, proto)
        if group:
            return [{'proto': proto,
                     'from_port': port,
                     'to_port': port,
                     'group_id': sg} for sg in hosts for port in map(int, ports.split(','))]
        return [{'proto': proto,
                 'from_port': port,
                 'to_port': port,
                 'cidr_ip': host} for host in hosts for port in map(int, ports.split(','))]
    else:
        raise errors.AnsibleFilterError('list of hosts or security groups must be a list')


def get_sg_result(result_list):
    if isinstance(result_list, list) and len(result_list) > 0:
        for result in result_list:
            if result.get('group_id'):
                return result
    else:
        raise errors.AnsibleFilterError('results list is empty or not a list')


def get_sg_id_result(result_list):
    if isinstance(result_list, list) and len(result_list) > 0:
        for result in result_list:
            if result.get('group_id'):
                return result.get('group_id')
    else:
        raise errors.AnsibleFilterError('results list is empty or not a list')


def get_launch_configs(launch_configs, stack_name):
    import json
    configs = []
    launch_configs = json.loads(launch_configs)

    if 'LaunchConfigurations' in launch_configs:
        for launch_config in launch_configs['LaunchConfigurations']:
            if stack_name in launch_config['LaunchConfigurationName']:
                configs.append(launch_config['LaunchConfigurationName'])

    return configs

def get_attached_ips(record_sets, filter):
    attached_ips = []

    if 'ResourceRecordSets' in record_sets:
        for record_set in record_sets['ResourceRecordSets']:
            if "A" == record_set['Type']:
                if 'Name' in record_set and filter in record_set['Name']:
                    if 'ResourceRecords' in record_set:
                        for resource in record_set['ResourceRecords']:
                            attached_ips.append(resource["Value"])

    return attached_ips

def get_rds_subnet_groups(subnet_groups, stack_name):
    import json
    subnet_groups_names = []
    subnet_groups = json.loads(subnet_groups)

    if 'DBSubnetGroups' in subnet_groups:
        for subnet_group in subnet_groups['DBSubnetGroups']:
            if stack_name in subnet_group['DBSubnetGroupName']:
                subnet_groups_names.append(subnet_group['DBSubnetGroupName'])

    return subnet_groups_names

def get_ecc_subnet_groups(subnet_groups, stack_name):
    import json
    subnet_groups_names = []
    subnet_groups = json.loads(subnet_groups)

    if 'CacheSubnetGroups' in subnet_groups:
        for subnet_group in subnet_groups['CacheSubnetGroups']:
            if stack_name in subnet_group['CacheSubnetGroupName']:
                subnet_groups_names.append(subnet_group['CacheSubnetGroupName'])

    return subnet_groups_names

def get_network_acls(acl_list, vpc_id):
    import json
    network_acl_ids = []
    acl_list = json.loads(acl_list)

    if 'NetworkAcls' in acl_list:
        for acl in acl_list['NetworkAcls']:
            if vpc_id == acl['VpcId'] and not acl['IsDefault']:
                network_acl_ids.append(acl['NetworkAclId'])

    return network_acl_ids

def get_eip_data(nat_list, vpc_id):
    import json
    eip_data = []
    nat_list = json.loads(nat_list)

    if 'NatGateways' in nat_list:
        for gw in nat_list['NatGateways']:
            if vpc_id == gw['VpcId']:
                for gwa in gw['NatGatewayAddresses']:
                    eip_data.append(gwa['AllocationId'])
    return eip_data

def get_vpc_sgs(sg_list, vpc_id):
    import json
    vpc_sgs = []
    sg_list = json.loads(sg_list)

    if 'SecurityGroups' in sg_list:
        for sg in sg_list['SecurityGroups']:
            if vpc_id == sg['VpcId'] and 'Tags' in sg:
                vpc_sgs.append(sg)

    return vpc_sgs

def get_vpc_elbs(elb_list, vpc_id):
    import json
    vpc_elbs = []
    elb_list = json.loads(elb_list)

    if 'LoadBalancerDescriptions' in elb_list:
        for elb in elb_list['LoadBalancerDescriptions']:
            if vpc_id == elb['VPCId']:
                vpc_elbs.append(elb['LoadBalancerName'])

    return vpc_elbs

def get_vpc_dhcp_option_sets(dhcp_options, target):
    import json
    option_sets = []
    dhcp_options = json.loads(dhcp_options)

    if 'DhcpOptions' in dhcp_options:
        for option in dhcp_options['DhcpOptions']:
            if 'Tags' in option:
                for tag in option['Tags']:
                    if target in tag['Value']:
                        option_sets.append(option['DhcpOptionsId'])

    return option_sets

def get_internet_gateways(gateways, vpc_id):
    import json
    internet_gateways = []
    gateways = json.loads(gateways)

    if 'InternetGateways' in gateways:
        for gateway in gateways['InternetGateways']:
            if 'Attachments' in gateway:
                for attachment in gateway['Attachments']:
                    if vpc_id == attachment['VpcId']:
                        internet_gateways.append(gateway['InternetGatewayId'])

    return internet_gateways

def get_network_interface_assoc(network_assocs, vpc_id):
    import json
    association_ids = []
    network_assocs = json.loads(network_assocs)

    if 'NetworkInterfaces' in network_assocs:
        for network_assoc in network_assocs['NetworkInterfaces']:
            if vpc_id == network_assoc['VpcId']:
                if 'Association' in network_assoc:
                    if 'AssociationId' in network_assoc['Association']:
                        association_ids.append(network_assoc['Association']['AssociationId'])

    return association_ids

def unique_instance_stacks(instance_list, target):
    stack_names = []

    if 'instances' in instance_list:
        for instance in instance_list['instances']:
            if 'tags' in instance:
                if 'Stack' in instance['tags']:
                    if target != instance['tags']['Stack']:
                        stack_names.append(instance['tags']['Stack'])

    return list(set(stack_names))

def split_part(string, index, separator='-'):
    return string.split(separator)[index]


class FilterModule(object):
    def filters(self):
        filter_list = {
            'make_rules': make_rules,
            'rules_from_dict': rules_from_dict,
            'get_sg_result': get_sg_result,
            'get_sg_id_result': get_sg_id_result,
            'get_zone_id': get_zone_id,
            'get_launch_configs': get_launch_configs,
            'get_attached_ips': get_attached_ips,
            'get_rds_subnet_groups': get_rds_subnet_groups,
            'get_ecc_subnet_groups': get_ecc_subnet_groups,
            'get_network_acls': get_network_acls,
            'get_eip_data': get_eip_data,
            'get_vpc_sgs': get_vpc_sgs,
            'get_vpc_elbs': get_vpc_elbs,
            'get_vpc_dhcp_option_sets': get_vpc_dhcp_option_sets,
            'get_internet_gateways': get_internet_gateways,
            'get_network_interface_assoc': get_network_interface_assoc,
            'unique_instance_stacks': unique_instance_stacks,
            'split_part': split_part
        }
        return filter_list
