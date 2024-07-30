#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mobility-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/energy-module.h"
#include "ns3/command-line.h"

#include <iostream>
#include <vector>
#include <map>
#include <fstream>
#include <iomanip>

using namespace ns3;
using namespace ns3::energy;

NS_LOG_COMPONENT_DEFINE("WirelessNetworkExample");

int main(int argc, char *argv[])
{
    // Set the locale to support Unicode output in the console
    std::setlocale(LC_ALL, "");

    // Set a random seed
    RngSeedManager::SetSeed(1);
    RngSeedManager::SetRun(1);

    // Simulation parameters
    uint32_t nWifi = 10;
    double simulationTime = 10.0; // seconds
    double txPower = 50.0;        // dBm    
    double lossExponent = 4.0;    // dB
    double referenceLoss = 40.0;  // dB

    // Command line arguments
    CommandLine cmd;
    cmd.AddValue("nWifi", "Number of wifi STA devices", nWifi);
    cmd.AddValue("simulationTime", "Simulation time in seconds", simulationTime);
    cmd.Parse(argc, argv);

    // Create nodes
    NodeContainer wifiStaNodes;
    wifiStaNodes.Create(nWifi);
    NodeContainer wifiApNode;
    wifiApNode.Create(1);

    // Map to store node ID mappings
    std::map<Ptr<Node>, uint32_t> nodeIdMap;

    // Configure WiFi Channel
    YansWifiPhyHelper phy = YansWifiPhyHelper();
    phy.SetPcapDataLinkType(YansWifiPhyHelper::DLT_IEEE802_11_RADIO);

    YansWifiChannelHelper channel = YansWifiChannelHelper();
    channel.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel");
    channel.AddPropagationLoss("ns3::LogDistancePropagationLossModel",
                               "Exponent", DoubleValue(lossExponent),
                               "ReferenceLoss", DoubleValue(referenceLoss));
    phy.SetChannel(channel.Create());

    // Set transmission power and standard
    phy.Set("TxPowerStart", DoubleValue(txPower));
    phy.Set("TxPowerEnd", DoubleValue(txPower));
    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211a);

    // Install WiFi to all nodes
    WifiMacHelper mac;
    Ssid ssid = Ssid("ns-3-ssid");
    mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssid), "ActiveProbing", BooleanValue(false));
    NetDeviceContainer staDevices;
    staDevices = wifi.Install(phy, mac, wifiStaNodes);

    mac.SetType("ns3::ApWifiMac", "Ssid", SsidValue(ssid));
    NetDeviceContainer apDevices;
    apDevices = wifi.Install(phy, mac, wifiApNode);

    // Set mobility
    MobilityHelper mobility;
    
    
    Ptr<ListPositionAllocator> staPositionAlloc = CreateObject<ListPositionAllocator>();
for (uint32_t i = 0; i < nWifi; ++i)
{
    double angle = 2 * M_PI * i / nWifi;
    
    
    // Create a uniform random variable
    Ptr<UniformRandomVariable> uniformRandom = CreateObject<UniformRandomVariable>();
    uniformRandom->SetAttribute("Min", DoubleValue(0.0));
    uniformRandom->SetAttribute("Max", DoubleValue(1.0));    
    
    // Generate a random distance up to stApDistance
    double distance = 50* uniformRandom->GetValue();
    
    double x = distance * std::cos(angle);
    double y = distance * std::sin(angle);
    staPositionAlloc->Add(Vector(x, y, 0.0));
}
mobility.SetPositionAllocator(staPositionAlloc);
mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
mobility.Install(wifiStaNodes);

    
    
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(wifiApNode);

    // Install Internet stack
    InternetStackHelper stack;
    stack.Install(wifiApNode);
    stack.Install(wifiStaNodes);

    // Assign fixed IDs to nodes
    for (uint32_t i = 0; i < nWifi; ++i)
    {
        nodeIdMap[wifiStaNodes.Get(i)] = i + 1;
    }
    nodeIdMap[wifiApNode.Get(0)] = nWifi + 1;

    // Assign IP addresses
    Ipv4AddressHelper address;
    address.SetBase("10.1.3.0", "255.255.255.0");
    Ipv4InterfaceContainer staInterfaces;
    staInterfaces = address.Assign(staDevices);
    Ipv4InterfaceContainer apInterface;
    apInterface = address.Assign(apDevices);

    // Install applications
    UdpEchoServerHelper echoServer(9);
    ApplicationContainer serverApp = echoServer.Install(wifiApNode.Get(0));
    serverApp.Start(Seconds(1.0));
    serverApp.Stop(Seconds(simulationTime + 1));

    // Random traffic generator using OnOffApplication
    ApplicationContainer clientApp;
    OnOffHelper onOff("ns3::UdpSocketFactory", Address(InetSocketAddress(apInterface.GetAddress(0), 9)));
    onOff.SetAttribute("DataRate", StringValue("50Mbps"));
    onOff.SetAttribute("PacketSize", UintegerValue(1024));
    onOff.SetAttribute("OnTime", StringValue("ns3::ExponentialRandomVariable[Mean=4]"));
    onOff.SetAttribute("OffTime", StringValue("ns3::ExponentialRandomVariable[Mean=4]"));
    onOff.SetAttribute("MaxBytes", UintegerValue(1 * 1024 * 1024)); // Set maximum bytes to 1MB

    for (uint32_t i = 0; i < nWifi; ++i)
    {
        clientApp.Add(onOff.Install(wifiStaNodes.Get(i)));
    }

    clientApp.Start(Seconds(2.0));
    clientApp.Stop(Seconds(simulationTime + 1));

    // Energy model configuration
    LiIonEnergySourceHelper liIonSourceHelper;
    liIonSourceHelper.Set("LiIonEnergySourceInitialEnergyJ", DoubleValue(100.0)); // Initial energy of 100 J
    liIonSourceHelper.Set("InitialCellVoltage", DoubleValue(3.7));                // Initial cell voltage

    EnergySourceContainer sources = liIonSourceHelper.Install(wifiStaNodes);

    WifiRadioEnergyModelHelper radioEnergyHelper;
    DeviceEnergyModelContainer deviceModels = radioEnergyHelper.Install(staDevices, sources);

    // Collect initial energy levels
    std::vector<double> initialEnergies(nWifi);
    for (uint32_t j = 0; j < wifiStaNodes.GetN(); ++j)
    {
        Ptr<LiIonEnergySource> liIonSourcePtr = DynamicCast<LiIonEnergySource>(sources.Get(j));
        initialEnergies[j] = liIonSourcePtr->GetRemainingEnergy();
    }

    // Flow monitor
    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    // Run simulation
    Simulator::Stop(Seconds(simulationTime + 2));
    Simulator::Run();

    // Print results
    monitor->CheckForLostPackets();
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

    // Get the position of the AP
    Ptr<Node> apNode = wifiApNode.Get(0);
    Ptr<MobilityModel> apMobility = apNode->GetObject<MobilityModel>();

    // Output network performance statistics
    std::cout << "\nNETWORK PERFORMANCE STATISTICS:" << std::endl;
    for (std::map<FlowId, FlowMonitor::FlowStats>::const_iterator i = stats.begin(); i != stats.end(); ++i)
    {
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(i->first);

        // Check if it's a transmission to the server
        if (t.destinationAddress == apInterface.GetAddress(0))
        {
            uint32_t clientId = 0;

            // Find the corresponding node index based on the source address
            for (auto &nodePair : nodeIdMap)
            {
                Ptr<Ipv4> ipv4 = nodePair.first->GetObject<Ipv4>();
                Ipv4Address addr = ipv4->GetAddress(1, 0).GetLocal();
                if (addr == t.sourceAddress)
                {
                    clientId = nodePair.second;                    

                    std::cout << "\nClient: " << clientId << " (Flow ID " << i->first << ")"
                              << " (" << t.sourceAddress << " -> " << t.destinationAddress << ")" << std::endl;
                    std::cout << "Tx Packets = " << i->second.txPackets << std::endl;
                    std::cout << "Rx Packets = " << i->second.rxPackets << std::endl;
                    std::cout << "Throughput = " << std::fixed << std::setprecision(6) << i->second.rxBytes * 8.0 / (simulationTime - 1) / 1024 / 1024 << " Mbps" << std::endl;
                    std::cout << "Delay = " << std::fixed << std::setprecision(6) << (i->second.rxPackets > 0 ? i->second.delaySum.GetSeconds() / i->second.rxPackets : INFINITY) << " s" << std::endl;
                    std::cout << "Packet Loss Ratio = " << std::fixed << std::setprecision(6) << (i->second.txPackets > 0 ? (i->second.txPackets - i->second.rxPackets) * 100.0 / i->second.txPackets : INFINITY) << " %" << std::endl;
                    break;
                }
            }
        }
    }

    // Output statistics to CSV file
    std::ofstream outputFile("ns3_results.csv");
    outputFile << "Client, Tx_Packets,Rx_Packets,Throughput_(Mbps),Delay_(s),Packet_Loss_Ratio_(%)\n";

    for (std::map<FlowId, FlowMonitor::FlowStats>::const_iterator i = stats.begin(); i != stats.end(); ++i)
    {
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(i->first);

        // Check if it's a transmission to the server
        if (t.destinationAddress == apInterface.GetAddress(0))
        {
            uint32_t clientId = 0;

            // Find the corresponding node index based on the source address
            for (auto &nodePair : nodeIdMap)
            {
                Ptr<Ipv4> ipv4 = nodePair.first->GetObject<Ipv4>();
                Ipv4Address addr = ipv4->GetAddress(1, 0).GetLocal();
                if (addr == t.sourceAddress)
                {
                    clientId = nodePair.second;

                    outputFile << clientId << ","
                               << i->second.txPackets << "," << i->second.rxPackets << ","
                               << std::fixed << std::setprecision(6) << i->second.rxBytes * 8.0 / (simulationTime - 1) / 1024 / 1024 << ","
                               << std::fixed << std::setprecision(6) << (i->second.rxPackets > 0 ? i->second.delaySum.GetSeconds() / i->second.rxPackets : INFINITY) << ","
                               << std::fixed << std::setprecision(6) << (i->second.txPackets > 0 ? (i->second.txPackets - i->second.rxPackets) * 100.0 / i->second.txPackets : INFINITY) << ",\n";
                               
                }
            }
        }
    }

    outputFile.close();
    std::cout << "\nStatistics written to CSV file.\n" << std::endl;

    // Cleanup
    Simulator::Destroy();

    return 0;
}

