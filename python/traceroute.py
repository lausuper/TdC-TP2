#!/usr/bin/env python2
# encoding: utf-8

import argparse
import os
import sys
import socket
import logging
logging.getLogger('scapy.runtime').setLevel(logging.ERROR)
from scapy.all import *
from random import randint
from route import Route
from statistics import print_statistics

MAX_TTL         = 30
PACKET_TIMEOUT  = 1

def traceroute(hostname, seconds):
    dst_ip = socket.gethostbyname(hostname)
    route = Route(dst_ip)

    print 'Tracing route to %s...' % hostname

    t0 = time.time()

    while time.time() - t0 < seconds:
        try:
            pkts = [IP(dst=dst_ip, ttl=ttl) / ICMP(id=randint(0, 65535))
                    for ttl in range(1, MAX_TTL + 1)]
            ans, unans = sr(pkts, verbose=0, timeout=PACKET_TIMEOUT)
        except socket.error as e:
            sys.exit(e)

        for snd, rcv in ans:
            ttl  = snd.ttl
            ip   = rcv.src
            type = rcv.type
            rtt  = (rcv.time - snd.sent_time) * 1000
            route[ttl].add_reply(ip, type, rtt)

        os.system('clear')
        print_statistics(route)

    return route

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('hostname',
                        help='trace route to [hostname] and measure round-trip times to each hop')
    parser.add_argument('-t', '--time',
                        type=int, default=10,
                        help='measure round-trip times for TIME seconds (default 10)')
    parser.add_argument('-o', '--output',
                        help='save machine-readable output to OUTPUT')
    args = parser.parse_args()

    # Do the actual traceroute 
    route = traceroute(args.hostname, args.time)

    # Display results
    print_statistics(route)

    # Display results for machines
    if args.output:
       route.save(args.output)
       print 'Results saved to %s.' % args.output