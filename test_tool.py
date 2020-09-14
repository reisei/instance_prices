import boto3
from tabulate import tabulate

# Some hardcode variables
#
# Ohio AWS region
AWS_REGION = 'us-east-1'
# Number of days to look on spot instances prices
SPOT_HISTORY_DAYS = 7
# Instances hardcoded price
INSTANCES = [
             {'i_type': 't2.nano', 'platform': 'Linux', 'i_price': 0.0058},
             {'i_type': 't2.nano', 'platform': 'Windows', 'i_price': 0.0081},
             {'i_type': 't2.nano', 'platform': 'SUSE', 'i_price': 0.0158},
             {'i_type': 't2.micro', 'platform': 'Linux', 'i_price': 0.0116},
             {'i_type': 't2.micro', 'platform': 'Windows', 'i_price': 0.0162},
             {'i_type': 't2.micro', 'platform': 'SUSE', 'i_price': 0.0216},
             {'i_type': 't3.nano', 'platform': 'Linux', 'i_price': 0.0052},
             {'i_type': 't3.nano', 'platform': 'Windows', 'i_price': 0.0098},
             {'i_type': 't3.nano', 'platform': 'SUSE', 'i_price': 0.0052},
             {'i_type': 't3.micro', 'platform': 'Linux', 'i_price': 0.0104},
             {'i_type': 't3.micro', 'platform': 'Windows', 'i_price': 0.0196},
             {'i_type': 't3.micro', 'platform': 'SUSE', 'i_price': 0.0104},
        ]

# client definition
ec2 = boto3.resource('ec2', region_name=AWS_REGION)


# return price on needed type/platform, else return None
def get_on_demand_price(i_type, platform):
    for i in INSTANCES:
        if i.get('i_type') == i_type and i.get('platform') == platform:
            return i.get('i_price')
        else:
            return None


def get_spot_price():
    pass


def platforms():
    platforms_unique = set([i['platform'] for i in INSTANCES])
    return list(platforms_unique)


def i_types():
    types_unique = set([i['i_type'] for i in INSTANCES])
    return list(types_unique)


def get_instances():
    data = []
    r_platforms = platforms()
    r_types = i_types()
    filters = [
            {
                'Name': 'platform',
                'Values': r_platforms,
            },
            {
                'Name': 'instance-type',
                'Values': r_types,
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
            ]
    instances = ec2.instances.filter(Filters=filters)
    for instance in instances:
        on_demand_price = get_on_demand_price(instance.instance-type, instance.platform)
        spot_price = get_spot_price()

        price_diff = on_demand_price - spot_price
        i_data = [instance.id, instance.instance-type, instance.platform, on_demand_price, spot_price, price_diff]
        data.append(i_data)
    return data


def run():
    headers = [
                'Name',
                'InstanceType',
                'AZ',
                'PlatformDet',
                'PriceOD',
                'PriceSpot',
                'PriceDiff'
            ]
    data = get_instances()
    return tabulate(data, headers=headers)


if __name__ == '__main__':
    run()
