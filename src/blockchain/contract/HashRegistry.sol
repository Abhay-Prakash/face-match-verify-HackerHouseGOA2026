// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title HashRegistry
 * @notice Stores SHA-256 payload hashes from the face-match discovery pipeline.
 *
 * Overwrite behavior: calling storeHash() with a hash that already exists
 * overwrites the previous Record (dataHash, submitter, timestamp). This is
 * intentional for a demo registry — resubmitting the same hash updates metadata
 * rather than reverting. Document this limitation; do not treat timestamp as
 * immutable provenance once a hash has been stored more than once.
 */
contract HashRegistry {
    struct Record {
        bytes32 dataHash;
        address submitter;
        uint256 timestamp;
    }

    mapping(bytes32 => Record) public records;

    event HashStored(bytes32 indexed hash, address indexed submitter, uint256 timestamp);

    function storeHash(bytes32 _hash) external {
        records[_hash] = Record({
            dataHash: _hash,
            submitter: msg.sender,
            timestamp: block.timestamp
        });
        emit HashStored(_hash, msg.sender, block.timestamp);
    }

    /// @return exists True if this hash has been stored at least once.
    /// @return timestamp Unix timestamp (seconds) when the hash was last stored.
    function verifyHash(bytes32 _hash) external view returns (bool exists, uint256 timestamp) {
        Record memory record = records[_hash];
        exists = record.timestamp != 0;
        timestamp = record.timestamp;
    }
}
