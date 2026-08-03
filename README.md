# instance_prices

CLI tool comparing on-demand vs spot EC2 pricing for running instances across instance families.

## Setup

```bash
python -m venv env && source env/bin/activate
pip install -r requirements.txt
```

Configure AWS credentials:

```bash
export AWS_ACCESS_KEY_ID=<access-key-id>
export AWS_SECRET_ACCESS_KEY=<secret-access-key>
```

## Usage

```bash
python main.py
python main.py --region eu-west-1
python main.py --region us-west-2 --days 14
```

```
InstanceId           InstanceType    AZ            Platform    PriceOD    PriceSpot    PriceDiff
-------------------  --------------  ------------  ----------  ---------  -----------  -----------
i-0a1b2c3d4e5f6789  t3.micro        us-east-2a    Linux/UNIX  0.0104     0.0031       0.0073
```

## Options

| Flag | Default | Description |
|---|---|---|
| `--region` | `us-east-2` | AWS region to query |
| `--days` | `7` | Spot price history window |
