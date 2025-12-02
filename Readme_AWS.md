# AWS to Snipe-IT Asset Inventory Synchronization

This toolset automatically discovers AWS EC2 instances across multiple accounts and synchronizes them to Snipe-IT asset management system.
Prerequisites

    - Python 3.8+
    - Docker and Docker Compose (for Snipe-IT)
    - AWS CLI configured with appropriate credentials
    - WSL (if running on Windows)

Required Python Packages:

```bash
pip install -r requirements.txt
```
				
            
Setup Instructions
1. Configure Snipe-IT
 Start Snipe-IT using Docker:
```bash
docker compose up -d
```
				
            

Access Snipe-IT at http://localhost:8000 and complete initial setup.
2. Generate Snipe-IT API Token

    - Login to Snipe-IT web interface
    - Navigate to: User Menu → Account Settings → API Keys
    - Click "Create New Token"
    - Copy the generated token

3. Configure AWS Credentials

Ensure your ~/.aws/credentials and ~/.aws/config are properly configured with the desired profiles.
			
            

4. Create Environment Configuration

Create a .env file in your project directory:
```bash
SNIPEIT_URL=http://localhost:8000
SNIPEIT_API_TOKEN=your-actual-api-token-here
```
				
            

5. Initialize Snipe-IT Structure

Run the setup script to create categories, models, and custom fields:
```bash
python3 setup_snipeit.py
```
				
            

Copy the output configuration values and update inventory.py with the provided:

    DEFAULT_CATEGORY_ID
    DEFAULT_MODEL_ID
    DEFAULT_STATUS_ID
    CUSTOM_FIELD_MAP

6. Update Inventory Script

Edit inventory.py and paste the configuration from setup script output.

Update the AWS accounts list:
```python
AWS_ACCOUNTS = [
    {'name': 'Account 1 - Internal', 'profile_name': 'profile1'},
    {'name': 'Account 2 - Customers', 'profile_name': 'profile2'},
]
```
				
Usage
Run Asset Discovery and Sync
```bash
python3 inventory.py
```
				
This will:

    Scan all AWS regions in configured accounts
    Discover running and stopped EC2 instances
    Create or update assets in Snipe-IT


Check asset count and verify synchronization succeeded.
View Assets in Snipe-IT

Access Snipe-IT web interface:

    Navigate to Assets → List All
    Filter by Category: "Cloud Infrastructure"
    Filter by Model: "EC2 Instance"


           
### Asset Data Collected

Each EC2 instance is tracked with:

    Instance ID (as Asset Tag and Serial)
    Instance Name (from AWS Name tag)
    Instance Type (t3a.large, etc.)
    IP Addresses (private and public)
    Operating System Platform
    VPC and Subnet IDs
    Security Groups
    AWS Region and Account
    Launch Time
    AMI ID
    Architecture and Virtualization Type

### Troubleshooting
If no Assets Appear in Snipe-IT

Run verification script to check actual count:
```bash
python3 check_assets.py
```		
              

If AWS Connection Issues

Verify AWS credentials are configured:
```bash
aws configure list --profile profile1
aws configure list --profile profile2
```
				
If Custom Fields Not Populated

Ensure field IDs in CUSTOM_FIELD_MAP match the IDs from setup script output.