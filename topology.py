from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

def create_topology():
    setLogLevel('info')
    net = Mininet(controller=RemoteController, switch=OVSSwitch)

    c0 = net.addController(ip='127.0.0.1', port=6633)
    s1 = net.addSwitch('s1')

    client = net.addHost('client', mac='00:00:00:00:00:01')
    server1 = net.addHost('server1', mac='00:00:00:00:00:02')
    server2 = net.addHost('server2', mac='00:00:00:00:00:03')
    server3 = net.addHost('server3', mac='00:00:00:00:00:04')

    net.addLink(client, s1)
    net.addLink(server1, s1)
    net.addLink(server2, s1)
    net.addLink(server3, s1)

    net.start()

    server1.cmd('echo "Server 1" > index.html')
    server2.cmd('echo "Server 2" > index.html')
    server3.cmd('echo "Server 3" > index.html')

    server1.cmd('python3 -m http.server 80 &')
    server2.cmd('python3 -m http.server 80 &')
    server3.cmd('python3 -m http.server 80 &')

    CLI(net)

    net.stop()

if __name__ == '__main__':
    create_topology()
