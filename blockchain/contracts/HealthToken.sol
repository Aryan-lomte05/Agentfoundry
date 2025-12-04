// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title HealthToken
 * @dev ERC-20 token for healthcare rewards
 */
contract HealthToken is ERC20, Ownable {
    
    // Token rewards for different activities
    uint256 public constant ADHERENCE_REWARD = 10 * 10**18;  // 10 tokens
    uint256 public constant TREATMENT_COMPLETION_REWARD = 50 * 10**18;  // 50 tokens
    uint256 public constant STREAK_BONUS_PER_DAY = 2 * 10**18;  // 2 tokens per day
    
    // Authorized addresses that can mint rewards
    mapping(address => bool) public authorizedMinters;
    
    // Patient reward history
    struct RewardRecord {
        address patient;
        uint256 amount;
        string reason;
        uint256 timestamp;
    }
    
    RewardRecord[] public rewardHistory;
    
    // Patient streak tracking
    mapping(address => uint256) public patientStreaks;
    
    // Events
    event RewardMinted(
        address indexed patient,
        uint256 amount,
        string reason,
        uint256 timestamp
    );
    
    event StreakUpdated(
        address indexed patient,
        uint256 newStreak
    );
    
    constructor() ERC20("HealthToken", "HLTH") Ownable(msg.sender) {
        // Mint initial supply to contract owner
        _mint(msg.sender, 1000000 * 10**18);  // 1 million tokens
        
        // Set contract owner as authorized minter
        authorizedMinters[msg.sender] = true;
    }
    
    modifier onlyAuthorized() {
        require(authorizedMinters[msg.sender], "Not authorized to mint");
        _;
    }
    
    /**
     * @dev Add authorized minter
     */
    function addAuthorizedMinter(address minter) public onlyOwner {
        authorizedMinters[minter] = true;
    }
    
    /**
     * @dev Remove authorized minter
     */
    function removeAuthorizedMinter(address minter) public onlyOwner {
        authorizedMinters[minter] = false;
    }
    
    /**
     * @dev Mint reward tokens to patient
     * @param patient Patient address
     * @param amount Amount to mint
     * @param reason Reason for reward
     */
    function mintReward(
        address patient,
        uint256 amount,
        string memory reason
    ) public onlyAuthorized {
        require(patient != address(0), "Invalid patient address");
        require(amount > 0, "Amount must be positive");
        
        _mint(patient, amount);
        
        // Record reward
        rewardHistory.push(RewardRecord({
            patient: patient,
            amount: amount,
            reason: reason,
            timestamp: block.timestamp
        }));
        
        emit RewardMinted(patient, amount, reason, block.timestamp);
    }
    
    /**
     * @dev Reward adherence with streak bonus
     * @param patient Patient address
     * @param streakDays Number of consecutive days
     */
    function rewardAdherence(address patient, uint256 streakDays) public onlyAuthorized {
        require(patient != address(0), "Invalid patient address");
        
        uint256 baseReward = ADHERENCE_REWARD;
        uint256 streakBonus = streakDays * STREAK_BONUS_PER_DAY;
        uint256 totalReward = baseReward + streakBonus;
        
        _mint(patient, totalReward);
        
        patientStreaks[patient] = streakDays;
        
        rewardHistory.push(RewardRecord({
            patient: patient,
            amount: totalReward,
            reason: string(abi.encodePacked("Adherence: ", uintToString(streakDays), " day streak")),
            timestamp: block.timestamp
        }));
        
        emit RewardMinted(patient, totalReward, "Adherence reward", block.timestamp);
        emit StreakUpdated(patient, streakDays);
    }
    
    /**
     * @dev Reward treatment completion
     * @param patient Patient address
     */
    function rewardTreatmentCompletion(address patient) public onlyAuthorized {
        require(patient != address(0), "Invalid patient address");
        
        _mint(patient, TREATMENT_COMPLETION_REWARD);
        
        rewardHistory.push(RewardRecord({
            patient: patient,
            amount: TREATMENT_COMPLETION_REWARD,
            reason: "Treatment completion",
            timestamp: block.timestamp
        }));
        
        emit RewardMinted(patient, TREATMENT_COMPLETION_REWARD, "Treatment completion", block.timestamp);
    }
    
    /**
     * @dev Get patient's reward history count
     */
    function getRewardHistoryCount() public view returns (uint256) {
        return rewardHistory.length;
    }
    
    /**
     * @dev Get patient's current streak
     */
    function getPatientStreak(address patient) public view returns (uint256) {
        return patientStreaks[patient];
    }
    
    /**
     * @dev Burn tokens to unlock premium features
     * @param amount Amount to burn
     */
    function burnForPremium(uint256 amount) public {
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        _burn(msg.sender, amount);
    }
    
    // Helper function to convert uint to string
    function uintToString(uint256 v) internal pure returns (string memory) {
        if (v == 0) {
            return "0";
        }
        uint256 j = v;
        uint256 len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        bytes memory bstr = new bytes(len);
        uint256 k = len;
        while (v != 0) {
            k = k - 1;
            uint8 temp = (48 + uint8(v - v / 10 * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            v /= 10;
        }
        return string(bstr);
    }
}
