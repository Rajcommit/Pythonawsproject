# NAT Gateway - Gives private subnets outbound internet access
# Private subnets route 0.0.0.0/0 → NAT Gateway
# Requires: an Elastic IP + a public subnet to live in

from network.aws_client import get_client
from network.state import load_state, save_state


def create_nat_gateway(config):
    """Allocate an EIP, create a NAT Gateway in the specified public
    subnet, and add a route in the private route table pointing 0.0.0.0/0 → NAT."""
    ec2 = get_client('ec2')
    state = load_state()
    tags = config['tags']
    nat_config = config['nat_gateway']
    nat_name = nat_config['name']
    nat_subnet_name = nat_config['subnet']

    # --------------- Step 1: Allocate Elastic IP ---------------

    if 'nat_eip_alloc_id' not in state:
        response = ec2.allocate_address(Domain='vpc')
        eip_alloc_id = response['AllocationId']
        print(f"Allocated Elastic IP: {eip_alloc_id}")

        state['nat_eip_alloc_id'] = eip_alloc_id
        save_state(state)
    else:
        eip_alloc_id = state['nat_eip_alloc_id']
        print(f"Elastic IP already exists: {eip_alloc_id}")

    # --------------- Step 2: Create NAT Gateway ---------------

    if 'nat_id' not in state:
        subnet_id = state[nat_subnet_name]
        response = ec2.create_nat_gateway(
            SubnetId=subnet_id,
            AllocationId=eip_alloc_id
        )
        nat_id = response['NatGateway']['NatGatewayId']
        print(f"Created NAT Gateway: {nat_id}")

        # Step 3: Wait for NAT to become available
        print("Waiting for NAT Gateway to become available (1-2 min)...")
        waiter = ec2.get_waiter('nat_gateway_available')
        waiter.wait(NatGatewayIds=[nat_id])
        print("NAT Gateway is now available")

        # Step 4: Tag it
        tag_list = [{'Key': 'Name', 'Value': nat_name}]
        for key, value in tags.items():
            tag_list.append({'Key': key, 'Value': value})
        ec2.create_tags(Resources=[nat_id], Tags=tag_list)

        # Save to state
        state['nat_id'] = nat_id
        save_state(state)
        print(f"Saved NAT Gateway to state")

    else:
        nat_id = state['nat_id']
        print(f"NAT Gateway already exists: {nat_id}")

    # --------------- Step 5: Add route in private route table ---------------

    if 'private_nat_route' not in state:
        private_rt_id = state['private_rt_id']
        ec2.create_route(
            RouteTableId=private_rt_id,
            DestinationCidrBlock='0.0.0.0/0',
            NatGatewayId=nat_id
        )
        print(f"Added route: 0.0.0.0/0 → {nat_id} in private route table")

        state['private_nat_route'] = True
        save_state(state)
    else:
        print("Private route to NAT already exists")

    print("NAT Gateway done.")
    return state
