from network.aws_client import get_client
from network.state import load_state, save_state


def create_route_tables(config):
    ec2 = get_client('ec2')
    state = load_state()
    vpc_id = state['vpc_id']
    igw_id = state['igw_id']
    tags = config['tags']

    #-----------  PUBLIC ROUTE TABLE ---------------
    if 'public_rt_id' not in state:

        # Step1: Create the route table
        response = ec2.create_route_table(VpcId=vpc_id)
        public_rt_id = response['RouteTable']['RouteTableId']
        print(f"Created public route table: {public_rt_id}")


        #. Step 2: Add route --> all internet traffic goes to IGW
        ec2.create_route(
            RouteTableId=public_rt_id,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=igw_id
        )
        print(f"Added route: '0.0.0.0/0' {public_rt_id}")


        #Step 3: Tag it
        tag_list = [{'Key': 'Name', 'Value': 'public-rt'}]
        for key, value in tags.items():
            tag_list.append({'Key': key, 'Value': value})
        ec2.create_tags(Resources=[public_rt_id], Tags=tag_list)

        #Step 4: Saving it to state
        state['public_rt_id'] = public_rt_id
        save_state(state)
        print(f"Public route table already exists: {public_rt_id}")

    else:
       public_rt_id = state['public_rt_id']
       print(f"Public route table already exsists: {public_rt_id}")
       '''If already created skip the creation and load from state file'''


    # -------- ASSOCIATE PUBLIC SUBNETS --------

    for subnet in config['subnets']['public']:
        assoc_key = f"{subnet['name']}_rt_assoc"

        if assoc_key in state:
            print(f" Already associated: {subnet['name']}")
            continue
        subnet_id = state[subnet['name']]
        response = ec2.associate_route_table(
            RouteTableId=public_rt_id,
            SubnetId=subnet_id
        )

        #Step 5: Saving it to state
        assoc_id = response['AssociationId']
        state[assoc_key] = assoc_id
        save_state(state)


      # -------- PRIVATE ROUTE TABLE --------
    if 'private_rt_id' not in state:

          # Step 1: Create the route table
          response = ec2.create_route_table(VpcId=vpc_id)
          private_rt_id = response['RouteTable']['RouteTableId']
          print(f"Created private route table: {private_rt_id}")

          # Step 2: Tag it
          tag_list = [{'Key': 'Name', 'Value': 'private-rt'}]
          for key, value in tags.items():
              tag_list.append({'Key': key, 'Value': value})
          ec2.create_tags(Resources=[private_rt_id], Tags=tag_list)

          # Step 3: Save to state (NO route added yet — NAT comes later)
          state['private_rt_id'] = private_rt_id
          save_state(state)
          print("Saved private route table to state")

    else:
          private_rt_id = state['private_rt_id']
          print(f"Private route table already exists: {private_rt_id}")

      # -------- ASSOCIATE PRIVATE SUBNETS --------
    for subnet in config['subnets']['private']:
          assoc_key = f"{subnet['name']}_rt_assoc"

          if assoc_key in state:
              print(f"  Already associated: {subnet['name']}")
              continue

          subnet_id = state[subnet['name']]
          response = ec2.associate_route_table(
              RouteTableId=private_rt_id,
              SubnetId=subnet_id
          )
          assoc_id = response['AssociationId']
          state[assoc_key] = assoc_id
          save_state(state)
          print(f"  Associated {subnet['name']} → private route table")

    print("Route tables done.")
    return state
