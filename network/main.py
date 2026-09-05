#main.py -- The command center
#One CLI to. operate all
#Usage:
   #python main.py plan
   #python main.py apply
   #python main.py destroy

import sys
import yaml
import time

from network.planner import generate_plan, display_plan, load_config
from network.vpc import create_vpc
from network.subnets import create_subnet
from network.route_tables import create_route_tables
from network.nat_gateway import create_nat_gateway
from network.state import load_state, save_state
from network.aws_client import get_client
from network.internet_gateway import creating_igw
from network.security_groups import create_security_groups

def command_plan(config):
    """RECON MISSON: show that what exsists snad what is smissing"""
    print("\n Scanning the  battlefiend that is config file")
    plan = generate_plan(config)
    display_plan(plan)
    return plan

def command_apply(config):
    """Deploy: Build everything that is missing, in order"""
    print("\n DEPLOYING - Building Infra........\n")
    plan = generate_plan(config)
    display_plan(plan)

    creates = [p for p in plan if p['action'] == 'CREATE']

    if len(creates) == 0:
        print("\n Nothing to build. Base is fully operational")

        return

    print(f"\n Building {len(creates)} resources(s)....\n")


    ## Execution should be in order
    #Step 1 VPC required as base first
    if any (p['type'] == 'vpc' and p['action'] == 'CREATE' for p in plan):
        print ("━━━ Step 1: Building the base (VPC) ━━━")
        create_vpc(config)

    #Step 2: Subnets
    if any (p['type'] == 'subnet' and p['action'] == 'CREATE' for p in plan):
        print ("━━━ Step 2: Building the rooms (Subnets) ━━━")
        create_subnet(config)

    #Step 3: Internet Gateway
    if any (p['type'] == 'internet_gateway' and p['action'] == 'CREATE' for p in plan):
        print ("━━━ Step 3: Installing the front gate (IGW) ━━━")
        creating_igw(config)

    #Step 4: Route Tables
    if any (p['type'] == 'route_table' and p['action'] == 'CREATE' for p in plan):
        print ("━━━ Step 4: Putting up road signs (Route Tables) ━━━")
        create_route_tables(config)

    #Step 5: NAT Gateway
    if any (p['type'] == 'nat_gateway' and p['action'] == 'CREATE' for p in plan):
        print ("━━━ Step 5: Deploying secure messenger (NAT Gateway) ━━━")
        create_nat_gateway(config)

    #Step 6: Security Groups
    if any(p['type'] == 'security_group' and p['action'] == 'CREATE' for p in plan):
        print("━━━ Step 6: Building the firewall (Security Groups) ━━━")
        create_security_groups(config)

    print("\n DEPLOYMENT COMPLETE. All operational")

def command_destroy(config):
    """RETREAT: Destroy everything in REVERSE order."""
    print("\n RETREAT ORDER - Demolishing infrastructure ...\n")

    ec2 = get_client('ec2')
    state = load_state()

    if not state:
        print("Nothing to destroy. Base is already empty.")
        return

    # ===== Step 1: Delete NAT Gateway =====
    if 'nat_id' in state:
        print("===== Destroying NAT Gateway =====")
        nat_id = state['nat_id']
        try:
            ec2.delete_nat_gateway(NatGatewayId=nat_id)
            print(f"  Waiting for NAT {nat_id} to die...")
        except Exception as e:
            print(f"  NAT already gone or couldn't delete: {e}")
        time.sleep(90)
        del state['nat_id']
        if 'private_nat_route' in state:
            del state['private_nat_route']
        save_state(state)
        print("  NAT Gateway deleted.")

    # ===== Step 2: Release Elastic IP =====
    if 'nat_eip_alloc_id' in state:
        print("===== Releasing Elastic IP =====")
        try:
            ec2.release_address(AllocationId=state['nat_eip_alloc_id'])
        except Exception as e:
            print(f"  EIP already released or couldn't release: {e}")
        del state['nat_eip_alloc_id']
        save_state(state)
        print("  EIP released. Thanks for choosing the service.")

    # ===== Step 3a: Disassociate Route Tables =====
    print("===== Disassociating Route Tables =====")
    for key in list(state.keys()):
        if '_rt_assoc' in key:
            print(f"  Unfollowing: {key}")
            try:
                ec2.disassociate_route_table(AssociationId=state[key])
            except Exception as e:
                print(f"  Already unfollowed: {e}")
            del state[key]
            save_state(state)

    # ===== Step 3b: Delete Route Tables =====
    print("===== Deleting Route Tables =====")
    for rt_key in ['public_rt_id', 'private_rt_id']:
        if rt_key in state:
            rt_id = state[rt_key]
            print(f"  Shredding: {rt_id}")
            try:
                ec2.delete_route_table(RouteTableId=rt_id)
            except Exception as e:
                print(f"  Couldn't shred {rt_id}: {e}")
            del state[rt_key]
            save_state(state)

    # ===== Step 4: Detach + Delete Internet Gateway =====
    if 'igw_id' in state:
        print("===== Detaching + Deleting IGW =====")
        igw_id = state['igw_id']
        vpc_id = state['vpc_id']

        # Block 1: DETACH (break the relationship — needs both IDs)
        try:
            ec2.detach_internet_gateway(
                InternetGatewayId=igw_id,
                VpcId=vpc_id
            )
            print(f"  IGW {igw_id} unhooked from VPC.")
        except Exception as e:
            print(f"  Already detached: {e}")

        # Block 2: DELETE (always runs even if Block 1 failed)
        try:
            ec2.delete_internet_gateway(InternetGatewayId=igw_id)
            print(f"  IGW {igw_id} deleted.")
        except Exception as e:
            print(f"  Couldn't delete IGW: {e}")

        del state['igw_id']
        save_state(state)
        print("  IGW gone. No more front door.")

    #  ====== Step 4.5: Delete Securoty Groups ========
    for key in list(state.keys()):
        if key.startswith('sg_'):
            sg_id  =  state[key]
            print(f" Deleteing Security Group: {sg_id} ({key})")
            try:
                ec2.delete_security_group(GroupId=sg_id)
            except Exception as e:
                print(f" Could't delete SG: {e}")
            del state[key]
            save_state(state)

    # ===== Step 5: Delete Subnets =====
    print("===== Deleting Subnets =====")
    subnet_keys = [
        'public-subnet-az1',
        'public-subnet-az2',
        'private-subnet-az1',
        'private-subnet-az2'
    ]
    for key in subnet_keys:
        if key in state:
            subnet_id = state[key]
            print(f"  Demolishing: {subnet_id} ({key})")
            try:
                ec2.delete_subnet(SubnetId=subnet_id)
            except Exception as e:
                print(f"  Couldn't delete {subnet_id}: {e}")
            del state[key]
            save_state(state)

    # ===== Step 6: Delete VPC — The Grand Finale =====
    if 'vpc_id' in state:
        print("===== Deleting VPC =====")
        vpc_id = state['vpc_id']
        try:
            ec2.delete_vpc(VpcId=vpc_id)
            print(f"  VPC {vpc_id} imploded.")
        except Exception as e:
            print(f"  Couldn't delete VPC: {e}")
        del state['vpc_id']
        if 'vpc_name' in state:
            del state['vpc_name']
        save_state(state)
        print("  VPC gone. The universe is empty again.")

    print("\n DEMOLITION COMPLETE. Nothing remains.")

if __name__ == '__main__':
    config = load_config()

    if len(sys.argv) < 2:
        print("Usage: Python -m network.main [plan|apply|destroy]")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == 'plan':
       command_plan(config)
    elif cmd == 'apply':
       command_apply(config)
    elif cmd == 'destroy':
       command_destroy(config)
    else:
      print(f"Unknown command: '{cmd}'. Use plan, apply , or destroy")
      sys.exit(1)
