// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title ServiceDeliveryTracker
 * @notice Secure contract for anchoring municipal service reports.
 * @dev Features:
 * - Admin + agent role model
 * - Prevents duplicate anchors (hash -> timestamp)
 * - Emits Anchored events for audit logs
 * @dev Notes:
 * - Deployer/admin should be a multisig on mainnet.
 * - Event-based architecture reduces storage costs.
 */
contract ServiceDeliveryTracker {
    // ============ State Variables ============
    address public admin;
    mapping(address => bool) public isAgent;
    mapping(bytes32 => uint256) public anchoredAt; // hash => timestamp

    // ============ Events ============
    event Anchored(
        uint256 indexed id,
        bytes32 indexed hash,
        uint256 timestamp,
        string eventType,
        address indexed reporter
    );
    event AgentAdded(address indexed agent);
    event AgentRemoved(address indexed agent);
    event AdminTransferred(address indexed oldAdmin, address indexed newAdmin);

    // ============ Errors ============
    error NotAdmin();
    error NotAgent();
    error ZeroAddress();
    error AlreadyAgent();
    error NotAnAgent();
    error ZeroHash();
    error AlreadyAnchored();

    // ============ Modifiers ============
    modifier onlyAdmin() {
        if (msg.sender != admin) revert NotAdmin();
        _;
    }

    modifier onlyAgent() {
        if (!isAgent[msg.sender]) revert NotAgent();
        _;
    }

    // ============ Constructor ============
    constructor() payable {
        admin = msg.sender;
        emit AdminTransferred(address(0), admin); // Initial admin set
    }

    // ============ Admin Functions ============
    /**
     * @notice Add a new agent (authorized reporter).
     * @param agent Address of the new agent.
     */
    function addAgent(address agent) external onlyAdmin {
        if (agent == address(0)) revert ZeroAddress();
        if (isAgent[agent]) revert AlreadyAgent();

        isAgent[agent] = true;
        emit AgentAdded(agent);
    }

    /**
     * @notice Remove an agent.
     * @param agent Address of the agent to remove.
     */
    function removeAgent(address agent) external onlyAdmin {
        if (!isAgent[agent]) revert NotAnAgent();

        isAgent[agent] = false;
        emit AgentRemoved(agent);
    }

    /**
     * @notice Transfer admin rights to a new address.
     * @param newAdmin Address of the new admin.
     */
    function transferAdmin(address newAdmin) external onlyAdmin {
        if (newAdmin == address(0)) revert ZeroAddress();

        emit AdminTransferred(admin, newAdmin);
        admin = newAdmin;
        isAgent[newAdmin] = true; // New admin is implicitly an agent
    }

    // ============ Core Functions ============
    /**
     * @notice Anchor a service report hash to the blockchain.
     * @dev Prevents duplicate anchors and emits an event for auditing.
     * @param id Unique identifier for the report.
     * @param hash Keccak256 hash of the report data.
     * @param eventType Type of event (e.g., "Water", "Electricity").
     */
    function anchorReport(
        uint256 id,
        bytes32 hash,
        string calldata eventType
    ) external onlyAgent {
        if (hash == bytes32(0)) revert ZeroHash();
        if (anchoredAt[hash] != 0) revert AlreadyAnchored();

        anchoredAt[hash] = block.timestamp;
        emit Anchored(id, hash, block.timestamp, eventType, msg.sender);
    }

    /**
     * @notice Check if a hash has been anchored.
     * @param hash Keccak256 hash to check.
     * @return True if anchored, false otherwise.
     */
    function isAnchored(bytes32 hash) external view returns (bool) {
        return anchoredAt[hash] != 0;
    }

    // Cheaper than OpenZeppelin's SafeERC20 for simple transfers
    function transferToken(address token, address to, uint256 amount) internal {
        (bool success, ) = token.call(abi.encodeWithSignature("transfer(address,uint256)", to, amount));
        require(success, "Transfer failed");
    }
}