import boto3
from tabulate import tabulate
from datetime import datetime, timedelta

# Some hardcode variables
#
# Ohio AWS region
AWS_REGION = 'us-east-2'
# Number of days to look on spot instances prices
SPOT_HISTORY_DAYS = 7
# Instances hardcoded price
INSTANCES = [
             {'i_type': 't2.nano', 'platform': 'Linux/UNIX', 'i_price': 0.0058},
             {'i_type': 't2.nano', 'platform': 'Windows', 'i_price': 0.0081},
             {'i_type': 't2.nano', 'platform': 'SUSE Linux', 'i_price': 0.0158},
             {'i_type': 't2.micro', 'platform': 'Linux/UNIX', 'i_price': 0.0116},
             {'i_type': 't2.micro', 'platform': 'Windows', 'i_price': 0.0162},
             {'i_type': 't2.micro', 'platform': 'SUSE Linux', 'i_price': 0.0216},
             {'i_type': 't3.nano', 'platform': 'Linux/UNIX', 'i_price': 0.0052},
             {'i_type': 't3.nano', 'platform': 'Windows', 'i_price': 0.0098},
             {'i_type': 't3.nano', 'platform': 'SUSE Linux', 'i_price': 0.0052},
             {'i_type': 't3.micro', 'platform': 'Linux/UNIX', 'i_price': 0.0104},
             {'i_type': 't3.micro', 'platform': 'Windows', 'i_price': 0.0196},
             {'i_type': 't3.micro', 'platform': 'SUSE Linux', 'i_price': 0.0104},
        ]

# client definition
client = boto3.client('ec2', region_name=AWS_REGION)

# resource definition
ec2 = boto3.resource('ec2', region_name=AWS_REGION)


# return price on needed type/platform, else return None
def get_on_demand_price(i_type, platform):
    for i in INSTANCES:
        if i.get('platform') == platform and i.get('i_type') == i_type:
            return i.get('i_price')
    return None


def get_platform_dict(images_ids):
    images = client.describe_images(ImageIds=images_ids)
    return {i['ImageId']: i['PlatformDetails'] for i in images['Images']}


def get_spot_prices_data():
    r_types = i_types()
    r_platforms = platforms()
    start_time = datetime.now()
    end_time = start_time - timedelta(days=SPOT_HISTORY_DAYS)
    request = client.describe_spot_price_history(
            InstanceTypes=r_types,
            ProductDescriptions=r_platforms,
            EndTime=end_time
            )
    return request


def get_spot_price(data, i_type, platform, availability_zone):
    for price in data['SpotPriceHistory']:
        if price['InstanceType'] == i_type and \
                platform in price['ProductDescription'] and \
                price['AvailabilityZone'] == availability_zone:
            return float(price['SpotPrice'])
    return 0


def platforms():
    platforms_unique = set([i['platform'] for i in INSTANCES])
    platforms = list(platforms_unique)
    platforms.extend([i + ' (Amazon VPC)' for i in platforms])
    return platforms


def i_types():
    types_unique = set([i['i_type'] for i in INSTANCES])
    return list(types_unique)


def get_instances():
    spot_prices_data = get_spot_prices_data()
    data = []
    r_types = i_types()
    filters = [
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
    image_ids = [i.image_id for i in instances]
    platform_dict = get_platform_dict(image_ids)
    for instance in instances:
        instance_platform = platform_dict.get(instance.image_id)
        on_demand_price = get_on_demand_price(instance.instance_type, instance_platform)
        spot_price = get_spot_price(spot_prices_data,
                                    instance.instance_type,
                                    instance_platform,
                                    instance.placement['AvailabilityZone'])
        if spot_price is not 0:
            diff_price = on_demand_price - spot_price
        else:
            diff_price = 0
        if on_demand_price is not None:
            i_data = [
                    instance.instance_id,
                    instance.instance_type,
                    instance.placement['AvailabilityZone'],
                    instance_platform,
                    on_demand_price,
                    spot_price,
                    diff_price
                    ]
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
    print(tabulate(data, headers=headers))


if __name__ == '__main__':
    run()
