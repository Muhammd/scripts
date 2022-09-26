#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import subprocess
import re

#-----------------------------------------------------------------------------
# The script reads an IP address range and list of TCP ports from the command
# line and first runs an ICMP scan against all the IP addresses. Next, a SYN
# scan is run against any live IP addresses discovered during the ICMP scan.
# The SYN scan uses the TCP port list specified on the command line.
#
# Discovered IP addresses, ports, and services are formatted and written to a
# file. The raw Nmap output is also written to files using the -oA switch.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Compiled Regular Expressions
#-----------------------------------------------------------------------------
report_re = re.compile('Nmap scan report for (.*)')
target_re = re.compile('[0-9]+.[0-9]+.[0-9].[0-9]+[0-9/]*')
gnmap_re = re.compile('Host: (.*)Ports:')
version_re = re.compile('# Nmap 6.25 scan initiated')
host_re = re.compile('Host: (.*) .*Ports:')
ports_re = re.compile('Ports: (.*)\sIgnored State:')
os_re = re.compile('OS: (.*)\sSeq Index:')


#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def run_command(cmd):
    print cmd
    p = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    resp = p.stdout.read()
    warnings = p.stderr.read()
    p.stdout.close()
    p.stderr.close()

    # Return any warnings and the raw response.
    return warnings, resp


def print_warnings(warnings):
    for w in warnings.split('\n'):
        if w == '':
            continue
        print '[-] {0}'.format(w)
        if w == 'QUITTING!':
            sys.exit()


def save_targets(file_name, ips):
    print '[*] Saving live target to {0}'.format(file_name)

    out = open(file_name, 'w')
    out.write('\n'.join(ips))
    out.close()


def parse_ports(port_str, broken=False):
    '''
    The 6.25 version of Nmap broke the port format by dropping a field. If
    broken is True then assume we have 6.25 output otherwise do not.
    '''
    ports = []
    for port in port_str.split(','):
        if broken is True:
            num, stat, proto, x, sn, serv, y = port.split('/')
        else:
            num, stat, proto, x, sn, y, serv, z = port.split('/')

        if serv == '':
            service = sn
        else:
            service = serv

        s = '{0}/{1} ({2}) - {3}'.format(proto, num.strip(), stat, service)
        ports.append(s)

    return ports


def parse_gnmap(file_name):
    hosts = {}
    broken = False
    gnmap = open('{0}.gnmap'.format(file_name), 'r')
    for line in gnmap:
        m = version_re.search(line)
        if m is not None:
            broken = True

        m = gnmap_re.search(line)
        if m is not None:
            # Get Hostname
            h = host_re.search(line)
            if h is None:
                host = 'Unknown'
            else:
                host = h.group(1)

            # Get Ports
            p = ports_re.search(line)
            if p is not None:
                ports = parse_ports(p.group(1), broken)
            else:
                ports = ''

            # Get OS
            o = os_re.search(line)
            if o is None:
                os = 'Unknown'
            else:
                os = o.group(1)

            hosts[host] = {'os': os,
                           'ports': ports}

    gnmap.close()

    return hosts

#-----------------------------------------------------------------------------
# Main Program
#-----------------------------------------------------------------------------

#
# Parse command line options
#
usage = '''
USAGE:

discover.py IP_addresses <port_list>

Addresses must be a valid Nmap IP address range and ports must be a valid Nmap
port list. Any ports provided will be added to the default ports that are
scanned: 21, 22, 23, 25, 53, 80, 110, 119, 143, 443, 135, 139, 445, 593, 1352,
1433, 1498, 1521, 3306, 5432, 389, 1494, 1723, 2049, 2598, 3389, 5631, 5800,
5900, and 6000. The script should be run with root privileges.
'''

if len(sys.argv) == 2:
    target = sys.argv[1]
    other_ports = ''
elif len(sys.argv) == 3:
    target = sys.argv[1]
    other_ports = sys.argv[2]
else:
    print usage
    sys.exit()

#
# Setup global variables
#
ping_fname = '{0}_ping_scan'.format(target.replace('/', '.'))
target_fname = '{0}_targets.txt'.format(target.replace('/', '.'))
syn_fname = '{0}_syn_scan'.format(target.replace('/', '.'))
result_fname = '{0}_results.md'.format(target.replace('/', '.'))

ports = '21,22,23,25,53,80,110,119,143,443,135,139,445,593,1352,1433,1498,'
ports += '1521,3306,5432,389,1494,1723,2049,2598,3389,5631,5800,5900,6000'
if other_ports != '':
    ports += ',' + other_ports

#
# Run discovery scans against the address range
#
print '[*] Running discovery scan against targets {0}'.format(target)

# Do we have an IP range as our target?
m = target_re.search(target)
print m
if m is None:
    cmd = 'nmap -sn PE -n -A {0} -iL {0}'.format(ping_fname, target)
else:
    cmd = 'nmap -sn -PE -n -oA {0} {1}'.format(ping_fname, target)

warnings, resp = run_command(cmd)
print_warnings(warnings)

ips = report_re.findall(resp)
print '[+] Found {0} live targets'.format(len(ips))

if len(ips) == 0:
    print '[-] No targets to scan. Quitting.'
    sys.exit()

save_targets(target_fname, ips)
print '[*] Ping scan complete.\n'

#
# Run full scans against each IP address.
#
print '[*] Running full scan on live addresses using ports {0}'.format(ports)
cmd = 'nmap -sS -n -A -p {0} --open '.format(ports)
cmd += '-oA {0} -iL {1}'.format(syn_fname, target_fname)
warnings, resp = run_command(cmd)
print_warnings(warnings)
print '[*] Full scan complete.\n'

#
# Parse full scan results and write them to a file.
#
print '[*] Parsing Scan results.'
hosts = parse_gnmap(syn_fname)

print '[*] Saving results to {0}'.format(result_fname)
out = open(result_fname, 'w')
for host in hosts:
    out.write(host + '\n')
    out.write('=' * len(host) + '\n\n')
    out.write('OS\n')
    out.write('--\n')
    out.write(hosts[host]['os'] + '\n\n')
    out.write('Ports\n')
    out.write('-----\n')
    out.write('\n'.join(hosts[host]['ports']))
    out.write('\n\n\n')

out.close()
print '[*] Parsing results is complete.'
