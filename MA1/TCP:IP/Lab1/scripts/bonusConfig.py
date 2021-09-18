#!/usr/bin/python

"""
This example shows how to create a Mininet object and add nodes to it manually.
"""
"Importing Libraries"
from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from parse import *
import os

def averageParser(fileName):
    fp = open(fileName, 'r')
    count = -1
    stats = []
    for cnt, line in enumerate(fp):
        p = parse("--- {} ping statistics ---", line)
        if p is not None:
            count += 1
        else :
            p = parse("{} packets transmitted, {} received, +{} errors, {}% packet loss, time {}ms", line)    
            if p is not None:
                stats.append([float(p[3]), -1])
            else:
                p = parse("rtt min/avg/max/mdev = {}/{}/{}/{} ms{}", line)
                if p is not None:
                    stats[count][1] = float(p[1])
                else:
                    p = parse("{} packets transmitted, {} received, {}% packet loss, time {}ms", line)
                    if p is not None:
                        stats.append([float(p[2]), -1])

    newStats = {'avg' : 0, 'wiseAvg' : 0, 'plAvg' : 0}
    wiseCount = 0.0
    for i in range(len(stats)):
        if stats[i][1] > 0.0:
            newStats['avg'] += stats[i][1]
            weight = (100.0 - stats[i][0])/100.0
            
            newStats['wiseAvg'] += stats[i][1] * weight
            wiseCount += weight
        newStats['plAvg'] += stats[i][0]
    newStats['avg'] /= count
    newStats['wiseAvg'] /= wiseCount
    newStats['plAvg'] /= count
    
    fp.close()
    return newStats
    

"Function definition: This is called from the main function"
def complexNetwork(N, pings, pingFlow):

    
    
    "Create an empty network and add nodes to it."
    net = Mininet()
    info( '*** Adding controller\n' )
    net.addController( 'c0' )
    
    info( '*** Adding hosts, switchs, links\n' )
    
    PC = []
    s = []
    PCR = net.addHost( 'PCR', ip='10.10.0.254/24')
    testPrefix = ''
    if pingFlow == 0:
        testPrefix = 'FromR'
    elif pingFlow == 1:
        testPrefix = 'Circular'
    elif pingFlow == 2:
        testPrefix = 'EveryToEvery'
    elif pingFlow >= 3:
        testPrefix = str(pingFlow - 1)+'Neighbours'
        
    testDir = testPrefix+'Test'+str(N)+'Machines'+str(pings)+'Pings'
    testDirLogs = testDir + '/logs'
    testDirFinalLogs = testDir + '/finalLogs'
    PCR.cmd('mkdir ' + testDir + ' ' + testDirLogs + ' ' + testDirFinalLogs)
    for i in range(0, N):
        info( str(i) + ' ')
        PC.append(net.addHost( 'PC'+str(i), ip='10.10.'+str(i)+'.1/24'))
        s.append(net.addSwitch( 's'+str(i)))
        net.addLink( PC[i], s[i])
        net.addLink( PCR, s[i])
        PCR.cmd('ip addr add 10.10.'+ str(i) +'.254/24 dev PCR-eth'+ str(i))
        
    info( '\n*** Forwarding activated on router\n' )
    PCR.cmd('echo 1 > /proc/sys/net/ipv4/ip_forward')
    
    info( '*** Starting network\n')
    net.start()
    for i in range(0, N):
        PC[i].cmd('ip route add default via 10.10.'+ str(i) +'.254')

    "This is used to run commands on the hosts"

    info( '*** Starting terminals on hosts\n' )
    PCR.cmd('xterm -xrm "XTerm.vt100.allowTitleOps: false" -T PCR &')

    info( '*** Launching pings\n' )

    if pingFlow == 0:
        for i in range(0,N):
            info('(R : ' + str(i) + '),')
            PCR.cmd('ping -c '+str(pings)+' 10.10.'+str(i)+'.1 > '+testDirLogs+'/pingFromRto'+str(i)+'.txt &')
    elif pingFlow == 1:
        for i in range(0,N-1):
            info('(' + str(i) + ' : ' + str(i+1) + '),')
            PC[i].cmd('ping -c '+str(pings)+' 10.10.'+str(i)+'.1 > '+testDirLogs+'/pingFrom'+str(i)+'to'+str(i+1)+'.txt &')
        info('(' + str(N-1) + ' : 0)')
        PC[N-1].cmd('ping -c '+str(pings)+' 10.10.0.1 > '+testDirLogs+'/pingFrom'+str(N-1)+'to0.txt &')
    elif pingFlow == 2:
        for i in range(0, N):
            for j in range(0, N):
                if i != j:
                    info('(' + str(i) + ' : ' + str(j) + '),')  
                    PC[i].cmd('ping -c '+str(pings)+' 10.10.'+str(j)+'.1 > '+testDirLogs+'/pingFrom'+str(i)+'to'+str(j)+'.txt &')        
    elif pingFlow >= 3:
        M = int(min (N, pingFlow) /2)
        for i in range(0, N):
            for l in range(i - M, i + M + 1):
                j = l%N
                if i != j:
                    info('(' + str(i) + ' : ' + str(j) + '),')
                    PC[i].cmd('ping -c '+str(pings)+' 10.10.'+str(j)+'.1 > '+testDirLogs+'/pingFrom'+str(i)+'to'+str(j)+'.txt &')
        
    info( '\n ***' )
    

    info( '*** Running the command line interface\n' )
    CLI( net )

    info( '*** Closing the terminals on the hosts\n' )
                    
    PCR.cmd("killall xterm")
    stats = {}        
    info( '*** Compiling final datas\n' )
    if pingFlow == 0 :
        PCR.cmd('grep -h --no-group-separator -A 3 \'statistics\' '+ testDirLogs+'/pingFromRto*.txt > '+testDirFinalLogs+'/pingFromR.txt')
        stats = averageParser(testDirFinalLogs+'/pingFromR.txt')
    elif pingFlow == 1 :
        PCR.cmd('grep -h --no-group-separator -A 3 \'statistics\' '+ testDirLogs+'/pingFrom*to*.txt > '+testDirFinalLogs+'/pingCircular.txt')
        stats = averageParser(testDirFinalLogs+'/pingCircular.txt')
    elif pingFlow >= 2 :     
        for i in range(0, N):
            PCR.cmd('grep -h --no-group-separator -A 3 \'statistics\' '+ testDirLogs+'/pingFrom'+str(i)+'to*.txt > '+testDirFinalLogs+'/pingFrom'+str(i)+'.txt')
        PCR.cmd('grep -h --no-group-separator -A 3 \'statistics\' '+ testDirLogs+'/pingFrom*to*.txt > '+testDirFinalLogs+'/pingFromEveryToEvery.txt')
        stats = averageParser(testDirFinalLogs+'/pingFromEveryToEvery.txt')
    reply = 'Stats for '+str(N)+' PCs in star topology, with '+str(pings)+' pings issued in a \"'+testPrefix+'\" test way.\nAverage without taking in \
account Loss : '+str(stats['avg'])+'\nAverage with weight of Loss : ' + str(stats['wiseAvg'])+  '\nAverage of Packet Loss : ' + str(stats['plAvg'])
    PCR.cmd( 'echo \"'+reply+'\" > ' +testDirFinalLogs+'/averageStatistics.txt')
    
    
    
    info( '*** Stopping network' )
    net.stop()

"main Function: This is called when the Python file is run"
if __name__ == '__main__':
    setLogLevel( 'info' )
    import argparse

    parser = argparse.ArgumentParser(description='Create a tester for scalability of Network')
    parser.add_argument('--N', metavar='int', required=True,
                        help='the number of PC')
    parser.add_argument('--pings', metavar='int', required=True,
                        help='the number of pings to issue\n')
    parser.add_argument('--pingFlow', metavar='int', required=True,
                        help='the way ping will be sent\n ### 0 : Router to Every\n ### 1 : Circular chain\n ### 2 : Every to Every\n ### 3 or more ... < N : Neighbours count')
    args = parser.parse_args()
    complexNetwork(N=int(args.N), pings=int(args.pings), pingFlow=int(args.pingFlow))
    
