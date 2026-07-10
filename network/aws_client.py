import boto3

_session = None

def get_session(region_name="ap-south-1"):
    global _session
    if _session is None:
      _session = boto3.Session(region_name=region_name)
    return _session

def get_client(service_name, region_name="ap-south-1"):
    return get_session(region_name).client(service_name)
    
