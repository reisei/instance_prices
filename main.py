import argparse
import boto3
from tabulate import tabulate
from datetime import datetime, timedelta

SPOT_HISTORY_DAYS = 7

INSTANCES = [
    {'i_type': 't2.nano',  'platform': 'Linux/UNIX',  'i_price': 0.0058},
    {'i_type': 't2.nano',  'platform': 'Windows',     'i_price': 0.0081},
    {'i_type': 't2.nano',  'platform': 'SUSE Linux',  'i_price': 0.0158},
    {'i_type': 't2.micro', 'platform': 'Linux/UNIX',  'i_price': 0.0116},
    {'i_type': 't2.micro', 'platform': 'Windows',     'i_price': 0.0162},
    {'i_type': 't2.micro', 'platform': 'SUSE Linux',  'i_price': 0.0216},
    {'i_type': 't3.nano',  'platform': 'Linux/UNIX',  'i_price': 0.0052},
    {'i_type': 't3.nano',  'platform': 'Windows',     'i_price': 0.0098},
    {'i_type': 't3.nano',  'platform': 'SUSE Linux',  'i_price': 0.0052},
    {'i_type': 't3.micro', 'platform': 'Linux/UNIX',  'i_price': 0.0104},
    {'i_type': 't3.micro', 'platform': 'Windows',     'i_price': 0.0196},
    {'i_type': 't3.micro', 'platform': 'SUSE Linux',  'i_price': 0.0104},
]


def get_on_demand_price(i_type, platform):
    for i in INSTANCES:
        if i['platform'] == platform and i['i_type'] == i_type:
            return i['i_price']
    return None


def get_platform_dict(client, image_ids):
    if not image_ids:
        return {}
    images = client.describe_images(ImageIds=image_ids)
    return {i['ImageId']: i['PlatformDetails'] for i in images['Images']}


def get_spot_prices_data(client, days):
    r_types = list({i['i_type'] for i in INSTANCES})
    r_platforms = list({i['platform'] for i in INSTANCES})
    r_platforms.extend([p + ' (Amazon VPC)' for p in r_platforms])
    start_time = datetime.now() - timedelta(days=days)
    return client.describe_spot_price_history(
        InstanceTypes=r_types,
        ProductDescriptions=r_platforms,
        StartTime=start_time,
    )


def get_spot_price(data, i_type, platform, availability_zone):
    for price in data['SpotPriceHistory']:
        if (price['InstanceType'] == i_type
                and platform in price['ProductDescription']
                and price['AvailabilityZone'] == availability_zone):
            return float(price['SpotPrice'])
    return None


def get_instances(region, days):
    client = boto3.client('ec2', region_name=region)
    ec2 = boto3.resource('ec2', region_name=region)

    spot_prices_data = get_spot_prices_data(client, days)

    r_types = list({i['i_type'] for i in INSTANCES})
    filters = [
        {'Name': 'instance-type', 'Values': r_types},
        {'Name': 'instance-state-name', 'Values': ['running']},
    ]
    instances = list(ec2.instances.filter(Filters=filters))

    image_ids = [i.image_id for i in instances]
    platform_dict = get_platform_dict(client, image_ids)

    data = []
    for instance in instances:
        instance_platform = platform_dict.get(instance.image_id)
        on_demand_price = get_on_demand_price(instance.instance_type, instance_platform)
        if on_demand_price is None:
            continue

        spot_price = get_spot_price(
            spot_prices_data,
            instance.instance_type,
            instance_platform,
            instance.placement['AvailabilityZone'],
        )
        if spot_price is None:
            spot_price = 0
        diff_price = on_demand_price - spot_price

        data.append([
            instance.instance_id,
            instance.instance_type,
            instance.placement['AvailabilityZone'],
            instance_platform,
            on_demand_price,
            spot_price,
            diff_price,
        ])
    return data


def run():
    parser = argparse.ArgumentParser(
        description='Compare on-demand vs spot EC2 prices for running instances.'
    )
    parser.add_argument('--region', default='us-east-2', help='AWS region (default: us-east-2)')
    parser.add_argument('--days', type=int, default=SPOT_HISTORY_DAYS,
                        help='Spot price history window in days (default: 7)')
    args = parser.parse_args()

    headers = ['InstanceId', 'InstanceType', 'AZ', 'Platform', 'PriceOD', 'PriceSpot', 'PriceDiff']
    data = get_instances(args.region, args.days)
    print(tabulate(data, headers=headers))


if __name__ == '__main__':
    run()
