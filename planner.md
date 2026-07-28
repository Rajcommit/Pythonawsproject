# 🧠 The Planner — Stewie's Evil Whiteboard

## A Family Guy Guide to Understanding `planner.py`

---

## What IS the Planner?

Remember how Stewie has that whiteboard in his room where he draws his evil plans? He writes:

> "Step 1: Build mind-control device. Step 2: Enslave humanity. Step 3: Cancel Meg."

Then he looks around his lab and checks: *"Okay, the mind-control device is built... humanity is NOT enslaved yet... and Meg is unfortunately still here."*

**That's the planner.** It compares:
- 📋 **What you WANT** (network.yaml) → Stewie's whiteboard
- 🏠 **What actually EXISTS** (AWS / state.json) → reality

And produces a **plan**:
```
VPC:            ✅ EXISTS — no action needed
Subnets:        ✅ EXISTS — no action needed  
IGW:            ✅ EXISTS — no action needed
NAT Gateway:    ✅ EXISTS — no action needed
Security Group: ❌ MISSING — need to CREATE
```

---

## Why Do We Need It?

### 🎬 Scene: Peter Destroys Things Without Checking

Imagine Peter decides to "fix" the house. He doesn't check what's already built. He just starts:

> *"I'm gonna build a door!"*
> 
> "Peter, there's already a door—"
> 
> *"I SAID I'M BUILDING A DOOR!"*

Now you have two front doors. One leads to the street. The other leads directly into Quagmire's bedroom. Giggity.

**Without a planner**, your code is like Peter — it just DOES things without checking if they're needed. You'd end up with:
- Duplicate VPCs
- Two NAT Gateways (that's $64/month for no reason)
- Routes that conflict

---

### 🎬 Scene: Stewie Plans Everything

Stewie would NEVER just start building. He:
1. Looks at the blueprint (network.yaml)
2. Looks at what exists (state/AWS)
3. Makes a **plan** (what to create, what to skip, what to destroy)
4. Only THEN executes

**That's professional infrastructure management.** That's what Terraform does. That's what YOUR tool will do.

---

## The Interview Answer 🎤

> **Interviewer:** "Why did you build a planner?"
>
> **You:** "I implemented a plan-before-apply workflow — similar to Terraform's `terraform plan`. The planner acts as a diff engine. It reads the desired state from a YAML config file, compares it against both the local state file AND the actual AWS resources via describe API calls, and generates an execution manifest of CREATE, UPDATE, DELETE, or NO-OP actions. This gives the operator visibility into what WILL change before anything is actually mutated in the AWS account. It prevents duplicate resource creation, catches configuration drift, and makes the tool safe for production use."
>
> **Interviewer:** *impressed Pikachu face*

---

## What Does The Planner Actually Do? (The 3 Checks)

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

## The Workflow (How It'll Be Used)

When everything is already built:
```
$ python main.py plan
┌─────────────────────────────────────────────┐
│  EXECUTION PLAN                             │
│                                             │
│  vpc "dev-vpc"          → EXISTS (no-op)    │
│  subnet "public-az1"    → EXISTS (no-op)    │
│  subnet "public-az2"    → EXISTS (no-op)    │
│  subnet "private-az1"   → EXISTS (no-op)    │
│  subnet "private-az2"   → EXISTS (no-op)    │
│  igw "dev-igw"          → EXISTS (no-op)    │
│  nat "dev-nat"          → EXISTS (no-op)    │
│                                             │
│  0 to create, 0 to delete, 7 unchanged     │
└─────────────────────────────────────────────┘
Nothing to do. Infrastructure matches desired state. ✅
```

When you ADD something new to network.yaml (like a new subnet):
```
$ python main.py plan
┌─────────────────────────────────────────────┐
│  EXECUTION PLAN                             │
│                                             │
│  vpc "dev-vpc"          → EXISTS (no-op)    │
│  subnet "public-az1"    → EXISTS (no-op)    │
│  subnet "dmz-az1"       → CREATE ⚡         │  ← NEW!
│  ...                                        │
│                                             │
│  1 to create, 0 to delete, 7 unchanged     │
└─────────────────────────────────────────────┘
Run 'python main.py apply' to execute.
```

---

## Architecture of the Planner

```
planner.py
│
├── generate_plan(config)
│       │
│       ├── Load network.yaml (desired state)
│       ├── Load state.json (known state)
│       ├── Call AWS describe_* APIs (actual state)
│       │
│       └── For each resource type:
│               Compare desired vs actual
│               → CREATE / NO-OP / DELETE
│
└── display_plan(plan)
        └── Pretty-print the actions table
```

---

## The Family Guy Character Map (Full Project)

| AWS Thing | Griffin Equivalent |
|---|---|
| **VPC** | The Griffin house 🏠 |
| **Public Subnet** | The living room (has windows to the street) 🛋️ |
| **Private Subnet** | Stewie's secret basement lab (NO windows) 🔬 |
| **Internet Gateway (IGW)** | The front door 🚪 |
| **NAT Gateway** | Lois standing at the front door, relaying messages 👩 |
| **Route Table** | Signs on the walls telling people where to go 🪧 |
| **Elastic IP** | Lois's phone number that the pizza guy calls back on 📱 |
| **Planner** | Stewie's evil whiteboard — checks plan vs reality 🧠 |
| **state.json** | The family photo album — proof of what was built 📸 |
| **network.yaml** | Stewie's master plan on the whiteboard 📋 |

---

## The Full Network Flow (What We've Built So Far)

```
STEWIE (Private Subnet)
    "I need plutonium from the internet!"
         │
         ▼
   🪧 Sign on wall says: "Go ask Lois"     ← PRIVATE ROUTE TABLE
         │
         ▼
   👩 LOIS (NAT Gateway, lives in Living Room)
    "Fine, I'll order it"
         │
         ▼
   🚪 FRONT DOOR (Internet Gateway)
         │
         ▼
   🌍 INTERNET (Amazon delivers plutonium)
         │
         ▼
   👩 LOIS receives it, brings it downstairs
         │
         ▼
   STEWIE gets his plutonium 😈
```

---

## The Complete Architecture Diagram

```
INTERNET
    │
    ▼
┌─────────┐
│   IGW   │  ← Front door
└────┬────┘
     │
     ├──────────────────────────────┐
     ▼                              ▼
┌──────────┐                 ┌──────────┐
│PUBLIC RT  │                 │ NAT GW   │ (Lois in the living room)
│0.0.0.0→IGW│                 │ EIP: 📱  │
└─────┬────┘                 └────┬─────┘
      │                           │
      ▼                           ▼
┌───────────┐              ┌──────────┐
│Public      │              │PRIVATE RT │
│Subnets     │              │0.0.0.0→NAT│ ← "Ask Lois" sign
│(az1, az2)  │              └─────┬────┘
└───────────┘                     │
                                  ▼
                           ┌───────────┐
                           │Private     │
                           │Subnets     │ ← Stewie's lab
                           │(az1, az2)  │
                           └───────────┘
```

---

## The NAT Gateway Lesson (What We Learned The Hard Way)

### Why the KeyError happened:

You built Lois (NAT Gateway) but forgot to put up the fridge (route table).

Your code said:
```python
private_rt_id = state['private_rt_id']   # "Where's the fridge?!"
```

Python: **"WHAT FRIDGE?! There IS no fridge!"** 💥 KeyError

### The fix:
Run `route_tables.py` BEFORE `nat_gateway.py`. The order matters:

```
1. ✅ Build the house          (vpc.py)
2. ✅ Build the rooms          (subnets.py)  
3. ✅ Install the front door   (internet_gateway.py)
4. ✅ Put up the fridge/signs  (route_tables.py)
5. ✅ Hire Lois for the door   (nat_gateway.py)
6. 🔲 Stewie's whiteboard     (planner.py)       ← NEXT
7. 🔲 Peter's remote control  (main.py)          ← AFTER THAT
```

---

## Key Lessons For Interviews

### 1. Idempotency
"Every function checks state BEFORE creating. If it exists, skip. If not, create and save."
— Like Stewie checking the whiteboard before building anything.

### 2. State Management
"We use an atomic write pattern (write to .tmp, then os.replace) to prevent state corruption on crashes."
— Because Peter WILL trip over the power cord mid-execution.

### 3. Plan-Before-Apply
"The planner shows you what WILL happen before it happens. No surprises."
— Stewie shows the plan on the whiteboard. Doesn't just randomly start building lasers.

### 4. NAT Gateway vs IGW
"IGW gives public subnets two-way internet access. NAT Gateway gives private subnets outbound-only access — the outside world can't reach in."
— Peter can answer the front door (public). Stewie can ORDER things from the basement but nobody can FIND his lab (private).

### 5. Why NAT doesn't need attach()
"NAT Gateway is placed IN a subnet (which is already in the VPC). IGW is a VPC-level resource that must be explicitly attached."
— Lois just stands in the living room (she's already in the house). The front door needs to be bolted onto the house.

---

## Summary Table: Without Planner vs With Planner

| Without Planner | With Planner |
|----------------|--------------|
| Peter: "I'M BUILDING A DOOR!" *crashes through existing door* | Stewie: "I shall EXAMINE the premises first..." |
| Duplicates, wasted money, chaos | Clean, intentional, idempotent |
| `terraform yolo` | `terraform plan` |
| Cleveland's house falling off the cliff AGAIN | Stewie's perfectly executed world domination |

---

## Cost Awareness

| Resource | Monthly Cost | Peter Analogy |
|----------|-------------|---------------|
| NAT Gateway | ~$32/month + data | Lois's salary for standing at the door |
| Elastic IP (unused) | ~$3.60/month | Paying for a phone line nobody uses |
| VPC, Subnets, Route Tables, IGW | FREE | The house structure costs nothing |

**Always destroy what you don't need. That's why we save everything to state — so a destroy function can clean it all up.**

---

## What's Next: Building planner.py

The planner will:
1. Read `network.yaml` (what we want)
2. Read `state.json` (what we've built)
3. Optionally call AWS `describe_*` APIs (verify reality)
4. For each resource: compare and decide CREATE / NO-OP / DELETE
5. Print a nice table showing the plan

*"It's not enough to BUILD the infrastructure, Brian. One must have the INTELLIGENCE to VERIFY it."* — Stewie, probably

---

*Last updated: July 20, 2026*
*Project: pythonawsproject*
*Status: Network layer COMPLETE ✅ | Planner: IN PROGRESS 🔲*
