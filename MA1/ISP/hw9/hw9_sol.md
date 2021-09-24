- [Forewords](#forewords)
- [The blocks](#the-blocks)
  - [Block->init](#block-init)
  - [Block->hash](#block-hash)
  - [Block->encode](#block-encode)
  - [Block->decode](#block-decode)
- [The chain](#the-chain)
  - [BlockChain->init](#blockchain-init)
  - [BlockChain->append](#blockchain-append)
- [Genesis block](#genesis-block)
  - [Block->init v2](#block-init-v2)
- [First debug](#first-debug)
  - [A skeleton](#a-skeleton)
  - [BlockChain->`__str__`](#blockchain-__str__)
  - [Block->`__str__`](#block-__str__)
- [Miner](#miner)
  - [Parsing](#parsing)
  - [Miner->`__init__`](#miner-__init__)
  - [Miner->broadcast](#miner-broadcast)
  - [Miner->run](#miner-run)
    - [The listener](#the-listener)
    - [The miner](#the-miner)
    - [Testing again](#testing-again)
- [Concurrency](#concurrency)
  - [Queue](#queue)
  - [Genesis block](#genesis-block-1)
  - [Main process (Miner->run)](#main-process-miner-run)
  - [Consensus](#consensus)
  - [Printing the chain](#printing-the-chain)
    - [`Block->__init__`](#block-__init__)
    - [`Blockchain->append`](#blockchain-append-1)
    - [`Miner->run`](#miner-run-1)
- [Proof of Work](#proof-of-work)
  - [Block](#block)
  - [MinerClass->run](#minerclass-run)
  - [Blockchain->append](#blockchain-append-2)
- [Conclusion](#conclusion)


# Forewords
As this homework makes use of multiple files that interconnect, we can easily lose track of the types and signatures. To make things easier to read and have some nice help from the IDE, the solution uses [_type hints_](https://docs.python.org/3.8/library/typing.html). This was introduced in Python3.5, and is supported by most modern IDEs. If you encounter problems, you can simply remove them (or upgrade to a more recent python version or IDE). This is optional, and is only a helper for the developer. You don't need to specifically worry about it.

Also, we will regularly go back and forth between files/classes. This is because the process is iterative. When it's not obvious, to indicate which file/method we are talking about, we will use the notation
`class->method`. For example: `Block->__init__` refers to the `__init__` method of the Block class. When it is clear, we won't do that.

# The blocks
## Block->init
What defines a block?

![block](./block.png)
* Its data
* Its pointer to the previous block (if not Genesis)
* And the hash of the previous block (if not Genesis)

The hash has no need to be particularly stored, we can simply dynamically compute it whenever needed. Also, we now only focus on a non-genesis block. For more robustness, we allow for `data` to be either bytes or a string (in which case we encode ourselves); also, previous can be either a block, or a block's hash (also for robustness) So the init is give or take the one of the skeleton:
```py
from typing import Union

def __init__(self,
             data: Union[bytes, str],
             previous: Union[bytes, "Block"]) -> None:
        # robust "data" assignment
        if isinstance(data, str):
            self.data = data.encode()
        elif isinstance(data, bytes):
            self.data = bytes(data)
        else:
            raise NotImplementedError()

        # robust "previous_hash" assignment
        self.previous_hash: bytes = GENESIS_PREVIOUS_HASH
        if isinstance(previous, Block):
            self.previous_hash = previous.hash()
        elif isinstance(previous, bytes):
            self.previous_hash = previous
```

## Block->hash
This one is also relatively straightforward. We don't need anything in particular, and simply hash the pointer and the data:
```py
from hashlib import sha256
...
def hash(self) -> bytes:
    h = sha256()
    h.update(self.data)
    h.update(self.previous_hash)
    return h.digest()
```

## Block->encode
Here again, relatively simple:
```py
import json
...
def encode(self) -> bytes:
    data_b64 = b64encode(self.data).decode()
    prev_hash = self.previous_hash.hex()
    return json.dumps({"data": data_b64,
                        "previous_hash": prev_hash
                      }).encode()
```
Simply encode the data in base64, take the hex representation of the previous hash, and dump it to a json representation.

## Block->decode
Some Python magic here. When we define a class and its methods, the methods are usually called as a method on the _instance_. In our case, for example, the `Block->encode` method is called on an instance of the block, and will behave differently depending on the instance (obviously). But sometime we want generic method that don't depend on the instance. These are the static methods. Simply by calling `Blocks.decode(somebytes)`, it will decode the bytes, as wished. Note there is no "self" argument, as it's independent from the instance (and thus we can't use instance methods/members such as `self.data`). We could also define this helper method somewhere else; but as it returns a Block, it makes sense to define it as a static method.

```py
@staticmethod
def decode(b: bytes):
    js = json.loads(b) # js becomes a kind of dictionary
    previous = bytes.fromhex(js["previous_hash"])
    data = b64decode(js["data"])
    return Block(data=data,
                 previous=previous)
```

# The chain
Now that the basics of a block were implemented, we focus on a chain. You will need to import the `Block` class. For that: `from miner.block import Block`.

## BlockChain->init
A chain, at minimum, is defined by its root and its head. We also obviously need to store somewhere the blocks in themselves. To make things a bit simpler, we also keep a dictionary of all blocks in the chain, identified by their hash. This will allow for easy access and traversal.

We make use of a new class member `number` that indicates the position of a block within the chain. We will adapt later the `Block` class to have a default (null) number. This is not necessary, but makes things easier within the IDE.
```py
def __init__(self, genesis_block: Block):
    # create the "chain": a dict of all blocks referenced by their hash
    self.blocks: Dict[bytes, Block] = dict()
    # add the genesis to the chain, initiate its number
    gen_hash = genesis_block.hash()
    self.blocks[gen_hash] = genesis_block
    self.blocks[gen_hash].number = 0
    # set root and head as genesis
    self.root: Block = genesis_block
    self.head: Block = genesis_block
```

## BlockChain->append
Now we're getting to the real code. Appending a new block requires a few verifications, and some potentials pitfalls. We need to:
1. Ensure the previous block, pointed in the new block, belongs in our chain
2. Store it in our chain
3. Adapt the head (accordingly). We'll come back to that in a second.

Our code for `append` looks like that:

```py
def append(self, new_block):
    # step 1: ensure the new's previous belongs in our chain
    previous_block = self.blocks.get(new_block.previous_hash)
    if not previous_block:
        print("no such previous block", new_block.previous_hash.hex())
        return None

    # step 2: store it in our chain
    new_block_num = previous_block.number + 1
    self.blocks[new_block.hash()] = new_block
    self.blocks[new_block.hash()].number = new_block_num

    # step 3: adapt the head
    self.head = new_block

    return new_block
```

# Genesis block
Since the beginning, we've eluded a special case: the genesis block. If the argument is __True__,, the chain is started with a genesis block. As defined in the handout:

> [...] the genesis block [...] can have any valid payload and has null bytes as `previous_hash`

Thus we need to adapt some functions in `Block` to account for that.

## Block->init v2
We need to account for a null previous hash. So instead of always assigning the `previous_hash`, we suppose it _can_ be null. This changes the type hinting and the content:
```py
from typing import Optional

# 32-bytes null hash
GENESIS_PREVIOUS_HASH = (0).to_bytes(32, byteorder="big")

# previous can be None -> Optional
def __init__(self, data: bytes, previous: Optional[bytes]) -> None:
    self.data: bytes = data
    # if we have a previous_hash, we assign it
    # otherwise, null hash
    self.number: int = -1 # as promised
    self.previous_hash: bytes = GENESIS_PREVIOUS_HASH
    if previous is not None:
        self.previous_hash = previous
```


# First debug
At this point, it is suggested to stop and do some debug.

## A skeleton
Our first tentative looks like that:
```py
from miner.blockchain import BlockChain
from miner.block import Block

gen_block = Block(("In the beginning God created the heavens and the earth. "
                   "The earth was without form, and void; and darkness was on "
                   "the face of the deep. And the Spirit of God was hovering "
                   "over the face of the waters.").encode())

chain = BlockChain(gen_block)

block2 = Block(("Then God said, “Let there be light”; and there was light. "
                "And God saw the light, that it was good; "
                "and God divided the light from the darkness. God called the "
                "light Day, and the darkness He called Night. So the evening "
                "and the morning were the first day.").encode(),
               gen_block.hash())

head = chain.append(block2)

block3 = Block(("Then God said, “Let there be a firmament in the midst of the"
                " waters, and let it divide the waters from the waters.” "
                "Thus God made the firmament, and divided the waters which "
                "were under the firmament from the waters which were above the"
                " firmament; and it was so. 8 And God called the firmament"
                " Heaven. So the evening and the morning "
                "were the second day.").encode(),
               head.hash())
chain.append(block3)
print(chain)
```
You can save it in a file, for instance `test.py`.

Roughly:
1. We create a genesis block
2. We create a chain using that block
3. We create a new block, pointing to the genesis block
4. We append it to the chain (and retrieve the head)
5. We create yet another block, that points to the head.
6. We print the chain.

Now, printing the chain won't be a pretty sight. Simply because Python doesn't know what it means to print a `BlockChain`. That's why we add a new ("magic") method to both the chain and the block: `__str__` (4 underscore, 2 before and 2 after). This method is automatically called when something tries to cast our object as a string (like printing).

## BlockChain->`__str__`
To display a chain, we use the following method:
```py
def __str__(self):
    ret = "(HEAD)"
    b: Block = self.head
    while b.hash() != self.root.hash():
        ret = "\n---\n" + str(b) + ret
        b = self.blocks[b.previous_hash]
    ret = "(ROOT)" + str(b) + ret
    return ret
```

This prints the head, then goes backward and appends blocks one after the other but at the beginning of the string. It will look like that
```
(ROOT) <genesis>
---
<block1>
---
<block2>
---
......
---
<head> (HEAD)
```
Simple, but enough for us to debug. We still need to decide how we "print" a block.

## Block->`__str__`
There are countless smart ways to display a block. To keep things simple, we only display its data (decoded) and the beginning of the hash.
```py
def __str__(self):
    return "{} ({})".format(self.data.decode(), self.hash().hex()[:5])
```

At this point, launching the debug code will display a nice blockchain, with a root and 2 blocks!

# Miner
Now that the "server" is in place, time to create the "client". We start from the provided template. As suggested, we run it once to see the required arguments. They are as follow:
```
Usage: python3 miner.py [addr] [others] [genesis]
```
With
* `addr`: address of the miner in the format host:port
* `others`: comma-separated list of the other miners' addresses in the format host:port,host:port,...
* `genesis`: optional, "genesis" if the miner must generate the genesis block

Also as suggested, we first do an implementation that can either listen or send blocks. We will worry about concurrency later.

## Parsing
When the program is started, we receive all arguments in `sys.argv`. We must parse them in a usable format first. Remember that `sys.argv` is a list, with in its first position the name of the file. Real arguments are space-separated, and start at the second position of the list.

As we are expecting to parse multiple addresses (format: `host:port`) we write a simple method to parse it. This helper method can also accept the format `host:` and will default to port 5000. Then the host and port (as an int) will be returned.
```py
def parse_addresses(hostport: str):
    hostport = hostport.split(":")
    port = 5000 if len(hostport) == 1 else int(hostport[1])
    return hostport[0], port
```

From here, we simply read the arguments, parse them, and create a miner:
```py
if __name__ == '__main__':
    if len(sys.argv) < 3:
        ...
    # retrieve arguments
    self_host_port = sys.argv[1]
    others_hosts_ports = sys.argv[2].split(",")
    # parse "genesis"
    gen_genesis = len(sys.argv) >= 4 and sys.argv[3] == "genesis"

    #parse "addr"
    host, port = parse_addresses(self_host_port)
    # parse "others"
    miners = [parse_addresses(x) for x in others_hosts_ports]

    miner = Miner(host, port, miners, gen_genesis)
    try:
        miner.run()
    except KeyboardInterrupt:
        # makes exit graceful
        print("stopping...")
```

## Miner->`__init__`
As usual in an init method, we mostly store everything for later use. Also, we create a [socket](https://docs.python.org/3/library/socket.html). If you already took the TCP/IP course you're probably familiar with this library. If not no worries, we won't dive too deep.

```py
import socket
...
def __init__(self, host: str, port: int, miners: list, genesis: bool):
    # store everything in convenient formats
    self.host: str = host
    self.port: int = port
    self.miner_name: str = "%s:%i" % (host, port)
    self.miner_address: Tuple[str, int] = (host, port)
    self.miners: list = miners
    self.mine_genesis: bool = genesis

    # prepare a socket
    # AF_INET == IPv4, SOCK_DGRAM == UDP
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
```

## Miner->broadcast
A quite simple method, to send a block to all (other) miners:
```py
def broadcast(self, block: "Block"):
    for miner in self.miners:
        if miner != self.miner_address:
            self.sock.sendto(block.encode(), miner)
```
Not much to explain here. We iterate through all different miners than self. Then we send them the block (byte-encoded).

## Miner->run
This one is more interesting. We first consider the simplest case: only 2 miners; one that mines, one that listens. Obviously, this means that the one that mines must start the genesis block. We don't specifically enforce it, but keep it in mind for testing. To begin with, we will decide which miner mines and which listens based on their port: even port mines, odd port listens (we will use ports 5000 and 5001). Our structure thus looks like the following:
```py
class Miner:
    ...
    def run(self):
        if self.port % 2 == 0:
            # mine and send
        else:
            # listen and update
```
But first thing first:
### The listener
We just need to infinitely listen on the socket, and when we receive a block, append it to the chain.

```py
...
else:
    # listen and update
    chain = None
    while True:
        data, addr = self.sock.rec(65507)
        new_block = Block.decode(data)
        if chain is None:
            chain = BlockChain(new_block)
        else:
            chain.append(new_block)
        print(chain)
```

As per the counterpart:
### The miner
Similarly: infinitely, generate a new block, add it to your local chain, and broadcast it.
```py
import random
import time

if self.port % 2 == 0:
    chain = None
    previous = None
    while True:
        #### Mock block generation
        time.sleep(random.randint(5, 10))
        block = Block(("This is some random mumbo jumbo, {}"
                        .format(random.randint(0, 100)).encode()),
                        previous)
        ### End of mock block generation
        self.broadcast(block)
        if chain is None:
            chain = BlockChain(block)
            previous = block
        else:
            previous = chain.append(block)
        print(chain, end="\r")
```

First thing to notice here: the block generation. Normally, the content would make sense (i.e. smart contracts, bitcoin transactions,...), and would require some work to achieve. As we don't have any meaningful content, we just add some random data. Finally, as we haven't implemented the Proof-of-Work yet, we simply wait for a random time. This will change later.

### Testing again
We can now test things! Each time a block is sent/received, the chain is printed. Thus, we can run the process twice, and see the chain being updated in real time.

You may want to check out [tmux](https://github.com/tmux/tmux). It allows you to split your terminal, and see multiple things at once. The same can be achieved with the terminal emulator Tilix. Very handy!

By running the following commands, in two separate terminals:
```bash
python miner/miner.py 127.0.0.1:5001 127.0.0.1:5000
python miner/miner.py 127.0.0.1:5000 127.0.0.1:5001 genesis
```

They will start to communicate. You should now see the chain growing every 5 or so seconds.

# Concurrency
To have concurrency, we need to set up a few things. The most important is the _processes_ that will do the job. Namely, the `MineTask` and the `ListenTask`. Both of those can put an object in a shared queue. Then the main process constantly tries to get an item from the queue. Once it can get one, it will try to update the chain. According to the situation (was the block ours? was it valid?) we may take various actions (terminating and starting a new mining task, broadcast the block,...).

So we need to have these two additional processes in the background. Let's define them:

```py
from multiprocessing import Process, Queue

class MineTask(Process):

    def __init__(self, miner: "Miner",
                 block: "Block",
                 data: Union[bytes, str]):
        super(Process, self).__init__()
        self.miner: Miner = miner
        self.block: Block = block
        self.data: Union[bytes, str] = data

    def run(self):
        try:
            time.sleep(random.randint(5, 8))
            next_block = Block(self.data, previous=self.block)
            next_block.miner = self.miner.miner_name
            self.miner.blockQueue.put(next_block)
        except KeyboardInterrupt:
            # for graceful exit
            return


class ListenTask(Process):
    def __init__(self, blockQueue: Queue, sock: socket.socket):
        super(Process, self).__init__()
        self.blockQueue: Queue = blockQueue
        self.sock: socket.socket = sock

    def run(self):
        try:
            while True:
                data, addr = self.sock.recvfrom(65507)
                new_block = Block.decode(data)
                new_block.miner = "{}:{}".format(addr[0], addr[1])
                self.blockQueue.put(new_block)
        except KeyboardInterrupt:
            # for graceful exit
            return
```

## Queue
These rely on a `self.miner.blockQueue` that isn't defined yet. We will define it in the `Miner` class, as we only need to have one per miner.

It's important you convince yourself only one queue is necessary, and that the implementation works. Here are some tips:
* As explained before, the main process constantly tries to read from the queue (sole consumer)
* The background processes both try to add elements to the queue
* Once the main processes gets one block from the queue, there are 2 possibilities:
  * It's from an other miner: -> try to add it to your chain; interrupt the miner; start a new mining process (with a new "previous" block); keep listening
  * It's your block: -> try to add it to your chain; broadcast it; start a new mining process; keep listening.
* Note that you first need to ensure the block is valid before stopping anything (the chain accepts it)

## Genesis block
We also need to take care of the special genesis block. Here, we will do the following artificial setup: we manually decide which miner does the genesis block; meanwhile, they all wait for it to come. Once it's done, no more friends, and may the fastest win!

## Main process (Miner->run)
Now we can attack the main process. The big picture is the following:
1. Prepare the socket
2. "Get" the genesis block (by mining or waiting)
3. For genesis-creator: broadcast the genesis and start listening
4. Create the chain using the genesis block
5. Start to mine the next block
6. Infinitely:
   1. Wait for a block
   2. Try to add to chain. If success:
   3. Share (if applicable), interrupt the mining (if applicable), start a new mining task

This translates in this way:
```py
def run(self):
        # prepare the socket
        self.sock.bind((self.host, self.port))

        # mine or wait for genesis
        if self.mine_genesis:
            MineTask(self, None, "Genesis").start()
        else:
            self.listen_task.start()
        genesis: Block = self.blockQueue.get()
        print("Genesis generated/received:", genesis)

        # create chain
        self.chain: BlockChain = BlockChain(genesis)

        # genesis-creator must start to listen and broadcast genesis
        if self.mine_genesis:
            self.listen_task.start()
            self.broadcast(genesis)

        i = 0 # keep track of how many block each miner created (opt)
        mined_block: Block = genesis

        # start to mine the next block
        self.mine_task = MineTask(self, genesis,
                                  ("{}:{}".format(self.miner_name, i)))
        self.mine_task.start()

        # infinitely:
        while True:
            # wait for a new block
            new_block = self.blockQueue.get()
            # try to append to chain
            if self.chain.append(new_block):
                #if success:
                if new_block.miner == self.miner_name:
                    # if mine, increment i and broadcast
                    print("My block! Broadcasting")
                    i += 1
                    self.broadcast(new_block)
                else:
                    # if someone else's, interrupt the task
                    self.mine_task.terminate()
                    print("Dang, someone got me...")
                if mined_block != self.chain.head:
                    # get head, if not done
                    mined_block = self.chain.head
                    # start new mining, based on current head
                    self.mine_task = MineTask(self,
                                              mined_block,
                                              "{}:{}".format(self.miner_name,
                                                             i))
                    self.mine_task.start()
                print(self.chain)
            else:
                print("rejected block from", new_block.miner)
            print("######################################")
```

## Consensus
Up until now, when a block is valid, we append it to the chain, and mark it as the new head. As a reminder, an extract from `Blockchain->append`: `self.head = new_block` and that's it. But what happens if we have two blocks that arrive roughly at the same time? Or if a malicious miner decides to send a second "block 2" (for which the previous is the genesis)? Our current code will accept it as is, and set it as the new head. No good...

This is the point of the consensus. The head is the block with the highest number (remember, the number is not defined by the miners but by the chain). For that, the head is defined according to the highest block number. If two two blocks have the same number, then it will be decided randomly between those two.

The new `Blockchain->append`:
```py
...
# Determine new head
if self.head.number < new_block_num:
    # if new head is newer, change head
    self.head = new_block
elif self.head.number == new_block_num:
    # if new head same number, decide randomly (1/2)
    self.head = new_block if bool(random.getrandbits(1)) else self.head
```

With this solution, the head will be decided. But we keep all the valid blocks we receive. And if a new block doesn't point to the current head, but has a larger number, it will become the new head. That way, miners can create new blocks, that will be kept, but only one head (and thus chain) will exist.

## Printing the chain
Now that we may have multiple potential heads, and forks, our old printing method is not sufficient enough. We turn ourselves to the `pptree` library. Small problem: by printing a node, we will only print its predecessors. At the moment, we have no knowledge of diverging branches, from a block. The easiest way to solve that, is to keep (for each block) a list of its "children": the blocks that point to it. When a block is added to the chain, the predecessor is informed and will keep it.

### `Block->__init__`
Add a member: `self.children: Set[Block] = set()`

### `Blockchain->append`
Inform the predecessor: `self.blocks[previous_block.hash()].children.add(new_block)`

### `Miner->run`
Print the genesis instead of the chain:
```py
from pptree import print_tree
...

# print(self.chain)
print_tree(self.chain.root, "children", horizontal=False)
```
If you run your clients, you will see the chain growing. And if you reduce the random interval (say, a blocked is mined every 1-5 seconds), conflicts will appear. But everyone will agree on the longest chain, and the tree will be identical for everyone.

# Proof of Work
For the moment, a block is mined randomly at certain intervals. But that is up to the client (in a sense), because the block contains no verification whatsoever (except that the previous block exists).

As explained in the handout, we need to make sure miners don't spam with their own, malicious block. In our case we are using dummy block data, but if it were bitcoin transactions, everyone damn hope that the blocks are legitimate!

Our proof of work will be located in the Block class. It is equivalent to the `nonce` you saw in class. The actual mining is exactly that: finding the correct `nonce` (proof-of-work) that matches a certain criterion.

Our criterion: the hash of the block (`SHA-256(block.data||block.previous_hash||block.p_o_w)`), once interpreted as an integer, must be smaller than a certain TARGET. So instead of counting the number of leading 0's (as other blockchain do), we impose a maximum value. At the limits: the maximum target would be `int("0xffffff..ff")` (any hash works), and the minimum would be `int("0x0000..000")` (extremely hard to find a pow).

Some numbers: the maximum integer representable with 64 base-16 characters, is 0xffff...ff and is 115792089237316195423570985008687907853269984665640564039457584007913129639935, or 2^256, or 1.15e77, or 115 quattuorvigintillion. As the hashes are uniformly distributed, finding a valid hash (at random) has probability $\frac{TARGET}{int(0xffff...ff)}$.

In the case of cryptocurrencies, we want to have a (relatively) constant rate of blocks. Bitcoin aims for [10 minutes per block](https://en.bitcoin.it/wiki/Help:FAQ#Why_do_I_have_to_wait_10_minutes_before_I_can_spend_money_I_received.3F). There are a lot of other factors at play here, but roughly the target is adapted to keep that number steady. With more miners, you need to lower the target, with less miners you can higher it.

## Block
In our case, we will go with 2^235 (totally arbitrary). We add that as a constant (`TARGET = 2**235`)

Then, we move the mining to the block, as a  additional method.
```py
def mine(self, target):
    # prepare the hash
    h = sha256()
    h.update(self.data)
    h.update(self.previous_hash)
    # start with nonce=0
    inc = 0
    hp = h.copy()
    # as long as the hash is too big, retry
    while inc == 0 or int.from_bytes(hp.digest(), signed=False, byteorder="big") > target:
        hp = h.copy()
        inc += 1
        hp.update(inc.to_bytes(8, byteorder="big"))
    # not the inc is correct: save as pow
    self.p_o_w = inc.to_bytes(8, byteorder="big")
    return self
```

And obviously prepare the member in `Block->__init__`: `self.p_o_w = None`.

Next: adapt the hashing function of a block, to incorporate the pow:
```py
def hash(self) -> bytes:
        """Return a bytes object containing the hash of the block.

        Returns:
            bytes: Hash digest of the block
        """
        h = sha256()
        h.update(self.data)
        h.update(self.previous_hash)
        h.update(self.p_o_w) # <-- add that
        return h.digest()
```

Very important: the encoding/decoding of a block must contain the pow:

```py
def encode(self) -> bytes:
        """Return a bytes object containing a UTF-8 encoded JSON object."""
        return json.dumps({"data": b64encode(self.data).decode(),
                           "previous_hash": self.previous_hash.hex(),
                           "p_o_w": self.p_o_w.hex()
                           }).encode()

    @staticmethod
    def decode(b: bytes):
        js = json.loads(b)
        previous = bytes.fromhex(js["previous_hash"])
        data = b64decode(js["data"])
        p_o_w = bytes.fromhex(js["p_o_w"]) if "p_o_w" in js else None
        return Block(data=data,
                     previous=previous,
                     p_o_w=p_o_w)
```

And finally, when creating a block (e.g. after decoding), one must accept a pow:

```py
class Block:
    def __init__(self,
                 data: Union[bytes, str],
                 previous: Optional[Union[bytes, 'Block']] = None,
                 p_o_w: Optional[bytes] = None) -> None:
        ...
        self.p_o_w = p_o_w if p_o_w else (0).to_bytes(8, byteorder="big")
        ...
```
## MinerClass->run
Now that we have a dedicated mining method, we need to replace the "wait for a random time" by the actual mining:

```py
from block import TARGET
...
next_block = Block(self.data, previous=self.block)
#time.sleep(random.randint(10,30)) # not anymore
next_block.mine(TARGET)
```


## Blockchain->append
The last modification to do is the verification of a block. Now that a block has a proof of work, the chain must ensure it is also correct before accepting the block. The mechanism is the following:
```py
if int.from_bytes(new_block.hash(), signed=False, byteorder="big") > self.target:
    print("invalid block", new_block.hash().hex())
    return None
```

# Conclusion
This implementation is not complete. We are relatively robust to malicious workers, and can show that the blocks are all legitimate, thanks to the proof of work.

There are still some real-life problems we didn't consider. What do we do with incorrect paths? Sometimes a head was replaced, and is left hanging? We can implement a pruning system for that. After a decided amount of blocks, if a stub hasn't made any progress, we could delete the block and save space.

Also, our mining process is single-threaded. We could leverage some more computing power with more threads.

And what about transactions? Where do they come from? We used dummy content, but crypto-currencies use transactions. We need to find a way to accept such transactions. And a whole system to sign transactions, and "identify" workers.

If a new workers comes along, how do we know? Who send them the current chain?

Finally, reward. Miners need an incentive to lend their computing power. We need to identify the worker(s) that mined the block, and give them a reward, in form of a transaction. And what about pools of workers?
