#!/usr/bin/env python2
# encoding: utf-8

import sys
import socket
import logging
logging.getLogger('scapy.runtime').setLevel(logging.ERROR)
from scapy.all import *
from time import time
from math import sqrt

PACKAGES_PER_TTL = 50
PACKAGE_TIMEOUT  = 1
MAX_TTL          = 64

###############################################################################
# Traceroute                                                                  #
###############################################################################

def avg_rtt(ans):
    rtt_total = 0
    for i in range(0, len(ans)):
        rtt_total += ans[i][1].time - ans[i][0].sent_time
    return rtt_total / len(ans) * 1000

def extract_src(ans):
    src = []
    for i in range(0, len(ans)):
        ip = ans[i][1].src
        if ip not in src: src.append(ip)
    return src

def tracehop(hostname, ttl):
    try:
        ans, unans = sr(IP(dst=hostname, ttl=ttl) / ICMP() * PACKAGES_PER_TTL,
                        verbose=0, timeout=PACKAGE_TIMEOUT)

        if len(ans) == 0:
            src = '*'
            rtt = '*'
            destination_reached = False
        else:
            src = extract_src(ans)
            rtt = avg_rtt(ans)
            destination_reached = True if ans[0][1].type == 0 else False

        return {'hop': ttl, 'src': src, 'rtt': rtt}, destination_reached

    except socket.error as e:
        sys.exit(e)

def traceroute(hostname, human):
    hops = []

    for i in range(1, MAX_TTL):
        hop, destination_reached = tracehop(hostname, i)
        hops.append(hop)

        if human:
            if hop['src'] == '*':
                print '%-3d hops away: no reply' % i
            else:
                print '%-3d hops away: %-15s %0.03f ms' % (i, hop['src'][0], hop['rtt'])
                for i in range(1, len(hop['src'])):
                    print '               %s' % hop['src'][i]

        if destination_reached:
            if human: print 'Destination reached.'
            break

    return hops

###############################################################################
# Statistics                                                                  #
###############################################################################

def exclude_noreply(hops):
    return filter(lambda x: x['src'] != '*', hops)

def extract_rtts(hops):
    return map(lambda x: x['rtt'], exclude_noreply(hops))

def mean(rtts):
    return sum(rtts) / len(rtts)

def stdev(rtts):
    n  = len(rtts)
    mu = mean(rtts)
    return sqrt(sum([(rtt - mu)**2 for rtt in rtts]) / n)

def zrtt(rtt, mu, sigma):
    return (rtt - mu) / sigma

###############################################################################
# Main                                                                        #
###############################################################################

def help():
    return 'Usage: %s [hostname]\tfor human-friendly output\n' \
           '       %s [hostname] -m\tfor machine readable output' \
           % (sys.argv[0], sys.argv[0])

if __name__ == '__main__':
    if len(sys.argv) < 2 or len(sys.argv) > 3:     sys.exit(help())
    if len(sys.argv) == 3 and sys.argv[2] != '-m': sys.exit(help())

    hostname = sys.argv[1]
    human    = len(sys.argv) == 2

    hops = traceroute(hostname, human)

    rtts  = extract_rtts(hops)
    mu    = mean(rtts)
    sigma = stdev(rtts)

    if human:
        print '\nStatistics:\n'

        print 'Hop  IP Addresses    RTT      ZRTT'
        for hop in exclude_noreply(hops):
            print '%-3d  %-15s %-8.3f %-8.3f' % \
                (hop['hop'], hop['src'][0], hop['rtt'], zrtt(hop['rtt'], mu, sigma))
            for i in range(1, len(hop['src'])):
                print '     %s' % hop['src'][i]

        print ''
        print 'Mean RTT:       %0.3f ms' % mean(rtts)
        print 'Std. deviation: %0.3f ms' % stdev(rtts)
        print ''

    else:
        print 'Machine readable output not yet implemented.'
