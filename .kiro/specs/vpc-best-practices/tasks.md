# Implementation Plan: VPC Best Practices Deployment

## Overview

This implementation plan breaks down the production-ready VPC deployment into discrete, testable tasks. Each task builds incrementally toward a complete, highly available, and secure network infrastructure following AWS best practices. The plan emphasizes property-based testing to ensure correctness across all deployment variations.

## Tasks

### Phase 1: Foundation Setup

- [x] 1. Set up project structure and provider configuration
  - Create directory structure for VPC best practices module
  - Set up versions.tf with OpenTofu and AWS provider constraints
  - Configure data.tf with availability zone discovery
  - Create locals.tf for common calculations
  - _Requirements: 10.1, 10.7_

- [x] 2. Implement comprehensive variable definitions
  - Create variables.tf with all VPC, subnet, NAT, and security variables
  - Add validation rules for CIDR blocks, NAT strategy, and AZ configuration
  - Set appropriate defaults for production and cost-optimized deployments
  - Create terraform.tfvars.example with multiple deployment scenarios
  - _Requirements: 10.2, 8.1_

- [x] 2.1 Write property test for variable validation
  - Test CIDR block validation across various inputs
  - Test NAT strategy validation
  - Test subnet CIDR allocation logic
  - **Property: Variable validation compliance**
  - **Validates: Requirements 10.2**

### Phase 2: VPC and Subnet Creation

- [x] 3. Implement VPC resource with best practices
  - Create VPC resource with /16 CIDR block
  - Enable DNS hostnames and DNS support
  - Apply comprehensive tagging strategy
  - Configure instance tenancy
  - _Requirements: 1.1, 1.3, 1.4, 10.8_

- [x] 3.1 Write property test for VPC CIDR configuration
  - **Property 1: VPC CIDR Configuration Compliance**
  - Test VPC creation with various CIDR blocks
  - Verify DNS settings are enabled
  - Validate VPC exists in correct region
  - **Validates: Requirements 1.1, 1.3, 1.4**

- [ ] 4. Implement public subnet configuration
  - Create public subnets across multiple AZs
  - Enable map_public_ip_on_launch for public subnets
  - Apply appropriate CIDR allocation (10.0.1.0/24, 10.0.2.0/24, etc.)
  - Add subnet-specific tags
  - _Requirements: 2.1, 2.3, 2.4, 2.6, 2.8_

- [ ] 5. Implement private subnet configuration
  - Create private subnets across multiple AZs
  - Disable auto-assign public IP for private subnets
  - Apply appropriate CIDR allocation (10.0.11.0/24, 10.0.12.0/24, etc.)
  - Add subnet-specific tags
  - _Requirements: 2.2, 2.3, 2.5, 2.7, 2.8_

- [ ] 5.1 Write property test for subnet distribution
  - **Property 2: Multi-AZ Subnet Distribution**
  - Test subnet creation across 2, 3, and 4 AZs
  - Verify exactly N public and N private subnets for N AZs
  - Validate no CIDR overlap between subnets
  - Verify each subnet in different AZ
  - **Validates: Requirements 1.2, 2.1, 2.2, 2.3**

- [ ] 5.2 Write property test for public subnet configuration
  - **Property 3: Public Subnet Configuration Compliance**
  - Verify map_public_ip_on_launch is enabled
  - Test across different AZ configurations
  - **Validates: Requirements 2.4, 2.6, 3.2**

- [ ] 5.3 Write property test for private subnet configuration
  - **Property 4: Private Subnet Configuration Compliance**
  - Verify map_public_ip_on_launch is disabled
  - Test across different AZ configurations
  - **Validates: Requirements 2.5, 2.7, 3.3, 3.5**

### Phase 3: Internet Connectivity

- [ ] 6. Implement Internet Gateway
  - Create Internet Gateway resource
  - Attach IGW to VPC
  - Apply consistent naming and tagging
  - _Requirements: 3.1_

- [ ] 6.1 Write property test for Internet Gateway
  - **Property 6: Internet Gateway Attachment**
  - Verify exactly one IGW per VPC
  - Validate IGW is attached to VPC
  - **Validates: Requirements 3.1, 3.7**

- [ ] 7. Implement NAT Gateway with HA strategy
  - Create Elastic IP resources for NAT Gateways
  - Implement conditional NAT Gateway creation based on strategy
  - Deploy NAT Gateway per AZ for 'per_az' strategy
  - Deploy single NAT Gateway for 'single' strategy
  - Apply appropriate tags indicating AZ assignment
  - _Requirements: 3.3, 3.4, 3.6, 7.2, 8.1_

- [ ] 7.1 Write property test for NAT Gateway HA
  - **Property 5: NAT Gateway High Availability**
  - Test 'per_az' strategy creates one NAT per AZ
  - Verify each NAT in public subnet
  - Validate each NAT has Elastic IP
  - Test 'single' strategy creates only one NAT
  - **Validates: Requirements 3.3, 3.4, 3.6, 7.2**

- [ ] 7.2 Write property test for cost optimization
  - **Property 16: Cost Optimization Options**
  - Verify single NAT strategy minimizes resources
  - Test cost-effective configuration options
  - **Validates: Requirements 8.1, 8.3**

### Phase 4: Routing Configuration

- [ ] 8. Implement public route tables
  - Create public route table with route to IGW
  - Associate public subnets with public route table
  - Apply consistent naming and tags
  - _Requirements: 3.2, 3.7_

- [ ] 9. Implement private route tables
  - Create private route table per AZ (for HA NAT strategy)
  - Add routes to appropriate NAT Gateway
  - Associate private subnets with their AZ's route table
  - Handle single NAT strategy with shared route table
  - _Requirements: 3.5, 3.7, 7.5_

- [ ] 9.1 Write property test for route table associations
  - **Property 20: Route Table Associations**
  - Verify all subnets have explicit route table associations
  - Validate public subnets route to IGW
  - Validate private subnets route to NAT Gateway
  - Test across different NAT strategies
  - **Validates: Requirements 3.7, 3.2, 3.5**

### Phase 5: Network Access Control Lists

- [ ] 10. Implement public NACL
  - Create public NACL with appropriate rules
  - Add inbound rules for HTTP (80), HTTPS (443), SSH (22)
  - Add inbound rule for ephemeral ports (1024-65535)
  - Add corresponding outbound rules
  - Associate with public subnets
  - Use rule numbering that allows insertions (100, 110, 120, etc.)
  - _Requirements: 4.1, 4.2, 4.3, 4.6, 4.7_

- [ ] 10.1 Write property test for public NACL rules
  - **Property 7: Public NACL Rules Compliance**
  - Verify all required inbound ports are allowed
  - Verify ephemeral ports are open
  - Validate outbound rules match inbound
  - Test rule ordering and numbering
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.6, 4.7**

- [ ] 11. Implement private NACL
  - Create private NACL with restrictive rules
  - Add inbound rules for VPC CIDR and ephemeral ports
  - Add outbound rules for VPC CIDR and HTTPS
  - Associate with private subnets
  - Use appropriate rule numbering
  - _Requirements: 4.4, 4.5, 4.6, 4.7_

- [ ] 11.1 Write property test for private NACL rules
  - **Property 8: Private NACL Rules Compliance**
  - Verify only VPC CIDR is allowed inbound
  - Validate ephemeral ports for responses
  - Test outbound restrictions
  - **Validates: Requirements 4.4, 4.5, 4.6, 4.7**

### Phase 6: Security Group Implementation

- [ ] 12. Implement bastion security group
  - Create bastion security group with descriptive name
  - Add ingress rule for SSH from admin CIDR blocks
  - Add egress rule for SSH to application security group
  - Apply comprehensive tags
  - _Requirements: 5.1, 5.2, 5.6_

- [ ] 12.1 Write property test for bastion security group
  - **Property 10: Bastion Security Group Rules**
  - Verify SSH ingress from admin CIDRs only
  - Validate outbound SSH to app SG only
  - Test with different admin CIDR configurations
  - **Validates: Requirements 5.2**

- [ ] 13. Implement web tier security group
  - Create web security group for load balancers/web servers
  - Add ingress rules for HTTP (80) and HTTPS (443) from internet
  - Add egress rule to application security group
  - Document rule justifications
  - _Requirements: 5.1, 5.3, 5.6, 9.5_

- [ ] 13.1 Write property test for web security group
  - **Property 11: Web Security Group Rules**
  - Verify HTTP/HTTPS from internet
  - Validate outbound to app SG only
  - Test rule references vs CIDR blocks
  - **Validates: Requirements 5.3**

- [ ] 14. Implement application tier security group
  - Create application security group
  - Add ingress from web SG and bastion SG
  - Add egress to database SG and HTTPS to internet
  - Use security group references for ingress rules
  - _Requirements: 5.1, 5.4, 5.6, 5.7_

- [ ] 14.1 Write property test for application security group
  - **Property 12: Application Security Group Rules**
  - Verify ingress only from web and bastion SGs
  - Validate outbound to DB SG and internet HTTPS
  - Test security group reference chain
  - **Validates: Requirements 5.4, 5.7**

- [ ] 15. Implement database tier security group
  - Create database security group
  - Add ingress from application SG only
  - Configure minimal explicit egress rules
  - Document least privilege approach
  - _Requirements: 5.1, 5.5, 5.6, 5.8_

- [ ] 15.1 Write property test for database security group
  - **Property 13: Database Security Group Rules**
  - Verify ingress only from app SG
  - Validate minimal egress configuration
  - Test isolation from internet
  - **Validates: Requirements 5.5, 5.8**

- [ ] 15.2 Write comprehensive property test for security group layering
  - **Property 9: Security Group Layering**
  - Verify all four SG tiers exist
  - Validate naming conventions
  - Test descriptions are descriptive
  - **Validates: Requirements 5.1, 5.6**

### Phase 7: Monitoring and Logging

- [ ] 16. Implement VPC Flow Logs
  - Create CloudWatch Log Group for flow logs
  - Create IAM role for VPC Flow Logs service
  - Attach policy allowing logs:* actions
  - Create VPC Flow Log resource
  - Configure to capture ALL traffic
  - Make flow logs optional via variable
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 16.1 Write property test for VPC Flow Logs
  - **Property 14: VPC Flow Logs Configuration**
  - Verify flow logs enabled when variable is true
  - Validate ALL traffic capture setting
  - Test CloudWatch integration
  - Verify IAM role and policy
  - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

### Phase 8: High Availability Validation

- [ ] 17. Write property test for HA resource distribution
  - **Property 15: High Availability Resource Distribution**
  - Verify critical resources across >= 2 AZs
  - Test NAT Gateway redundancy
  - Validate AZ tagging
  - Simulate AZ failure scenarios
  - **Validates: Requirements 7.1, 7.2, 7.4**

### Phase 9: Security Best Practices

- [ ] 18. Implement security hardening
  - Restrict default security group (remove all rules)
  - Ensure default NACL remains with default rules
  - Document security group rule justifications
  - _Requirements: 9.1, 9.2, 9.4, 9.5_

- [ ] 18.1 Write property test for security best practices
  - **Property 18: Security Best Practices Compliance**
  - Verify default SG has no rules
  - Validate no public IPs in private subnets
  - Test least privilege enforcement
  - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.7**

### Phase 10: Outputs and Documentation

- [ ] 19. Implement comprehensive outputs
  - Add outputs for VPC ID and CIDR
  - Add outputs for all subnet IDs (grouped by type)
  - Add outputs for NAT Gateway IDs and EIPs
  - Add outputs for security group IDs (as map)
  - Add output for Internet Gateway ID
  - Add outputs for route table IDs
  - Format outputs for easy consumption by other modules
  - _Requirements: 10.3_

- [ ] 19.1 Write property test for infrastructure code organization
  - **Property 19: Infrastructure Code Organization**
  - Verify logical file organization
  - Validate all values are parameterized
  - Test output completeness
  - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7**

- [ ] 20. Implement resource tagging strategy
  - Create locals.tf with common tags
  - Apply tags to all resources
  - Add subnet-specific tags
  - Include cost center and owner tags
  - _Requirements: 8.4, 10.8_

- [ ] 20.1 Write property test for tagging consistency
  - **Property 17: Resource Tagging Consistency**
  - Verify all resources have required tags
  - Validate tag format and values
  - Test subnet-specific tags
  - **Validates: Requirements 8.4, 10.8**

### Phase 11: Integration Testing

- [ ] 21. Write integration test for network connectivity
  - Deploy test EC2 instances in public and private subnets
  - Test internet connectivity from public subnet
  - Test internet connectivity from private subnet via NAT
  - Test intra-VPC communication
  - Verify security group rules block unauthorized access
  - _Requirements: All connectivity requirements_

- [ ] 22. Write integration test for HA behavior
  - Deploy resources across multiple AZs
  - Simulate NAT Gateway failure
  - Verify other AZs continue functioning
  - Test route table failover
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 23. Write integration test for security validation
  - Attempt direct internet access to private subnet (should fail)
  - Test bastion as only entry point
  - Validate security group chain (web -> app -> db)
  - Test NACL effectiveness
  - _Requirements: 9.1, 9.3, 9.4, 9.6_

### Phase 12: Documentation and Examples

- [ ] 24. Create comprehensive README
  - Document architecture and design decisions
  - Provide usage examples for different scenarios
  - Include cost comparison table (HA vs single NAT)
  - Add troubleshooting guide
  - Document prerequisites and dependencies
  - Include architecture diagrams
  - _Requirements: 8.5, 10.6_

- [ ] 25. Create example configurations
  - Create production.tfvars example (HA, all features)
  - Create dev.tfvars example (single NAT, cost-optimized)
  - Create test.tfvars example (minimal setup)
  - Document cost implications of each configuration
  - _Requirements: 8.1, 8.5_

### Phase 13: Final Validation

- [ ] 26. Run complete test suite
  - Execute all property-based tests
  - Run all integration tests
  - Verify test coverage for all requirements
  - Ensure all tests pass consistently
  - _Requirements: 11.1 - 11.8_

- [ ] 27. Perform end-to-end deployment validation
  - Deploy complete VPC stack in test environment
  - Validate all resources created correctly
  - Test connectivity scenarios
  - Verify monitoring and logging
  - Perform cleanup and verify no orphaned resources
  - _Requirements: All requirements_

- [ ] 28. Final checkpoint - Complete validation
  - Review all requirements are met
  - Verify all property tests pass
  - Validate documentation completeness
  - Ensure cost optimization options work
  - Confirm code quality and organization

## Testing Matrix

### Property-Based Tests Summary

| Property # | Description | Requirements | Test Variations |
|-----------|-------------|--------------|-----------------|
| 1 | VPC CIDR Configuration | 1.1, 1.3, 1.4 | Various /16 CIDRs |
| 2 | Multi-AZ Subnet Distribution | 1.2, 2.1-2.3 | 2, 3, 4 AZs |
| 3 | Public Subnet Configuration | 2.4, 2.6, 3.2 | Different AZ counts |
| 4 | Private Subnet Configuration | 2.5, 2.7, 3.3, 3.5 | Different AZ counts |
| 5 | NAT Gateway HA | 3.3, 3.4, 3.6, 7.2 | per_az vs single |
| 6 | Internet Gateway | 3.1, 3.7 | VPC attachment |
| 7 | Public NACL Rules | 4.1-4.3, 4.6-4.7 | Rule variations |
| 8 | Private NACL Rules | 4.4-4.7 | VPC CIDR variations |
| 9 | Security Group Layering | 5.1, 5.6 | All tiers |
| 10 | Bastion SG Rules | 5.2 | Admin CIDR variations |
| 11 | Web SG Rules | 5.3 | Rule references |
| 12 | Application SG Rules | 5.4, 5.7 | SG references |
| 13 | Database SG Rules | 5.5, 5.8 | Isolation rules |
| 14 | VPC Flow Logs | 6.1-6.5 | Enable/disable |
| 15 | HA Distribution | 7.1, 7.2, 7.4 | AZ failure simulation |
| 16 | Cost Optimization | 8.1, 8.3 | NAT strategies |
| 17 | Tagging Consistency | 8.4, 10.8 | Tag variations |
| 18 | Security Best Practices | 9.1-9.4, 9.7 | Security validations |
| 19 | Code Organization | 10.1-10.7 | Module structure |
| 20 | Route Table Associations | 3.7 | Subnet associations |

### Integration Tests Summary

1. **Network Connectivity Test**: End-to-end connectivity validation
2. **High Availability Test**: AZ failure simulation and recovery
3. **Security Validation Test**: Penetration testing and access control
4. **Cost Analysis Test**: Resource counting and cost estimation

## Notes

- All tasks are designed to be incremental and testable
- Property tests should run with minimum 50 iterations each
- Integration tests require real AWS resources and incur costs
- Cleanup is critical after each test run to avoid charges
- NAT Gateway costs ~$32/month per gateway - document clearly
- VPC Flow Logs incur CloudWatch Logs storage costs
- All tests should clean up resources even on failure
- Use separate AWS account or strict cost limits for testing
