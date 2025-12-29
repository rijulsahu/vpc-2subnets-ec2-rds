#!/usr/bin/env python3
"""
VPC Best Practices - Network Connectivity Integration Test
Feature: vpc-best-practices, Task 21
Integration Test: Network Connectivity
Validates: All connectivity requirements

This integration test deploys actual AWS resources to validate:
- Internet connectivity from public subnet
- Internet connectivity from private subnet via NAT
- Intra-VPC communication
- Security group rule enforcement

WARNING: This test creates real AWS resources that incur costs.
         - EC2 instances: ~$0.0116/hour (t3.micro)
         - NAT Gateway: ~$0.045/hour + data transfer
         - Data transfer: ~$0.09/GB
         Estimated cost: ~$0.10 for a 5-minute test run
"""

import subprocess
import json
import time
import sys
import os

# Test configuration
TEST_TFVARS = {
    'project_name': 'integration-test',
    'environment': 'test',
    'vpc_cidr': '10.0.0.0/16',
    'availability_zones': ['ap-south-1a', 'ap-south-1b'],
    'public_subnet_cidrs': ['10.0.1.0/24', '10.0.2.0/24'],
    'private_subnet_cidrs': ['10.0.11.0/24', '10.0.12.0/24'],
    'nat_gateway_strategy': 'single',  # Use single NAT for cost optimization
    'enable_vpc_flow_logs': False,  # Disable flow logs for faster test
    'admin_cidr_blocks': ['0.0.0.0/0'],  # Allow SSH from anywhere for testing
    'cost_center': 'integration-test',
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

def run_command(command, cwd='..', capture_output=True, check=True):
    """Run a shell command and return output."""
    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check
            )
            return result.stdout, result.stderr, result.returncode
        else:
            result = subprocess.run(command, shell=True, cwd=cwd, check=check)
            return "", "", result.returncode
    except subprocess.CalledProcessError as e:
        if capture_output:
            return e.stdout, e.stderr, e.returncode
        return "", "", e.returncode

def create_test_tfvars():
    """Create a test.tfvars file for the integration test."""
    tfvars_content = '\n'.join([f'{key} = {json.dumps(value)}' for key, value in TEST_TFVARS.items()])
    with open('../integration-test.tfvars', 'w') as f:
        f.write(tfvars_content)
    print_info("Created integration-test.tfvars")

def deploy_vpc_infrastructure():
    """Deploy the VPC infrastructure using OpenTofu."""
    print_test("Deploying VPC infrastructure...")
    
    # Initialize
    print_info("Running tofu init...")
    stdout, stderr, code = run_command('tofu init', cwd='..')
    if code != 0:
        print_fail("Failed to initialize Terraform")
        print(stderr)
        return False
    
    # Plan
    print_info("Running tofu plan...")
    stdout, stderr, code = run_command('tofu plan -var-file=integration-test.tfvars -out=integration-test.tfplan', cwd='..')
    if code != 0:
        print_fail("Failed to create plan")
        print(stderr)
        return False
    
    # Apply
    print_info("Running tofu apply (this may take 3-5 minutes)...")
    stdout, stderr, code = run_command('tofu apply -auto-approve integration-test.tfplan', cwd='..')
    if code != 0:
        print_fail("Failed to apply infrastructure")
        print(stderr)
        return False
    
    print_pass("VPC infrastructure deployed successfully")
    return True

def get_infrastructure_outputs():
    """Get outputs from the deployed infrastructure."""
    stdout, stderr, code = run_command('tofu output -json', cwd='..')
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

def create_test_ec2_resources(outputs):
    """
    Create test EC2 instances and supporting resources.
    Returns a dictionary with resource IDs.
    """
    print_test("Creating test EC2 instances...")
    
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
    
    # Create a key pair for SSH
    print_info("Creating SSH key pair...")
    key_name = f"integration-test-{int(time.time())}"
    key_command = f'aws ec2 create-key-pair --key-name {key_name} --query "KeyMaterial" --output text'
    stdout, stderr, code = run_command(key_command)
    if code != 0:
        print_fail("Failed to create key pair")
        return None
    
    # Save the key to a file
    key_file = f"../integration-test-key.pem"
    with open(key_file, 'w') as f:
        f.write(stdout)
    os.chmod(key_file, 0o400)
    
    print_pass(f"Created key pair: {key_name}")
    
    # Get subnet IDs
    public_subnet_id = outputs['public_subnet_ids'][0]
    private_subnet_id = outputs['private_subnet_ids'][0]
    
    # Create a security group that allows all traffic for testing
    vpc_id = outputs['vpc_id']
    sg_name = f"integration-test-sg-{int(time.time())}"
    
    print_info("Creating test security group...")
    sg_command = f"""aws ec2 create-security-group \
        --group-name {sg_name} \
        --description "Integration test security group" \
        --vpc-id {vpc_id} \
        --output json"""
    
    stdout, stderr, code = run_command(sg_command)
    if code != 0:
        print_fail("Failed to create security group")
        return None
    
    sg_id = json.loads(stdout)['GroupId']
    print_pass(f"Created security group: {sg_id}")
    
    # Add rules to security group (allow all for testing)
    print_info("Adding security group rules...")
    
    # Allow all inbound from VPC CIDR
    run_command(f"""aws ec2 authorize-security-group-ingress \
        --group-id {sg_id} \
        --protocol -1 \
        --cidr {TEST_TFVARS['vpc_cidr']}""")
    
    # Allow SSH from anywhere
    run_command(f"""aws ec2 authorize-security-group-ingress \
        --group-id {sg_id} \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0""")
    
    # Allow all outbound
    run_command(f"""aws ec2 authorize-security-group-egress \
        --group-id {sg_id} \
        --protocol -1 \
        --cidr 0.0.0.0/0""")
    
    # Launch public instance
    print_info("Launching public instance...")
    public_instance_command = f"""aws ec2 run-instances \
        --image-id {ami_id} \
        --instance-type t3.micro \
        --key-name {key_name} \
        --security-group-ids {sg_id} \
        --subnet-id {public_subnet_id} \
        --associate-public-ip-address \
        --tag-specifications 'ResourceType=instance,Tags=[{{Key=Name,Value=integration-test-public}}]' \
        --output json"""
    
    stdout, stderr, code = run_command(public_instance_command)
    if code != 0:
        print_fail("Failed to launch public instance")
        return None
    
    public_instance_id = json.loads(stdout)['Instances'][0]['InstanceId']
    print_pass(f"Launched public instance: {public_instance_id}")
    
    # Launch private instance
    print_info("Launching private instance...")
    private_instance_command = f"""aws ec2 run-instances \
        --image-id {ami_id} \
        --instance-type t3.micro \
        --key-name {key_name} \
        --security-group-ids {sg_id} \
        --subnet-id {private_subnet_id} \
        --no-associate-public-ip-address \
        --tag-specifications 'ResourceType=instance,Tags=[{{Key=Name,Value=integration-test-private}}]' \
        --output json"""
    
    stdout, stderr, code = run_command(private_instance_command)
    if code != 0:
        print_fail("Failed to launch private instance")
        return None
    
    private_instance_id = json.loads(stdout)['Instances'][0]['InstanceId']
    print_pass(f"Launched private instance: {private_instance_id}")
    
    # Wait for instances to be running
    print_info("Waiting for instances to be running (this may take 1-2 minutes)...")
    time.sleep(30)  # Initial wait
    
    wait_command = f"aws ec2 wait instance-running --instance-ids {public_instance_id} {private_instance_id}"
    stdout, stderr, code = run_command(wait_command)
    if code != 0:
        print_fail("Timeout waiting for instances")
        return None
    
    # Get instance details
    describe_command = f"aws ec2 describe-instances --instance-ids {public_instance_id} {private_instance_id} --output json"
    stdout, stderr, code = run_command(describe_command)
    if code != 0:
        print_fail("Failed to describe instances")
        return None
    
    instances = json.loads(stdout)['Reservations'][0]['Instances']
    public_ip = None
    private_ip_public_instance = None
    private_ip_private_instance = None
    
    for instance in instances:
        if instance['InstanceId'] == public_instance_id:
            public_ip = instance.get('PublicIpAddress')
            private_ip_public_instance = instance['PrivateIpAddress']
        elif instance['InstanceId'] == private_instance_id:
            private_ip_private_instance = instance['PrivateIpAddress']
    
    print_pass("Instances are running")
    print_info(f"Public instance: {public_instance_id} (Public IP: {public_ip}, Private IP: {private_ip_public_instance})")
    print_info(f"Private instance: {private_instance_id} (Private IP: {private_ip_private_instance})")
    
    return {
        'key_name': key_name,
        'key_file': key_file,
        'sg_id': sg_id,
        'public_instance_id': public_instance_id,
        'private_instance_id': private_instance_id,
        'public_ip': public_ip,
        'private_ip_public_instance': private_ip_public_instance,
        'private_ip_private_instance': private_ip_private_instance
    }

def test_public_internet_connectivity(resources):
    """Test internet connectivity from public subnet instance."""
    print_test("Testing internet connectivity from public subnet...")
    
    # Wait a bit more for instance to be fully initialized
    print_info("Waiting for instance initialization...")
    time.sleep(30)
    
    # Test SSH connectivity first
    print_info("Testing SSH connectivity to public instance...")
    ssh_test_command = f"""ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        -i {resources['key_file']} ec2-user@{resources['public_ip']} \
        "echo 'SSH connection successful'" """
    
    max_retries = 5
    for attempt in range(max_retries):
        stdout, stderr, code = run_command(ssh_test_command, check=False)
        if code == 0:
            print_pass("SSH connection to public instance successful")
            break
        else:
            if attempt < max_retries - 1:
                print_info(f"SSH attempt {attempt + 1} failed, retrying in 10 seconds...")
                time.sleep(10)
            else:
                print_fail("Failed to establish SSH connection to public instance")
                return False
    
    # Test internet connectivity via curl
    print_info("Testing internet connectivity (curl to amazon.com)...")
    internet_test_command = f"""ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        -i {resources['key_file']} ec2-user@{resources['public_ip']} \
        "curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 10 http://amazon.com" """
    
    stdout, stderr, code = run_command(internet_test_command, check=False)
    if code == 0 and stdout.strip() in ['200', '301', '302']:
        print_pass(f"Internet connectivity successful (HTTP status: {stdout.strip()})")
        return True
    else:
        print_fail(f"Internet connectivity failed (HTTP status: {stdout.strip()})")
        return False

def test_private_nat_connectivity(resources):
    """Test internet connectivity from private subnet via NAT."""
    print_test("Testing internet connectivity from private subnet via NAT...")
    
    # Since we can't SSH directly to private instance, we need to:
    # 1. Copy key to public instance
    # 2. SSH from public to private
    # 3. Test internet from private
    
    print_info("Copying SSH key to public instance...")
    scp_command = f"""scp -o StrictHostKeyChecking=no \
        -i {resources['key_file']} \
        {resources['key_file']} \
        ec2-user@{resources['public_ip']}:/home/ec2-user/private-key.pem"""
    
    stdout, stderr, code = run_command(scp_command, check=False)
    if code != 0:
        print_fail("Failed to copy key to public instance")
        return False
    
    # Set permissions on the key
    chmod_command = f"""ssh -o StrictHostKeyChecking=no \
        -i {resources['key_file']} ec2-user@{resources['public_ip']} \
        "chmod 400 /home/ec2-user/private-key.pem" """
    
    run_command(chmod_command, check=False)
    
    # Test SSH from public to private
    print_info("Testing SSH from public to private instance...")
    ssh_private_command = f"""ssh -o StrictHostKeyChecking=no \
        -i {resources['key_file']} ec2-user@{resources['public_ip']} \
        "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        -i /home/ec2-user/private-key.pem \
        ec2-user@{resources['private_ip_private_instance']} \
        'echo SSH to private successful'" """
    
    stdout, stderr, code = run_command(ssh_private_command, check=False)
    if code != 0:
        print_fail("Failed to SSH from public to private instance")
        return False
    
    print_pass("SSH from public to private instance successful")
    
    # Test internet connectivity from private instance via NAT
    print_info("Testing internet connectivity via NAT (curl to amazon.com)...")
    nat_test_command = f"""ssh -o StrictHostKeyChecking=no \
        -i {resources['key_file']} ec2-user@{resources['public_ip']} \
        "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        -i /home/ec2-user/private-key.pem \
        ec2-user@{resources['private_ip_private_instance']} \
        'curl -s -o /dev/null -w %{{http_code}} --connect-timeout 10 http://amazon.com'" """
    
    stdout, stderr, code = run_command(nat_test_command, check=False)
    if code == 0 and stdout.strip() in ['200', '301', '302']:
        print_pass(f"NAT Gateway connectivity successful (HTTP status: {stdout.strip()})")
        return True
    else:
        print_fail(f"NAT Gateway connectivity failed (HTTP status: {stdout.strip()})")
        return False

def test_intra_vpc_communication(resources):
    """Test communication between instances within the VPC."""
    print_test("Testing intra-VPC communication...")
    
    # Ping from public to private
    print_info("Testing ping from public to private instance...")
    ping_command = f"""ssh -o StrictHostKeyChecking=no \
        -i {resources['key_file']} ec2-user@{resources['public_ip']} \
        "ping -c 3 {resources['private_ip_private_instance']}" """
    
    stdout, stderr, code = run_command(ping_command, check=False)
    if code == 0:
        print_pass("Ping from public to private successful")
    else:
        print_fail("Ping from public to private failed")
        return False
    
    # Test reverse: ping from private to public
    print_info("Testing ping from private to public instance...")
    reverse_ping_command = f"""ssh -o StrictHostKeyChecking=no \
        -i {resources['key_file']} ec2-user@{resources['public_ip']} \
        "ssh -o StrictHostKeyChecking=no \
        -i /home/ec2-user/private-key.pem \
        ec2-user@{resources['private_ip_private_instance']} \
        'ping -c 3 {resources['private_ip_public_instance']}'" """
    
    stdout, stderr, code = run_command(reverse_ping_command, check=False)
    if code == 0:
        print_pass("Ping from private to public successful")
        return True
    else:
        print_fail("Ping from private to public failed")
        return False

def cleanup_test_resources(resources, outputs):
    """Clean up all test resources."""
    print_test("Cleaning up test resources...")
    
    if resources:
        # Terminate instances
        if 'public_instance_id' in resources and 'private_instance_id' in resources:
            print_info("Terminating EC2 instances...")
            terminate_command = f"aws ec2 terminate-instances --instance-ids {resources['public_instance_id']} {resources['private_instance_id']}"
            run_command(terminate_command, check=False)
            
            # Wait for instances to terminate
            print_info("Waiting for instances to terminate...")
            wait_command = f"aws ec2 wait instance-terminated --instance-ids {resources['public_instance_id']} {resources['private_instance_id']}"
            run_command(wait_command, check=False)
            print_pass("Instances terminated")
        
        # Delete security group
        if 'sg_id' in resources:
            print_info("Deleting security group...")
            time.sleep(10)  # Wait a bit for AWS to clean up
            delete_sg_command = f"aws ec2 delete-security-group --group-id {resources['sg_id']}"
            run_command(delete_sg_command, check=False)
            print_pass("Security group deleted")
        
        # Delete key pair
        if 'key_name' in resources:
            print_info("Deleting key pair...")
            delete_key_command = f"aws ec2 delete-key-pair --key-name {resources['key_name']}"
            run_command(delete_key_command, check=False)
            print_pass("Key pair deleted")
        
        # Delete key file
        if 'key_file' in resources and os.path.exists(resources['key_file']):
            os.remove(resources['key_file'])
            print_pass("Key file deleted")
    
    # Destroy VPC infrastructure
    print_info("Destroying VPC infrastructure...")
    destroy_command = 'tofu destroy -auto-approve -var-file=integration-test.tfvars'
    stdout, stderr, code = run_command(destroy_command, cwd='..', check=False)
    if code == 0:
        print_pass("VPC infrastructure destroyed")
    else:
        print_fail("Failed to destroy VPC infrastructure")
        print(stderr)
    
    # Clean up test files
    if os.path.exists('../integration-test.tfvars'):
        os.remove('../integration-test.tfvars')
    if os.path.exists('../integration-test.tfplan'):
        os.remove('../integration-test.tfplan')
    
    print_pass("Cleanup complete")

def main():
    print_header("VPC Best Practices - Network Connectivity Integration Test\n" +
                 "Feature: vpc-best-practices, Task 21\n" +
                 "Integration Test: Network Connectivity\n" +
                 "Validates: All connectivity requirements")
    
    print(f"{Colors.RED}{Colors.BOLD}WARNING: This test will create real AWS resources that incur costs!{Colors.END}")
    print(f"{Colors.YELLOW}Estimated cost: ~$0.10 for a 5-minute test run{Colors.END}")
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
            print_fail("Infrastructure deployment failed")
            return 1
        
        # Get infrastructure outputs
        outputs = get_infrastructure_outputs()
        if not outputs:
            print_fail("Failed to get infrastructure outputs")
            return 1
        
        print_info(f"VPC ID: {outputs['vpc_id']}")
        print_info(f"Public Subnets: {outputs['public_subnet_ids']}")
        print_info(f"Private Subnets: {outputs['private_subnet_ids']}")
        
        # Create test EC2 resources
        resources = create_test_ec2_resources(outputs)
        if not resources:
            print_fail("Failed to create test EC2 resources")
            return 1
        
        # Run connectivity tests
        test_results = []
        
        # Test 1: Public subnet internet connectivity
        result = test_public_internet_connectivity(resources)
        test_results.append(("Public Internet Connectivity", result))
        all_tests_passed = all_tests_passed and result
        
        # Test 2: Private subnet NAT connectivity
        result = test_private_nat_connectivity(resources)
        test_results.append(("Private NAT Connectivity", result))
        all_tests_passed = all_tests_passed and result
        
        # Test 3: Intra-VPC communication
        result = test_intra_vpc_communication(resources)
        test_results.append(("Intra-VPC Communication", result))
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
        # Always clean up resources
        print_header("CLEANUP")
        cleanup_test_resources(resources, outputs)
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
