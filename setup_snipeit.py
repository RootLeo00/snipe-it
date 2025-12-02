# setup_snipeit_fixed.py
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

SNIPEIT_API_TOKEN = os.getenv("APP_KEY", "")
SNIPEIT_BASE_URL = "http://localhost:8000"

headers = {
    'Authorization': f'Bearer {SNIPEIT_API_TOKEN}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

print("Setting up Snipe-IT for AWS EC2 Assets...\n")

# Step 1: Check/Create Category
print("1. Checking for existing Asset Category...")
cat_list_response = requests.get(f"{SNIPEIT_BASE_URL}/api/v1/categories", headers=headers)
category_id = None

if cat_list_response.status_code == 200:
    categories = cat_list_response.json()
    print(f"   Found {categories.get('total', 0)} categories")
    for cat in categories.get('rows', []):
        if cat['name'] == 'Cloud Infrastructure':
            category_id = cat['id']
            print(f"   ✅ Will use existing category ID: {category_id}")
            break

if not category_id:
    print("   Creating new Asset Category...")
    category_payload = {
        'name': 'Cloud Infrastructure',
        'category_type': 'asset',
        'eula': False
    }
    
    cat_response = requests.post(
        f"{SNIPEIT_BASE_URL}/api/v1/categories",
        headers=headers,
        json=category_payload
    )
    
    if cat_response.status_code == 200:
        cat_data = cat_response.json()
        if cat_data.get('status') == 'success':
            category_id = cat_data['payload']['id']
            print(f"   ✅ Category created with ID: {category_id}")
        else:
            print(f"   ❌ Error: {cat_data}")
            exit(1)

# Step 2: Check/Create Manufacturer
print("\n2. Checking for existing Manufacturer...")
mfg_list_response = requests.get(f"{SNIPEIT_BASE_URL}/api/v1/manufacturers", headers=headers)
manufacturer_id = None

if mfg_list_response.status_code == 200:
    manufacturers = mfg_list_response.json()
    for mfg in manufacturers.get('rows', []):
        if mfg['name'] == 'Amazon Web Services':
            manufacturer_id = mfg['id']
            print(f"   ✅ Found existing manufacturer with ID: {manufacturer_id}")
            break

if not manufacturer_id:
    print("   Creating new Manufacturer...")
    mfg_payload = {
        'name': 'Amazon Web Services',
        'url': 'https://aws.amazon.com'
    }
    
    mfg_response = requests.post(
        f"{SNIPEIT_BASE_URL}/api/v1/manufacturers",
        headers=headers,
        json=mfg_payload
    )
    
    if mfg_response.status_code == 200:
        mfg_data = mfg_response.json()
        if mfg_data.get('status') == 'success':
            manufacturer_id = mfg_data['payload']['id']
            print(f"   ✅ Manufacturer created with ID: {manufacturer_id}")

# Step 3: Check/Create Model
print("\n3. Checking for existing Asset Model...")
model_list_response = requests.get(f"{SNIPEIT_BASE_URL}/api/v1/models", headers=headers)
model_id = None

if model_list_response.status_code == 200:
    models = model_list_response.json()
    for model in models.get('rows', []):
        if model['name'] == 'EC2 Instance':
            model_id = model['id']
            print(f"   ✅ Found existing model with ID: {model_id}")
            break

if not model_id:
    print("   Creating new Asset Model...")
    model_payload = {
        'name': 'EC2 Instance',
        'manufacturer_id': manufacturer_id,
        'category_id': category_id,
        'model_number': 'EC2'
    }
    
    model_response = requests.post(
        f"{SNIPEIT_BASE_URL}/api/v1/models",
        headers=headers,
        json=model_payload
    )
    
    if model_response.status_code == 200:
        model_data = model_response.json()
        if model_data.get('status') == 'success':
            model_id = model_data['payload']['id']
            print(f"   ✅ Model created with ID: {model_id}")

# Step 4: Create Custom Fields
print("\n4. Creating Custom Fields...")

custom_fields = [
    {'name': 'Instance Type', 'format': 'ANY', 'element': 'text'},
    {'name': 'Description', 'format': 'ANY', 'element': 'textarea'},
    {'name': 'Private IP Address', 'format': 'IP', 'element': 'text'},
    {'name': 'Public IP Address', 'format': 'IP', 'element': 'text'},
    {'name': 'Platform', 'format': 'ANY', 'element': 'text'},
    {'name': 'VPC ID', 'format': 'ANY', 'element': 'text'},
    {'name': 'DNS Name', 'format': 'ANY', 'element': 'text'},
    {'name': 'MAC Address', 'format': 'MAC', 'element': 'text'},
    {'name': 'Vendor Support End Date', 'format': 'ANY', 'element': 'text'},
    {'name': 'Criticality', 'format': 'ANY', 'element': 'text'},
    {'name': 'Asset Owner', 'format': 'ANY', 'element': 'text'},
    {'name': 'AWS Region', 'format': 'ANY', 'element': 'text'},
    {'name': 'AWS Account', 'format': 'ANY', 'element': 'text'},
    {'name': 'Availability Zone', 'format': 'ANY', 'element': 'text'},
    {'name': 'Subnet ID', 'format': 'ANY', 'element': 'text'},
    {'name': 'Security Groups', 'format': 'ANY', 'element': 'textarea'},
    {'name': 'Instance State', 'format': 'ANY', 'element': 'text'},
    {'name': 'Launch Time', 'format': 'ANY', 'element': 'text'},
    {'name': 'AMI ID', 'format': 'ANY', 'element': 'text'},
    {'name': 'Architecture', 'format': 'ANY', 'element': 'text'},
    {'name': 'Root Device Type', 'format': 'ANY', 'element': 'text'},
    {'name': 'Virtualization Type', 'format': 'ANY', 'element': 'text'},
]

# Get existing custom fields first
existing_fields = {}
fields_list_response = requests.get(f"{SNIPEIT_BASE_URL}/api/v1/fields", headers=headers)
if fields_list_response.status_code == 200:
    fields_data = fields_list_response.json()
    for field in fields_data.get('rows', []):
        # Use .get() to safely access db_column
        existing_fields[field['name']] = {
            'id': field['id'],
            'db_column': field.get('db_column', field.get('db_column_name', f"_snipeit_{field['name'].lower().replace(' ', '_')}_{field['id']}"))
        }
    print(f"   Found {len(existing_fields)} existing custom fields")

field_ids = {}

for idx, field in enumerate(custom_fields, 1):
    # Check if field already exists
    if field['name'] in existing_fields:
        field_id = existing_fields[field['name']]['id']
        db_column = existing_fields[field['name']]['db_column']
        field_ids[field['name']] = {'id': field_id, 'db_column': db_column}
        print(f"   ✅ Using existing '{field['name']}' (ID: {field_id})")
        continue
    
    # Create new field
    field_payload = {
        'name': field['name'],
        'element': field['element'],
        'format': field['format'],
        'custom_format': '',
        'field_encrypted': False,
        'show_in_listview': True if idx <= 5 else False,
    }
    
    field_response = requests.post(
        f"{SNIPEIT_BASE_URL}/api/v1/fields",
        headers=headers,
        json=field_payload
    )
    
    if field_response.status_code == 200:
        field_data = field_response.json()
        if field_data.get('status') == 'success':
            field_id = field_data['payload']['id']
            db_column = field_data['payload'].get('db_column_name', field_data['payload'].get('db_column', f"_snipeit_{field['name'].lower().replace(' ', '_')}_{field_id}"))
            field_ids[field['name']] = {'id': field_id, 'db_column': db_column}
            print(f"   ✅ Created '{field['name']}' (ID: {field_id})")
        else:
            print(f"   ⚠️  Field '{field['name']}': {field_data.get('messages')}")
    else:
        print(f"   ❌ Error creating '{field['name']}': {field_response.status_code}")

# Merge existing and new fields
all_fields = {**existing_fields, **field_ids}

# Print Summary
print(f"\n{'='*70}")
print("✅ SETUP COMPLETE!")
print(f"{'='*70}")
print(f"\n🔧 Copy this configuration to your inventory.py:\n")
print(f"DEFAULT_CATEGORY_ID = {category_id}  # Cloud Infrastructure")
print(f"DEFAULT_MODEL_ID = {model_id}  # EC2 Instance")
print(f"DEFAULT_STATUS_ID = 2  # Ready to Deploy\n")
print("CUSTOM_FIELD_MAP = {")

# Create the mapping in order
mapping_keys = [
    ('instance_type', 'Instance Type'),
    ('description', 'Description'),
    ('private_ip', 'Private IP Address'),
    ('public_ip', 'Public IP Address'),
    ('platform', 'Platform'),
    ('vpc_id', 'VPC ID'),
    ('dns_name', 'DNS Name'),
    ('mac_address', 'MAC Address'),
    ('vendor_support_end', 'Vendor Support End Date'),
    ('criticity', 'Criticality'),
    ('asset_owner', 'Asset Owner'),
    ('aws_region', 'AWS Region'),
    ('aws_account', 'AWS Account'),
    ('availability_zone', 'Availability Zone'),
    ('subnet_id', 'Subnet ID'),
    ('security_groups', 'Security Groups'),
    ('instance_state', 'Instance State'),
    ('launch_time', 'Launch Time'),
    ('ami_id', 'AMI ID'),
    ('architecture', 'Architecture'),
    ('root_device_type', 'Root Device Type'),
    ('virtualization_type', 'Virtualization Type'),
]

for key, field_name in mapping_keys:
    if field_name in all_fields:
        print(f"    '{key}': {all_fields[field_name]['id']},")

print("}")

print(f"\n{'='*70}")
print("Field IDs Summary:")
print(f"{'='*70}")
for key, field_name in mapping_keys:
    if field_name in all_fields:
        print(f"{field_name}: ID={all_fields[field_name]['id']}, Column={all_fields[field_name]['db_column']}")