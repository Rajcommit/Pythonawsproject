####Creating subnet in the crated VPC####
## What subnet.py must do:
#1> Reading the VPC ID from state.json - subnet live INSIDE a VPC, so we need the
#2> Looping through all four subnet from the YML (2 Private +2 public)
# 3> First check if subnets are there if not create
#4> We will be handling the public flag as if public subnet need mappubliconlaunch = true.


from network.aws_client import get_client
from network.state  import load_state, save_state

# def _create_one_subnet(ec2, state,vpc_id, subnet_config, tags, is_public):
#     """Create a single subnet if it doesnot exsists"""
#     name = subnet_config['name']

#     ##If VPC was already prenet
#     if name in state:
#         print(f"Subnet already exsists: {name}")
#         return

#     #create it
#     response = ec2.create_subnet(
#       VpcId = vpc_id,
#       CidrBlock=subnet_config['cidr'],
#       AvailabilityZone=subnet_config['az']
#   )
#     subnet_id = response['Subnet']['SubnetId']
#     print(f" Created subnet: {name} -> {subnet_id}")

#   ##Public subnets: auto-assign Public IP
#     if is_public:
#         ec2.modify_subnet_attribute(
#               SubnetId=subnet_id,
#               MapPublicIpOnLaunch={'Value':True}
#         )
#    # Tag it
#     tag_list = [{'Key': 'Name', 'Value': name}]
#     for key, value in tags.items():
#         tag_list.append({'Key': key, 'Value': value})
#     ec2.create_tags(Resources=[subnet_id], Tags=tag_list)

#     # Save to state
#     state[name] = subnet_id
#     save_state(state)
#     print(f"Saved {name}")


# def create_subnet(config):
#     """Creating all subnet public and private inside the VPC"""
#     ec2 = get_client('ec2')
#     state = load_state()

#     try:
#       ec2.describe_vpcs(VpcIds=[state['vpc_id']])
#       print("Confirmed: VPC exsists on AWS")

#     except ec2.exceptions.ClientError:
#       print("VPC was deleted externally! Please chcek cloud trail")
#       del state['vpc_id']
#       save_state(state)

#     #. ------ DEPENDENCY CHECK ------
#     # All know the subnet cannot exist without a VPC.
#     if 'vpc_id' not in state:
#         raise RuntimeError("VPC Not found in the estate run vpc.py first")

#     vpc_id = state['vpc_id']
#     tags = config['tags']

# ## ------- PBLIC SUBNET ------
#     for subnet_config in config['subnets']['public']:
#         _create_one_subnet(ec2, state, vpc_id, subnet_config, tags, is_public=True)

# ## ------- PRIVATE SUBNET ------
#     for subnet_config in config['subnets']['private']:
#         _create_one_subnet(ec2, state, vpc_id, subnet_config, tags, is_public=False)

#     return state




def create_subnet(config):
    ec2 = get_client('ec2')
    state = load_state()

    # We need the VPC_ID (subnets live inside VPC)
    vpc_id = state['vpc_id']
    tags = config['tags']

    #Loop through All subnets (public + private comined)

    all_subnets = config['subnets']['public'] + config['subnets']['private']
    print(f"{all_subnets}")

    for subnet in all_subnets:
        name = subnet['name']

        #If in case Already created? Skip.
        if name in state:
            print (f"Subnet already Exsists by name: {name}")
            continue

        # Create it on AWS
        response = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=subnet['cidr'],
            AvailabilityZone=subnet['az']
        )
        print(f"{response}")
        subnet_id = response['Subnet']['SubnetId']
        print(f"Created: {name} --> {subnet_id}")
     # Tag it
        tag_list = [{'Key': 'Name', 'Value': name}]
        for key, value in tags.items():
            tag_list.append({'Key': key, 'Value': value})
        ec2.create_tags(Resources=[subnet_id], Tags=tag_list)


        # Save to state
        state[name] = subnet_id
        save_state(state)
        print(f"Saved {name}")
    # Now enable public IP on public subnets only
    for subnet in config['subnets']['public']:
        subnet_id = state[subnet['name']]
        ec2.modify_subnet_attribute(
            SubnetId=subnet_id,
            MapPublicIpOnLaunch={'Value': True}
        )

    print("All subnets done.")
    return state
