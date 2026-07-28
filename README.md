# 🏗️ PythonAWSProject — Infrastructure as Code (From Scratch)

> A custom-built AWS Infrastructure as Code tool written in pure Python + boto3. No Terraform. No CloudFormation. Just Python, a YAML config, and brains.

*"Why would I use Terraform when I can build my own? That's what distinguishes us from the Megs of the world."* — Stewie 🧠

---

## 📖 What Is This?

A **plan-before-apply** infrastructure tool (like a mini-Terraform) that manages AWS networking resources through a declarative YAML configuration. It follows the same mental model as Terraform:

1. **Reads** a YAML config file → what you WANT (desired state)
2. **Verifies** against live AWS → what ACTUALLY exists (real state)
3. **Plans** the difference → what needs to CREATE / DELETE / stay
4. **Executes** the plan → builds or destroys resources in dependency order

No HCL to learn. No state locking wars. No mysterious provider bugs. Just Python talking directly to AWS via boto3.

---

## 📂 Project Structure

```
pythonawsproject/
│
├── main.py                    ← Root entry point (WIP)
├── config/
│   └── network.yaml           ← Desired state declaration (the master plan)
├── state/
│   └── state.json             ← Tracks created resource IDs (the photo album)
├── network/
│   ├── __init__.py            ← Package marker
│   ├── aws_client.py          ← boto3 singleton session + client factory
│   ├── state.py               ← Atomic load/save for state.json
│   ├── vpc.py                 ← Create + tag VPC
│   ├── subnets.py             ← Create 4 subnets (2 public, 2 private)
│   ├── internet_gateway.py    ← Create + attach Internet Gateway
│   ├── route_tables.py        ← Create route tables + subnet associations
│   ├── nat_gateway.py         ← Allocate EIP + create NAT + private routes
│   ├── planner.py             ← The brain — drift detection + plan generation
│   └── main.py                ← CLI command center (plan / apply / destroy)
├── understand_planner.md      ← Line-by-line learning guide (Family Guy style 🎬)
├── Blueprint.md               ← Architecture & design decisions
├── planner.md                 ← Planner module documentation
└── vpc.ipynb                  ← Jupyter notebook (development/testing sandbox)
```

---

## ⚙️ Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.12+ |
| **boto3** | AWS SDK for Python |
| **PyYAML** | YAML config parser |
| **AWS CLI** | Configured with valid credentials |
| **Region** | `ap-south-1` (Mumbai) |

---

## 🔧 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/pythonawsproject.git
cd pythonawsproject
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install boto3 pyyaml
```

### 4. Configure AWS credentials

```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=ap-south-1
```

### 5. Verify setup

```bash
aws sts get-caller-identity
```

---

## 🚀 Usage

### CLI Commands

```bash
cd pythonawsproject

# 🗺️ PLAN — Scout the battlefield (show what's needed)
python -m network.main plan

# 🚀 APPLY — Deploy! Build all missing resources in order
python -m network.main apply

# 💣 DESTROY — Retreat! Tear everything down (WIP)
python -m network.main destroy
```

### From Jupyter Notebook

```python
# Cell 1 (REQUIRED after every kernel restart):
import os
os.chdir('/path/to/pythonawsproject')

# Cell 2 — Run the planner:
from network.planner import run_planner
plan = run_planner()
```

> ⚠️ **After every kernel restart**, you must run the `os.chdir(...)` cell first. Python forgets its working directory — like Peter waking up with amnesia. ☕

---

## 🏗️ What It Builds

All resources are defined in `config/network.yaml`:

| # | Resource Type | Name | CIDR / Details | AZ |
|---|---------------|------|----------------|-----|
| 1 | VPC | `dev-vpc` | `10.0.0.0/16` | — |
| 2 | Public Subnet | `public-subnet-az1` | `10.0.1.0/24` | `ap-south-1a` |
| 3 | Public Subnet | `public-subnet-az2` | `10.0.2.0/24` | `ap-south-1b` |
| 4 | Private Subnet | `private-subnet-az1` | `10.0.3.0/24` | `ap-south-1a` |
| 5 | Private Subnet | `private-subnet-az2` | `10.0.4.0/24` | `ap-south-1b` |
| 6 | Internet Gateway | `dev-igw` | Attached to VPC | — |
| 7 | NAT Gateway | `dev-nat` | In `public-subnet-az1` | `ap-south-1a` |
| 8 | Route Table | `public-route-table` | `0.0.0.0/0` → IGW | — |
| 9 | Route Table | `private-route-table` | `0.0.0.0/0` → NAT | — |

### Network Architecture

```
                         ┌─── Internet ───┐
                         │                │
                    ┌────┴────┐           │
                    │   IGW   │           │
                    └────┬────┘           │
                         │                │
              ┌──────────┴──────────┐     │
              │      PUBLIC RT      │     │
              │  0.0.0.0/0 → IGW   │     │
              └──────────┬──────────┘     │
                         │                │
          ┌──────────────┼──────────────┐ │
          │              │              │ │
   ┌──────┴──────┐ ┌────┴──────┐       │ │
   │ public-az1  │ │ public-az2│       │ │
   │ 10.0.1.0/24 │ │10.0.2.0/24│       │ │
   └──────┬──────┘ └───────────┘       │ │
          │                             │ │
     ┌────┴────┐                        │ │
     │   NAT   │────────────────────────┘ │
     └────┬────┘                          │
          │                               │
   ┌──────┴───────────────┐               │
   │     PRIVATE RT       │               │
   │  0.0.0.0/0 → NAT    │               │
   └──────────┬───────────┘               │
              │                            │
   ┌──────────┼──────────────┐             │
   │          │              │             │
┌──┴────────┐ ┌┴───────────┐              │
│private-az1│ │private-az2 │              │
│10.0.3.0/24│ │10.0.4.0/24 │              │
└───────────┘ └────────────┘              │
                                          │
          ┌───────────────────────────────┘
          │   VPC: dev-vpc (10.0.0.0/16)
          └───────────────────────────────
```

---

## 🧠 Key Features

### 1. Drift Detection (Smart Planner)
The planner doesn't blindly trust `state.json`. It calls AWS `describe_*` APIs to **verify** every resource still exists before generating a plan. If someone manually deletes a NAT Gateway from the console, the planner catches it immediately.

```
🔍 Verifying resources against AWS...
  ⚠️  DRIFT: NAT nat-0081de96b9cc8f604 gone!
  📸 State synced! Removed 1 stale entries.
```

### 2. Idempotent Operations
Run `apply` 100 times — same result. It only creates what's **actually missing**. Each module checks state before creating, never duplicates resources.

### 3. Atomic State Management
State writes use a crash-safe pattern: write to `.tmp` file → `os.replace()` to final location. If the process crashes mid-write, state.json won't be corrupted.

### 4. Dependency-Safe Ordering
Resources are created and destroyed in the correct dependency order:

```
BUILD:    VPC → Subnets → IGW → Route Tables → NAT Gateway
DESTROY:  NAT Gateway → EIP → Route Tables → IGW → Subnets → VPC (reverse!)
```

### 5. Cascading State Cleanup
When a parent resource is gone, related entries are automatically cleaned:
- VPC gone → **entire state cleared** (everything depends on VPC)
- NAT gone → EIP allocation + private route entries removed
- Route table gone → all `_rt_assoc` entries removed

### 6. Config/Logic Separation
YAML defines **what** should exist. Python defines **how** to create it. Change the config, re-run apply — that's it.

---

## 🔍 How The Planner Works

The planner implements a **refresh-then-diff** workflow (like `terraform refresh` + `terraform plan`):

```
┌─────────────────────────────────────────────────────────────┐
│                    THE PLANNER PIPELINE                       │
│                                                              │
│   1. load_config()          → Read network.yaml (DESIRED)    │
│   2. load_state()           → Read state.json (LAST KNOWN)   │
│   3. sync_state_with_aws()  → Verify each resource via AWS   │
│      └── verify_vpc_exists()                                 │
│      └── verify_subnet_exists()                              │
│      └── verify_igw_exists()                                 │
│      └── verify_nat_exists()  (checks State field!)          │
│      └── verify_route_table_exists()                         │
│      └── Remove dead entries from state                      │
│   4. generate_plan()        → Compare YAML vs clean state    │
│      └── For each resource: in state? NO-OP : CREATE         │
│   5. display_plan()         → Pretty-print the plan          │
└─────────────────────────────────────────────────────────────┘
```

### The 3 Scenarios:

| Scenario | What It Means | Action |
|----------|---------------|--------|
| In YAML + In AWS | Resource exists and matches | **NO-OP** (skip) |
| In YAML + NOT in AWS | Resource is missing | **CREATE** |
| In state + NOT in YAML | Resource shouldn't exist | **DELETE** |

---

## 📦 Module Reference

### `network/aws_client.py` — The Phone to AWS 📞

| Function | Purpose |
|----------|---------|
| `get_session(region_name="ap-south-1")` | Creates/returns a singleton boto3 Session |
| `get_client(service_name, region_name="ap-south-1")` | Returns a boto3 client for any AWS service |

Uses a **singleton pattern** — one session shared across all modules. Avoids creating a new connection for every API call.

---

### `network/state.py` — The Photo Album 📸

| Function | Purpose |
|----------|---------|
| `load_state()` | Reads `state/state.json` → returns Python dict |
| `save_state(state)` | Writes dict → `state/state.json` (crash-safe via `.tmp` + `os.replace`) |

**Crash-safe write pattern:**
```python
# Write to temp file first
with open(STATE_PATH + '.tmp', 'w') as f:
    json.dump(state, f)
# Atomic rename — either fully succeeds or fully fails
os.replace(STATE_PATH + '.tmp', STATE_PATH)
```

---

### `network/vpc.py` — Build the House 🏠

| Function | Purpose |
|----------|---------|
| `create_vpc(config)` | Creates VPC if not in state, tags it, saves to state |

**AWS APIs:** `create_vpc`, `get_waiter('vpc_available')`, `create_tags`  
**State keys written:** `vpc_id`, `vpc_name`

---

### `network/subnets.py` — Build the Rooms 🛋️

| Function | Purpose |
|----------|---------|
| `create_subnet(config)` | Creates all 4 subnets (2 public + 2 private), enables auto-assign public IP on public subnets |

**AWS APIs:** `create_subnet`, `create_tags`, `modify_subnet_attribute`  
**State keys written:** `public-subnet-az1`, `public-subnet-az2`, `private-subnet-az1`, `private-subnet-az2`

---

### `network/internet_gateway.py` — Install the Front Door 🚪

| Function | Purpose |
|----------|---------|
| `creating_igw(config)` | Creates IGW, attaches to VPC, tags it |

**AWS APIs:** `create_internet_gateway`, `attach_internet_gateway`, `create_tags`  
**State keys written:** `igw_id`

---

### `network/route_tables.py` — Put Up Road Signs 🪧

| Function | Purpose |
|----------|---------|
| `create_route_tables(config)` | Creates public + private RTs, adds IGW route to public RT, associates subnets |

**AWS APIs:** `create_route_table`, `create_route`, `create_tags`, `associate_route_table`  
**State keys written:** `public_rt_id`, `private_rt_id`, `{subnet_name}_rt_assoc` (x4)

---

### `network/nat_gateway.py` — Deploy the Secure Messenger 👩

| Function | Purpose |
|----------|---------|
| `create_nat_gateway(config)` | Allocates EIP, creates NAT in public subnet, waits for availability, adds route to private RT |

**AWS APIs:** `allocate_address`, `create_nat_gateway`, `get_waiter('nat_gateway_available')`, `create_tags`, `create_route`  
**State keys written:** `nat_eip_alloc_id`, `nat_id`, `private_nat_route`

---

### `network/planner.py` — Stewie's Brain 🧠

| Function | Purpose |
|----------|---------|
| `load_config()` | Reads `config/network.yaml` → Python dict |
| `verify_vpc_exists(ec2, vpc_id)` | Checks if VPC exists in AWS |
| `verify_subnet_exists(ec2, subnet_id)` | Checks if subnet exists in AWS |
| `verify_igw_exists(ec2, igw_id)` | Checks if IGW exists in AWS |
| `verify_nat_exists(ec2, nat_id)` | Checks if NAT exists AND is `available`/`pending` |
| `verify_route_table_exists(ec2, rt_id)` | Checks if route table exists in AWS |
| `sync_state_with_aws(state, ec2)` | Verifies all resources against AWS, removes dead entries |
| `generate_plan(config)` | Syncs state, then compares YAML vs state → returns plan |
| `display_plan(plan)` | Pretty-prints plan with ✅/⚡/💀 symbols |
| `run_planner()` | Entry point: load_config → generate_plan → display_plan |

---

### `network/main.py` — Peter's Remote Control 🎮

| Function | Purpose |
|----------|---------|
| `command_plan(config)` | Runs planner, shows execution plan |
| `command_apply(config)` | Runs planner, builds all CREATE items in dependency order |
| `command_destroy(config)` | Destroys everything in reverse dependency order (WIP) |

---

## 🗄️ State File Reference (`state/state.json`)

All possible keys tracked in state:

| Key | Value Format | Written By |
|-----|-------------|------------|
| `vpc_id` | `vpc-xxx` | `vpc.py` |
| `vpc_name` | `"dev-vpc"` | `vpc.py` |
| `public-subnet-az1` | `subnet-xxx` | `subnets.py` |
| `public-subnet-az2` | `subnet-xxx` | `subnets.py` |
| `private-subnet-az1` | `subnet-xxx` | `subnets.py` |
| `private-subnet-az2` | `subnet-xxx` | `subnets.py` |
| `igw_id` | `igw-xxx` | `internet_gateway.py` |
| `public_rt_id` | `rtb-xxx` | `route_tables.py` |
| `private_rt_id` | `rtb-xxx` | `route_tables.py` |
| `public-subnet-az1_rt_assoc` | `rtbassoc-xxx` | `route_tables.py` |
| `public-subnet-az2_rt_assoc` | `rtbassoc-xxx` | `route_tables.py` |
| `private-subnet-az1_rt_assoc` | `rtbassoc-xxx` | `route_tables.py` |
| `private-subnet-az2_rt_assoc` | `rtbassoc-xxx` | `route_tables.py` |
| `nat_eip_alloc_id` | `eipalloc-xxx` | `nat_gateway.py` |
| `nat_id` | `nat-xxx` | `nat_gateway.py` |
| `private_nat_route` | `true` (boolean) | `nat_gateway.py` |

> **Note:** `state/state.json` is in `.gitignore` — it's environment-specific, like `terraform.tfstate`.

---

## 📺 Example Output

### When everything exists (no drift):

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

### When drift is detected (NAT deleted from console):

```
🔍 Verifying resources against AWS...
  ⚠️  DRIFT: NAT nat-0081de96b9cc8f604 gone!

  📸 State synced! Removed 1 stale entries.

============================================================
  EXECUTION PLAN
============================================================
  ✅ vpc                  "dev-vpc" → EXISTS (vpc-04e3648d954b21c...)
  ✅ subnet               "public-subnet-az1" → EXISTS (subnet-0bd5069...)
  ✅ subnet               "public-subnet-az2" → EXISTS (subnet-00161c7...)
  ✅ subnet               "private-subnet-az1" → EXISTS (subnet-0c5bb1...)
  ✅ subnet               "private-subnet-az2" → EXISTS (subnet-05b1dd...)
  ✅ internet_gateway     "dev-igw" → EXISTS (igw-0927984aabe4aa1...)
  ⚡ nat_gateway          "dev-nat" → NEEDS CREATION
  ✅ route_table          "public-route-table" → EXISTS (rtb-02defa987...)
  ✅ route_table          "private-route-table" → EXISTS (rtb-069052ef...)
============================================================
  1 to create, 0 to delete, 8 unchanged
============================================================

  ⚡ Run 'python main.py apply' to execute this plan.
```

---

## 🏛️ Architecture Comparison: This Project vs Terraform

| Feature | PythonAWSProject | Terraform |
|---------|-----------------|-----------|
| Config language | YAML | HCL |
| Desired state file | `config/network.yaml` | `.tf` files |
| State tracking | `state/state.json` | `terraform.tfstate` |
| Drift detection | `sync_state_with_aws()` | `terraform refresh` |
| Plan generation | `generate_plan()` | `terraform plan` |
| Execution | `command_apply()` | `terraform apply` |
| Teardown | `command_destroy()` | `terraform destroy` |
| State locking | ❌ (future: DynamoDB) | ✅ DynamoDB |
| Multiple providers | ❌ (AWS only) | ✅ Multi-cloud |
| Modules/reuse | ❌ (single config) | ✅ Modules |
| Language | Python + boto3 | Go (core) + HCL |

---

## 🏷️ Resource Tagging

All resources are tagged with:

```yaml
ManagedBy: "PythonIAC"
Layer: "Networking"
Environment: "Dev"
```

These tags help identify resources created by this tool in the AWS console.

---

## 🧩 Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| **Singleton** | `aws_client.py` — one boto3 session shared across all modules | Avoid creating new connections per API call |
| **Idempotency** | Every create module checks state first | Never duplicate resources |
| **Crash-safe writes** | `state.py` — write `.tmp` → `os.replace()` | Prevent corrupted state on crash |
| **Refresh-then-diff** | `planner.py` — verify AWS before planning | Catch drift from manual changes |
| **Cascading cleanup** | `sync_state_with_aws()` — parent gone = children removed | Keep state consistent |
| **Config/logic separation** | YAML = what, Python = how | Change infra without changing code |
| **Communication via state** | Modules share data through `state.json`, not imports | Loose coupling between modules |
| **Dependency ordering** | `command_apply()` builds in DAG order | Prevent AWS DependencyViolation errors |

---

## 💰 Cost Awareness

| Resource | Monthly Cost | Notes |
|----------|-------------|-------|
| VPC | **Free** | No charge for VPC itself |
| Subnets | **Free** | No charge for subnets |
| Internet Gateway | **Free** | No charge (data transfer costs apply) |
| Route Tables | **Free** | No charge |
| **NAT Gateway** | **~$32/month** | ⚠️ $0.045/hr + data processing charges |
| **Elastic IP (unused)** | **~$3.60/month** | ⚠️ Charged when NOT attached to running instance |

> ⚠️ **Always run `destroy` when not actively using the infrastructure!** NAT Gateway alone costs ~$32/month sitting idle.

---

## 🛠️ Development Status

- [x] AWS Client Factory (`aws_client.py`)
- [x] Atomic State Management (`state.py`)
- [x] VPC Creation + Tagging (`vpc.py`)
- [x] Subnet Creation — 2 public + 2 private (`subnets.py`)
- [x] Internet Gateway — Create + Attach (`internet_gateway.py`)
- [x] Route Tables + Associations (`route_tables.py`)
- [x] NAT Gateway + EIP + Private Routes (`nat_gateway.py`)
- [x] Smart Planner with Drift Detection (`planner.py`)
- [x] CLI — `plan` command
- [x] CLI — `apply` command (dependency-ordered)
- [ ] CLI — `destroy` command (template ready, implementation in progress)
- [ ] Root `main.py` entry point
- [ ] Security Groups module
- [ ] EC2 Instance module
- [ ] S3 remote state backend
- [ ] DynamoDB state locking

---

## 🚧 Known Limitations

1. **Single region only** — hardcoded to `ap-south-1` (Mumbai)
2. **No remote state** — state.json is local (no team collaboration support yet)
3. **No state locking** — concurrent runs could corrupt state
4. **Destroy is WIP** — template exists but full implementation pending
5. **No update/modify support** — can only CREATE or detect drift, cannot reconcile attribute changes
6. **Bare `except:` clauses** — planner catches all exceptions (should catch `ClientError` specifically)

---

## 🗺️ Future Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Complete `command_destroy()` with reverse-order teardown | 🔨 In Progress |
| 2 | Security Groups module | 📋 Planned |
| 3 | EC2 Instance module (consume network layer) | 📋 Planned |
| 4 | S3 remote state backend | 📋 Planned |
| 5 | DynamoDB state locking (prevent concurrent access) | 📋 Planned |
| 6 | GitHub Actions CI/CD (GitOps workflow) | 📋 Planned |
| 7 | Multi-region support | 📋 Planned |

---

## 📚 Learning Resources

This project includes extensive documentation for learning:

| File | What's In It |
|------|-------------|
| `understand_planner.md` | 800+ line guide explaining planner.py line-by-line with Family Guy analogies |
| `Blueprint.md` | Architecture decisions, scope, design rationale |
| `planner.md` | Planner module docs with character mapping and cost awareness |

---

## 🔒 What's NOT in Git

Per `.gitignore`:

```
__pycache__/          # Python bytecode cache
*.pyc / *.pyo         # Compiled Python files
.env                  # AWS credentials / secrets
state/                # State files (environment-specific)
*.ipynb               # Jupyter notebooks (dev tooling)
2026-*.md             # Session notes (personal dev logs)
```

---

## 👤 Author

Built from scratch as a learning project to understand:
- AWS VPC networking from first principles
- Infrastructure as Code design patterns
- Plan-before-apply architecture (Terraform internals)
- Python/boto3 for cloud automation

No frameworks. No abstractions. No copying from tutorials. Just reading AWS docs and building.

---

*"It's not enough to BUILD the infrastructure, Brian. One must have the INTELLIGENCE to VERIFY it."* — Stewie Griffin 🧠🎬
