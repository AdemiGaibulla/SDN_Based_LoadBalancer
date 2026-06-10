from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

def create_topology():
    setLogLevel('info')
    net = Mininet(controller=RemoteController, switch=OVSSwitch)

    c0 = net.addController(ip='127.0.0.1', port=6633)
    s1 = net.addSwitch('s1')

    server1 = net.addHost('server1', ip='10.0.0.1', mac='00:00:00:00:00:01')
    server2 = net.addHost('server2', ip='10.0.0.2', mac='00:00:00:00:00:02')
    server3 = net.addHost('server3', ip='10.0.0.3', mac='00:00:00:00:00:03')

    client1 = net.addHost('client1', ip='10.0.0.4', mac='00:00:00:00:00:04')
    client2 = net.addHost('client2', ip='10.0.0.5', mac='00:00:00:00:00:05')
    client3 = net.addHost('client3', ip='10.0.0.6', mac='00:00:00:00:00:06')
    client4 = net.addHost('client4', ip='10.0.0.7', mac='00:00:00:00:00:07')
    client5 = net.addHost('client5', ip='10.0.0.8', mac='00:00:00:00:00:08')
    client6 = net.addHost('client6', ip='10.0.0.9', mac='00:00:00:00:00:09')

    net.addLink(server1, s1)
    net.addLink(server2, s1)
    net.addLink(server3, s1)
    
    net.addLink(client1, s1)
    net.addLink(client2, s1)
    net.addLink(client3, s1)
    net.addLink(client4, s1)
    net.addLink(client5, s1)
    net.addLink(client6, s1)

    net.start()

    server1.cmd('echo "OK" > /tmp/index.html')
    server2.cmd('echo "OK" > /tmp/index.html')
    server3.cmd('echo "OK" > /tmp/index.html')

    server1.cmd('cd /tmp && python3 -m http.server 80 &')
    server2.cmd('cd /tmp && python3 -m http.server 80 &')
    server3.cmd('cd /tmp && python3 -m http.server 80 &')

    CLI(net)

    net.stop()

if __name__ == '__main__':
    create_topology()