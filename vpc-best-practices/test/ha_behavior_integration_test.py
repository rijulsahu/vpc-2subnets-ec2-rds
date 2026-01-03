#!/usr/bin/env python3
"""
VPC Best Practices - High Availability Behavior Integration Test
Feature: vpc-best-practices, Task 22
Integration Test: HA Behavior
Validates: Requirements 7.1, 7.2, 7.3

This integration test deploys actual AWS resources to validate:
- Resources deployed across multiple AZs
- NAT Gateway failure simulation
- Continued functionality in other AZs during failure
- Route table failover behavior

WARNING: This test creates real AWS resources that incur costs.
         - EC2 instances: ~$0.0104/hour per instance (t3.micro) x 3 = ~$0.0312/hour
         - NAT Gateway: ~$0.045/hour per gateway x 2 = ~$0.09/hour + data transfer
         - Data transfer: ~$0.09/GB
         Estimated cost: ~$0.20 for a 10-minute test run
"""

import subprocess
import json
import time
import sys
import os
from pathlib import Path

# Resolve paths to work from any directory
SCRIPT_DIR = Path(__file__).parent.resolve()  # test/
VPC_DIR = SCRIPT_DIR.parent  # vpc-best-practices/
KEY_FILE = VPC_DIR / "ha-test-key.pem"
TEST_TFVARS_FILE = VPC_DIR / "ha-test.tfvars"
TEST_PLAN_FILE = VPC_DIR / "ha-test.tfplan"

# Test configuration
TEST_TFVARS = {
    'project_name': 'ha-test',
    'environment': 'development',
    'vpc_cidr': '10.0.0.0/16',
    'availability_zones': ['ap-south-1a', 'ap-south-1b'],
    'public_subnet_cidrs': ['10.0.1.0/24', '10.0.2.0/24'],
    'private_subnet_cidrs': ['10.0.11.0/24', '10.0.12.0/24'],
    'nat_gateway_strategy': 'per_az',  # HA strategy - one NAT per AZ
    'enable_vpc_flow_logs': False,
    'admin_cidr_blocks': ['0.0.0.0/0'],
    'cost_center': 'ha-test',
    'owner': 'automated-test'
}

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_test(text):
    print(f"{Colors.YELLOW}Testing: {text}{Colors.END}")

def print_pass(text):
    print(f"{Colors.GREEN}  PASS: {text}{Colors.END}")

def print_fail(text):
    print(f"{Colors.RED}  FAIL: {text}{Colors.END}")

def print_info(text):
    print(f"  INFO: {text}")

def run_command(command, cwd='..', capture_output=True, check=True, timeout=600):
    """Run a shell command and return output.
    
    Args:
        command: Shell command to run
        cwd: Working directory
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit
        timeout: Command timeout in seconds (default: 600 = 10 minutes)
    """
    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check,
                timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        else:
            result = subprocess.run(command, shell=True, cwd=cwd, check=check, timeout=timeout)
            return "", "", result.returncode
    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout} seconds", -1
    except subprocess.CalledProcessError as e:
        if capture_output:
            return e.stdout, e.stderr, e.returncode
        return "", "", e.returncode

def create_test_tfvars():
    """Create a test.tfvars file for the integration test."""
    tfvars_content = '\n'.join([f'{key} = {json.dumps(value)}' for key, value in TEST_TFVARS.items()])
    with open(TEST_TFVARS_FILE, 'w') as f:
        f.write(tfvars_content)
    print_info("Created ha-test.tfvars")

def deploy_vpc_infrastructure():
    """Deploy the VPC infrastructure using OpenTofu."""
    print_test("Deploying VPC infrastructure with HA NAT gateways...")
    
    # Initialize
    print_info("Running tofu init...")
    stdout, stderr, code = run_command('tofu init', cwd=str(VPC_DIR))
    if code != 0:
        print_fail("Failed to initialize Terraform")
        print(stderr)
        return False
    
    # Plan
    print_info("Running tofu plan...")
    stdout, stderr, code = run_command('tofu plan -var-file=ha-test.tfvars -out=ha-test.tfplan', cwd=str(VPC_DIR))
    if code != 0:
        print_fail("Failed to create plan")
        print(stderr)
        return False
    
    # Apply
    print_info("Running tofu apply (this may take 5-7 minutes for NAT gateways)...")
    stdout, stderr, code = run_command('tofu apply -auto-approve ha-test.tfplan', cwd=str(VPC_DIR))
    if code != 0:
        print_fail("Failed to apply infrastructure")
        print(stderr)
        return False
    
    print_pass("VPC infrastructure deployed successfully")
    return True

def get_infrastructure_outputs():
    """Get outputs from the deployed infrastructure."""
    stdout, stderr, code = run_command('tofu output -json', cwd=str(VPC_DIR))
    if code != 0:
        print_fail("Failed to get outputs")
        return None
    
    outputs = json.loads(stdout)
    # Extract values from output structure
    result = {}
    for key, value in outputs.items():
        if isinstance(value, dict) and 'value' in value:
            result[key] = value['value']
        else:
            result[key] = value
    
    return result

def create_test_instances(outputs):
    """Create test EC2 instances in each private subnet."""
    print_test("Creating test EC2 instances in each AZ...")
    
    # Track all created resources for cleanup (even on partial failures)
    created_instance_ids = []
    created_key_name = None
    created_sg_id = None
    
    # Get the latest Amazon Linux 2 AMI
    print_info("Finding Amazon Linux 2 AMI...")
    ami_command = """aws ec2 describe-images \
        --owners amazon \
        --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" "Name=state,Values=available" \
        --query "sort_by(Images, &CreationDate)[-1].ImageId" \
        --output text"""
    
    stdout, stderr, code = run_command(ami_command)
    if code != 0:
        print_fail("Failed to find AMI")
        return None
    
    ami_id = stdout.strip()
    print_info(f"Using AMI: {ami_id}")
    
    # Create a key pair
    print_info("Creating SSH key pair...")
    key_name = f"ha-test-{int(time.time())}"
    key_command = f'aws ec2 create-key-pair --key-name {key_name} --query "KeyMaterial" --output text'
    stdout, stderr, code = run_command(key_command)
    if code != 0:
        print_fail("Failed to create key pair")
        return None
    
    created_key_name = key_name  # Track for cleanup
    
    # Save key file to test directory with timestamp
    test_dir = os.path.dirname(os.path.abspath(__file__))
    key_file = os.path.join(test_dir, f"ha-test-key-{int(time.time())}.pem")
    
    try:
        with open(key_file, 'w') as f:
            f.write(stdout)
        # Set permissions (may not work on Windows, but try anyway)
        try:
            os.chmod(key_file, 0o400)
        except (OSError, NotImplementedError):
            print_info("Note: Unable to set file permissions on Windows (this is normal)")
    except Exception as e:
        print_fail(f"Failed to save key file: {e}")
        run_command(f'aws ec2 delete-key-pair --key-name {key_name}', check=False)
        return None
    
    print_pass(f"Created key pair: {key_name}")
    print_info(f"Key file saved to: {key_file}")
    
    # Create security group
    vpc_id = outputs['vpc_id']
    sg_name = f"ha-test-sg-{int(time.time())}"
    
    print_info("Creating test security group...")
    sg_command = f"""aws ec2 create-security-group \
        --group-name {sg_name} \
        --description "HA test security group" \
        --vpc-id {vpc_id} \
        --output json"""
    
    stdout, stderr, code = run_command(sg_command)
    if code != 0:
        print_fail("Failed to create security group")
        return {'key_name': created_key_name, 'key_file': key_file, 'instance_ids': created_instance_ids}
    
    sg_id = json.loads(stdout)['GroupId']
    created_sg_id = sg_id  # Track for cleanup
    print_pass(f"Created security group: {sg_id}")
    
    # Add rules to allow all internal VPC traffic and outbound internet
    print_info("Adding security group rules...")
    
    # Ingress: Allow SSH from anywhere for testing (we'll rely on subnet isolation)
    ingress_ssh_command = f"""aws ec2 authorize-security-group-ingress \
        --group-id {sg_id} \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0"""
    run_command(ingress_ssh_command, check=False)
    
    # Ingress: Allow all from VPC CIDR
    ingress_command = f"""aws ec2 authorize-security-group-ingress \
        --group-id {sg_id} \
        --protocol -1 \
        --cidr {TEST_TFVARS['vpc_cidr']}"""
    run_command(ingress_command, check=False)
    
    # Egress: Allow all outbound (default, but explicit)
    egress_command = f"""aws ec2 authorize-security-group-egress \
        --group-id {sg_id} \
        --protocol -1 \
        --cidr 0.0.0.0/0"""
    run_command(egress_command, check=False)
    
    print_pass("Security group rules configured")
    
    # Launch instances in each private subnet
    private_subnets = outputs['private_subnet_ids']
    instance_details = {}
    
    for idx, subnet_id in enumerate(private_subnets):
        az = TEST_TFVARS['availability_zones'][idx]
        print_info(f"Launching instance in {az} (subnet {subnet_id})...")
        
        launch_command = f"""aws ec2 run-instances \
            --image-id {ami_id} \
            --instance-type t3.micro \
            --key-name {key_name} \
            --security-group-ids {sg_id} \
            --subnet-id {subnet_id} \
            --no-associate-public-ip-address \
            --tag-specifications "ResourceType=instance,Tags=[{{Key=Name,Value=ha-test-{az}}}]" \
            --output json"""
        
        stdout, stderr, code = run_command(launch_command)
        if code != 0:
            print_fail(f"Failed to launch instance in {az}")
            print_info(f"Error: {stderr[:500]}")
            return {'key_name': created_key_name, 'key_file': key_file, 'sg_id': created_sg_id, 'instance_ids': created_instance_ids}
        
        instance_id = json.loads(stdout)['Instances'][0]['InstanceId']
        created_instance_ids.append(instance_id)  # Track immediately
        instance_details[az] = {'id': instance_id}
        print_pass(f"Launched instance in {az}: {instance_id}")
    
    # Launch a bastion instance in public subnet
    print_info("Launching bastion instance in public subnet...")
    public_subnet_id = outputs['public_subnet_ids'][0]
    
    bastion_command = f"""aws ec2 run-instances \
        --image-id {ami_id} \
        --instance-type t3.micro \
        --key-name {key_name} \
        --security-group-ids {sg_id} \
        --subnet-id {public_subnet_id} \
        --associate-public-ip-address \
        --tag-specifications "ResourceType=instance,Tags=[{{Key=Name,Value=ha-test-bastion}}]" \
        --output json"""
    
    stdout, stderr, code = run_command(bastion_command)
    if code != 0:
        print_fail("Failed to launch bastion instance")
        print_info(f"Error: {stderr[:500]}")
        return {'key_name': created_key_name, 'key_file': key_file, 'sg_id': created_sg_id, 'instance_ids': created_instance_ids}
    
    bastion_instance_id = json.loads(stdout)['Instances'][0]['InstanceId']
    created_instance_ids.append(bastion_instance_id)  # Track immediately
    print_pass(f"Launched bastion instance: {bastion_instance_id}")
    
    # Wait for instances to be running
    print_info("Waiting for instances to be running...")
    all_instance_ids = created_instance_ids
    time.sleep(30)
    wait_command = f"aws ec2 wait instance-running --instance-ids {' '.join(all_instance_ids)}"
    run_command(wait_command)
    
    # Wait for status checks to pass (instances fully initialized with SSH ready)
    print_info("Waiting for instances to pass status checks (SSH services ready)...")
    status_check_command = f"aws ec2 wait instance-status-ok --instance-ids {' '.join(all_instance_ids)}"
    stdout, stderr, code = run_command(status_check_command, check=False, timeout=600)
    if code != 0:
        # Status check wait can timeout, but let's continue with additional time
        print_info("Status check wait timed out or failed, adding extra initialization time...")
        time.sleep(90)  # Give even more time for all instances to fully initialize
    else:
        print_pass("All instances passed status checks")
        # Even after status checks, give SSH daemon more time
        print_info("Waiting additional 30 seconds for SSH daemons to stabilize...")
        time.sleep(30)
    
    # Get instance details
    describe_command = f"aws ec2 describe-instances --instance-ids {' '.join(all_instance_ids)} --output json"
    stdout, stderr, code = run_command(describe_command)
    
    result = json.loads(stdout)
    bastion_ip = None
    
    for reservation in result.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            instance_id = instance['InstanceId']
            
            if instance_id == bastion_instance_id:
                bastion_ip = instance.get('PublicIpAddress')
                print_info(f"Bastion: {bastion_instance_id} (Public: {bastion_ip})")
            else:
                az = instance['Placement']['AvailabilityZone']
                private_ip = instance['PrivateIpAddress']
                
                for az_key, details in instance_details.items():
                    if details['id'] == instance_id:
                        details['private_ip'] = private_ip
                        print_info(f"Instance in {az}: {instance_id} (Private: {private_ip})")
                        break
    
    print_pass("All instances running")
    
    return {
        'key_name': key_name,
        'key_file': key_file,
        'sg_id': sg_id,
        'instance_ids': created_instance_ids,
        'bastion_instance_id': bastion_instance_id,
        'bastion_ip': bastion_ip,
        'private_instances': instance_details
    }

def test_multi_az_deployment(outputs):
    """Verify resources are deployed across multiple AZs."""
    print_test("Verifying multi-AZ resource deployment...")
    
    # Check NAT gateways
    nat_gateway_ids = outputs.get('nat_gateway_ids', [])
    if not isinstance(nat_gateway_ids, list):
        nat_gateway_ids = [nat_gateway_ids]
    
    num_azs = len(TEST_TFVARS['availability_zones'])
    
    if len(nat_gateway_ids) == num_azs:
        print_pass(f"Correct number of NAT gateways: {len(nat_gateway_ids)} (one per AZ)")
    else:
        print_fail(f"Expected {num_azs} NAT gateways, found {len(nat_gateway_ids)}")
        return False
    
    # Check subnets
    public_subnets = outputs['public_subnet_ids']
    private_subnets = outputs['private_subnet_ids']
    
    if len(public_subnets) == num_azs and len(private_subnets) == num_azs:
        print_pass(f"Correct number of subnets: {len(public_subnets)} public, {len(private_subnets)} private")
    else:
        print_fail(f"Expected {num_azs} subnets per type")
        return False
    
    # Verify subnets are in different AZs
    describe_subnets_command = f"""aws ec2 describe-subnets \
        --subnet-ids {' '.join(public_subnets + private_subnets)} \
        --output json"""
    
    stdout, stderr, code = run_command(describe_subnets_command)
    if code != 0:
        print_fail("Failed to describe subnets")
        return False
    
    subnets = json.loads(stdout)['Subnets']
    azs = set(subnet['AvailabilityZone'] for subnet in subnets)
    
    if len(azs) >= 2:
        print_pass(f"Subnets distributed across {len(azs)} AZs: {', '.join(sorted(azs))}")
    else:
        print_fail(f"Subnets only in {len(azs)} AZ(s)")
        return False
    
    return True

def test_baseline_connectivity(resources):
    """Test that all instances can reach the internet before failure."""
    print_test("Testing baseline internet connectivity from all instances...")
    
    # First, test basic bastion connectivity
    print_info("Testing bastion SSH connectivity...")
    bastion_test_command = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -o ConnectTimeout=10 \
        -i "{resources['key_file']}" ec2-user@{resources['bastion_ip']} \
        "echo 'Bastion SSH OK'" """
    
    stdout, stderr, code = run_command(bastion_test_command, check=False, timeout=30)
    if code != 0:
        print_fail(f"Cannot connect to bastion via SSH")
        print_info(f"Error code: {code}")
        print_info(f"Stderr: {stderr[:500]}")
        return False
    print_pass("Bastion SSH connectivity confirmed")
    
    # Copy key to bastion
    print_info("Setting up bastion for SSH proxying...")
    scp_command = f"""scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -i "{resources['key_file']}" \
        "{resources['key_file']}" \
        ec2-user@{resources['bastion_ip']}:/home/ec2-user/key.pem"""
    
    stdout, stderr, code = run_command(scp_command, check=False)
    if code != 0:
        print_info(f"Warning: SCP failed (code {code}), stderr: {stderr[:300]}")
        print_info("Retrying in 5 seconds...")
        time.sleep(5)
        stdout, stderr, code = run_command(scp_command, check=False)
        if code != 0:
            print_fail(f"SCP retry failed: {stderr[:300]}")
            return False
    
    chmod_command = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -i "{resources['key_file']}" ec2-user@{resources['bastion_ip']} \
        "chmod 400 /home/ec2-user/key.pem" """
    
    run_command(chmod_command, check=False)
    print_pass("Bastion configured for SSH proxying")
    
    # Test SSH connectivity to each private instance first
    print_info("Testing SSH connectivity to private instances...")
    for az, details in resources['private_instances'].items():
        print_info(f"Testing SSH to {az} ({details['private_ip']})...")
        
        ssh_test_command = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
            -o ConnectTimeout=15 \
            -i "{resources['key_file']}" ec2-user@{resources['bastion_ip']} \
            "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
            -o ConnectTimeout=15 \
            -i /home/ec2-user/key.pem \
            ec2-user@{details['private_ip']} \
            'echo SSH_OK'" """
        
        stdout, stderr, code = run_command(ssh_test_command, check=False, timeout=45)
        if code != 0 or 'SSH_OK' not in stdout:
            print_fail(f"Cannot SSH to {az}")
            print_info(f"Error code: {code}")
            print_info(f"Stdout: {stdout[:200]}")
            print_info(f"Stderr: {stderr[:300]}")
            return False
        print_pass(f"SSH to {az} confirmed")
    
    # Now test internet connectivity from each instance
    print_info("Testing internet connectivity from private instances...")
    all_connected = True
    for az, details in resources['private_instances'].items():
        print_info(f"Testing connectivity from {az}...")
        
        test_command = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
            -o ConnectTimeout=15 \
            -i "{resources['key_file']}" ec2-user@{resources['bastion_ip']} \
            "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
            -o ConnectTimeout=15 \
            -i /home/ec2-user/key.pem \
            ec2-user@{details['private_ip']} \
            'curl -s -o /dev/null -w %{{http_code}} --connect-timeout 15 --max-time 20 https://amazon.com'" """
        
        stdout, stderr, code = run_command(test_command, check=False, timeout=60)
        if code == 0 and stdout.strip() in ['200', '301', '302']:
            print_pass(f"Instance in {az} can reach internet (HTTP {stdout.strip()})")
        else:
            print_fail(f"Instance in {az} cannot reach internet")
            print_info(f"Error code: {code}, Stdout: {stdout[:100]}, Stderr: {stderr[:200]}")
            all_connected = False
    
    return all_connected

def simulate_nat_failure(outputs):
    """Simulate NAT Gateway failure by modifying route table."""
    print_test("Simulating NAT Gateway failure in first AZ...")
    
    # Get the first NAT gateway
    nat_gateway_ids = outputs.get('nat_gateway_ids', [])
    if not isinstance(nat_gateway_ids, list):
        nat_gateway_ids = [nat_gateway_ids]
    
    if len(nat_gateway_ids) < 2:
        print_fail("Need at least 2 NAT gateways for HA test")
        return None
    
    target_nat_id = nat_gateway_ids[0]
    print_info(f"Targeting NAT Gateway: {target_nat_id}")
    
    # Find the route table that uses this NAT gateway
    describe_rts_command = f"""aws ec2 describe-route-tables \
        --filters "Name=vpc-id,Values={outputs['vpc_id']}" \
        --output json"""
    
    stdout, stderr, code = run_command(describe_rts_command)
    if code != 0:
        print_fail("Failed to describe route tables")
        return None
    
    route_tables = json.loads(stdout)['RouteTables']
    target_rt_id = None
    
    for rt in route_tables:
        for route in rt.get('Routes', []):
            if route.get('NatGatewayId') == target_nat_id:
                target_rt_id = rt['RouteTableId']
                break
        if target_rt_id:
            break
    
    if not target_rt_id:
        print_fail(f"Could not find route table using NAT {target_nat_id}")
        return None
    
    print_info(f"Found route table: {target_rt_id}")
    
    # Delete the default route to simulate NAT failure
    print_info("Deleting default route to simulate NAT failure...")
    delete_route_command = f"""aws ec2 delete-route \
        --route-table-id {target_rt_id} \
        --destination-cidr-block 0.0.0.0/0"""
    
    stdout, stderr, code = run_command(delete_route_command, check=False)
    if code == 0:
        print_pass("Simulated NAT failure by removing route")
    else:
        print_fail("Failed to delete route")
        print_info(f"Error: {stderr[:300]}")
        return None
    
    return {
        'failed_nat_id': target_nat_id,
        'affected_rt_id': target_rt_id,
        'affected_az': TEST_TFVARS['availability_zones'][0]
    }

def test_ha_failover(resources, failure_info):
    """Test that the other AZ continues to function during failure."""
    print_test("Testing HA behavior - other AZ should continue functioning...")
    
    affected_az = failure_info['affected_az']
    other_azs = [az for az in resources['private_instances'].keys() if az != affected_az]
    
    # Test that affected AZ cannot reach internet
    print_info(f"Verifying {affected_az} is affected...")
    affected_details = resources['private_instances'][affected_az]
    
    test_command = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -o ConnectTimeout=15 \
        -i "{resources['key_file']}" ec2-user@{resources['bastion_ip']} \
        "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -o ConnectTimeout=15 \
        -i /home/ec2-user/key.pem \
        ec2-user@{affected_details['private_ip']} \
        'timeout 15 curl -s -o /dev/null -w %{{http_code}} --connect-timeout 10 --max-time 15 https://amazon.com'" """
    
    stdout, stderr, code = run_command(test_command, check=False, timeout=45)
    if code != 0 or stdout.strip() not in ['200', '301', '302']:
        print_pass(f"Confirmed: {affected_az} cannot reach internet (as expected)")
    else:
        print_fail(f"{affected_az} can still reach internet (unexpected)")
        print_info(f"Output: {stdout.strip()}")
        return False
    
    # Test that other AZs still work
    all_working = True
    for az in other_azs:
        print_info(f"Testing {az} still has connectivity...")
        details = resources['private_instances'][az]
        
        test_command = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
            -o ConnectTimeout=15 \
            -i "{resources['key_file']}" ec2-user@{resources['bastion_ip']} \
            "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
            -o ConnectTimeout=15 \
            -i /home/ec2-user/key.pem \
            ec2-user@{details['private_ip']} \
            'curl -s -o /dev/null -w %{{http_code}} --connect-timeout 15 --max-time 20 https://amazon.com'" """
        
        stdout, stderr, code = run_command(test_command, check=False, timeout=60)
        if code == 0 and stdout.strip() in ['200', '301', '302']:
            print_pass(f"{az} continues to function normally (HTTP {stdout.strip()})")
        else:
            print_fail(f"{az} lost connectivity (unexpected)")
            print_info(f"Error code: {code}, Output: {stdout[:100] if stdout else 'None'}")
            all_working = False
    
    return all_working

def restore_nat_gateway(failure_info, outputs):
    """Restore the NAT Gateway route."""
    print_test("Restoring NAT Gateway route...")
    
    restore_command = f"""aws ec2 create-route \
        --route-table-id {failure_info['affected_rt_id']} \
        --destination-cidr-block 0.0.0.0/0 \
        --nat-gateway-id {failure_info['failed_nat_id']}"""
    
    stdout, stderr, code = run_command(restore_command, check=False)
    if code == 0:
        print_pass("NAT Gateway route restored")
        return True
    else:
        # Check if route already exists (not really an error)
        if 'RouteAlreadyExists' in stderr:
            print_pass("NAT Gateway route already exists (already restored)")
            return True
        else:
            print_fail("Failed to restore NAT Gateway route")
            print_info(f"Error: {stderr[:300]}")
            return False

def cleanup_test_resources(resources, outputs):
    """Clean up all test resources, handling partial failures gracefully."""
    print_test("Cleaning up test resources...")
    
    cleanup_errors = []
    
    # Terminate instances
    if resources and 'instance_ids' in resources and resources['instance_ids']:
        print_info(f"Terminating {len(resources['instance_ids'])} EC2 instance(s)...")
        terminate_command = f"aws ec2 terminate-instances --instance-ids {' '.join(resources['instance_ids'])}"
        stdout, stderr, code = run_command(terminate_command, check=False)
        
        if code != 0:
            cleanup_errors.append(f"Failed to terminate instances: {stderr}")
            print_fail(f"Error terminating instances: {stderr[:300]}")
        else:
            print_pass("Instance termination initiated")
            
            print_info("Waiting for instances to terminate (max 3 minutes)...")
            wait_command = f"aws ec2 wait instance-terminated --instance-ids {' '.join(resources['instance_ids'])}"
            stdout, stderr, code = run_command(wait_command, check=False, timeout=240)
            
            if code != 0:
                cleanup_errors.append("Timeout waiting for instance termination")
                print_fail("Timeout waiting for termination (instances may still be terminating)")
            else:
                print_pass("All instances terminated")
    
    # Delete security group (wait a bit for ENIs to detach)
    if resources and 'sg_id' in resources:
        print_info("Waiting for ENIs to detach...")
        time.sleep(15)
        
        print_info(f"Deleting security group: {resources['sg_id']}...")
        delete_sg_command = f"aws ec2 delete-security-group --group-id {resources['sg_id']}"
        stdout, stderr, code = run_command(delete_sg_command, check=False)
        
        if code != 0:
            cleanup_errors.append(f"Failed to delete security group: {stderr}")
            print_fail(f"Error deleting security group: {stderr[:300]}")
        else:
            print_pass("Security group deleted")
    
    # Delete key pair
    if resources and 'key_name' in resources:
        print_info(f"Deleting key pair: {resources['key_name']}...")
        delete_key_command = f"aws ec2 delete-key-pair --key-name {resources['key_name']}"
        stdout, stderr, code = run_command(delete_key_command, check=False)
        
        if code != 0:
            cleanup_errors.append(f"Failed to delete key pair: {stderr}")
            print_fail(f"Error deleting key pair: {stderr[:300]}")
        else:
            print_pass("Key pair deleted")
    
    # Delete key file
    if resources and 'key_file' in resources and os.path.exists(resources['key_file']):
        print_info("Deleting key file...")
        max_retries = 3
        deleted = False
        
        for attempt in range(max_retries):
            try:
                # Try to change permissions first (may help on Windows)
                try:
                    os.chmod(resources['key_file'], 0o666)
                except:
                    pass
                
                os.remove(resources['key_file'])
                print_pass("Key file deleted")
                deleted = True
                break
            except (PermissionError, OSError) as e:
                if attempt < max_retries - 1:
                    print_info(f"Deletion attempt {attempt + 1} failed, waiting 2 seconds...")
                    time.sleep(2)
                else:
                    # Last resort: try using Windows del command
                    print_info("Trying Windows del command...")
                    try:
                        result = subprocess.run(f'del /F "{resources["key_file"]}"', 
                                              shell=True, 
                                              capture_output=True, 
                                              text=True)
                        if not os.path.exists(resources['key_file']):
                            print_pass("Key file deleted using Windows command")
                            deleted = True
                            break
                    except:
                        pass
        
        if not deleted:
            cleanup_errors.append(f"Failed to delete key file: {resources['key_file']}")
            print_info("Note: Unable to delete key file automatically")
            print_info(f"Please manually delete: {resources['key_file']}")
    
    # Destroy VPC infrastructure
    print_info("Destroying VPC infrastructure (this may take a few minutes)...")
    destroy_command = 'tofu destroy -auto-approve -var-file=ha-test.tfvars'
    stdout, stderr, code = run_command(destroy_command, cwd=str(VPC_DIR), check=False, timeout=600)
    if code == 0:
        print_pass("VPC infrastructure destroyed")
    else:
        cleanup_errors.append(f"Failed to destroy VPC infrastructure: {stderr}")
        print_fail("Failed to destroy VPC infrastructure")
        print(stderr[:500])
    
    # Clean up test files
    try:
        if TEST_TFVARS_FILE.exists():
            TEST_TFVARS_FILE.unlink()
        if TEST_PLAN_FILE.exists():
            TEST_PLAN_FILE.unlink()
    except Exception as e:
        cleanup_errors.append(f"Failed to delete test files: {str(e)}")
    
    # Report cleanup status
    if cleanup_errors:
        print_fail(f"Cleanup completed with {len(cleanup_errors)} error(s):")
        for error in cleanup_errors:
            print(f"  - {error}")
        print(f"\n{Colors.YELLOW}IMPORTANT: Manually verify resource cleanup in AWS Console!{Colors.END}")
        print(f"{Colors.YELLOW}Run these commands to check for leaked resources:{Colors.END}")
        print(f"  aws ec2 describe-instances --filters 'Name=tag:Name,Values=ha-test-*' --query 'Reservations[*].Instances[*].[InstanceId,State.Name]'")
        print(f"  aws ec2 describe-security-groups --filters 'Name=group-name,Values=ha-test-*'")
        print(f"  aws ec2 describe-key-pairs --filters 'Name=key-name,Values=ha-test-*'")
    else:
        print_pass("Cleanup completed successfully")

def main():
    print_header("VPC Best Practices - HA Behavior Integration Test\n" +
                 "Feature: vpc-best-practices, Task 22\n" +
                 "Integration Test: HA Behavior\n" +
                 "Validates: Requirements 7.1, 7.2, 7.3")
    
    print(f"{Colors.RED}{Colors.BOLD}WARNING: This test will create real AWS resources that incur costs!{Colors.END}")
    print(f"{Colors.YELLOW}Estimated cost: ~$0.20 for a 10-minute test run{Colors.END}")
    print(f"{Colors.YELLOW}Press Ctrl+C within 10 seconds to cancel...{Colors.END}\n")
    
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test cancelled by user{Colors.END}")
        return 0
    
    resources = None
    outputs = None
    failure_info = None
    all_tests_passed = True
    
    try:
        # Create test configuration
        create_test_tfvars()
        
        # Deploy VPC infrastructure
        if not deploy_vpc_infrastructure():
            return 1
        
        # Get infrastructure outputs
        outputs = get_infrastructure_outputs()
        if not outputs:
            return 1
        
        # Create test instances
        resources = create_test_instances(outputs)
        if not resources or not resources.get('instance_ids'):
            return 1
        
        # Run HA tests
        test_results = []
        
        # Test 1: Multi-AZ deployment
        result = test_multi_az_deployment(outputs)
        test_results.append(("Multi-AZ Deployment", result))
        all_tests_passed = all_tests_passed and result
        
        # Test 2: Baseline connectivity
        result = test_baseline_connectivity(resources)
        test_results.append(("Baseline Connectivity", result))
        all_tests_passed = all_tests_passed and result
        
        # Test 3: Simulate NAT failure
        failure_info = simulate_nat_failure(outputs)
        if failure_info:
            test_results.append(("NAT Failure Simulation", True))
            
            # Test 4: HA failover
            result = test_ha_failover(resources, failure_info)
            test_results.append(("HA Failover Behavior", result))
            all_tests_passed = all_tests_passed and result
            
            # Restore NAT
            restore_nat_gateway(failure_info, outputs)
        else:
            test_results.append(("NAT Failure Simulation", False))
            all_tests_passed = False
        
        # Print summary
        print_header("TEST SUMMARY")
        for test_name, result in test_results:
            status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
            print(f"{status}: {test_name}")
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        print(f"\nResults: {passed}/{total} tests passed")
        print(f"{'='*80}")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        all_tests_passed = False
    except Exception as e:
        print_fail(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        all_tests_passed = False
    finally:
        # Restore NAT if needed
        if failure_info and outputs:
            restore_nat_gateway(failure_info, outputs)
        
        # Clean up resources
        print_header("CLEANUP")
        cleanup_test_resources(resources, outputs)
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
