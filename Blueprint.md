# AWS Network Layer — Project Blueprint

## 1. Goal

Build the network layer (VPC, subnets, Internet Gateway, route tables, NAT
gateway) as a custom Python/boto3 tool instead of reaching for Terraform,
CDK, or Pulumi — config-driven and idempotent, with a plan-before-apply
workflow. This becomes the foundation that a later compute/infra layer
(EC2, ALB, ASG) builds on top of.

## 2. Scope

**In scope:** VPC, public/private subnets, Internet Gateway, route tables,
NAT Gateway, Elastic IP.

**Out of scope (for now):** EC2/compute, security groups, IAM, ECS/EKS —
these belong to the compute/infra layer that comes after this one.

## 3. Architecture

```
pythonawsproject/
├── config/
│   └── network.yaml        # desired state: CIDR, AZs, subnet types, NAT/IGW flags
├── network/
│   ├── __init__.py
│   ├── aws_client.py        # boto3 session/client factory (region, profile)
│   ├── state.py             # read/write local state.json (logical name -> resource id)
│   ├── vpc.py                # create/find VPC
│   ├── subnets.py             # create public/private subnets across AZs
│   ├── internet_gateway.py     # create/attach IGW
│   ├── route_tables.py          # create route tables, associate subnets
│   ├── nat_gateway.py             # allocate EIP, create NAT GW in public subnet
│   └── planner.py                  # diff engine: desired (yaml) vs actual (describe_*) -> plan
├── state/
│   └── state.json            # generated — logical-name-to-AWS-id map, gitignored
└── main.py                    # CLI entrypoint: plan / apply / destroy
```

## 4. Design Decisions & Why

**Idempotency via local state file (rather than tags-only)**

Relying purely on AWS tags to discover existing resources introduces
latency (heavy API scanning) and runtime risks due to eventual consistency
in the AWS control plane. A structured `state.json` acts as our
deterministic "source of truth" for what our tool created. It explicitly
maps a stable logical key (`public_subnet_az1`) to its physical AWS ID
(`subnet-0123456789abcdef0`), preventing orphaned resources if AWS tags
are accidentally modified or stripped by external processes.

**Hand-rolled plan-before-apply engine**

Building a graph-aware diffing engine provides a first-principles
understanding of infrastructure dependency management. It forces the
developer to handle the implicit DAG inherent to cloud infrastructure —
ensuring a subnet isn't created before its parent VPC exists, and a route
table isn't deleted while still associated with subnets. It's also a
stronger portfolio differentiator than plain YAML scripting.

**Environment assumptions**

To limit initial complexity, the engine targets a single AWS account in
the `ap-south-1` (Mumbai) region. Multi-region support or cross-account
assume-role logic is intentionally deferred to avoid configuration
bloat in MVP v1.

## 5. Build Order / Milestones

1. **Foundations** (`aws_client.py` & `state.py`) — establish safe boto3
   connections; build atomic file read/write operations for `state.json`
   to prevent state corruption.
2. **The Core Fabric** (`vpc.py` & `subnets.py`) — implement basic VPC and
   subnet creation, storing physical IDs into state immediately upon
   successful allocation.
3. **Edge Routing** (`internet_gateway.py`) — provision the IGW and attach
   it to the tracked VPC ID.
4. **Explicit Routing** (`route_tables.py`) — create public and private
   route tables; stitch subnets to their respective route tables.
5. **Outbound Network Translation** (`nat_gateway.py`) — allocate an EIP,
   spin up a NAT Gateway in a public subnet, and program the private
   route tables to target it for external traffic.
6. **The Brain** (`planner.py`) — write the diffing engine that reads
   `network.yaml` and `state.json`, producing an execution manifest of
   Create/Update/Delete/NoOp actions.
7. **Interface CLI** (`main.py`) — wrap everything in a CLI (argparse or
   click) that cleanly displays the plan before execution is permitted.

## 6. Future Direction

- **Downstream consumption:** expose `state.json` via a clean read-only
  Python utility so a separate `compute_layer/` script can look up
  subnet IDs dynamically when launching EC2 instances or load balancers.
- **State externalization:** move state storage from local `state.json`
  to an S3 bucket with DynamoDB state locking, to mimic production-grade
  multi-user concurrency control.
- **CI/CD GitOps:** run `python main.py plan` in GitHub Actions on every
  pull request to check for architectural drift, and `python main.py apply`
  automatically on merge to `main`.

## 7. Open Questions & Resolutions

**Q: Multi-AZ strategy vs. cost?**
Resolution: configure exactly 2 Availability Zones (`ap-south-1a` and
`ap-south-1b`) to exercise multi-AZ logic without paying for a third zone.

**Q: Single NAT Gateway vs. high availability (NAT per AZ)?**
Resolution: make the topology configurable in `network.yaml`
(`nat_strategy: single` vs `nat_strategy: multi_az`). Default to a single
NAT Gateway in Public Subnet A for MVP to keep costs minimal, while
ensuring the engine can scale to multi-NAT without structural changes.

**Q: Tagging convention?**
Resolution: every resource provisioned by the engine receives a mandatory
tag map:

```yaml
Tags:
  ManagedBy: "CustomPythonIaC"
  Layer: "Networking"
  Environment: "Dev"
```

**Q: How do we handle partial failures?**
Resolution: if a provisioning step fails halfway through (e.g. a timeout
creating a NAT Gateway), the engine must immediately flush all
successfully created resources up to that point out to `state.json`
before crashing. This guarantees that a subsequent `apply` or `destroy`
command knows exactly what infrastructure was orphaned.
