# Final Bill of Materials (BOM) - P4PP System

This list reflects the final components used to construct the P4PP system and is synchronized with **`P4PP_BOM_Final.csv`**. Item numbers match the `BOM #xx` references used throughout the guides. The 15-item movement list is transcribed from `4pp_movement_BOM_list.xlsx`; the existing switch (#24) and stepper motor (#36) rows were updated in place to avoid duplicates.

## 1. Controller & ADC (Core)

| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **1** | 1 | Core / Controller | Arduino Nano 33 IoT (3.3V) | Main controller and SPI master |
| **2** | 1 | Core / ADC | ADS1220 24-bit ADC breakout | Precise voltage/current measurement |

## 2. Constant Current Source & Relay Switching

| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **3** | 1 | Current Source | Adjustable current source IC (TO-92) | LM334 constant current source |
| **4** | 1 | Current Source | Rset for 1.0 mA (68.1 Ω, 0.1%) | General measurements such as ITO |
| **5** | 1 | Current Source | Rset for 100 µA (681 Ω, 0.1%) | Swappable for higher-resistance samples |
| **6** | 1 | Current Sense | Shunt resistor for current monitor (100 Ω, 0.1%) | Current-monitoring shunt |
| **7** | 1 | Current Reversal | DPDT relay, 12 V coil | Delta-mode reversal relay |
| **8** | 1 | Relay Driver | NPN transistor (TO-92) | PN2222A relay driver |
| **9** | 1 | Relay Driver | Flyback diode for relay coil | Relay back-EMF protection |
| **10** | 2 | Relay Driver | Base resistor (1 kΩ) | Base protection and pull-down |

## 3. Probe Head, Input Protection & Connectors

| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **11** | 1 | ADC Input Protection | BAT54A common-anode diode array | V+/V− protection |
| **12** | 1 | ADC Input Protection | BAT54C common-cathode diode array | Complementary V+/V− protection |
| **13** | 2 | ADC Input Protection | SOT23-to-DIP adapter | SMD diode adapter |
| **18** | 1 | Probe Connector | Black binding post | Probe I/V connection |
| **19** | 1 | Probe Connector | Red binding post | Probe I/V connection |
| **20** | 1 | Probe Connector | Green binding post | Probe I/V connection |
| **21** | 1 | Probe Connector | Blue binding post | Probe I/V connection |
| **50** | 1 | Probe Head | Signatone SP4-40085TFJ | Reused laboratory stock, ~$300–400 (quotation) |

## 4. Main Power, Protection & Filtering

| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **14** | 1 | Power | 12 V wall adapter, 60 W (12 V/5 A), 2.5 mm | Main power adapter |
| **15** | 1 | Power | Power cord | Adapter power cord |
| **25** | 1 | Power (DC input) | 5.5 mm OD × 2.5 mm ID DC barrel jack | 12 V enclosure input |
| **26** | 1 | Power Protection | Inline ATC/ATO blade-fuse holder | Short-circuit protection |
| **27** | 1 | Power Protection | ATC/ATO blade fuse, 5 A, 32 V | Replaceable fuse |
| **28** | 1 | Stabilizing | 10 Ω, 1%, 0.25 W resistor | 3.3 V low-pass filtering |
| **29** | 1 | Stabilizing | 1 µF, 10%, 16 V ceramic capacitor | Power decoupling |
| **30** | 1 | Stabilizing | 0.1 µF, 10%, 50 V ceramic capacitor | High-frequency filtering |
| **31** | 1 | Power Decoupling | 470 µF, 25 V low-ESR electrolytic capacitor | Motor-driver bulk decoupling |

## 5. Motion Drive Electronics

| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **33** | 2 | Linear Motion | TMC2209 stepper motor driver | Linear and rotational motor drivers |

## 6. Movement Hardware (15 Source Items)

| No. | Qty | Supplier / SKU | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **24** | 2 | Mouser / V-153-1C25 | Omron snap-action SPDT switch | $5.75 each; homing limit switches |
| **36** | 2 | Stepperonline / 17HS08-1004S | Stepper motor | Linear and rotational axes |
| **37** | 1 | goBILDA / 1309-0016-2005 | sonic hub | Connect rotation motor shaft to sample stage |
| **38** | 2 | McMaster-Carr / 47065t101 | t slotted frame, 1 ft | Structural frame |
| **39** | 1 | McMaster-Carr / 88805K515 | l bracket stock, aluminum, 1 ft | Machine two 6-inch brackets; fixes shaft bores and linear motor |
| **40** | 1 | goBILDA / 4002-0005-0008 | Flexible clamping shaft coupler, 5 mm to 8 mm | Connect linear motor to 8 mm lead screw |
| **41** | 1 | goBILDA / 3501-0804-0250 | 8 mm lead, 4-start lead screw, 250 mm | Linear axis lead screw |
| **42** | 2 | goBILDA / 2100-0008-0250 | 8 mm stainless-steel shaft, 250 mm | Linear-stage stability |
| **43** | 4 | goBILDA / 1310-0016-0008 | 1310 Series Hyper Hub, 8 mm bore | Fix shafts to L-brackets |
| **44** | 1 | goBILDA / 1612-0815-0024 | 8 mm ID linear ball bearing, 2-pack | Shaft bearings |
| **45** | 2 | goBILDA / 1302-0032-0015 | 1302 Series Clamping Hub, 15 mm bore | Fix linear bearings to the 4PP stage |
| **46** | 1 | goBILDA / 3500-0804-1216 | 8 mm lead, 4-start lead-screw barrel nut | Fix lead screw to the 4PP stage |
| **47** | 1 | goBILDA / 1301-0016-0012 | 1301 Series Clamping Hub, 12 mm bore | Fix barrel nut to the 4PP stage |
| **48** | 1 | goBILDA / 1310-0016-5008 | 1310 Series Hyper Hub, 4-start lead-screw bore | Fix lead screw to top L-bracket |
| **49** | 1 | McMaster-Carr / 8975K74 | Multipurpose 6061 aluminum bar, 2 in × 1/2 ft × 0.5 in | 3.5 inches used for stage and probe-head mount |

The 15 source items total **$176.75**, matching the source workbook. This subtotal includes the updated switch (#24) and existing stepper motor (#36).

## 7. Boards, Headers, Wiring & Accessories

| No. | Qty | Category | Item Name | Notes / Usage |
| :---: | :---: | :--- | :--- | :--- |
| **16** | 1 | Headers | Male header, 1×40, 2.54 mm | Arduino mounting and general interconnects |
| **17** | 1 | Headers | Female header, 1×40, 2.54 mm | Swappable Rset sockets and interconnects |
| **22** | 1 | EMI / Noise Control | Ferrite clamp | Motor-cable noise suppression |
| **23** | 1 | Wiring | Shielded 22 AWG wire | Optional V+/V− shielding |
| **32** | 1 | Cables | Micro-USB cable | Arduino Nano-to-PC connection |
| **34** | 1 | Breadboard | Perma-Proto full-sized breadboard PCB | Measurement circuit boards |
| **35** | 3 | Breadboard | Perma-Proto mint-tin-size breadboard PCB | Switching and motor boards |
