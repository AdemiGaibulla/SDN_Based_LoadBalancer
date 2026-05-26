from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.lib.packet import packet, ethernet, ipv4, arp

VIRTUAL_IP = '10.0.0.10'
VIRTUAL_MAC = '00:00:00:00:00:10'
SERVERS = [
    {'ip' : '10.0.0.2', 'mac' : '00:00:00:00:00:02'},
    {'ip' : '10.0.0.3', 'mac' : '00:00:00:00:00:03'},
    {'ip' : '10.0.0.4', 'mac' : '00:00:00:00:00:04'}
]

class LoadBalancer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LoadBalancer, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.current_server = -1
        self.server_rqst_count = [0,0,0]
        self.selected_server = None
        self.rqst_count = 0

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)

    def next_server(self):
        if self.current_server == 2:
            self.current_server = 0
        else:
            self.current_server += 1
        server = SERVERS[self.current_server]
        self.server_rqst_count[self.current_server] += 1

        self.rqst_count += 1

        print("Request #",self.rqst_count," handled: ")
        print("Server1 = ", self.server_rqst_count[0], ", Server2 = ", self.server_rqst_count[1], ", Server3 = ", self.server_rqst_count[2])
        return server

    def arp_handler(self, datapath, in_port, eth_pkt, arp_pkt, parser, ofproto):
        self.selected_server = self.next_server()
        reply_mac = self.selected_server['mac']

        reply = packet.Packet()
        reply.add_protocol(ethernet.ethernet(ethertype=0x0806,
                                            dst=eth_pkt.src,
                                            src=reply_mac))
        reply.add_protocol(arp.arp(opcode=arp.ARP_REPLY,
                                   src_mac=reply_mac, src_ip=VIRTUAL_IP,
                                    dst_mac=arp_pkt.src_mac, dst_ip=arp_pkt.src_ip))
        reply.serialize()

        out = parser.OFPPacketOut(datapath=datapath, 
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=[parser.OFPActionOutput(in_port)],
                                  data=reply.data)
        datapath.send_msg(out)

    def ip_handler(self, datapath, in_port, eth_pkt, ip_pkt, parser, ofproto, msg):
        server = self.selected_server
        if server['mac'] in self.mac_to_port:
            out_port = self.mac_to_port[server['mac']]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionSetField(ipv4_dst=server['ip']),
                   parser.OFPActionSetField(eth_dst=server['mac']),
                   parser.OFPActionOutput(out_port)]
        
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_type=0x0800, ipv4_dst=VIRTUAL_IP)
            self.add_flow(datapath, 100, match, actions)

        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port,
                                  actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)

        

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        in_port = msg.match['in_port']

        self.mac_to_port[eth_pkt.src] = in_port

        if arp_pkt and arp_pkt.dst_ip == VIRTUAL_IP:
            self.arp_handler(dp, in_port, eth_pkt, arp_pkt, ofp_parser, ofp)
            return

        if ip_pkt and ip_pkt.dst == VIRTUAL_IP:
            self.ip_handler(dp, in_port, eth_pkt, ip_pkt, ofp_parser, ofp,msg)
            return


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser

        match = ofp_parser.OFPMatch()
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_CONTROLLER,
                                          ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 1, match, actions)

        print('Switch connected!')
