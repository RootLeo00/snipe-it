# verify_assets.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SNIPEIT_API_TOKEN = os.getenv("APP_KEY", "")
SNIPEIT_BASE_URL = "http://localhost:8000"

headers = {
    'Authorization': f'Bearer {SNIPEIT_API_TOKEN}',
    'Accept': 'application/json',
}

print("Checking all assets in Snipe-IT...\n")

# Get all assets with pagination
offset = 0
limit = 500
all_assets = []

response = requests.get(
    f"{SNIPEIT_BASE_URL}/api/v1/hardware",
    headers=headers,
    params={'limit': limit, 'offset': offset}
)

if response.status_code == 200:
    data = response.json()
    total = data.get('total', 0)
    all_assets = data.get('rows', [])
    
    print(f"✅ Total assets in Snipe-IT: {total}")
    print(f"✅ Assets retrieved: {len(all_assets)}\n")
    
    if total > 0:
        print("Assets list:")
        print("=" * 80)
        for idx, asset in enumerate(all_assets, 1):
            print(f"{idx}. Asset Tag: {asset.get('asset_tag')} | Name: {asset.get('name')} | Model: {asset.get('model', {}).get('name')}")
        
        # Check for AWS instances specifically
        aws_instances = [a for a in all_assets if a.get('asset_tag', '').startswith('i-')]
        print(f"\n✅ AWS EC2 Instances found: {len(aws_instances)}")
        
        if len(aws_instances) > 0:
            print("\nFirst 5 AWS instances:")
            for asset in aws_instances[:5]:
                print(f"  - {asset.get('asset_tag')} | {asset.get('name')}")
    else:
        print("❌ No assets found in Snipe-IT!")
        print("\nPossible reasons:")
        print("1. Assets were created but with errors")
        print("2. Assets are in a different status")
        print("3. Database issue")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

# Check if there are archived assets
print("\n" + "="*80)
print("Checking for archived/pending assets...")
for status_id in [1, 3]:  # Pending and Archived
    response = requests.get(
        f"{SNIPEIT_BASE_URL}/api/v1/hardware",
        headers=headers,
        params={'status_id': status_id}
    )
    if response.status_code == 200:
        data = response.json()
        count = data.get('total', 0)
        status_name = "Pending" if status_id == 1 else "Archived"
        if count > 0:
            print(f"  Found {count} assets with status: {status_name}")