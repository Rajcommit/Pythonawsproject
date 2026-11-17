import boto3
import os

_session = None

##Read the toggle for once
USE_LOCALSTACK = os.getenv("USE_LOCALSTACK") == "1"
LOCALSTACK_URL = os.getenv("LOCALSTACK_URL", "http://192.168.1.30:4566")

def get_session(region_name="ap-south-1"):
    global _session
    if _session is None:
      if USE_LOCALSTACK:
        # Fake credentials - floci anyways ignores the creds, but make sure to use it in case of boto3
        _session = boto3.Session(
          region_name=region_name,
          aws_access_key_id="test",
          aws_secret_access_key="test"
          )
      else:
        _session = boto3.Session(region_name=region_name)
    return _session

def get_client(service_name, region_name="ap-south-1"):
  if USE_LOCALSTACK:
    #Dial localstack floci in tead of calling AWs
    return get_session(region_name).client(
      service_name,
      endpoint_url=LOCALSTACK_URL
    )
  else:
    return get_session(region_name).client(service_name)
