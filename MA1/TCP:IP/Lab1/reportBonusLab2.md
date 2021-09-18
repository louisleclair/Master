# Report TCP/IP Lab02 Bonus

## Execution:

To run the program you must have installed the Python package __parse__ with the command _pip install parse_, after that, you can run it with the following command: 

```
sudo python bonusConfig.py --N <nb of PCs> --pings <nb of pings> --pingFlow <see below>
```
After you run the code, you need to wait the number of seconds you put in the number of pings. After that, you have to write ``` exit ``` in the terminal to quit and have the results.

If you need help you can tap ```sudo python bonusConfig.py -h ``` and the documentation will appear. 

## Explication 

All our tests are made on a __star topology__ network composed of __N__ PCs and 1 Router.
A defined number of __pings__ will be sent and the statistics will be saved and compiled with global averages.
We defined several modes of testing, where the argument defining it is __pingFlow__ :

- Router to every (=0): Only the router pings all the host
- Circular Chain (=1): is the wrong way to name an organization where every PCi send to PCi+1 modulo of N PCs, but all packets still go through the same Router since the network adopts a star topology.
- Every to Every (=2): Every host send a ping to every host
- Every to pingFlow-1 Neighbors (=3+): Every host sends a ping to the pingFlow-1 neighbors around it.


## Hardware 

We made our tests on the MininetVM given for the course. But we found that our physical devices influence a lot the result we found. Here the description of our respective machine:

- MacBook Pro 2020 on SSD | __CPU__: 2,3 GHz Quad-Core Intel Core i7 | __RAM__: 32 GB 3733 MHz LPDDR4X
- HP ProBook 430 G3 2016 on SSD | __CPU__: IntelⓇ Core™ I3-6100U Skylake-U/Y @2.30 GHz | __RAM__: 8 GB Single-Channel 1063MHz

## Conclusion
We did here 4 types of test (as explained before) on our machines : 

- Every to Every (ETE)
- Router to Every (RTE)
- Circular Chain (Circ)
- Every to N/2 Neighbours (NeighN/2)

With the intensive use of inefficient hardware, we encounter significant difficulties around 14-16 PCs. We tried to compute the most representative data by calculating the latency average while taking into account the errors and the packet loss, this way we get only the time on successful packets (In our little custom statistic logs, there are still the raw average).

It's interesting to notice that "Router to Every" and "Circular Chain" represent N simultaneous pings, and so the packet loss is really stabilized around 0. However there is a significant difference in the latency, "Circular Chain" really seems to have a better flow than "Router to Every". 

![Alt text](/Users/louis/Coding/EPFL/MA/MA1/TCP:IP/Lab02/lab1ReportImages/LouisCircRTEWAvg.png)

![Alt text](/Users/louis/Coding/EPFL/MA/MA1/TCP:IP/Lab02/lab1ReportImages/MattCircRTEWAvg.png)

![Alt text](/Users/louis/Coding/EPFL/MA/MA1/TCP:IP/Lab02/lab1ReportImages/LouisETENN2WAvg.png)

![Alt text](/Users/louis/Coding/EPFL/MA/MA1/TCP:IP/Lab02/lab1ReportImages/MattETENN2WAvg.png)

The Packet Loss, in general, represents well the situation of overloading when it comes to using the "Every to Every" and the "Half of Neighbours" tests. As said before, for the to left other cases, the traffic is too low to provoke any overload.

![Alt text](/Users/louis/Coding/EPFL/MA/MA1/TCP:IP/Lab02/lab1ReportImages/LouisPacketLoss.png)

![Alt text](/Users/louis/Coding/EPFL/MA/MA1/TCP:IP/Lab02/lab1ReportImages/MattPacketLoss.png)


	