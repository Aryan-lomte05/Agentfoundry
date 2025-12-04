// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title AgentCommunicationLog
 * @dev Log all agent-to-agent communications for audit trail
 */
contract AgentCommunicationLog {
    
    struct Message {
        address fromAgent;
        address toAgent;
        string messageType;
        bytes32 payloadHash;
        uint256 timestamp;
        bool isCritical;
    }
    
    Message[] public messages;
    
    // Mapping: agent address => message indices
    mapping(address => uint256[]) public agentMessages;
    
    // Authorized agents that can log messages
    mapping(address => bool) public authorizedAgents;
    
    address public owner;
    
    // Events
    event MessageLogged(
        address indexed fromAgent,
        address indexed toAgent,
        string messageType,
        uint256 timestamp,
        bool isCritical
    );
    
    event AgentAuthorized(address indexed agent);
    event AgentDeauthorized(address indexed agent);
    
    constructor() {
        owner = msg.sender;
        authorizedAgents[msg.sender] = true;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }
    
    modifier onlyAuthorized() {
        require(authorizedAgents[msg.sender], "Not authorized");
        _;
    }
    
    /**
     * @dev Authorize an agent to log messages
     */
    function authorizeAgent(address agent) public onlyOwner {
        authorizedAgents[agent] = true;
        emit AgentAuthorized(agent);
    }
    
    /**
     * @dev Deauthorize an agent
     */
    function deauthorizeAgent(address agent) public onlyOwner {
        authorizedAgents[agent] = false;
        emit AgentDeauthorized(agent);
    }
    
    /**
     * @dev Log a message between agents
     */
    function logMessage(
        address toAgent,
        string memory messageType,
        bytes32 payloadHash,
        bool isCritical
    ) public onlyAuthorized {
        require(toAgent != address(0), "Invalid recipient");
        
        Message memory newMessage = Message({
            fromAgent: msg.sender,
            toAgent: toAgent,
            messageType: messageType,
            payloadHash: payloadHash,
            timestamp: block.timestamp,
            isCritical: isCritical
        });
        
        messages.push(newMessage);
        uint256 messageIndex = messages.length - 1;
        
        // Add to both agents' message lists
        agentMessages[msg.sender].push(messageIndex);
        agentMessages[toAgent].push(messageIndex);
        
        emit MessageLogged(msg.sender, toAgent, messageType, block.timestamp, isCritical);
    }
    
    /**
     * @dev Get total message count
     */
    function getMessageCount() public view returns (uint256) {
        return messages.length;
    }
    
    /**
     * @dev Get messages for specific agent
     */
    function getAgentMessages(address agent) public view returns (uint256[] memory) {
        return agentMessages[agent];
    }
    
    /**
     * @dev Get critical messages in time range
     */
    function getCriticalMessages(uint256 fromTime, uint256 toTime) public view returns (Message[] memory) {
        uint256 count = 0;
        
        // Count critical messages in range
        for (uint256 i = 0; i < messages.length; i++) {
            if (messages[i].isCritical && 
                messages[i].timestamp >= fromTime && 
                messages[i].timestamp <= toTime) {
                count++;
            }
        }
        
        // Create array of critical messages
        Message[] memory criticalMessages = new Message[](count);
        uint256 index = 0;
        
        for (uint256 i = 0; i < messages.length; i++) {
            if (messages[i].isCritical && 
                messages[i].timestamp >= fromTime && 
                messages[i].timestamp <= toTime) {
                criticalMessages[index] = messages[i];
                index++;
            }
        }
        
        return criticalMessages;
    }
}
