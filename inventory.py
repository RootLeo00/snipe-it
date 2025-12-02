import boto3
import requests
import json
from botocore.exceptions import ClientError
from time import sleep
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# ==============================================================================
# 1. CONFIGURATION (MANDATORY)
# ==============================================================================

# Snipe-IT API Settings
SNIPEIT_API_URL = os.getenv("APP_URL", "https://your-snipeit-domain.com") + "/api/v1/hardware"
SNIPEIT_API_KEY = os.getenv("APP_KEY", "YourSnipeITApiTokenHere")
SNIPEIT_HEADERS = {
    'Authorization': f'Bearer {SNIPEIT_API_KEY}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# AWS Account Settings
# Use AWS Profile names configured in your ~/.aws/credentials file.
AWS_ACCOUNTS = [
    {'name': 'Account 1 - Internal', 'profile_name': 'profile1', 'default_region': 'eu-south-1'},
    {'name': 'Account 2 - Customers', 'profile_name': 'profile2', 'default_region': 'eu-south-1'},
]

# Snipe-IT IDs for Categories, Models, and Statuses
# You MUST retrieve these numerical IDs from your Snipe-IT Admin interface.
# The script assumes you have an Asset Model set up for AWS EC2 instances.
DEFAULT_CATEGORY_ID = 2  # Cloud Infrastructure
DEFAULT_MODEL_ID = 1     # EC2 Instance
DEFAULT_STATUS_ID = 2    # Ready to Deploy

# ==============================================================================
# 2. CUSTOM FIELD MAPPING (MANDATORY)
# ==============================================================================

# This dictionary maps the fields retrieved from AWS (Keys) to the specific
# Custom Field ID in Snipe-IT (Values).
# You MUST replace the placeholder numbers (e.g., 999) with the actual ID
# of your custom fields in Snipe-IT.
CUSTOM_FIELD_MAP = {
    'instance_type': 3,
    'description': 4,
    'private_ip': 13,
    'public_ip': 14,
    'platform': 7,
    'vpc_id': 8,
    'dns_name': 9,
    'mac_address': 1,
    'vendor_support_end': 15,
    'criticity': 16,
    'asset_owner': 12,
    'aws_region': 17,
    'aws_account': 18,
    'availability_zone': 19,
    'subnet_id': 20,
    'security_groups': 21,
    'instance_state': 22,
    'launch_time': 23,
    'ami_id': 24,
    'architecture': 25,
    'root_device_type': 26,
    'virtualization_type': 27,
}

# ==============================================================================
# 3. CORE FUNCTIONS
# ==============================================================================

def get_tag_value(tags, key):
    """Helper function to safely extract a value from the AWS Tags list."""
    if tags:
        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']
    return None

def process_aws_instance(instance, account_name, region_name):
    """Extracts and formats key data points from a single AWS EC2 instance."""
    
    instance_id = instance.get('InstanceId')
    asset_tag = instance_id
    tags = instance.get('Tags', [])
    instance_name = get_tag_value(tags, 'Name') or asset_tag
    
    # Determine OS platform
    platform_details = instance.get('PlatformDetails', 'Linux/UNIX')
    
    # Get launch time
    launch_time = instance.get('LaunchTime').strftime('%Y-%m-%d') if instance.get('LaunchTime') else None
    
    # Get security groups
    security_groups = ', '.join([sg.get('GroupId', '') for sg in instance.get('SecurityGroups', [])])
    
    # Get network interface details
    network_interfaces = instance.get('NetworkInterfaces', [])
    mac_address = network_interfaces[0].get('MacAddress', 'N/A') if network_interfaces else 'N/A'
    
    # Map AWS data to Snipe-IT structure - CORRECT FORMAT
    snipeit_payload = {
        'asset_tag': asset_tag,
        'serial': asset_tag,
        'name': instance_name,
        'status_id': DEFAULT_STATUS_ID,
        'model_id': DEFAULT_MODEL_ID,
        'purchase_date': launch_time,
        'notes': f"AWS Account: {account_name}, Region: {region_name}",
        
        # Custom Fields using the _snipeit_fieldname_ID format
        '_snipeit_instance_type_3': instance.get('InstanceType', 'N/A'),
        '_snipeit_description_4': get_tag_value(tags, 'Description') or 'No description',
        '_snipeit_private_ip_address_13': instance.get('PrivateIpAddress', 'N/A'),
        '_snipeit_public_ip_address_14': instance.get('PublicIpAddress', 'N/A'),
        '_snipeit_platform_7': platform_details,
        '_snipeit_vpc_id_8': instance.get('VpcId', 'N/A'),
        '_snipeit_dns_name_9': instance.get('PrivateDnsName', 'N/A'),
        '_snipeit_mac_address_1': mac_address,
        '_snipeit_vendor_support_end_date_15': get_tag_value(tags, 'SupportEnd') or 'N/A',
        '_snipeit_criticality_16': get_tag_value(tags, 'Criticity') or 'Medium',
        '_snipeit_asset_owner_12': get_tag_value(tags, 'Owner') or 'Unassigned',
        '_snipeit_aws_region_17': region_name,
        '_snipeit_aws_account_18': account_name,
        '_snipeit_availability_zone_19': instance.get('Placement', {}).get('AvailabilityZone', 'N/A'),
        '_snipeit_subnet_id_20': instance.get('SubnetId', 'N/A'),
        '_snipeit_security_groups_21': security_groups,
        '_snipeit_instance_state_22': instance.get('State', {}).get('Name', 'unknown'),
        '_snipeit_launch_time_23': launch_time or 'N/A',
        '_snipeit_ami_id_24': instance.get('ImageId', 'N/A'),
        '_snipeit_architecture_25': instance.get('Architecture', 'N/A'),
        '_snipeit_root_device_type_26': instance.get('RootDeviceType', 'N/A'),
        '_snipeit_virtualization_type_27': instance.get('VirtualizationType', 'N/A'),
    }
    
    return snipeit_payload, asset_tag
    


def get_aws_assets(account_profile):
    """Connects to AWS account and retrieves EC2 instance data across all regions."""
    
    print(f"\n--- Starting discovery for {account_profile['name']} ---")
    all_assets = []
    
    try:
        # Create session with profile
        session = boto3.Session(profile_name=account_profile['profile_name'])
        
        # Check if session has credentials
        credentials = session.get_credentials()
        if not credentials:
            print(f"  [ERROR] No credentials found for profile '{account_profile['profile_name']}'")
            return all_assets
        
        # Get available regions - explicitly set region for this call
        # Try to get region from session, otherwise default to us-east-1
        default_region = account_profile['default_region'] or 'eu-south-1'
        print(f"  Using default region: {default_region}")
        
        ec2_client = session.client('ec2', region_name=default_region)
        
        # Get all regions where EC2 is available
        try:
            regions_response = ec2_client.describe_regions()
            regions = [region['RegionName'] for region in regions_response['Regions']]
            print(f"  Found {len(regions)} regions to scan")
        except Exception as e:
            print(f"  [ERROR] Failed to retrieve regions: {e}")
            # Fallback to common regions if describe_regions fails
            regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-1']
            print(f"  Using fallback regions: {regions}")
        
        for region in regions:
            print(f"  -> Scanning region: {region}")
            try:
                ec2_regional_client = session.client('ec2', region_name=region)
                paginator = ec2_regional_client.get_paginator('describe_instances')
                
                # Use paginator to handle large number of instances
                pages = paginator.paginate(
                    Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped']}]
                )
                
                instance_count = 0
                for page in pages:
                    for reservation in page['Reservations']:
                        for instance in reservation['Instances']:
                            # Skip terminated instances
                            if instance['State']['Name'] not in ['terminated', 'shutting-down']:
                                asset_data, asset_tag = process_aws_instance(instance, account_profile['name'], region)
                                all_assets.append({'payload': asset_data, 'asset_tag': asset_tag})
                                instance_count += 1
                
                if instance_count > 0:
                    print(f"     Found {instance_count} instances")
                    
            except ClientError as e:
                print(f"  [ERROR] Failed to scan region {region}: {e}")
            except Exception as e:
                print(f"  [ERROR] Unexpected error in region {region}: {e}")
                            
    except ClientError as e:
        print(f"  [ERROR] AWS API call failed for {account_profile['name']}: {e}")
    except Exception as e:
        print(f"  [ERROR] Unexpected error for {account_profile['name']}: {e}")
        
    return all_assets



def find_snipeit_asset_by_tag(asset_tag):
    """Checks if an asset with the given tag already exists in Snipe-IT."""
    
    search_url = f"{SNIPEIT_API_URL}?search={asset_tag}&asset_tag={asset_tag}"
    
    try:
        response = requests.get(search_url, headers=SNIPEIT_HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data and data.get('total') > 0:
            # Found the existing asset
            return data['rows'][0]['id']
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Failed to search Snipe-IT for asset {asset_tag}: {e}")
        return None

def create_or_update_snipeit_asset(asset_data, asset_id=None):
    """Creates a new asset or updates an existing one in Snipe-IT."""
    
    asset_tag = asset_data['asset_tag']
    
    if asset_id:
        # Update existing asset
        url = f"{SNIPEIT_API_URL}/{asset_id}"
        http_method = 'PATCH'  # Changed from PUT to PATCH
        action = 'Updated'
    else:
        # Create new asset
        url = SNIPEIT_API_URL
        http_method = 'POST'
        action = 'Created'

    try:
        response = requests.request(http_method, url, headers=SNIPEIT_HEADERS, json=asset_data, timeout=15)
        response.raise_for_status()
        
        # CHECK THE JSON RESPONSE STATUS!
        response_data = response.json()
        
        if response_data.get('status') == 'success':
            print(f"  [SUCCESS] Asset {asset_tag} - {action}.")
            return True
        else:
            # The API returned 200 but with an error status
            error_messages = response_data.get('messages', 'Unknown error')
            print(f"  [FAILURE] Asset {asset_tag} - API Error: {error_messages}")
            return False
        
    except requests.exceptions.HTTPError as e:
        error_message = response.json().get('messages', e) if response.text else str(e)
        print(f"  [FAILURE] Asset {asset_tag} - Failed to {action.lower()}: {error_message}")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Network error during Snipe-IT API call for {asset_tag}: {e}")
        return False


# ==============================================================================
# 4. MAIN EXECUTION
# ==============================================================================

def main():
    """Orchestrates the discovery and synchronization process."""
    
    all_aws_assets = []
    
    # 1. Discover assets from all AWS accounts
    for account in AWS_ACCOUNTS:
        assets = get_aws_assets(account)
        all_aws_assets.extend(assets)
        
    print(f"\nTotal unique assets discovered across all AWS accounts: {len(all_aws_assets)}")
    
    # 2. Sync assets with Snipe-IT
    print("\n--- Starting Snipe-IT Synchronization ---")
    
    for asset in all_aws_assets:
        payload = asset['payload']
        asset_tag = asset['asset_tag']
        
        # 2a. Check if asset exists
        snipeit_id = find_snipeit_asset_by_tag(asset_tag)
        
        # 2b. Create or Update
        if snipeit_id:
            print(f"  [MATCH] Found existing asset {asset_tag} (ID: {snipeit_id}). Attempting update...")
            create_or_update_snipeit_asset(payload, asset_id=snipeit_id)
        else:
            print(f"  [NEW] Asset {asset_tag} not found. Attempting creation...")
            create_or_update_snipeit_asset(payload)
            
        sleep(0.5) # Be kind to the API and avoid rate limiting

    print("\n--- Synchronization Complete ---")


if __name__ == "__main__":
    main()