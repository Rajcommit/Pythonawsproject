# 🧠 Understanding Planner.py — The Complete Guide

## A Family Guy Guide to Infrastructure Planning

*Last updated: July 21, 2026*
*Project: pythonawsproject*

---

## What IS the Planner?

Remember how Stewie has that whiteboard in his room where he draws his evil plans?

> "Step 1: Build mind-control device. Step 2: Enslave humanity. Step 3: Cancel Meg."

Then he looks around his lab and checks what's actually there vs what's on the whiteboard.

**That's the planner.** It compares:
- 📋 **What you WANT** (network.yaml) → Stewie's whiteboard
- 🏠 **What actually EXISTS in AWS** → reality
- 📸 **What state.json THINKS exists** → the photo album

And produces a **plan**: CREATE / NO-OP / DELETE for each resource.

---

## Why Do We Need It?

### 🎬 Scene: Peter Destroys Things Without Checking

Peter decides to "fix" the house. He doesn't check what's already built:

> *"I'm gonna build a door!"*
> "Peter, there's already a door—"
> *"I SAID I'M BUILDING A DOOR!"*

Now you have two front doors. One leads to the street. The other leads into Quagmire's bedroom. Giggity.

**Without a planner**, your code is like Peter — it just DOES things without checking.
You'd end up with duplicate VPCs, two NAT Gateways ($64/month for no reason), conflicting routes.

### 🎬 Scene: Stewie Plans Everything

Stewie would NEVER just start building. He:
1. Looks at the blueprint (network.yaml)
2. Looks at what exists (verified against AWS)
3. Makes a **plan** (what to create, what to skip, what to destroy)
4. Only THEN executes

**That's professional infrastructure management.** That's what Terraform does.

---

## The Interview Answer 🎤

> **Interviewer:** "Why did you build a planner?"
>
> **You:** "I implemented a plan-before-apply workflow — similar to Terraform's
> `terraform plan`. The planner acts as a diff engine. It reads the desired state
> from a YAML config file, compares it against both the local state file AND the
> actual AWS resources via describe API calls, and generates an execution manifest
> of CREATE, UPDATE, DELETE, or NO-OP actions. This gives the operator visibility
> into what WILL change before anything is actually mutated in the AWS account.
> It prevents duplicate resource creation, catches configuration drift, and makes
> the tool safe for production use."
>
> **Interviewer:** *impressed Pikachu face*

---

## The Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    THE PLANNER                           │
│                                                         │
│   INPUT 1: network.yaml (what you WANT)                 │
│   INPUT 2: state.json (what you BUILT last time)        │
│   INPUT 3: AWS describe_* calls (what ACTUALLY exists)  │
│                                                         │
│   OUTPUT: A plan (list of actions)                      │
└─────────────────────────────────────────────────────────┘
```

### The 3 Scenarios It Handles:

| Scenario | Stewie Analogy | Action |
|----------|---------------|--------|
| In YAML, NOT in AWS | "I want a laser, but I don't have one yet" | **CREATE** |
| In YAML AND in AWS | "I wanted a laser and I have one. Excellent." | **NO-OP** (skip) |
| In state, NOT in YAML | "I don't need this cage anymore... Rupert is free" | **DELETE** |

---

## The Dumb Planner vs The Smart Planner

### Dumb Planner (v1 — what we had first):

Only checks state.json. Never talks to AWS.

> **Peter checking the photo album:** *"Is VPC in the album? YES! Done."*
> Meanwhile the house burned down. Peter doesn't know because he only looked at photos.

### Smart Planner (v2 — what we have now):

Verifies against LIVE AWS first, syncs state, THEN makes the plan.

> **Stewie walking into each room:** *"Is VPC in the album? Yes. But let me
> WALK OVER and check... it's actually GONE! Update the album. Mark for rebuild."*

---

## The File Structure (4 Sections)

```
planner.py
│
├── SECTION 1: Verify Functions (5 spies — one per resource)
│       verify_vpc_exists()
│       verify_subnet_exists()
│       verify_igw_exists()
│       verify_nat_exists()
│       verify_route_table_exists()
│
├── SECTION 2: Sync Engine (the brain upgrade)
│       sync_state_with_aws()
│
├── SECTION 3: Plan Generator (compare YAML vs state)
│       generate_plan()
│
├── SECTION 4: Display + Entry Point
│       display_plan()
│       run_planner()
│
└── HOW THEY CONNECT:
        run_planner() calls load_config()
        run_planner() calls generate_plan()
            generate_plan() calls sync_state_with_aws()  ← THE KEY
                sync_state_with_aws() calls verify_*() functions
            generate_plan() then compares YAML vs cleaned state
        run_planner() calls display_plan()
```

---

## CODE BREAKDOWN — Line by Line

---

### The Imports (The Toolbox)

```python
from network.state import load_state, save_state    # Read/write the photo album
from network.aws_client import get_client           # Phone to call AWS
import yaml                                         # Read the master plan (YAML)
```

**Stewie's toolbox:**
- 📸 `load_state / save_state` — Read and update the photo album
- 📞 `get_client` — Phone to call AWS and ask "does this exist?"
- 📋 `yaml` — Magnifying glass to read the master plan

---

### `load_config()` — Read The Evil Master Plan

```python
def load_config():
    with open("config/network.yaml", "r") as f:
        return yaml.safe_load(f)
```

Opens `network.yaml`, converts YAML to a Python dictionary, returns it.

**Stewie picks up his whiteboard:** *"What did I WANT to build?"*

---

### SECTION 1: The Verify Functions — Stewie's Spies 🕵️

These are like Stewie sending Brian to check each room.

#### The Pattern (SAME for all 5):

```python
def verify_SOMETHING_exists(ec2, resource_id):
    try:
        response = ec2.describe_SOMETHINGS(SOMETHINGIds=[resource_id])
        return len(response['SOMETHINGS']) > 0
    except:
        return False
```

**The recipe:**
1. Try to ask AWS: "Hey, does this ID still exist?"
2. If AWS says YES (list has items) → return `True`
3. If AWS says NO or crashes → return `False`

**Brian goes to check a room:**
- Room exists → *"Yes, it's here."* (True)
- Room gone → *"Uh... it's gone."* (False)
- Entire floor missing → *catches himself from falling* → "Not there." (except → False)

#### VPC:
```python
def verify_vpc_exists(ec2, vpc_id):
    try:
        response = ec2.describe_vpcs(VpcIds=[vpc_id])
        return len(response['Vpcs']) > 0
    except:
        return False
```

#### Subnet:
```python
def verify_subnet_exists(ec2, subnet_id):
    try:
        response = ec2.describe_subnets(SubnetIds=[subnet_id])
        return len(response['Subnets']) > 0
    except:
        return False
```

#### Internet Gateway:
```python
def verify_igw_exists(ec2, igw_id):
    try:
        response = ec2.describe_internet_gateways(InternetGatewayIds=[igw_id])
        return len(response['InternetGateways']) > 0
    except:
        return False
```

#### NAT Gateway (THE SPECIAL ONE):
```python
def verify_nat_exists(ec2, nat_id):
    try:
        response = ec2.describe_nat_gateways(NatGatewayIds=[nat_id])
        if len(response['NatGateways']) > 0:
            status = response['NatGateways'][0]['State']
            return status in ('available', 'pending')
        return False
    except:
        return False
```

**Why is NAT special?** NAT Gateways are drama queens. When deleted, they don't
disappear immediately — they sit in `"deleted"` state for an hour like a ghost.

- `available` → alive ✅
- `pending` → being born ✅
- `deleted` → ghost, treat as GONE ❌
- `deleting` → dying, treat as GONE ❌

#### Route Table:
```python
def verify_route_table_exists(ec2, rt_id):
    try:
        response = ec2.describe_route_tables(RouteTableIds=[rt_id])
        return len(response['RouteTables']) > 0
    except:
        return False
```

#### Why `try/except`?

If you ask AWS about an ID that's COMPLETELY gone (not just deleted, but VANISHED),
AWS throws an error. The `try/except` catches that error and says "nope, doesn't exist"
instead of crashing your whole program.

Like Brian going to check a room, but the entire floor collapsed. Instead of falling
and dying, he just reports back: *"Not there."*

---

### SECTION 2: `sync_state_with_aws()` — The Reality Check 🔍

**This is the HEART of the upgrade. This is what makes your planner SMART.**

```python
def sync_state_with_aws(state, ec2):
    drifts = []
```

- `state` → the photo album (dictionary from state.json)
- `ec2` → the phone to call AWS
- `drifts = []` → a list of dead things we found

---

#### VPC Check (The Foundation):

```python
    if 'vpc_id' in state:
        if not verify_vpc_exists(ec2, state['vpc_id']):
            print(f"  ⚠️  DRIFT: VPC {state['vpc_id']} gone from AWS!")
            state.clear()
            save_state(state)
            return state
```

**Why `state.clear()`?** If the HOUSE is gone, EVERYTHING inside it is gone too.
No point checking rooms if the building doesn't exist.

**Stewie:** *"The house... is gone?"*
**Brian:** *"Yep."*
**Stewie:** *"Then the living room, the basement, Meg's room... ALL GONE. Burn the ENTIRE photo album."*

- `state.clear()` → delete EVERYTHING from state
- `save_state(state)` → save the empty state
- `return state` → stop here, don't check anything else (house is gone!)

---

#### Subnet Check (The Rooms):

```python
    for key in list(state.keys()):
        value = state.get(key, '')
        if isinstance(value, str) and value.startswith('subnet-'):
            if not verify_subnet_exists(ec2, state[key]):
                del state[key]
                drifts.append(key)
```

**How does it find subnets?** It loops through ALL keys in state and looks for
values that start with `"subnet-"`. Smart — doesn't need a hardcoded list.

**`isinstance(value, str)`** — IMPORTANT FIX! Because `private_nat_route: true`
is a boolean, not a string. Can't call `.startswith()` on `true`. That crashed us earlier.

**`list(state.keys())`** — Why `list()`? Because you can't delete from a dictionary
while looping through it directly. Python gets confused (size changes mid-loop).
`list()` makes a COPY of the keys first, so we loop through the copy while
deleting from the original.

Like removing pages from a book — you photocopy the table of contents first,
then rip out pages while reading from the photocopy.

---

#### IGW Check (The Front Door):

```python
    if 'igw_id' in state:
        if not verify_igw_exists(ec2, state['igw_id']):
            del state['igw_id']
            drifts.append('igw_id')
```

Simple. *"Is the front door still there? No? Remove from album."*

---

#### NAT Check (Takes Friends With It):

```python
    if 'nat_id' in state:
        if not verify_nat_exists(ec2, state['nat_id']):
            del state['nat_id']
            if 'nat_eip_alloc_id' in state:
                del state['nat_eip_alloc_id']
            if 'private_nat_route' in state:
                del state['private_nat_route']
            drifts.append('nat_id')
```

**Why delete 3 things?** Because if Lois is gone:
- Her phone number (EIP) is useless → delete
- The sign that says "ask Lois" (private_nat_route) is meaningless → delete

*"Lois left the family. Remove her phone from contacts AND take down the
'Ask Lois' sign from the basement."*

---

#### Route Table Check (Takes Associations With It):

```python
    if 'public_rt_id' in state:
        if not verify_route_table_exists(ec2, state['public_rt_id']):
            del state['public_rt_id']
            for key in list(state.keys()):
                if key.startswith('public') and '_rt_assoc' in key:
                    del state[key]
            drifts.append('public_rt_id')
```

**Why delete associations?** If the sign board (route table) is destroyed, the glue
connecting rooms to that sign board (associations like `public-subnet-az1_rt_assoc`)
is also meaningless.

*"The sign is destroyed. The tape that held it to the wall is gone too."*

Same logic for private route table.

---

#### The Final Sync:

```python
    if drifts:
        save_state(state)
        print(f"\n  📸 State synced! Removed {len(drifts)} stale entries.")
    else:
        print("\n  ✅ No drift — state matches AWS.")

    return state
```

- Found dead things? → Save the cleaned photo album, tell the user how many ghosts we exorcised
- Everything alive? → *"All good, no ghosts here"*
- **Always return `state`** → so `generate_plan` uses the CLEANED version, not the stale one

---

### SECTION 3: `generate_plan()` — Compare Whiteboard vs Reality

```python
def generate_plan(config):
    ec2 = get_client('ec2')
    state = load_state()

    print("🔍 Verifying resources against AWS...")
    state = sync_state_with_aws(state, ec2)    # ← THE KEY LINE!

    plan = []
```

**THE KEY LINE:** `state = sync_state_with_aws(state, ec2)`

Before comparing, it VERIFIES against live AWS. The old planner skipped this.
The new planner doesn't trust the photo album blindly.

**Then for EACH resource, the SAME pattern:**

```python
    if 'RESOURCE_KEY' in state:        # Is it in the (verified) state?
        plan.append({
            "type": "...",
            "name": "...",
            "action": "NO-OP",          # Yes → already exists, skip
            "id": state['RESOURCE_KEY']
        })
    else:
        plan.append({
            "type": "...",
            "name": "...",
            "action": "CREATE",         # No → need to build it
            "id": None
        })
```

**Stewie's logic for each resource:**
1. *"Is it in the VERIFIED photo album?"*
2. YES → *"Moving on."* (NO-OP)
3. NO → *"NEEDS CREATION!"* (CREATE)

#### The checks in order:
1. VPC — `if 'vpc_id' in state`
2. Subnets (loops through all 4) — `if subnet_name in state`
3. Internet Gateway — `if 'igw_id' in state`
4. NAT Gateway — `if 'nat_id' in state`
5. Public Route Table — `if 'public_rt_id' in state`
6. Private Route Table — `if 'private_rt_id' in state`

The plan is just a list of dictionaries:
```python
[
    {"type": "vpc", "name": "dev-vpc", "action": "NO-OP", "id": "vpc-04e..."},
    {"type": "subnet", "name": "public-subnet-az1", "action": "NO-OP", "id": "subnet-0bd..."},
    {"type": "nat_gateway", "name": "dev-nat", "action": "CREATE", "id": None},
    ...
]
```

---

### SECTION 4: `display_plan()` — The PowerPoint Presentation 📺

```python
def display_plan(plan):
    creates = [p for p in plan if p['action'] == 'CREATE']
    noops = [p for p in plan if p['action'] == 'NO-OP']
    deletes = [p for p in plan if p['action'] == 'DELETE']
```

**List comprehensions** — Filters the plan into 3 buckets:
- ✅ "Things that are fine" pile (noops)
- ⚡ "Things to build" pile (creates)
- 💀 "Things to destroy" pile (deletes)

```python
    for item in plan:
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
```

- **`item['id'][:20]`** — Only shows first 20 chars (IDs are long and ugly)
- **`{rtype:20s}`** — Pads type name to 20 chars so columns align nicely

```python
    print(f"  {len(creates)} to create, {len(deletes)} to delete, {len(noops)} unchanged")

    if len(creates) == 0 and len(deletes) == 0:
        print("\n  ✅ Infrastructure matches desired state. Nothing to do.")
    else:
        print("\n  ⚡ Run 'python main.py apply' to execute this plan.")
```

- Nothing to do? → *"All good!"*
- Work needed? → *"Run apply to execute"*

---

### `run_planner()` — Peter's One-Button Remote 🎮

```python
def run_planner():
    config = load_config()        # 1. Read the whiteboard (YAML)
    plan = generate_plan(config)  # 2. Verify + compare
    display_plan(plan)            # 3. Show results
    return plan
```

One function that does everything. Press button, get plan.

---

## 🎬 The ENTIRE Flow As A Movie Scene

```
SCENE: Stewie's Lab, Morning

STEWIE: "Brian! Staff meeting. NOW."

    ┌─────────────────────────────────────────────┐
    │  Step 1: run_planner()                       │
    │  "Let's review operations."                  │
    └─────────────────────┬───────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │  Step 2: load_config()                       │
    │  *reads whiteboard*                          │
    │  "I WANT: VPC, 4 subnets, IGW, NAT, RTs"   │
    └─────────────────────┬───────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │  Step 3: load_state()                        │
    │  *opens photo album*                         │
    │  "Last I checked, we HAD all of these..."   │
    └─────────────────────┬───────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │  Step 4: sync_state_with_aws()               │
    │  *sends Brian to verify EACH resource*       │
    │                                              │
    │  Brian: "VPC? ✅ Here."                      │
    │  Brian: "Subnets? ✅✅✅✅ All here."          │
    │  Brian: "IGW? ✅ Here."                      │
    │  Brian: "NAT? ❌ GONE!"                      │
    │  Brian: "Route tables? ✅✅ Here."            │
    │                                              │
    │  *rips NAT photo out of album*              │
    │  *saves updated album*                       │
    └─────────────────────┬───────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │  Step 5: generate_plan()                     │
    │  *compares whiteboard vs verified album*     │
    │                                              │
    │  "VPC: want it, have it → NO-OP"           │
    │  "NAT: want it, DON'T have it → CREATE!"   │
    └─────────────────────┬───────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │  Step 6: display_plan()                      │
    │  *PowerPoint slides*                         │
    │                                              │
    │  "✅ VPC exists, ⚡ NAT needs creation"      │
    │  "1 to create, 0 to delete, 8 unchanged"   │
    └─────────────────────────────────────────────┘

STEWIE: "Victory shall be mine. Meeting adjourned."
```

---

## 🔑 How To Recreate This From Scratch (The Recipe)

If you ever need to write a planner from zero, follow this recipe:

```
STEP 1: Write verify functions (one per resource type)
        Recipe: try describe_*() → if list has items return True, else False
        Wrap in try/except → any error means "doesn't exist"

STEP 2: Write sync function
        Recipe: for each resource KEY in state:
                    call verify function
                    if verify says GONE → del state[key], append to drifts
                if drifts → save_state()
                return state

STEP 3: Write generate_plan function
        Recipe: call sync FIRST (verify reality)
                then for each resource in YAML:
                    if KEY in state → NO-OP
                    if KEY not in state → CREATE
                return plan (list of dicts)

STEP 4: Write display function
        Recipe: loop through plan list
                assign emoji per action type
                print formatted table
                show summary counts

STEP 5: Write run function (orchestrator)
        Recipe: load_config → generate_plan → display_plan → return plan
```

---

## The Family Guy Character Map (Full Reference)

| AWS Thing | Griffin Equivalent | Key in state.json |
|---|---|---|
| VPC | The Griffin house 🏠 | `vpc_id` |
| Public Subnet | Living room 🛋️ | `public-subnet-az1` |
| Private Subnet | Stewie's basement lab 🔬 | `private-subnet-az1` |
| Internet Gateway | Front door 🚪 | `igw_id` |
| NAT Gateway | Lois relaying messages 👩 | `nat_id` |
| Elastic IP | Lois's phone number 📱 | `nat_eip_alloc_id` |
| Public Route Table | Living room sign "go out front door" 🪧 | `public_rt_id` |
| Private Route Table | Basement sign "ask Lois" 🪧 | `private_rt_id` |
| Route Association | Tape holding sign to wall 📎 | `*_rt_assoc` |
| network.yaml | Stewie's evil whiteboard 📋 | — |
| state.json | Family photo album 📸 | — |
| Planner | Stewie's brain 🧠 | — |
| Drift | Something was destroyed but album wasn't updated 👻 | — |

---

## Bugs We Hit & Lessons Learned

### Bug 1: `AllocationID` vs `AllocationId`
**Error:** `ParamValidationError: Unknown parameter "AllocationID"`
**Lesson:** AWS boto3 is case-sensitive. It's `AllocationId` (lowercase d).
**Peter moment:** Like writing "LOIS" on the doorbell but she only responds to "Lois".

### Bug 2: `Values: vpc_id` instead of `Values: [vpc_id]`
**Error:** `Invalid type for parameter Filters[0].Values, valid types: list`
**Lesson:** AWS Filters always need a LIST, even for one value.
**Peter moment:** Amazon asks "what do you want?" and expects a shopping LIST, not just one word yelled at them.

### Bug 3: `state.get(key, '').startswith('subnet-')` on a boolean
**Error:** `AttributeError: 'bool' object has no attribute 'startswith'`
**Lesson:** State has mixed types (strings AND booleans). Check `isinstance(value, str)` first.
**Peter moment:** Peter trying to read a light switch like a book.

### Bug 4: Planner showing NO-OP after deleting resource
**Cause:** Old planner only checked state.json, never verified with AWS.
**Fix:** Added `sync_state_with_aws()` — verify against live AWS before planning.
**Peter moment:** Peter checking the photo album instead of looking out the window.

### Bug 5: `ModuleNotFoundError: No module named 'network'`
**Cause:** Kernel restart clears everything. Need to run `os.chdir(...)` first.
**Lesson:** After EVERY kernel restart, run cells from the top (setup → imports → work).
**Peter moment:** Peter waking up with amnesia. Needs his coffee (chdir) before doing anything.

### Bug 6: NAT Gateway showing as "exists" right after deletion
**Cause:** AWS keeps NAT in `"deleted"` state for ~1 hour before removing it.
**Fix:** Check `state in ('available', 'pending')` — anything else means it's gone.
**Peter moment:** Like a ghost haunting the house — technically "there" but not useful.

### Bug 7: `KeyError: 'private_rt_id'` in nat_gateway.py
**Cause:** Route tables step wasn't run before NAT gateway step.
**Fix:** Run scripts in order: VPC → Subnets → IGW → Route Tables → NAT.
**Peter moment:** Trying to put up a sign (route) before building the wall (route table).

---

## The Execution Order (ALWAYS follow this)

```
1. ✅ vpc.py              → Build the house
2. ✅ subnets.py          → Build the rooms
3. ✅ internet_gateway.py → Install the front door
4. ✅ route_tables.py     → Put up the signs
5. ✅ nat_gateway.py      → Hire Lois at the door
6. ✅ planner.py          → Stewie's brain (verify everything)
7. 🔲 main.py            → Peter's remote (CLI interface)
```

---

## How To Run The Planner

In your notebook (ALWAYS run setup cell first):

```python
# Cell 1 (REQUIRED after every kernel restart):
import os
os.chdir('/config/workspace/python/pythonawsproject')

# Cell 2:
from network.planner import run_planner
plan = run_planner()
```

### Expected output when everything exists:
```
🔍 Verifying resources against AWS...

  ✅ No drift — state matches AWS.

============================================================
  EXECUTION PLAN
============================================================
  ✅ vpc                  "dev-vpc" → EXISTS (vpc-04e3648d954b21c...)
  ✅ subnet               "public-subnet-az1" → EXISTS (subnet-0bd5069...)
  ✅ subnet               "public-subnet-az2" → EXISTS (subnet-00161c7...)
  ✅ subnet               "private-subnet-az1" → EXISTS (subnet-0c5bb1...)
  ✅ subnet               "private-subnet-az2" → EXISTS (subnet-05b1dd...)
  ✅ internet_gateway     "dev-igw" → EXISTS (igw-0927984aabe4aa1...)
  ✅ nat_gateway          "dev-nat" → EXISTS (nat-0081de96b9cc8f6...)
  ✅ route_table          "public-route-table" → EXISTS (rtb-02defa987...)
  ✅ route_table          "private-route-table" → EXISTS (rtb-069052ef...)
============================================================
  0 to create, 0 to delete, 9 unchanged
============================================================

  ✅ Infrastructure matches desired state. Nothing to do.
```

### Expected output when NAT Gateway is deleted:
```
🔍 Verifying resources against AWS...
  ⚠️  DRIFT: NAT nat-0081de96b9cc8f604 gone!

  📸 State synced! Removed 1 stale entries.

============================================================
  EXECUTION PLAN
============================================================
  ✅ vpc                  "dev-vpc" → EXISTS (vpc-04e3648d954b21c...)
  ...
  ⚡ nat_gateway          "dev-nat" → NEEDS CREATION
  ...
============================================================
  1 to create, 0 to delete, 8 unchanged
============================================================

  ⚡ Run 'python main.py apply' to execute this plan.
```

---

## Comparison: Your Planner vs Terraform

| Feature | Your Planner | Terraform |
|---------|-------------|-----------|
| Desired state file | network.yaml | .tf files |
| State tracking | state.json | terraform.tfstate |
| Drift detection | sync_state_with_aws() | terraform refresh |
| Plan generation | generate_plan() | terraform plan |
| Execution | (main.py apply — next step) | terraform apply |
| State locking | ❌ (future: DynamoDB) | ✅ DynamoDB |
| Multiple providers | ❌ (AWS only) | ✅ Multi-cloud |

---

## What's Next: main.py (Peter's Remote Control)

The planner SHOWS you what needs to happen. `main.py` will EXECUTE it:

```
$ python main.py plan     → shows the plan (what we just built)
$ python main.py apply    → actually creates/deletes resources
$ python main.py destroy  → tears everything down
```

---

*"It's not enough to BUILD the infrastructure, Brian. One must have the
INTELLIGENCE to VERIFY it."* — Stewie Griffin, probably

*End of guide. Go build something. 🧠🎬*
