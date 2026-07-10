####Creating subnet in the crated VPC####
## What subnet.py must do:
#1> Reading the VPC ID from state.json - subnet live INSIDE a VPC, so we need the
#2> Looping through all four subnet from the YML (2 Private +2 public)
# 3> First check if subnets are there if not create
#4> We will be handling the public flag as if public subnet need mappubliconlaunch = true.


from network.aws_client import get_client
from network.state  import load_state, save_state


def create
