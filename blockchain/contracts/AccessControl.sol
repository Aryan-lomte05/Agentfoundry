// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title MedicalRecordAccessControl
 * @dev Smart contract for managing medical record access permissions
 */
contract MedicalRecordAccessControl {
    
    struct AccessGrant {
        address doctor;
        uint256 expiry;
        bool isActive;
        bool isEmergency;
        uint256 grantedAt;
    }
    
    // Mapping: patient address => doctor address => AccessGrant
    mapping(address => mapping(address => AccessGrant)) public accessGrants;
    
    // Mapping: patient address => list of doctors with access
    mapping(address => address[]) public patientDoctors;
    
    // Emergency access log
    struct EmergencyAccess {
        address patient;
        address doctor;
        uint256 timestamp;
        string reason;
    }
    
    EmergencyAccess[] public emergencyAccessLog;
    
    // Events
    event AccessGranted(
        address indexed patient,
        address indexed doctor,
        uint256 duration,
        uint256 expiry
    );
    
    event AccessRevoked(
        address indexed patient,
        address indexed doctor,
        uint256 timestamp
    );
    
    event EmergencyAccessGranted(
        address indexed patient,
        address indexed doctor,
        uint256 timestamp,
        string reason
    );
    
    /**
     * @dev Grant access to a doctor
     * @param doctor Address of the doctor
     * @param duration Duration in seconds
     */
    function grantAccess(address doctor, uint256 duration) public {
        require(doctor != address(0), "Invalid doctor address");
        require(duration > 0, "Duration must be positive");
        
        uint256 expiry = block.timestamp + duration;
        
        accessGrants[msg.sender][doctor] = AccessGrant({
            doctor: doctor,
            expiry: expiry,
            isActive: true,
            isEmergency: false,
            grantedAt: block.timestamp
        });
        
        // Add to patient's doctor list if not already present
        bool exists = false;
        for (uint i = 0; i < patientDoctors[msg.sender].length; i++) {
            if (patientDoctors[msg.sender][i] == doctor) {
                exists = true;
                break;
            }
        }
        if (!exists) {
            patientDoctors[msg.sender].push(doctor);
        }
        
        emit AccessGranted(msg.sender, doctor, duration, expiry);
    }
    
    /**
     * @dev Revoke doctor access
     * @param doctor Address of the doctor
     */
    function revokeAccess(address doctor) public {
        require(accessGrants[msg.sender][doctor].isActive, "No active access");
        
        accessGrants[msg.sender][doctor].isActive = false;
        
        emit AccessRevoked(msg.sender, doctor, block.timestamp);
    }
    
    /**
     * @dev Grant emergency access (24 hours, logged)
     * @param patient Patient address
     * @param reason Emergency reason
     */
    function grantEmergencyAccess(address patient, string memory reason) public {
        require(patient != address(0), "Invalid patient address");
        
        uint256 expiry = block.timestamp + 24 hours;
        
        accessGrants[patient][msg.sender] = AccessGrant({
            doctor: msg.sender,
            expiry: expiry,
            isActive: true,
            isEmergency: true,
            grantedAt: block.timestamp
        });
        
        // Log emergency access
        emergencyAccessLog.push(EmergencyAccess({
            patient: patient,
            doctor: msg.sender,
            timestamp: block.timestamp,
            reason: reason
        }));
        
        emit EmergencyAccessGranted(patient, msg.sender, block.timestamp, reason);
    }
    
    /**
     * @dev Check if doctor has valid access
     * @param patient Patient address
     * @param doctor Doctor address
     */
    function hasAccess(address patient, address doctor) public view returns (bool) {
        AccessGrant memory grant = accessGrants[patient][doctor];
        
        if (!grant.isActive) {
            return false;
        }
        
        if (block.timestamp > grant.expiry) {
            return false;
        }
        
        return true;
    }
    
    /**
     * @dev Get all doctors with access to patient
     * @param patient Patient address
     */
    function getPatientDoctors(address patient) public view returns (address[] memory) {
        return patientDoctors[patient];
    }
    
    /**
     * @dev Get emergency access log count
     */
    function getEmergencyAccessCount() public view returns (uint256) {
        return emergencyAccessLog.length;
    }
    
    /**
     * @dev Auto-cleanup expired access grants (called by authorized address)
     */
    function cleanupExpiredGrants(address patient, address[] memory doctors) public {
        for (uint i = 0; i < doctors.length; i++) {
            AccessGrant storage grant = accessGrants[patient][doctors[i]];
            if (grant.isActive && block.timestamp > grant.expiry) {
                grant.isActive = false;
            }
        }
    }
}
