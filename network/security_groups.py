  # security_groups.py - Create Security Groups + Ingress/Egress Rules
  # A security group is a virtual firewall for your EC2 instances.
  # Ingress = what traffic can come IN
  # Egress = what traffic can go OUT
  # Lives inside the VPC — requires vpc_id from state

from network.aws_client import get_client
from network.state import load_state, save_state


def create_security_groups(config):
    """Create all security groups defined in network.yaml. """
    """Fucking prerequisits_I love it. """
    ec2 =  get_client('ec2')
    state = load_state()
    tags = config['tags']
    vpc_id = state['vpc_id']

    for sg_config in config['security_groups']:
        sg_name = sg_config['name']
        state_key = f"sg_{sg_name}"

        # ------------------  Already exsists? Skip -----------------
        if state_key in state:
            print(f"Security Group already exists: {state[state_key]} ({sg_name})")
            continue

        # Creating the Empty Security Group
        response = ec2.create_security_group(
            GroupName=sg_name,
            Description=sg_config['description'],
            VpcId=vpc_id
        )
        sg_id =  response['GroupId']
        print(f"Created Security Group: {sg_id} ({sg_name})")

        ## ------ Stage 3: Add Ingress Rules ----------------------------
        ingress_permissions = []
        for rule in sg_config['ingress']:
            permission = {
                'IpProtocol': rule['protocol'],
                'FromPort': rule['port'],
                'ToPort': rule['port'],
                'IpRanges': [{
                    'CidrIp': rule['cidr'],
                    'Description': rule.get('description', '')
                }]
            }
            ingress_permissions.append(permission)
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=ingress_permissions
        )
        print(f"  Added {len(ingress_permissions)} ingress rules")

        # --------------- Stage 4: Handle Egress Rules ---------------
        # Step A: Revoke the default "allow all outbound" rule AWS added
        try:
            ec2.revoke_security_group_egress(
                GroupId=sg_id,
                IpPermissions=[{
                    'IpProtocol': '-1',
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }]
            )
            print("  Revoked default egress (allow-all) rule")
        except Exception as e:
            print(f"  Default egress already removed: {e}")

        # Step B: Add user-defined egress rules from YAML
        egress_permission = []
        for rule in sg_config['egress']:
            permission = {
                'IpProtocol': rule['protocol'],
                'FromPort': rule['port'],
                'ToPort':  rule['port'],
                'IpRanges': [{'CidrIp': rule['cidr'], 'Description': rule.get('description','')}]
            }
            egress_permission.append(permission)

        ec2.authorize_security_group_egress(
            GroupId=sg_id,
            IpPermissions=egress_permission
        )

        # --------------- Stage 5: Tag + Save to State ---------------
        ec2.create_tags(
            Resources=[sg_id],
            Tags=[
                {'Key': 'Name', 'Value': sg_name},
                *[{'Key': k, 'Value': v} for k, v in tags.items()]
            ]
        )

        state[state_key] = sg_id
        save_state(state)
        print(f"  Tagged + saved: {state_key} = {sg_id}")

    print("Security Groups done.")
    return state

###To chcek if file is syntax proof ###

##cd /home/raj/python/pythonawsproject && python3 -c "import ast; ast.parse(open('network/security_groups.py').read()); print('✅ No syntax errors — security_groups.py is clean')"
