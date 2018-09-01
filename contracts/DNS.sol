pragma solidity ^0.4.24;

contract DNS {
    struct Registry {
        address owner;
        string ipv6;
        bool exist;
    }

    address public owner;

    constructor() public {
        owner = msg.sender;
    }

    mapping(bytes32 => Registry) public registry;

    function registerName(string _domain, string _ipv6) public {
        bytes memory _domain_bytes = bytes(_domain);
        require(!registry[keccak256(_domain_bytes)].exist);
        registry[keccak256(_domain_bytes)] = Registry(msg.sender, _ipv6, true);
    }

    function resolveName(string _domain) public view returns (string _ipv6, address _owner){
        bytes memory _domain_bytes = bytes(_domain);
        require(registry[keccak256(_domain_bytes)].exist);
        Registry memory reg = registry[keccak256(_domain_bytes)];
        _ipv6 = reg.ipv6;
        _owner = reg.owner;
    }
}
