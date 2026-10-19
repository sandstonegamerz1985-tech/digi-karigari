// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title DigiKarigari
 * @notice Artisan credentials, product provenance, and ETH escrow for the Digi-Karigari marketplace.
 * @dev Government identity review happens off-chain. Only an authorised owner can mark an artisan verified.
 */
contract DigiKarigari is ERC721, Ownable, ReentrancyGuard {
    uint256 private _nextTokenId = 1;
    uint256 public constant ESCROW_TIMEOUT = 30 days;

    enum TokenKind { TrustedPartner, ProductProvenance }
    struct TokenRecord {
        TokenKind kind;
        address artisan;
        bytes32 metadataHash;
    }
    struct Escrow {
        address buyer;
        address artisan;
        uint256 amount;
        uint64 createdAt;
        bool dispatched;
        bool settled;
        bytes32 trackingHash;
    }

    mapping(address => bool) public verifiedArtisan;
    mapping(address => uint256) public credentialToken;
    mapping(uint256 => TokenRecord) public tokenRecords;
    mapping(bytes32 => Escrow) public escrows;

    event ArtisanVerified(address indexed artisan, uint256 indexed credentialTokenId, bytes32 metadataHash);
    event ProductProvenanceMinted(address indexed artisan, uint256 indexed tokenId, bytes32 metadataHash);
    event EscrowCreated(bytes32 indexed orderId, address indexed buyer, address indexed artisan, uint256 amount);
    event DispatchConfirmed(bytes32 indexed orderId, bytes32 trackingHash);
    event EscrowReleased(bytes32 indexed orderId, address indexed artisan, uint256 amount);
    event EscrowRefunded(bytes32 indexed orderId, address indexed buyer, uint256 amount);

    constructor(address initialOwner) ERC721("Digi Karigari Certificate", "DKC") Ownable(initialOwner) {}

    /** @notice Mark an artisan as verified after off-chain identity review and mint their soulbound credential. */
    function verifyArtisan(address artisan, bytes32 metadataHash) external onlyOwner returns (uint256 tokenId) {
        require(artisan != address(0), "Invalid artisan");
        require(!verifiedArtisan[artisan], "Already verified");
        verifiedArtisan[artisan] = true;
        tokenId = _nextTokenId++;
        credentialToken[artisan] = tokenId;
        tokenRecords[tokenId] = TokenRecord(TokenKind.TrustedPartner, artisan, metadataHash);
        _safeMint(artisan, tokenId);
        emit ArtisanVerified(artisan, tokenId, metadataHash);
    }

    /** @notice Mint a provenance certificate for a product made by a verified artisan. */
    function mintProductProvenance(bytes32 metadataHash) external returns (uint256 tokenId) {
        require(verifiedArtisan[msg.sender], "Artisan not verified");
        tokenId = _nextTokenId++;
        tokenRecords[tokenId] = TokenRecord(TokenKind.ProductProvenance, msg.sender, metadataHash);
        _safeMint(msg.sender, tokenId);
        emit ProductProvenanceMinted(msg.sender, tokenId, metadataHash);
    }

    /** @notice Buyer deposits ETH for an order; funds remain locked until dispatch is confirmed and buyer releases. */
    function createEscrow(bytes32 orderId, address payable artisan) external payable nonReentrant {
        require(orderId != bytes32(0), "Invalid order ID");
        require(artisan != address(0) && artisan != msg.sender, "Invalid artisan");
        require(verifiedArtisan[artisan], "Artisan not verified");
        require(msg.value > 0, "Payment required");
        require(escrows[orderId].buyer == address(0), "Order already exists");
        escrows[orderId] = Escrow(msg.sender, artisan, msg.value, uint64(block.timestamp), false, false, bytes32(0));
        emit EscrowCreated(orderId, msg.sender, artisan, msg.value);
    }

    /** @notice Artisan records a courier/tracking reference hash. It does not prove delivery by itself. */
    function confirmDispatch(bytes32 orderId, bytes32 trackingHash) external {
        Escrow storage item = escrows[orderId];
        require(item.buyer != address(0), "Unknown order");
        require(msg.sender == item.artisan, "Only artisan");
        require(!item.settled && !item.dispatched, "Order not open");
        require(trackingHash != bytes32(0), "Tracking hash required");
        item.dispatched = true;
        item.trackingHash = trackingHash;
        emit DispatchConfirmed(orderId, trackingHash);
    }

    /** @notice Buyer releases escrow after reviewing dispatch/tracking details. */
    function releaseEscrow(bytes32 orderId) external nonReentrant {
        Escrow storage item = escrows[orderId];
        require(msg.sender == item.buyer, "Only buyer");
        require(item.dispatched && !item.settled, "Not releasable");
        item.settled = true;
        uint256 amount = item.amount;
        (bool ok, ) = payable(item.artisan).call{value: amount}("");
        require(ok, "Payment transfer failed");
        emit EscrowReleased(orderId, item.artisan, amount);
    }

    /** @notice Buyer may reclaim funds if dispatch was not recorded within the timeout. */
    function refundUndispatched(bytes32 orderId) external nonReentrant {
        Escrow storage item = escrows[orderId];
        require(msg.sender == item.buyer, "Only buyer");
        require(!item.dispatched && !item.settled, "Not refundable");
        require(block.timestamp >= uint256(item.createdAt) + ESCROW_TIMEOUT, "Timeout not reached");
        item.settled = true;
        uint256 amount = item.amount;
        (bool ok, ) = payable(item.buyer).call{value: amount}("");
        require(ok, "Refund failed");
        emit EscrowRefunded(orderId, item.buyer, amount);
    }

    /** @dev Soulbound Trusted Partner credentials cannot be transferred or approved. */
    function approve(address, uint256) public pure override { revert("Credentials are soulbound"); }
    function setApprovalForAll(address, bool) public pure override { revert("Credentials are soulbound"); }
    function transferFrom(address, address, uint256) public pure override { revert("Certificates are non-transferable"); }
    function safeTransferFrom(address, address, uint256) public pure override { revert("Certificates are non-transferable"); }
    function safeTransferFrom(address, address, uint256, bytes memory) public pure override { revert("Certificates are non-transferable"); }

    /** @notice ERC-165 and ERC-721 interface support is inherited from OpenZeppelin ERC721. */
}
