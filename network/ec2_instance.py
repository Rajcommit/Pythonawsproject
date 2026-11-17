from network.aws_client import get_client
from network.state import load_state, save_state

def create_ec2_instance(config):
    """Launch an EC2 instance if it doesn't already exsist."""
    ec2 = get_client('ec2')
    state = load_state()
    tags = config['tags']
    ec2_config = config['ec2']

    instance_name = ec2_config['name']
    ami_id = ec2_config['ami_id']
    instance_type = ec2_config['instance_type']
    subnet_name = ec2_config['subnet']
    sg_name = ec2_config['security_group']

    # Checking if ec2 already launched or not

    if 'ec2_instance_id' in state:
        print(f"EC2 instance already exsists: {state['ec2_instance_id']}")
        return state['ec2_instance_id']

    # translate names -> IDs from state
    subnet_id = state[subnet_name]
    sg_id = state[f"sg_{sg_name}"]

    # --------------- Launch the instance ---------------
    response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        SubnetId=subnet_id,
        SecurityGroupIds=[sg_id],
        MinCount=1,
        MaxCount=1
    )

    instance_id = response['Instances'][0]['InstanceId']
    print(f"Launched EC2 instance: {instance_id}")


    ## wait until the instance is running

    print("Waiting for instance to reach 'running' state...")
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    print("Instance is now running.")

    # Tag it:
    tag_list = [{'Key': 'Name', 'Value': instance_name}]
    for key, value in tags.items():
        tag_list.append({'Key':key,'Value':value})
    ec2.create_tags(Resources=[instance_id], Tags=tag_list)

    ##Save to state
    state['ec2_instance_id'] = instance_id
    save_state(state)
    print(f"Save EC@ instance to state: {instance_id}")

    return instance_id
