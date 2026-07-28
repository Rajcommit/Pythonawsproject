#main.py -- The command center
#One CLI to. operate all
#Usage:
   #python main.py plan
   #python main.py apply
   #python main.py destroy

import sys
import yaml

from network.planner import generate_plan, display_plan, load_config
from network.vpc import create_vpc
from network.subnets import create_subnet
from network.route_tables import create_route_tables
from network.nat_gateway import create_nat_gateway
from network.state import load_state, save_state
from network.aws_client import get_client
from network.internet_gateway import creating_igw

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


    print("\n DEPLOYMENT COMPLETE. All operational")

def command_destroy(config):
    """RETREAT: Destroy everything in REVERSE order."""
    print("/n RETREAT ORDER - Demolishing infrastucture ...\n")

    ec2 = get_client('ec2')
    state = load_state()

    if not state:
        print("Nothing to destroy. Base is already empty.")
        return

    # ====. STEP 1: Delete NAT Gateway ===
    if 'nat_id' in state:
        print("====Destroying NAT Gateway =====")
        ## What is this doing :
        #1> Get nat_id from state
        #2> Call ec2.delete_nat_gateway(..)
        #3> Wait (import time, time.sleep(60))
        #5> Remove private_nat_route from state (if exsists)
        #6> Save_state

    # ==Step 2: Release Elastic IP ====
    if 'nat_eip_alloc_id' in state:
        print("===== Releasing Elastic IP ======")
