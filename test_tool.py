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

# Client definition
client = boto3.client('ec2', region_name=AWS_REGION)

# Resource definition for a simplicity with instances data
ec2 = boto3.resource('ec2', region_name=AWS_REGION)


# Return price on needed type/platform, else return None
def get_on_demand_price(i_type, platform):
    for i in INSTANCES:
        if i.get('platform') == platform and i.get('i_type') == i_type:
            return i.get('i_price')
    return None


# Get platform type from image attributes
def get_platform_dict(images_ids):
    images = client.describe_images(ImageIds=images_ids)
    return {i['ImageId']: i['PlatformDetails'] for i in images['Images']}


# Get dict of spot prices data with our conditions: platforms, instances types
# and end time
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


# As with price on demand let's get the price from the array if all conditions are met
# If there are no spot instance, return None
def get_spot_price(data, i_type, platform, availability_zone):
    for price in data['SpotPriceHistory']:
        if price['InstanceType'] == i_type and \
                platform in price['ProductDescription'] and \
                price['AvailabilityZone'] == availability_zone:
            return float(price['SpotPrice'])
    return None


# Setup list with needed platforms
# Also add '(Amazon VPC)' postfix, because spot instances may be listed in such way
def platforms():
    platforms_unique = set([i['platform'] for i in INSTANCES])
    platforms = list(platforms_unique)
    platforms.extend([i + ' (Amazon VPC)' for i in platforms])
    return platforms


# So with the instances types
def i_types():
    types_unique = set([i['i_type'] for i in INSTANCES])
    return list(types_unique)


# Main method
def get_instances():
    # let's get spot prices array first
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
    # current working instances with our instance types settings in filter
    instances = ec2.instances.filter(Filters=filters)
    # list of image ids
    image_ids = [i.image_id for i in instances]
    # with image list I get platform description in one request
    platform_dict = get_platform_dict(image_ids)

    # instances loop, setting data for each instance
    for instance in instances:
        # define platform according to image of instance
        instance_platform = platform_dict.get(instance.image_id)
        on_demand_price = get_on_demand_price(instance.instance_type, instance_platform)
        # spot price with required instance type, platform and availability zone
        spot_price = get_spot_price(spot_prices_data,
                                    instance.instance_type,
                                    instance_platform,
                                    instance.placement['AvailabilityZone'])
        # get data only for instances with requied type and platform
        if on_demand_price is not None:

            if spot_price is not None:
                diff_price = on_demand_price - spot_price
            # if spot price is None, let's define it is null
            # if spot price is null, so should diff price, because we gain nothing
            else:
                spot_price = 0
                diff_price = 0

            # instance data
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
