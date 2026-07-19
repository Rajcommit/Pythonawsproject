## Internet Gateway  -- The ultimate door  tot he internet
## Without this , nothing in the VPC can reach the internet


from network.aws_client import get_client
from network.state import load_state, save_state

def creating_igw(config):
    """creating a aws igw"""
    ec2 = get_client('ec2')
    state = load_state()

    #we need the VPC ID (IGW gets attached to a VPC)
    vpc_id = state['vpc_id']
    igw_name = config['internet_gateway']['name']
    tags = config['tags']

    ##If there is preexsisting IGW then please do skip
    if 'igw_id' in state:
        print(f"IGW already exsists: {state['igw_id']}")
        return state['igw_id']

    ##Since now we have our internetgateway id if not we can create it
    response = ec2.create_internet_gateway()
    igw_id = response['InternetGateway']['InternetGatewayId']
    print(f"Created IGW: {igw_id}")

    ##Attaching Igw to the VPC:
    ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    print(f"Attachment IGW to VPC: {vpc_id}")

    #Tagging the IGW here
    tag_list = [{'Key': 'Name', 'Value': igw_name}]
    for key, value in tags.items():
        tag_list.append({'Key': key, 'Value': value})
    ec2.create_tags(Resources=[igw_id], Tags=tag_list)
    print(f"Tagged  IGW: {igw_name}")

    ##Saving the output to the state file:
    state['igw_id'] = igw_id
    save_state(state)
    print("Saved IGW to State")

    return igw_id
