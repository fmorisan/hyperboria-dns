import sys
import json
from web3 import Web3

ABI = json.loads('[{"constant":false,"inputs":[{"name":"_domain","type":"string"},{"name":"_new_ipv6","type":"string"}],"name":"updateNameIP","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_subdomain","type":"string"}],"name":"useResolver","outputs":[{"name":"_use_resolver","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"bytes32"}],"name":"names","outputs":[{"name":"owner","type":"address"},{"name":"ipv6","type":"string"},{"name":"exist","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_domain","type":"string"},{"name":"_resolver","type":"address"}],"name":"registerNameResolver","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_domain","type":"string"},{"name":"_new_resolver","type":"address"}],"name":"updateNameResolver","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"bytes32"}],"name":"expirationDates","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_subdomain","type":"string"}],"name":"resolveName","outputs":[{"name":"_ipv6","type":"string"},{"name":"_owner","type":"address"},{"name":"_registered","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"bytes32"}],"name":"resolvers","outputs":[{"name":"owner","type":"address"},{"name":"resolverAddress","type":"address"},{"name":"exist","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_domain","type":"string"},{"name":"_ipv6","type":"string"}],"name":"registerNameIP","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"_domain","type":"string"}],"name":"releaseName","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_subdomain","type":"string"}],"name":"getResolver","outputs":[{"name":"_resolver","type":"address"},{"name":"_owner","type":"address"},{"name":"_registered","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"name":"domain_hash","type":"bytes32"}],"name":"NameRegistered","type":"event"}]')
ROOT_RESOLVER_ADDRESS = '0xB57f72D70326ebF1b3578EAc3Cdf884427fD76B3'

w3 = Web3(Web3.HTTPProvider('https://ropsten.infura.io/v3/b3a8ec552d49493d853d3c8e2cc222f1'))
contract = w3.eth.contract(address=ROOT_RESOLVER_ADDRESS, abi=ABI)

import pdb; pdb.set_trace()
domain = 'test.mori.hyperboria'
ip = None

labels = domain.split('.')
while not ip:
    if labels:
        label = labels.pop()
    elif label:
        label = ''
    else:
        break
    if contract.functions.useResolver(_subdomain=label).call():
        new_address = contract.functions.getResolver(_subdomain=label).call()[0]
        print('redirecting query to address {}'.format(new_address))
        contract = w3.eth.contract(address=new_address, abi=ABI)
    else:
        ip_data = contract.functions.resolveName(_subdomain=label).call()
        if not ip_data[2]:
            break
        ip = ip_data[0]

if not ip:
    print("Name {} not found!".format(domain))
else:
    print("Name {} found: ip is {}".format(domain, ip))
