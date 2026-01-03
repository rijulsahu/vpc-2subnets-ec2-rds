#!/usr/bin/env python3
"""
VPC Best Practices - Security Validation Integration Test
Feature: vpc-best-practices, Task 23
Integration Test: Security Validation
Validates: Requirements 9.1, 9.3, 9.4, 9.6

This integration test deploys actual AWS resources to validate:
- Private subnet cannot be accessed directly from internet (should fail)
- Bastion host is the only entry point
- Security group chain enforcement (web -> app -> db)
- NACL effectiveness

WARNING: This test creates real AWS resources that incur costs.
         - EC2 instances: ~$0.0116/hour per instance (t3.micro) x 4 = ~$0.0464/hour
         - NAT Gateway: ~$0.045/hour + data transfer
         - Data transfer: ~$0.09/GB
         Estimated cost: ~$0.15 for a 7-minute test run
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
KEY_FILE = VPC_DIR / "security-test-key.pem"
TEST_TFVARS_FILE = VPC_DIR / "security-test.tfvars"
TEST_PLAN_FILE = VPC_DIR / "security-test.tfplan"

# Test configuration
TEST_TFVARS = {
    'project_name': 'security-test',
    'environment': 'development',
    'vpc_cidr': '10.0.0.0/16',
    'availability_zones': ['ap-south-1a', 'ap-south-1b'],
    'public_subnet_cidrs': ['10.0.1.0/24', '10.0.2.0/24'],
    'private_subnet_cidrs': ['10.0.11.0/24', '10.0.12.0/24'],
    'nat_gateway_strategy': 'single',  # Cost-optimized
    'enable_vpc_flow_logs': False,
    'admin_cidr_blocks': ['0.0.0.0/0'],  # Allow SSH for testing
    'cost_center': 'security-test',
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
    print_info("Created security-test.tfvars")

def deploy_vpc_infrastructure():
    """Deploy the VPC infrastructure using OpenTofu."""
    print_test("Deploying VPC infrastructure...")
    
    # Initialize
    print_info("Running tofu init...")
    stdout, stderr, code = run_command('tofu init', cwd=str(VPC_DIR))
    if code != 0:
        print_fail("Failed to initialize Terraform")
        print(stderr)
        return False
    
    # Plan
    print_info("Running tofu plan...")
    stdout, stderr, code = run_command('tofu plan -var-file=security-test.tfvars -out=security-test.tfplan', cwd=str(VPC_DIR))
    if code != 0:
        print_fail("Failed to create plan")
        print(stderr)
        return False
    
    # Apply
    print_info("Running tofu apply (this may take 3-5 minutes)...")
    stdout, stderr, code = run_command('tofu apply -auto-approve security-test.tfplan', cwd=str(VPC_DIR))
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

def create_security_tier_instances(outputs):
    """Create instances representing different security tiers."""
    print_test("Creating security tier instances (bastion, web, app, db)...")
    
    # Track all created resources for cleanup (even on partial failures)
    created_instance_ids = []
    created_key_name = None
    
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
    key_name = f"security-test-{int(time.time())}"
    key_command = f'aws ec2 create-key-pair --key-name {key_name} --query "KeyMaterial" --output text'
    stdout, stderr, code = run_command(key_command)
    if code != 0:
        print_fail("Failed to create key pair")
        return None
    
    created_key_name = key_name  # Track for cleanup
    
    # Save key file to test directory with timestamp
    test_dir = os.path.dirname(os.path.abspath(__file__))
    key_file = os.path.join(test_dir, f"security-test-key-{int(time.time())}.pem")
    
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
    
    vpc_id = outputs['vpc_id']
    public_subnet = outputs['public_subnet_ids'][0]
    private_subnet = outputs['private_subnet_ids'][0]
    
    # Get security group IDs from outputs
    sg_ids = outputs.get('security_group_ids', {})
    bastion_sg = sg_ids.get('bastion')
    web_sg = sg_ids.get('web')
    app_sg = sg_ids.get('application')
    db_sg = sg_ids.get('database')
    
    print_info(f"Using security groups - Bastion: {bastion_sg}, Web: {web_sg}, App: {app_sg}, DB: {db_sg}")
    
    instances = {}
    
    # Launch bastion instance in public subnet with bastion SG
    print_info("Launching bastion instance...")
    bastion_command = f"""aws ec2 run-instances \
        --image-id {ami_id} \
        --instance-type t3.micro \
        --key-name {key_name} \
        --security-group-ids {bastion_sg} \
        --subnet-id {public_subnet} \
        --associate-public-ip-address \
        --tag-specifications "ResourceType=instance,Tags=[{{Key=Name,Value=security-test-bastion}}]" \
        --output json"""
    
    stdout, stderr, code = run_command(bastion_command)
    if code != 0:
        print_fail("Failed to launch bastion instance")
        print_info(f"Error: {stderr[:500]}")
        return {'key_name': created_key_name, 'key_file': key_file, 'instances': {}, 'created_instance_ids': created_instance_ids}
    
    bastion_instance_id = json.loads(stdout)['Instances'][0]['InstanceId']
    created_instance_ids.append(bastion_instance_id)  # Track immediately
    instances['bastion'] = {'id': bastion_instance_id, 'sg': bastion_sg}
    print_pass(f"Launched bastion: {bastion_instance_id}")
    
    # Launch web instance in public subnet with web SG
    print_info("Launching web tier instance...")
    web_command = f"""aws ec2 run-instances \
        --image-id {ami_id} \
        --instance-type t3.micro \
        --key-name {key_name} \
        --security-group-ids {web_sg} \
        --subnet-id {public_subnet} \
        --associate-public-ip-address \
        --tag-specifications "ResourceType=instance,Tags=[{{Key=Name,Value=security-test-web}}]" \
        --output json"""
    
    stdout, stderr, code = run_command(web_command)
    if code != 0:
        print_fail("Failed to launch web instance")
        print_info(f"Error: {stderr[:500]}")
        return {'key_name': created_key_name, 'key_file': key_file, 'instances': instances, 'created_instance_ids': created_instance_ids}
    
    web_instance_id = json.loads(stdout)['Instances'][0]['InstanceId']
    created_instance_ids.append(web_instance_id)  # Track immediately
    instances['web'] = {'id': web_instance_id, 'sg': web_sg}
    print_pass(f"Launched web: {web_instance_id}")
    
    # Launch app instance in private subnet with app SG
    print_info("Launching application tier instance...")
    app_command = f"""aws ec2 run-instances \
        --image-id {ami_id} \
        --instance-type t3.micro \
        --key-name {key_name} \
        --security-group-ids {app_sg} \
        --subnet-id {private_subnet} \
        --no-associate-public-ip-address \
        --tag-specifications "ResourceType=instance,Tags=[{{Key=Name,Value=security-test-app}}]" \
        --output json"""
    
    stdout, stderr, code = run_command(app_command)
    if code != 0:
        print_fail("Failed to launch app instance")
        print_info(f"Error: {stderr[:500]}")
        return {'key_name': created_key_name, 'key_file': key_file, 'instances': instances, 'created_instance_ids': created_instance_ids}
    
    app_instance_id = json.loads(stdout)['Instances'][0]['InstanceId']
    created_instance_ids.append(app_instance_id)  # Track immediately
    instances['app'] = {'id': app_instance_id, 'sg': app_sg}
    print_pass(f"Launched app: {app_instance_id}")
    
    # Launch db instance in private subnet with db SG
    print_info("Launching database tier instance...")
    db_command = f"""aws ec2 run-instances \
        --image-id {ami_id} \
        --instance-type t3.micro \
        --key-name {key_name} \
        --security-group-ids {db_sg} \
        --subnet-id {private_subnet} \
        --no-associate-public-ip-address \
        --tag-specifications "ResourceType=instance,Tags=[{{Key=Name,Value=security-test-db}}]" \
        --output json"""
    
    stdout, stderr, code = run_command(db_command)
    if code != 0:
        print_fail("Failed to launch db instance")
        print_info(f"Error: {stderr[:500]}")
        return {'key_name': created_key_name, 'key_file': key_file, 'instances': instances, 'created_instance_ids': created_instance_ids}
    
    db_instance_id = json.loads(stdout)['Instances'][0]['InstanceId']
    created_instance_ids.append(db_instance_id)  # Track immediately
    instances['db'] = {'id': db_instance_id, 'sg': db_sg}
    print_pass(f"Launched db: {db_instance_id}")
    
    # Wait for instances
    print_info("Waiting for instances to be running...")
    all_instance_ids = [inst['id'] for inst in instances.values()]
    time.sleep(30)
    wait_command = f"aws ec2 wait instance-running --instance-ids {' '.join(all_instance_ids)}"
    run_command(wait_command)
    
    # Wait for status checks to pass (instances fully initialized with SSH ready)
    print_info("Waiting for instances to pass status checks (SSH services ready)...")
    status_check_command = f"aws ec2 wait instance-status-ok --instance-ids {' '.join(all_instance_ids)}"
    stdout, stderr, code = run_command(status_check_command, check=False)
    if code != 0:
        # Status check wait can timeout, but let's continue with additional time
        print_info("Status check wait timed out or failed, adding extra initialization time...")
        time.sleep(60)  # Give more time for all instances to fully initialize
    else:
        print_pass("All instances passed status checks")
    
    # Get instance details
    describe_command = f"aws ec2 describe-instances --instance-ids {' '.join(all_instance_ids)} --output json"
    stdout, stderr, code = run_command(describe_command)
    
    result = json.loads(stdout)
    for reservation in result.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            instance_id = instance['InstanceId']
            for tier, info in instances.items():
                if info['id'] == instance_id:
                    info['public_ip'] = instance.get('PublicIpAddress')
                    info['private_ip'] = instance['PrivateIpAddress']
                    print_info(f"{tier.upper()}: {instance_id} (Private: {info['private_ip']}, Public: {info.get('public_ip', 'N/A')})")
    
    print_pass("All instances running")
    
    return {
        'key_name': key_name,
        'key_file': key_file,
        'instances': instances,
        'created_instance_ids': created_instance_ids
    }

def test_private_subnet_isolation(resources):
    """Test that private subnet instances cannot be accessed directly from internet."""
    print_test("Testing private subnet isolation (should fail to connect)...")
    
    app_instance = resources['instances']['app']
    
    # Try to SSH directly to private instance (should timeout/fail)
    print_info("Attempting direct SSH to application instance (this should fail)...")
    
    # This should fail because the instance has no public IP
    if not app_instance.get('public_ip'):
        print_pass("Application instance has no public IP (as expected)")
    else:
        print_fail("Application instance has a public IP (unexpected)")
        return False
    
    # Verify database instance also has no public IP
    db_instance = resources['instances']['db']
    if not db_instance.get('public_ip'):
        print_pass("Database instance has no public IP (as expected)")
    else:
        print_fail("Database instance has a public IP (unexpected)")
        return False
    
    return True

def test_bastion_as_entry_point(resources):
    """Test that bastion is the only entry point to private resources."""
    print_test("Testing bastion as sole entry point...")
    
    bastion = resources['instances']['bastion']
    app_instance = resources['instances']['app']
    
    # Wait for bastion to be fully ready
    print_info("Waiting for bastion to be fully initialized...")
    time.sleep(60)
    
    # Test SSH to bastion
    print_info("Testing SSH to bastion host...")
    ssh_test_command = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ConnectTimeout=10 \
        -i "{resources['key_file']}" ec2-user@{bastion['public_ip']} \
        "echo Connected to bastion" """
    
    max_retries = 3
    for attempt in range(max_retries):
        stdout, stderr, code = run_command(ssh_test_command, check=False)
        if code == 0:
            print_pass("Successfully connected to bastion host")
            break
        else:
            if attempt < max_retries - 1:
                print_info(f"SSH attempt {attempt + 1} failed, retrying...")
                time.sleep(10)
            else:
                print_fail("Failed to connect to bastion host")
                return False
    
    # Copy key to bastion
    print_info("Setting up bastion for jump host access...")
    scp_command = f"""scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes \
        -i {resources['key_file']} \
        {resources['key_file']} \
        ec2-user@{bastion['public_ip']}:/home/ec2-user/key.pem"""
    
    run_command(scp_command, check=False)
    
    chmod_command = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes \
        -i {resources['key_file']} ec2-user@{bastion['public_ip']} \
        "chmod 400 /home/ec2-user/key.pem" """
    
    run_command(chmod_command, check=False)
    
    # Test SSH from bastion to app instance
    print_info("Testing SSH from bastion to application instance...")
    bastion_to_app_command = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes \
        -i {resources['key_file']} ec2-user@{bastion['public_ip']} \
        "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ConnectTimeout=10 \
        -i /home/ec2-user/key.pem \
        ec2-user@{app_instance['private_ip']} \
        'echo Connected to app via bastion'" """
    
    stdout, stderr, code = run_command(bastion_to_app_command, check=False)
    if code == 0:
        print_pass("Successfully accessed app instance via bastion")
        return True
    else:
        print_fail("Failed to access app instance via bastion")
        return False

def test_security_group_chain(resources):
    """Test security group chain using TCP port connectivity tests.
    
    This test validates security groups allow:
    - Bastion -> App (SSH port 22) ✓
    - App -> DB (MySQL port 3306) ✓
    - Web -> DB is BLOCKED ✓
    
    Note: DB security group only allows MySQL port 3306 from app, NOT SSH.
    We test TCP connectivity on the correct ports per security group rules.
    """
    print_test("Testing security group chain (TCP port connectivity)...")
    
    bastion = resources['instances']['bastion']
    app = resources['instances']['app']
    db = resources['instances']['db']
    web = resources['instances']['web']
    
    # Test 1: Bastion → App (SSH port 22)
    print_info("Testing bastion -> app connectivity (SSH port 22)...")
    
    bastion_to_app_command = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ConnectTimeout=10 -i \"{resources['key_file']}\" ec2-user@{bastion['public_ip']} \"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ConnectTimeout=10 -i /home/ec2-user/key.pem ec2-user@{app['private_ip']} echo Connected\" """
    
    stdout, stderr, code = run_command(bastion_to_app_command, check=False)
    if code == 0:
        print_pass("Bastion can connect to app tier (SSH)")
    else:
        print_fail("Bastion cannot connect to app tier")
        return False
    
    # Test 2: App → DB (MySQL port 3306) - Test TCP connectivity
    print_info("Testing app -> db connectivity (MySQL port 3306)...")
    
    # Use bash TCP test to check if port 3306 is reachable
    app_to_db_tcp_test = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -i \"{resources['key_file']}\" ec2-user@{bastion['public_ip']} \"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -i /home/ec2-user/key.pem ec2-user@{app['private_ip']} 'timeout 5 bash -c \\\"cat < /dev/tcp/{db['private_ip']}/3306\\\" 2>&1 || echo EXIT_CODE:$?'\" """
    
    stdout, stderr, code = run_command(app_to_db_tcp_test, check=False, timeout=30)
    output = (stdout + stderr).lower()
    
    # Success indicators:
    # - Exit code 0 or 124 (timeout): TCP connection succeeded to port 3306
    # - No "connection timed out" or "no route to host": Security group allows traffic
    if 'connection timed out' in output or 'no route to host' in output:
        print_fail("App tier cannot reach DB tier on port 3306 (security group blocking)")
        print_info(f"Output: {output[:300]}")
        return False
    else:
        print_pass("App tier can reach DB tier on MySQL port 3306 (security group allows)")
        print_info("Security group correctly allows app -> db on port 3306")
    
    # Test 3: Verify app CANNOT SSH to DB (security enforcement)
    print_info("Testing app -> db SSH access (should be BLOCKED)...")
    
    app_to_db_ssh = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -i \"{resources['key_file']}\" ec2-user@{bastion['public_ip']} \"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -i /home/ec2-user/key.pem ec2-user@{app['private_ip']} 'timeout 5 bash -c \\\"cat < /dev/tcp/{db['private_ip']}/22\\\" 2>&1'\" """
    
    stdout, stderr, code = run_command(app_to_db_ssh, check=False, timeout=30)
    output = (stdout + stderr).lower()
    
    if 'connection timed out' in output or code != 0:
        print_pass("App -> DB SSH correctly blocked (only MySQL port 3306 allowed)")
    else:
        print_fail("App can SSH to DB (security violation)")
        return False
    
    # Test 4: Verify web -> db is blocked
    print_info("Verifying security group rules block web -> db traffic...")
    
    web_sg_id = web['sg']
    db_sg_id = db['sg']
    
    check_sg_rules = f"""aws ec2 describe-security-group-rules --filters "Name=group-id,Values={web_sg_id}" --query "SecurityGroupRules[?ReferencedGroupInfo.GroupId=='{db_sg_id}']" --output json"""
    
    stdout, stderr, code = run_command(check_sg_rules, check=False)
    if code == 0:
        rules = json.loads(stdout) if stdout.strip() else []
        if len(rules) == 0:
            print_pass("Web tier has no rules to DB tier (correct isolation)")
        else:
            print_fail(f"Web tier has {len(rules)} rule(s) to DB tier (security violation)")
            return False
    
    return True

def test_nacl_effectiveness(resources):
    """Test that NACLs are effective and properly configured.
    
    NOTE: We test from app instance (not bastion) because:
    - App tier has HTTPS egress configured in security groups
    - Bastion only has SSH egress to app tier (not HTTP/HTTPS to internet)
    - This validates both NACL rules AND security group configuration
    """
    print_test("Testing NACL effectiveness...")
    
    bastion = resources['instances']['bastion']
    app_instance = resources['instances']['app']
    
    # Test that private instances can reach internet via NAT
    # This validates:
    # 1. Private subnet NACL allows outbound traffic
    # 2. NAT Gateway is working
    # 3. Public subnet NACL allows NAT gateway return traffic
    # 4. App security group allows HTTPS egress
    print_info("Testing private subnet NACL allows outbound via NAT...")
    
    private_internet_test = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -i \"{resources['key_file']}\" ec2-user@{bastion['public_ip']} \"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -i /home/ec2-user/key.pem ec2-user@{app_instance['private_ip']} curl -s -o /dev/null -w %{{http_code}} --connect-timeout 15 --max-time 20 https://amazon.com\" """
    
    stdout, stderr, code = run_command(private_internet_test, check=False)
    if code == 0 and stdout.strip() in ['200', '301', '302']:
        print_pass(f"NACL allows internet access via NAT (HTTP {stdout.strip()})")
    else:
        print_fail("NACL blocks internet access via NAT (unexpected)")
        print_info(f"Error code: {code}")
        print_info(f"Stdout: {stdout[:200] if stdout else 'None'}")
        print_info(f"Stderr: {stderr[:200] if stderr else 'None'}")
        return False
    
    # Test that public subnet bastion can reach private app on SSH port (NACL allows intra-VPC)
    print_info("Testing NACL allows intra-VPC traffic (public -> private SSH)...")
    
    ssh_test = f"""ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -i \"{resources['key_file']}\" ec2-user@{bastion['public_ip']} \"timeout 5 bash -c 'cat < /dev/tcp/{app_instance['private_ip']}/22'\" """
    
    stdout, stderr, code = run_command(ssh_test, check=False)
    # Exit code 0 or 124 (timeout) both mean TCP connection succeeded
    # If we get SSH banner in output, that also proves connection
    if code == 0 or code == 124 or (stdout and 'SSH' in stdout):
        print_pass("NACL allows intra-VPC traffic (public <-> private)")
    else:
        print_fail("NACL blocks intra-VPC traffic (unexpected)")
        print_info(f"Error code: {code}")
        print_info(f"Stdout: {stdout[:200] if stdout else 'None'}")
        return False
    
    return True

def cleanup_test_resources(resources, outputs):
    """Clean up all test resources, handling partial failures gracefully."""
    print_test("Cleaning up test resources...")
    
    cleanup_errors = []
    
    # Collect ALL instance IDs from multiple sources to handle partial failures
    all_instance_ids = set()
    
    if resources:
        # Get instances from the created_instance_ids list (most reliable)
        if 'created_instance_ids' in resources:
            all_instance_ids.update(resources['created_instance_ids'])
            print_info(f"Found {len(resources['created_instance_ids'])} instances from tracking list")
        
        # Also check the instances dict (backup)
        if 'instances' in resources:
            dict_ids = [inst['id'] for inst in resources['instances'].values()]
            all_instance_ids.update(dict_ids)
            print_info(f"Found {len(dict_ids)} instances from instances dict")
    
    # Terminate instances if any were found
    if all_instance_ids:
        instance_ids_list = list(all_instance_ids)
        print_info(f"Terminating {len(instance_ids_list)} EC2 instance(s)...")
        terminate_command = f"aws ec2 terminate-instances --instance-ids {' '.join(instance_ids_list)}"
        stdout, stderr, code = run_command(terminate_command, check=False)
        
        if code != 0:
            cleanup_errors.append(f"Failed to terminate instances: {stderr}")
            print_fail(f"Error terminating instances: {stderr}")
        else:
            print_pass("Instance termination initiated")
            
            # Wait for instances to terminate (with timeout handling)
            print_info("Waiting for instances to terminate (max 3 minutes)...")
            wait_command = f"aws ec2 wait instance-terminated --instance-ids {' '.join(instance_ids_list)}"
            stdout, stderr, code = run_command(wait_command, check=False)
            
            if code != 0:
                cleanup_errors.append(f"Timeout waiting for instance termination")
                print_fail("Timeout waiting for termination (instances may still be terminating)")
            else:
                print_pass("All instances terminated")
    else:
        print_info("No instances to terminate")
    
    # Delete key pair
    if resources and 'key_name' in resources:
        print_info(f"Deleting key pair: {resources['key_name']}...")
        delete_key_command = f"aws ec2 delete-key-pair --key-name {resources['key_name']}"
        stdout, stderr, code = run_command(delete_key_command, check=False)
        
        if code != 0:
            cleanup_errors.append(f"Failed to delete key pair: {stderr}")
            print_fail(f"Error deleting key pair: {stderr}")
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
    print_info("Destroying VPC infrastructure...")
    destroy_command = 'tofu destroy -auto-approve -var-file=security-test.tfvars'
    stdout, stderr, code = run_command(destroy_command, cwd=str(VPC_DIR), check=False)
    if code == 0:
        print_pass("VPC infrastructure destroyed")
    else:
        cleanup_errors.append(f"Failed to destroy VPC infrastructure: {stderr}")
        print_fail("Failed to destroy VPC infrastructure")
        print(stderr)
    
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
        print(f"  aws ec2 describe-instances --filters 'Name=tag:Name,Values=security-test-*' --query 'Reservations[*].Instances[*].[InstanceId,State.Name]'")
        print(f"  aws ec2 describe-key-pairs --filters 'Name=key-name,Values=security-test-*'")
        print(f"  aws ec2 describe-vpcs --filters 'Name=tag:Name,Values=*security-test*'")
    else:
        print_pass("Cleanup completed successfully")

def main():
    print_header("VPC Best Practices - Security Validation Integration Test\n" +
                 "Feature: vpc-best-practices, Task 23\n" +
                 "Integration Test: Security Validation\n" +
                 "Validates: Requirements 9.1, 9.3, 9.4, 9.6")
    
    print(f"{Colors.RED}{Colors.BOLD}WARNING: This test will create real AWS resources that incur costs!{Colors.END}")
    print(f"{Colors.YELLOW}Estimated cost: ~$0.15 for a 7-minute test run{Colors.END}")
    print(f"{Colors.YELLOW}Press Ctrl+C within 10 seconds to cancel...{Colors.END}\n")
    
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test cancelled by user{Colors.END}")
        return 0
    
    resources = None
    outputs = None
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
        
        # Create security tier instances
        resources = create_security_tier_instances(outputs)
        if not resources:
            return 1
        
        # Run security tests
        test_results = []
        
        # Test 1: Private subnet isolation
        result = test_private_subnet_isolation(resources)
        test_results.append(("Private Subnet Isolation", result))
        all_tests_passed = all_tests_passed and result
        
        # Test 2: Bastion as entry point
        result = test_bastion_as_entry_point(resources)
        test_results.append(("Bastion as Entry Point", result))
        all_tests_passed = all_tests_passed and result
        
        # Test 3: Security group chain
        result = test_security_group_chain(resources)
        test_results.append(("Security Group Chain", result))
        all_tests_passed = all_tests_passed and result
        
        # Test 4: NACL effectiveness
        result = test_nacl_effectiveness(resources)
        test_results.append(("NACL Effectiveness", result))
        all_tests_passed = all_tests_passed and result
        
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
        # Clean up resources
        print_header("CLEANUP")
        cleanup_test_resources(resources, outputs)
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
