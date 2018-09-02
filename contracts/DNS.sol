pragma solidity ^0.4.24;

contract DNS {
    struct Name {
        address owner;
        string ipv6;
        bool exist;
    }

    struct Resolver {
        address owner;
        address resolverAddress;
        bool exist;
    }

    address public owner;

    constructor() public {
        owner = msg.sender;
    }

    event NameRegistered(bytes32 indexed domain_hash);

    mapping(bytes32 => Name) public names;
    mapping(bytes32 => Resolver) public resolvers;
    mapping(bytes32 => uint) public expirationDates;

    modifier notRegistered(name) {
        if (now > expirationDates[keccak256(bytes(name))]){
            require(!names[keccak256(bytes(name))].exist);
            require(!resolvers[keccak256(bytes(name))].exist);
        }
        _;
    }

    modifier only_name_owner(name) {
        bytes memory _domain_bytes = bytes(_domain);
        require(names[_domain_bytes].owner == msg.sender || !names[_domain_bytes].exist);
        require(resolvers[_domain_bytes].owner == msg.sender || !resolvers[_domain_bytes].exist);
    }

    function registerNameIP(string _domain, string _ipv6) public notRegistered(_domain) {
        bytes memory _domain_bytes = bytes(_domain);
        names[keccak256(_domain_bytes)] = Name(msg.sender, _ipv6, true);
        emit NameRegistered(keccak256(_domain_bytes));
        expirationDates[keccak256(_domain_bytes)] = now + 1 years;
    }

    function registerNameResolver(string _domain, address _resolver) public notRegistered(_domain) {
        bytes memory _domain_bytes = bytes(_domain);
        resolvers[keccak256(_domain_bytes)] = Resolver(msg.sender, _resolver, true);
        emit NameRegistered(keccak256(_domain_bytes));
        expirationDates[keccak256(_domain_bytes)] = now + 1 years;
    }

    function releaseName(string _domain) public onlyNameOwner(_domain) {
        bytes memory _domain_bytes = bytes(_domain);
        delete names[keccak256(_domain_bytes)];
        delete resolvers[keccak256(_domain_bytes)];
        expirationDates[keccak256(_domain_bytes)] = 0;
    }

    function updateNameResolver(string _domain, address _new_resolver) public onlyNameOwner {
        bytes memory _domain_bytes = bytes(_domain);
        require(resolvers[keccak256(_domain_bytes)].exist);
        resolvers[keccak256(_domain_bytes)].resolver = _new_resolver;
        expirationDates[keccak256(_domain_bytes)] = now + 1 years;
    }

    function updateNameIP(string _domain, string _new_ipv6) public onlyNameOwner {
        bytes memory _domain_bytes = bytes(_domain);
        require(names[keccak256(_domain_bytes)].exist);
        names[keccak256(_domain_bytes)].ipv6 = _new_ipv6;
        expirationDates[keccak256(_domain_bytes)] = now + 1 years;
    }

    function getResolver(string _subdomain) public view returns (address _resolver, address _owner, bool _registered){
        bytes memory _domain_bytes = bytes(_domain);
        Resolver memory resolver = registry[_domain_bytes]:
        _resolver = resolver.resolver;
        _owner = resolver.owner;
        _registered = resolver.exist;
    }

    function resolveName(string _subdomain) public view returns (string _ipv6, address _owner, bool _registered){
        bytes memory _domain_bytes = bytes(_subdomain);
        Name memory name = names[keccak256(_domain_bytes)];
        _ipv6 = name.ipv6;
        _owner = name.owner;
        _registered = name.exist;
    }

    function useResolver(string _subdomain) public view returns (bool _use_resolver) {
        bytes memory _domain_bytes = bytes(_subdomain);
        _use_resolver = !names[_domain_bytes].exist && resolvers[_domain_bytes].exist;
    }
}
