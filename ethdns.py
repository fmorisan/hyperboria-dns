"""DNS server who handle .hyperboria domains."""
import json
import time
import ipaddress

from web3 import Web3

from dnslib import RR, QTYPE, AAAA, RCODE, DNSRecord
from dnslib.server import DNSServer, BaseResolver
from Crypto.Hash import SHA256

payload = [
    '[{"constant":false,"inputs":[{"name":"_domain","type":"string"},{"name',
    '":"_new_ipv6","type":"string"}],"name":"updateNameIP","outputs":[],"pa',
    'yable":false,"stateMutability":"nonpayable","type":"function"},{"const',
    'ant":true,"inputs":[{"name":"_subdomain","type":"string"}],"name":"use',
    'Resolver","outputs":[{"name":"_use_resolver","type":"bool"}],"payable"',
    ':false,"stateMutability":"view","type":"function"},{"constant":true,"i',
    'nputs":[{"name":"","type":"bytes32"}],"name":"names","outputs":[{"name',
    '":"owner","type":"address"},{"name":"ipv6","type":"string"},{"name":"e',
    'xist","type":"bool"}],"payable":false,"stateMutability":"view","type":',
    '"function"},{"constant":false,"inputs":[{"name":"_domain","type":"stri',
    'ng"},{"name":"_resolver","type":"address"}],"name":"registerNameResolv',
    'er","outputs":[],"payable":false,"stateMutability":"nonpayable","type"',
    ':"function"},{"constant":false,"inputs":[{"name":"_domain","type":"str',
    'ing"},{"name":"_new_resolver","type":"address"}],"name":"updateNameRes',
    'olver","outputs":[],"payable":false,"stateMutability":"nonpayable","ty',
    'pe":"function"},{"constant":true,"inputs":[],"name":"owner","outputs":',
    '[{"name":"","type":"address"}],"payable":false,"stateMutability":"view',
    '","type":"function"},{"constant":true,"inputs":[{"name":"","type":"byt',
    'es32"}],"name":"expirationDates","outputs":[{"name":"","type":"uint256',
    '"}],"payable":false,"stateMutability":"view","type":"function"},{"cons',
    'tant":true,"inputs":[{"name":"_subdomain","type":"string"}],"name":"re',
    'solveName","outputs":[{"name":"_ipv6","type":"string"},{"name":"_owner',
    '","type":"address"},{"name":"_registered","type":"bool"}],"payable":fa',
    'lse,"stateMutability":"view","type":"function"},{"constant":true,"inpu',
    'ts":[{"name":"","type":"bytes32"}],"name":"resolvers","outputs":[{"nam',
    'e":"owner","type":"address"},{"name":"resolverAddress","type":"address',
    '"},{"name":"exist","type":"bool"}],"payable":false,"stateMutability":"',
    'view","type":"function"},{"constant":false,"inputs":[{"name":"_domain"',
    ',"type":"string"},{"name":"_ipv6","type":"string"}],"name":"registerNa',
    'meIP","outputs":[],"payable":false,"stateMutability":"nonpayable","typ',
    'e":"function"},{"constant":false,"inputs":[{"name":"_domain","type":"s',
    'tring"}],"name":"releaseName","outputs":[],"payable":false,"stateMutab',
    'ility":"nonpayable","type":"function"},{"constant":true,"inputs":[{"na',
    'me":"_subdomain","type":"string"}],"name":"getResolver","outputs":[{"n',
    'ame":"_resolver","type":"address"},{"name":"_owner","type":"address"},',
    '{"name":"_registered","type":"bool"}],"payable":false,"stateMutability',
    '":"view","type":"function"},{"inputs":[],"payable":false,"stateMutabil',
    'ity":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{',
    '"indexed":true,"name":"domain_hash","type":"bytes32"}],"name":"NameReg',
    'istered","type":"event"}]']

ABI = json.loads(''.join((payload)))
ROOT_RESOLVER_ADDRESS = '0xB57f72D70326ebF1b3578EAc3Cdf884427fD76B3'
URL_PROVIDER = 'https://ropsten.infura.io/v3/b3a8ec552d49493d853d3c8e2cc222f1'

w3 = Web3(Web3.HTTPProvider(URL_PROVIDER))
mapping = {}


class MapResolver(BaseResolver):
    """
    Resolves names by looking in a mapping.
    If `name in mapping` then mapping[name] should return a IP
    else the next server in servers will be asked for name
    """
    def resolve(self, request, handler):
        contract = w3.eth.contract(address=ROOT_RESOLVER_ADDRESS, abi=ABI)
        qname = request.q.qname
        labels = [label.decode('ascii') for label in qname.label]
        reply = request.reply()
        ip = None
        labels_hash = SHA256.new()
        for label in labels:
            labels_hash.update(label.encode('ascii'))
        labels_hash = labels_hash.digest()
        if labels_hash in mapping:
            ip = mapping[labels_hash]
        elif labels[len(labels) - 1] == 'hyperboria':
            while not ip:
                if labels:
                    label = str(labels.pop())
                elif label:
                    label = '.'
                else:
                    break
                if contract.functions.useResolver(_subdomain=label).call():
                    new_address = contract.functions.getResolver(
                        _subdomain=label).call()[0]
                    print('redirecting query to address {}'.format(
                        new_address))
                    contract = w3.eth.contract(address=new_address, abi=ABI)
                else:
                    ip_data = contract.functions.resolveName(
                        _subdomain=label).call()
                    if not ip_data[2]:
                        break
                    ip = ip_data[0]
        if ip:
            try:
                ipaddress.ip_address(ip)
            except Exception as exc:
                print(repr(exc))
                reply.header.rcode = RCODE.NXDOMAIN
                return reply

            print("Name {} found: ip is {}".format('.'.join(labels), ip))
            reply.add_answer(RR(qname, QTYPE.AAAA, ttl=1, rdata=AAAA(ip)))
            mapping[labels_hash] = ip
            return reply
        else:
            proxy_r = request.send('8.8.8.8', 53)
            return DNSRecord.parse(proxy_r)


ethresolver = MapResolver()

if __name__ == '__main__':
    udp_server = DNSServer(ethresolver, port=5353, address='0.0.0.0')
    udp_server.start()
    while udp_server.isAlive():
        time.sleep(1)
