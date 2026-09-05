# planner.py - The Smart Diff Engine (Stewie's Brain)
# Compares what you WANT (network.yaml) vs what ACTUALLY EXISTS in AWS
# If state.json says something exists but AWS says NO → syncs state + marks CREATE
# Outputs: CREATE / NO-OP / DELETE decisions for each resource

from network.state import load_state, save_state
from network.aws_client import get_client
import yaml


def load_config():
    with open("config/network.yaml", "r") as f:
        return yaml.safe_load(f)
## converting a yaml. file in a python dictionary


# ==================== AWS VERIFICATION FUNCTIONS ====================
# These actually ASK AWS: "Hey, does this thing still exist?"

def verify_vpc_exists(ec2, vpc_id):
    """Ask AWS: does this VPC still exist?"""
    try:
        response = ec2.describe_vpcs(VpcIds=[vpc_id])
        return len(response['Vpcs']) > 0
    except:
        return False


def verify_subnet_exists(ec2, subnet_id):
    """Ask AWS: does this subnet still exist?"""
    try:
        response = ec2.describe_subnets(SubnetIds=[subnet_id])
        return len(response['Subnets']) > 0
    except:
        return False


def verify_igw_exists(ec2, igw_id):
    """Ask AWS: does this Internet Gateway still exist?"""
    try:
        response = ec2.describe_internet_gateways(InternetGatewayIds=[igw_id])
        return len(response['InternetGateways']) > 0
    except:
        return False


def verify_nat_exists(ec2, nat_id):
    """Ask AWS: does this Security Group still exist and is it active?"""
    try:
        response = ec2.describe_nat_gateways(NatGatewayIds=[nat_id])
        if len(response['NatGateways']) > 0:
            status = response['NatGateways'][0]['State']
            return status in ('available', 'pending')
        return False
    except:
        return False


def verify_route_table_exists(ec2, rt_id):
    """Ask AWS: does this route table still exist?"""
    try:
        response = ec2.describe_route_tables(RouteTableIds=[rt_id])
        return len(response['RouteTables']) > 0
    except:
        return False

def verify_sg_exists(ec2, sg_id):
    """Ask AWS: does this Security Group still exist?"""
    try:
        response = ec2.describe_security_groups(GroupIds=[sg_id])
        return len(response['SecurityGroups']) > 0
    except:
        return False

# ==================== THE SYNC ENGINE ====================
# Walks through state.json and verifies each resource against AWS
# If something is gone → removes it from state

def sync_state_with_aws(state, ec2):
    """Walk through state, verify each resource in AWS, remove dead ones."""
    drifts = []

    # Check VPC
    if 'vpc_id' in state:
        if not verify_vpc_exists(ec2, state['vpc_id']):
            print(f"  ⚠️  DRIFT: VPC {state['vpc_id']} gone from AWS!")
            state.clear()
            save_state(state)
            return state

    # Check subnets
    for key in list(state.keys()):
        value = state.get(key, '')
        if isinstance(value, str) and value.startswith('subnet-'):
            if not verify_subnet_exists(ec2, state[key]):
                print(f"  ⚠️  DRIFT: {key} gone from AWS!")
                del state[key]
                drifts.append(key)

    # Check IGW
    if 'igw_id' in state:
        if not verify_igw_exists(ec2, state['igw_id']):
            print(f"  ⚠️  DRIFT: IGW {state['igw_id']} gone!")
            del state['igw_id']
            drifts.append('igw_id')

    # Check NAT
    if 'nat_id' in state:
        if not verify_nat_exists(ec2, state['nat_id']):
            print(f"  ⚠️  DRIFT: NAT {state['nat_id']} gone!")
            del state['nat_id']
            if 'nat_eip_alloc_id' in state:
                del state['nat_eip_alloc_id']
            if 'private_nat_route' in state:
                del state['private_nat_route']
            drifts.append('nat_id')

    # Check public route table
    if 'public_rt_id' in state:
        if not verify_route_table_exists(ec2, state['public_rt_id']):
            print(f"  ⚠️  DRIFT: Public Route Table {state['public_rt_id']} gone!")
            del state['public_rt_id']
            # Remove associations too
            for key in list(state.keys()):
                if key.startswith('public') and '_rt_assoc' in key:
                    del state[key]
            drifts.append('public_rt_id')

    # Check private route table
    if 'private_rt_id' in state:
        if not verify_route_table_exists(ec2, state['private_rt_id']):
            print(f"  ⚠️  DRIFT: Private Route Table {state['private_rt_id']} gone!")
            del state['private_rt_id']
            # Remove associations too
            for key in list(state.keys()):
                if key.startswith('private') and '_rt_assoc' in key:
                    del state[key]
            drifts.append('private_rt_id')



    # Check Security Groups
    for key in list(state.keys()):
        if key.startswith('sg_'):
           sg_id = state[key]
           if not verify_sg_exists(ec2, sg_id):
              print(f" Drift:Security Group {sg_id} ({key}) gone!")
              del state[key]
              drifts.append(key)

    # Save synced state
    if drifts:
        save_state(state)
        print(f"\n  📸 State synced! Removed {len(drifts)} stale entries.")
    else:
        print("\n  ✅ No drift — state matches AWS.")

    return state


# ==================== THE PLAN GENERATOR ====================

def generate_plan(config):
    """Compare desired state (config) vs actual state (verified against AWS).
    Returns a list of action dicts."""
    ec2 = get_client('ec2')
    state = load_state()

    # STEP 1: Sync state with AWS (the smart part — Stewie checks with his own eyes)
    print("🔍 Verifying resources against AWS...")
    state = sync_state_with_aws(state, ec2)

    # STEP 2: Now compare desired (YAML) vs synced state
    plan = []

    # --- VPC Check ---
    vpc_name = config['vpc']['name']
    if 'vpc_id' in state:
        plan.append({
            "type": "vpc",
            "name": vpc_name,
            "action": "NO-OP",
            "id": state['vpc_id']
        })
    else:
        plan.append({
            "type": "vpc",
            "name": vpc_name,
            "action": "CREATE",
            "id": None
        })

    # --- Subnets Check (loop through all 4) ---
    all_subnets = (
        config['subnets']['public'] + config['subnets']['private']
    )
    for subnet in all_subnets:
        subnet_name = subnet['name']
        if subnet_name in state:
            plan.append({
                "type": "subnet",
                "name": subnet_name,
                "action": "NO-OP",
                "id": state[subnet_name]
            })
        else:
            plan.append({
                "type": "subnet",
                "name": subnet_name,
                "action": "CREATE",
                "id": None
            })

    # --- Internet Gateway Check ---
    igw_name = config['internet_gateway']['name']
    if 'igw_id' in state:
        plan.append({
            "type": "internet_gateway",
            "name": igw_name,
            "action": "NO-OP",
            "id": state['igw_id']
        })
    else:
        plan.append({
            "type": "internet_gateway",
            "name": igw_name,
            "action": "CREATE",
            "id": None
        })

    # --- NAT Gateway Check ---
    nat_name = config['nat_gateway']['name']
    if 'nat_id' in state:
        plan.append({
            "type": "nat_gateway",
            "name": nat_name,
            "action": "NO-OP",
            "id": state['nat_id']
        })
    else:
        plan.append({
            "type": "nat_gateway",
            "name": nat_name,
            "action": "CREATE",
            "id": None
        })

    # --- Route Table Check ---
    if 'public_rt_id' in state:
        plan.append({
            "type": "route_table",
            "name": "public-route-table",
            "action": "NO-OP",
            "id": state['public_rt_id']
        })
    else:
        plan.append({
            "type": "route_table",
            "name": "public-route-table",
            "action": "CREATE",
            "id": None
        })

    if 'private_rt_id' in state:
        plan.append({
            "type": "route_table",
            "name": "private-route-table",
            "action": "NO-OP",
            "id": state['private_rt_id']
        })
    else:
        plan.append({
            "type": "route_table",
            "name": "private-route-table",
            "action": "CREATE",
            "id": None
        })

    # ---  Security Group Check --------
    for sg in config['security_groups']:
        sg_name = sg['name']
        state_key = f"sg_{sg_name}"
        if state_key in state:
            plan.append({
                "type": "security_group",
                "name": sg_name,
                "action": "NO-OP",
                "id": state[state_key]

            })
        else:
            plan.append({
               "type": "security_group",
               "name": sg_name,
               "action": "CREATE",
               "id": None
            })
    return plan


# ==================== DISPLAY ====================

def display_plan(plan):
    """Print the execution plan in a nice formatted table."""

    creates = [p for p in plan if p['action'] == 'CREATE']
    noops = [p for p in plan if p['action'] == 'NO-OP']
    deletes = [p for p in plan if p['action'] == 'DELETE']

    print("\n" + "=" * 60)
    print("  EXECUTION PLAN")
    print("=" * 60)

    for item in plan:
        name = item['name']
        rtype = item['type']
        action = item['action']

        if action == "NO-OP":
            symbol = "✅"
            detail = f"EXISTS ({item['id'][:20]}...)"
        elif action == "CREATE":
            symbol = "⚡"
            detail = "NEEDS CREATION"
        elif action == "DELETE":
            symbol = "💀"
            detail = "WILL BE DELETED"

        print(f"  {symbol} {rtype:20s} \"{name}\" → {detail}")

    print("=" * 60)
    print(f"  {len(creates)} to create, {len(deletes)} to delete, {len(noops)} unchanged")
    print("=" * 60)

    if len(creates) == 0 and len(deletes) == 0:
        print("\n  ✅ Infrastructure matches desired state. Nothing to do.")
    else:
        print("\n  ⚡ Run 'python main.py apply' to execute this plan.")


# ==================== ENTRY POINT ====================

def run_planner():
    """Main entry point — load config, sync with AWS, generate plan, display it."""
    config = load_config()
    plan = generate_plan(config)
    display_plan(plan)
    return plan
