# 🧪 Reference Guide: Building `command_destroy()` — Rick and Morty Edition

> **Session Date:** July 28-31, 2026  
> **Project:** PythonAWSProject  
> **What we're building:** The `command_destroy()` function in `network/main.py`  
> **Teaching style:** Rick and Morty — Rick explains, Morty asks dumb-but-good questions  
> **Goal:** Learn to destroy AWS infrastructure in reverse dependency order

---

## 📋 HOW TO CONTINUE THIS SESSION

When starting a new Kiro session, use this prompt to resume:

```
I'm working on my PythonAWSProject at /home/raj/python/pythonawsproject.
I'm building the command_destroy() function in network/main.py.

Please read reference.md in my project — it has the full context of where I left off,
the teaching style I want, and what I've already learned.

Continue teaching me from where we stopped. Keep the Rick and Morty personality
(Rick explains concepts, Morty asks questions). Make it hilarious but technically
accurate. Teach one component at a time — don't dump everything at once.
Wait for me to confirm I understand before moving to the next step.

Also give me interview-ready answers after each concept so I can explain this
professionally.
```

---

## 🎯 THE TEACHING RULES (For AI to follow)

1. **ONE component at a time** — don't code-vomit the entire function
2. **Rick and Morty personality** — Rick is the genius who explains, Morty asks clarifying questions
3. **Rick burps, drinks, is impatient but ultimately teaches well**
4. **Morty asks "dumb" questions that are actually what the student is thinking**
5. **Every concept gets a real-world analogy** (not generic — specific and memorable)
6. **Interview-ready answer after each section** (professional language)
7. **Checkpoint after each step** — confirm understanding before proceeding
8. **Make it MEMORABLE** — humor exists to make concepts stick, not just for fun

---

## 🗺️ THE BIG PICTURE: Where We Are

### What's Already Built (✅ DONE):

| File | What It Does | Status |
|------|------|--------|
| `network/aws_client.py` | boto3 client factory (singleton) | ✅ |
| `network/state.py` | load_state() / save_state() with crash-safe writes | ✅ |
| `network/vpc.py` | create_vpc(config) | ✅ |
| `network/subnets.py` | create_subnet(config) — all 4 subnets | ✅ |
| `network/internet_gateway.py` | creating_igw(config) | ✅ |
| `network/route_tables.py` | create_route_tables(config) | ✅ |
| `network/nat_gateway.py` | create_nat_gateway(config) | ✅ |
| `network/planner.py` | Smart planner with drift detection | ✅ |
| `network/main.py` — plan | command_plan(config) | ✅ |
| `network/main.py` — apply | command_apply(config) | ✅ |
| `network/main.py` — destroy | command_destroy(config) | 🔨 IN PROGRESS |

### What We're Building NOW:

`command_destroy()` — tears down ALL infrastructure in REVERSE order.

### Progress on destroy:

```
Step 1: Delete NAT Gateway        ✅ LEARNED (explained + understood)
Step 2: Release Elastic IP         ✅ LEARNED (explained + understood)
Step 3: Delete Route Tables        ⬜ NEXT UP
Step 4: Detach + Delete IGW        ⬜
Step 5: Delete Subnets             ⬜
Step 6: Delete VPC                 ⬜
Entry Point: if __name__ block     ⬜
```

---

## 🧪 THE ONE RULE OF DESTROY

> **You can't delete a CONTAINER while things are still INSIDE it or ATTACHED to it.**

### The Pringles Analogy:

**Build order (putting chips IN the can):**
```
First in  → VPC (bottom of the can)
          → Subnets
          → IGW
          → Route Tables  
Last in   → NAT Gateway (top of the can)
```

**Destroy order (taking chips OUT):**
```
First out → NAT Gateway (it's on TOP)
          → EIP
          → Route Tables
          → IGW
          → Subnets
Last out  → VPC (it's on the BOTTOM)
```

**You eat Pringles from the top. You destroy infrastructure from the top.**

### Why This Order?

| If You Try To Delete... | Before Removing... | AWS Says... |
|---|---|---|
| VPC | Subnets still inside | ❌ DependencyViolation |
| Subnet | NAT Gateway sitting in it | ❌ DependencyViolation |
| Route Table | Subnets still linked | ❌ DependencyViolation |
| IGW | Still attached to VPC | ❌ DependencyViolation |

---

## 🧪 STEP 1: Delete NAT Gateway (✅ LEARNED)

### The Concept:

NAT Gateway is sitting INSIDE a subnet. You can't demolish the subnet while NAT is in it. Kill NAT first.

NAT is a drama queen — takes 60-90 seconds to fully die (goes through "deleting" state before disappearing).

### Rick's Explanation:

> "It's like trying to demolish a bathroom while someone's still on the toilet. You REMOVE THE PERSON FIRST."

### The Code:

```python
if 'nat_id' in state:
    print("━━━ Step 1: Destroying NAT Gateway ━━━")
    
    # 1. Tell AWS to kill it
    nat_id = state['nat_id']
    ec2.delete_nat_gateway(NatGatewayId=nat_id)
    
    # 2. Wait for it to die (slow dramatic death)
    import time
    print(f"  Waiting for NAT {nat_id} to die...")
    time.sleep(90)
    
    # 3. Remove from our records
    del state['nat_id']
    if 'private_nat_route' in state:
        del state['private_nat_route']
    save_state(state)
    print("  💀 NAT Gateway is dead.")
```

### Line-by-line:

| Line | What It Does | Rick Says |
|------|------|------|
| `if 'nat_id' in state:` | Check if we even HAVE a NAT | "Can't murder someone who doesn't exist" |
| `nat_id = state['nat_id']` | Get the target's ID | "Pull up the file before you erase them" |
| `ec2.delete_nat_gateway(NatGatewayId=nat_id)` | The kill shot — tell AWS to delete it | "One API call. Boom." |
| `time.sleep(90)` | Wait for it to fully die | "Drama queen needs 90 seconds for her final monologue" |
| `del state['nat_id']` | Remove from photo album | "It's dead, stop tracking it" |
| `del state['private_nat_route']` | Remove the route that pointed to NAT | "Sign points to a corpse — useless" |
| `save_state(state)` | Save immediately | "Save the game after every boss fight" |

### Why `time.sleep(90)` and not a waiter?

Rick: "The JUNIOR developer writes a waiter on day one. The SENIOR developer ships `time.sleep(90)` and moves on. Knowing WHICH corners to cut — that's the game."

### Why remove `private_nat_route` too?

Cascading cleanup. NAT dead → the route pointing to it is a dead-end road → remove the sign pointing to nowhere.

### Interview Answer:

> "NAT Gateways have an asynchronous deletion lifecycle — they transition through 'deleting' state before fully terminating. I added a wait period after issuing the delete call to ensure dependent resources like the subnet can be safely removed in subsequent steps. I also cascade the cleanup to remove the associated private route entry from state, since a route pointing to a non-existent NAT would create a traffic black hole."

---

## 🧪 STEP 2: Release Elastic IP (✅ LEARNED)

### The Concept:

EIP = a permanent public phone number we rented for the NAT Gateway. NAT is dead now. Nobody's using the phone number. But AWS keeps charging $3.60/month to RESERVE it. Cancel the plan.

### Rick's Explanation:

> "It's a phone sitting on a desk. No one's picking it up. But AWS charges you $3.60/month to KEEP that number reserved. It's like paying rent on an empty apartment."

### The Code:

```python
if 'nat_eip_alloc_id' in state:
    print("━━━ Step 2: Releasing Elastic IP ━━━")
    ec2.release_address(AllocationId=state['nat_eip_alloc_id'])
    del state['nat_eip_alloc_id']
    save_state(state)
    print("  💀 EIP released. Phone plan cancelled.")
```

### Line-by-line:

| Line | What It Does | Rick Says |
|------|------|------|
| `if 'nat_eip_alloc_id' in state:` | Do we have an EIP? | "Don't cancel a plan that's already cancelled" |
| `ec2.release_address(AllocationId=...)` | Tell AWS: release this IP back to the wild | "Hand the receipt back. We're done." |
| `del state['nat_eip_alloc_id']` | Remove from album | "Rip the receipt out" |
| `save_state(state)` | Save the game | "ALWAYS save after a kill" |

### Why is this SEPARATE from Step 1?

1. **You CAN'T release an EIP while NAT is still using it** — like cancelling someone's phone plan while they're still on a call
2. **Separation of concerns** — each step does ONE thing. Clean. Debuggable.

### What happens if you FORGET this step?

Orphaned EIP. Sits there costing $3.60/month doing NOTHING. AWS doesn't warn you. It just quietly appears on your bill. Month after month. Forever.

### Interview Answer:

> "The EIP doesn't get automatically released when the NAT is deleted — it becomes an orphaned resource that AWS continues to bill for. My destroy command explicitly releases the EIP as a separate step after confirming the NAT Gateway has fully terminated. This prevents cost leakage from unattached Elastic IPs, which are billed at approximately $0.005/hour."

---

## 🧪 STEP 3: Delete Route Tables (⬜ NEXT UP)

### Preview (what we'll learn next):

Route tables have ASSOCIATIONS — they're linked to subnets. You can't delete a route table while subnets are still connected to it.

**Two-step process:**
1. First: DISASSOCIATE (unlink the subnets)
2. Then: DELETE (destroy the route table)

Rick's preview: "It's like Jessica, Morty. You can't just DELETE her from your life. You have to BREAK UP first, THEN delete her number. Two steps."

---

## 🧩 THE FULL DESTROY FUNCTION (What it will look like when complete)

```python
def command_destroy(config):
    """RETREAT: Destroy everything in REVERSE order."""
    print("\n💣 RETREAT ORDER — Demolishing infrastructure...\n")

    ec2 = get_client('ec2')
    state = load_state()

    if not state:
        print("Nothing to destroy. Base is already empty.")
        return

    # Step 1: Delete NAT Gateway           ← ✅ LEARNED
    # Step 2: Release Elastic IP            ← ✅ LEARNED  
    # Step 3: Delete Route Tables           ← ⬜ NEXT
    # Step 4: Detach + Delete IGW           ← ⬜
    # Step 5: Delete Subnets               ← ⬜
    # Step 6: Delete VPC                   ← ⬜

    print("\n💣 DEMOLITION COMPLETE. Nothing remains. 🏚️")
```

---

## 🧩 PATTERNS TO REMEMBER

### Pattern 1: Check Before Killing
```python
if 'THING_ID' in state:    # Does it exist in our records?
    # ... delete it
```
Why: Can't kill what doesn't exist. Don't error out on missing resources.

### Pattern 2: Save After Every Kill
```python
del state['THING_ID']       # Remove from records
save_state(state)           # SAVE IMMEDIATELY
```
Why: If script crashes later, we know this thing is already gone. No double-deletion attempts.

### Pattern 3: Cascading Cleanup
```python
# When parent dies, kill related entries too
del state['nat_id']                    # Parent dead
if 'private_nat_route' in state:
    del state['private_nat_route']     # Dependent dead too
```
Why: Routes/associations that point to dead resources are useless. Clean them.

### Pattern 4: try/except on Already-Gone Resources
```python
try:
    ec2.disassociate_route_table(AssociationId=state[key])
except:
    pass  # Already gone from console? Fine. Move on.
```
Why: Someone might have manually deleted stuff from AWS console. Don't crash over it.

---

## 🎤 MASTER INTERVIEW ANSWERS

### "How does your destroy command work?"

> "It implements reverse-dependency teardown — resources are deleted in the opposite order they were created, respecting AWS dependency constraints. NAT Gateway first (since it occupies a subnet), then EIP release to prevent orphaned billing, route table disassociation and deletion, IGW detach-then-delete, subnets, and finally the VPC. State is atomically updated after each deletion to support crash recovery."

### "How do you handle partial failures during destroy?"

> "Each destruction step atomically updates the state file after completion. If the process crashes mid-execution, the next run will skip already-destroyed resources (they won't be in state) and continue from where it left off. This makes the destroy operation idempotent and resumable."

### "Why reverse order?"

> "AWS enforces dependency constraints — you cannot delete a VPC while subnets exist inside it, or a subnet while a NAT Gateway is deployed in it. Attempting to do so returns a DependencyViolation error. The reverse order ensures each resource is freed of its dependents before deletion."

---

## 📌 KEY CONCEPTS SUMMARY

| Concept | One-Liner | Rick Quote |
|---------|-----------|------------|
| Reverse order | Destroy from inside-out (top of Pringles first) | "LIFO, Morty. Last In, First Out. Like Pringles." |
| DependencyViolation | AWS won't let you delete containers with stuff inside | "Can't demolish bathroom while someone's on the toilet" |
| time.sleep(90) | NAT takes time to die | "Drama queen needs 90 seconds for her final monologue" |
| Cascading cleanup | When parent dies, dependents are useless | "When someone dies, their phone number doesn't work either" |
| Save after kill | Persist state after each deletion | "Save the game after every boss fight" |
| Orphaned EIP | Unreleased IP costs money forever | "Paying rent on an empty apartment" |
| Disassociate before delete | Unlink things before removing them | "Break up first, THEN delete her number" |
| Strategic laziness | time.sleep > complex waiter (for now) | "SENIOR developer ships sleep(90) and moves on" |

---

## 🧪 EARLIER SESSION RECAP: What We Built Before Destroy

### The main.py Journey (July 28, 2026)

Before we started destroy, we built `command_plan()` and `command_apply()`.

#### What IS main.py?

**Rick:** "It's the PORTAL GUN of this project, Morty. One device, three settings. You don't walk into each dimension manually — you point the gun and GO."

- `python -m network.main plan` → "Show me what's missing" (recon only)
- `python -m network.main apply` → "Build everything that's missing" (in order)
- `python -m network.main destroy` → "Burn it all down" (in reverse order)

Without main.py, you're running each module manually from Jupyter like a caveman.

#### command_plan() — The Scanner:

```python
def command_plan(config):
    plan = generate_plan(config)
    display_plan(plan)
    return plan
```

3 lines. Just calls the planner. "Hey Stewie, what's the situation?"

#### command_apply() — The Builder:

```python
def command_apply(config):
    plan = generate_plan(config)    # What's missing?
    display_plan(plan)
    
    creates = [p for p in plan if p['action'] == 'CREATE']
    
    if len(creates) == 0:
        print("Nothing to build.")
        return
    
    # Build in ORDER (dependencies matter!)
    # Step 1: VPC → Step 2: Subnets → Step 3: IGW → Step 4: Routes → Step 5: NAT
```

Key insight: Uses `any()` to check if a specific resource type needs creation:
```python
if any(p['type'] == 'vpc' and p['action'] == 'CREATE' for p in plan):
    create_vpc(config)
```

**Rick:** "any() is like asking a crowd — 'Does ANYONE here need a VPC?' If even ONE person raises their hand, we build it."

---

### Bugs We Fixed in main.py (The Crime Scene 🔍)

| Bug | What Was Wrong | Fix | Rick Says |
|-----|------|------|------|
| `create_nat_tables` | Wrong function name in import | `create_route_tables` | "Calling for Chef Natraj but his name is Routeraj" |
| `p['action]']` | Extra `]` inside quotes — SyntaxError | `p['action']` | "Writing 'pepperoni]' on the order slip" |
| `create_igw(config)` | Function is actually called `creating_igw` | `creating_igw(config)` | "Yelled CHEF IGGY but his name is CREATING-IGGY" |
| Missing import | `creating_igw` never imported at top | Added `from network.internet_gateway import creating_igw` | "Hired a chef but never gave him a badge" |
| `'igw'` type check | Planner uses `'internet_gateway'` not `'igw'` | Changed to `'internet_gateway'` | "Looking for someone by their nickname in a government database" |
| Print statements | All said "Step 1" | Fixed to Step 1-5 | "General yelling STEP 1 five times in a row" |

#### How to catch bugs:

```bash
# Syntax check (catches broken quotes, missing colons):
python3 -c "import ast; ast.parse(open('network/main.py').read()); print('✅ OK')"

# Import check (catches wrong function names):
python3 -c "from network.main import command_plan"
```

---

### The Entry Point (Still Needed ⬜)

```python
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m network.main [plan|apply|destroy]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    config = load_config()
    
    if command == 'plan':
        command_plan(config)
    elif command == 'apply':
        command_apply(config)
    elif command == 'destroy':
        command_destroy(config)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
```

**What `if __name__ == '__main__':` means:**

**Rick:** "It's a letter that says 'ONLY OPEN IF YOU'RE THE ONE READING THIS.' If someone IMPORTS your file, this block doesn't run. If someone RUNS your file directly from terminal, it runs."

- `python -m network.main plan` → block RUNS (running the file directly)
- `from network.main import command_plan` → block does NOT run (just importing)

**What `sys.argv` is:**

```
python -m network.main plan
                       ↑
                  sys.argv[1]
                  (the command)
```

**Rick:** "sys.argv is the words the user typed. argv[1] is what they want. It's like answering the phone — 'Rick's lab, what do you want?'"

---

## 🧪 HOW THE WHOLE PROJECT CONNECTS (The Dependency Map)

```
                    ┌──────────────────────────┐
                    │     network/main.py       │ ← YOU ARE HERE (building destroy)
                    │  plan | apply | destroy   │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
              ▼                  ▼                   ▼
    ┌─────────────────┐  ┌─────────────┐  ┌───────────────────┐
    │  planner.py     │  │  vpc.py     │  │  subnets.py       │
    │  (the brain)    │  │  igw.py     │  │  route_tables.py  │
    │                 │  │  nat_gw.py  │  │                   │
    └────────┬────────┘  └──────┬──────┘  └────────┬──────────┘
             │                  │                   │
             └──────────────────┼───────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   aws_client.py       │ ← boto3 (talks to AWS)
                    │   state.py            │ ← state.json (tracks what exists)
                    └──────────────────────┘
```

**Rick:** "Everything funnels down to TWO things, Morty: the PHONE (aws_client) and the ALBUM (state). Every module uses both. That's the whole architecture."

---

## 🧪 THE PLANNER RECAP (From Earlier Sessions — July 21)

### What It Does (One Sentence):

Compares what you WANT (YAML) vs what ACTUALLY EXISTS (AWS) and tells you what's missing.

### The Smart vs Dumb Planner:

- **Dumb planner (v1):** Only checked state.json. If state said "NAT exists" it believed it. Even if NAT was deleted from console.
- **Smart planner (v2 — current):** Calls AWS `describe_*` APIs to VERIFY each resource is actually alive before planning.

### The Pipeline:

```
run_planner()
  → load_config()              # Read YAML (what we WANT)
  → generate_plan(config)
      → load_state()           # Read state.json (what we THINK exists)
      → sync_state_with_aws()  # Verify against LIVE AWS (catch drift!)
          → verify_vpc_exists()
          → verify_subnet_exists()
          → verify_igw_exists()
          → verify_nat_exists()       # Checks State field! 'deleted' = gone
          → verify_route_table_exists()
      → Compare YAML vs cleaned state → CREATE or NO-OP
  → display_plan(plan)         # Pretty print with ✅/⚡/💀
```

### Key Planner Concepts:

| Concept | What It Means |
|---------|------|
| Drift | Reality doesn't match state.json (someone deleted stuff from console) |
| sync_state_with_aws() | The upgrade that makes planner SMART — verifies each resource |
| VPC gone = state.clear() | If the house is gone, everything inside is gone too |
| isinstance(value, str) | Guard against booleans in state (private_nat_route: true) |
| list(state.keys()) | Copy keys before deleting — can't modify dict while iterating |
| NAT 'deleted' state | AWS keeps NAT as a ghost for ~1 hour. Check status field. |

---

## 🧪 AWS CONCEPTS CHEAT SHEET

| AWS Thing | What It Is | Analogy |
|---|---|---|
| VPC | Virtual Private Cloud — your private network in AWS | The house 🏠 |
| Subnet | A section of the VPC with its own IP range | A room in the house |
| Public subnet | Has a route to the internet (via IGW) | Living room (front-facing) |
| Private subnet | No direct internet access (uses NAT) | Basement (hidden) |
| Internet Gateway | Connects VPC to the internet | Front door 🚪 |
| NAT Gateway | Lets private subnets access internet without being exposed | Messenger who relays mail 👩 |
| Elastic IP | A permanent public IP address | A phone number you rent 📱 |
| Route Table | Rules that say "traffic to X goes through Y" | Road signs 🪧 |
| Route Association | Links a subnet to a route table | Tape holding sign to wall 📎 |
| CIDR (10.0.0.0/16) | IP address range — /16 = 65,536 IPs | The lot size of your property |
| Availability Zone | Physical data center location (ap-south-1a, 1b) | Which side of town |
| describe_* APIs | Read-only calls to check if things exist | "Hey AWS, is this still alive?" |
| DependencyViolation | Error when deleting something that has dependents | "Can't demolish room while furniture is inside" |
| boto3 | Python SDK for AWS | The phone to call AWS 📞 |
| Singleton pattern | One shared connection, not one per call | One phone for the whole office |
| Idempotent | Run 100 times, same result | Pressing elevator button 50 times doesn't make it come faster |

---

## 🧪 THE FULL STATE.JSON (What Gets Tracked)

When everything is deployed, state.json looks like:

```json
{
    "vpc_id": "vpc-04e3648d954b21cf7",
    "vpc_name": "dev-vpc",
    "public-subnet-az1": "subnet-0bd50694843fc2e44",
    "public-subnet-az2": "subnet-00161c7d9391e5c18",
    "private-subnet-az1": "subnet-0c5bb17f94445a9c3",
    "private-subnet-az2": "subnet-05b1dd48afbd12345",
    "igw_id": "igw-0927984aabe4aa123",
    "public_rt_id": "rtb-02defa987c03fbc12",
    "private_rt_id": "rtb-069052ef3663f7b34",
    "public-subnet-az1_rt_assoc": "rtbassoc-0abc123...",
    "public-subnet-az2_rt_assoc": "rtbassoc-0def456...",
    "private-subnet-az1_rt_assoc": "rtbassoc-0ghi789...",
    "private-subnet-az2_rt_assoc": "rtbassoc-0jkl012...",
    "nat_eip_alloc_id": "eipalloc-0abc123...",
    "nat_id": "nat-0081de96b9cc8f604",
    "private_nat_route": true
}
```

After `destroy` completes, state.json should be:

```json
{}
```

---

## 🧪 COST TABLE (Burn This Into Your Brain)

| Resource | Cost | Destroy Priority |
|---|---|---|
| NAT Gateway | **$32/month** ($0.045/hr) | 🔥 KILL FIRST |
| Elastic IP (unattached) | **$3.60/month** ($0.005/hr) | 🔥 KILL SECOND |
| VPC | Free | Low priority |
| Subnets | Free | Low priority |
| Internet Gateway | Free | Low priority |
| Route Tables | Free | Low priority |

**Rick:** "The NAT and EIP are the only things costing REAL money. Everything else is free. If you're too lazy to destroy everything, AT LEAST kill NAT and release EIP. That saves $35.60/month."

---

## 🧪 DESIGN PATTERNS USED IN THIS PROJECT

| Pattern | Where | Rick Explains |
|---------|-------|------|
| Singleton | aws_client.py — one boto3 session | "One phone for the office. Not 50 phones." |
| Idempotency | Every create module checks state first | "Pressing elevator button twice doesn't summon two elevators" |
| Crash-safe writes | state.py — write .tmp → os.replace | "Save to draft first, then hit send. Never lose data." |
| Refresh-then-diff | planner.py — verify AWS before planning | "Don't trust photos. Go CHECK with your own eyes." |
| Cascading cleanup | sync_state_with_aws — parent gone = children removed | "House burned? Stop looking for the couch." |
| Config/logic separation | YAML = what, Python = how | "Menu says what to cook. Chef decides HOW." |
| Communication via state | Modules share through state.json, not imports | "Leave a note on the fridge. Don't call everyone." |
| Dependency ordering | command_apply builds in DAG order | "Foundation first. Roof last. Obviously." |
| LIFO destruction | command_destroy reverses the build order | "Pringles, Morty. Top comes out first." |

---

## 🧪 EXACT FUNCTION NAMES (For Quick Reference)

| File | Function | Takes | Returns |
|------|------|------|------|
| `aws_client.py` | `get_session(region_name="ap-south-1")` | region string | boto3 Session |
| `aws_client.py` | `get_client(service_name, region_name="ap-south-1")` | service string | boto3 Client |
| `state.py` | `load_state()` | nothing | dict |
| `state.py` | `save_state(state)` | dict | nothing |
| `vpc.py` | `create_vpc(config)` | config dict | nothing |
| `subnets.py` | `create_subnet(config)` | config dict | nothing |
| `internet_gateway.py` | `creating_igw(config)` | config dict | nothing |
| `route_tables.py` | `create_route_tables(config)` | config dict | nothing |
| `nat_gateway.py` | `create_nat_gateway(config)` | config dict | nothing |
| `planner.py` | `load_config()` | nothing | config dict |
| `planner.py` | `verify_vpc_exists(ec2, vpc_id)` | client, string | bool |
| `planner.py` | `verify_subnet_exists(ec2, subnet_id)` | client, string | bool |
| `planner.py` | `verify_igw_exists(ec2, igw_id)` | client, string | bool |
| `planner.py` | `verify_nat_exists(ec2, nat_id)` | client, string | bool |
| `planner.py` | `verify_route_table_exists(ec2, rt_id)` | client, string | bool |
| `planner.py` | `sync_state_with_aws(state, ec2)` | dict, client | cleaned dict |
| `planner.py` | `generate_plan(config)` | config dict | plan list |
| `planner.py` | `display_plan(plan)` | plan list | nothing |
| `planner.py` | `run_planner()` | nothing | plan list |
| `main.py` | `command_plan(config)` | config dict | plan list |
| `main.py` | `command_apply(config)` | config dict | nothing |
| `main.py` | `command_destroy(config)` | config dict | nothing (WIP) |

---

## 🔜 WHAT'S NEXT (When you resume)

1. **Step 3:** Delete Route Tables (disassociate first, then delete)
2. **Step 4:** Detach + Delete Internet Gateway (two-step: unhinge, then remove)
3. **Step 5:** Delete Subnets (loop through state, find subnet-* values)
4. **Step 6:** Delete VPC (the grand finale — state.clear())
5. **Entry point:** Add `if __name__ == '__main__':` block
6. **Test the full cycle:** plan → apply → plan → destroy → plan
7. **Push to Git**

---

*"Listen Morty, the universe is basically an infinite series of closing accounts and cancelling subscriptions. Infrastructure is no different. You create it, you maintain it, you destroy it. Circle of life. Now hand me that flask."* — Rick Sanchez, C-137 🧪
