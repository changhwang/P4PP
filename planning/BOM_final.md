# Final Bill of Materials (BOM) - P4PP System

This list reflects the final components used in the construction of the P4PP system, based on the **"P4PP_BOM_Final.csv"**. Each item number perfectly matches the reference numbers (`BOM #xx`) found throughout the entire set of guide documents.

## 1. Controller & ADC (Core)
| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **1** | 1 | Core / Controller | Arduino Nano 33 IoT (3.3V) | Main controller and SPI master |
| **2** | 1 | Core / ADC | ADS1220 24-bit ADC breakout | For precise voltage/current measurement |

## 2. 1mA Constant Current Source & Relay Switching
| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **3** | 1 | Current Source | Adjustable current source IC (TO-92) | LM334 constant current source |
| **4** | 1 | Current Source | Rset for 1.0 mA (68.1Ω, 0.1%) | For general measurements (e.g., ITO) |
| **5** | 1 | Current Source | Rset for 100 µA (681Ω, 0.1%) | Swappable for high-resistance (e.g., PEDOT) |
| **6** | 1 | Current Sense | Shunt resistor for current monitor (100Ω, 0.1%)| Current monitoring shunt resistor |
| **7** | 1 | Current Reversal | DPDT relay, 12V coil (through-hole) | Delta mode reversal relay |
| **8** | 1 | Relay Driver | NPN transistor (TO-92) | Relay driving switch (PN2222A) |
| **9** | 1 | Relay Driver | Flyback diode for relay coil | Relay back-EMF protection (1N4148) |
| **10** | 2 | Relay Driver | Base resistor (1kΩ, 0.1% / 1%) | Base protection and pull-down |

## 3. Probe Input Protection & Connectors
| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **11** | 1 | ADC Input Protection | Diode Array Common Anode 30V 200mA (BAT54A) | V+, V- protection |
| **12** | 1 | ADC Input Protection | Diode Array Common Cathode 30V 200mA (BAT54C)| Complementary V+, V- protection |
| **13** | 2 | ADC Input Protection | SOT23 TO DIP ADAPTER | SMD diode adapter |
| **18** | 1 | Connectors (Probe) | CONN BIND POST KNURLED BLACK | Binding Post |
| **19** | 1 | Connectors (Probe) | Binding Post Connector RED | Binding Post |
| **20** | 1 | Connectors (Probe) | Binding Post Connector GREEN | Binding Post |
| **21** | 1 | Connectors (Probe) | CONN BIND POST KNURLED BLUE | Binding Post |

## 4. Main Power, Protection & Filter Components
| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **14** | 1 | Power | 12V wall adapter, 60W (12V/5A), 2.5mm | Main 12V power adapter |
| **15** | 1 | Power | Power Cord | Adapter power cord |
| **25** | 1 | Power (DC input) | DC barrel jack, Panel Mount | Enclosure terminal for 12V adapter |
| **26** | 1 | Power Protection | Inline blade fuse holder (ATC/ATO) | Inline fuse holder for short-circuit protection |
| **27** | 1 | Power Protection | ATC/ATO blade fuse, 5A, 32V | Blade fuse |
| **28** | 1 | Stabilizing | 10 Ohms 1% 0.25W Resistor | 3.3V Low-Pass filter for power noise removal |
| **29** | 1 | Stabilizing | 1 µF 10% 16V Ceramic Capacitor | Main power decoupling |
| **30** | 1 | Stabilizing | 0.1 µF 10% 50V Ceramic Capacitor | 3.3V power grid high-frequency filtering |
| **31** | 1 | Power Decoupling | Bulk electrolytic capacitor, 470uF 25V | Essential to prevent TMC2209 driver burnout |

## 5. Linear Motion & Switches
| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **24** | 2 | Switch | SWITCH SNAP ACTION SPDT 15A 250V | Micro limit switches for homing (rotational/linear) |
| **33** | 2 | Linear Motion | TMC2209 Stepper Motor Driver | Driver for linear/rotational motors |
| **36** | 2 | Linear Motion | Stepper Motor (NEMA 17) | Stepper motors for rotation/vertical descent |

## 6. Boards, Headers, Wiring & Accessories
| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **16** | 1 | Headers | Male header, 1x40, 2.54mm | For Arduino mounting base, etc. |
| **17** | 1 | Headers | Female header, 1x40, 2.54mm | Rset (variable current) plug-and-play sockets, etc. |
| **22** | 1 | EMI / Noise control | Ferrite clamp (snap-on) | Core for motor noise control |
| **23** | 1 | Wiring | Shielded wire 22AWG | Shielded cable |
| **32** | 1 | Cables | Micro-USB cable | PC connection for Arduino Nano |
| **34** | 1 | Breadboard | Perma-Proto Full-sized Breadboard PCB | Soldering board for measurement circuit (Board A, B) |
| **35** | 3 | Breadboard | Perma-Proto Mint Tin Size Breadboard PCB | Soldering boards for switching (Board C) & motors (Board D) |

---
*All guides have been merged and perfectly synchronized.*
