# P4PP - Adafruit Perma-Proto (1606) Master Wiring Guide

> **Target Board**: Adafruit Perma-Proto Half-Size (30 Columns)
> The internal connection structure is identical to a standard breadboard. Follow the **Master Chessboard Layout** below to place and solder components, and the entire circuit will be perfectly assembled.

## 0. Understanding the Perma-Proto Board Structure
- **Top & Bottom Power Rails**: The long horizontal red (+) and blue (-) pads.
- **Central Component Area**: Vertical 5-hole groups (a-b-c-d-e, f-g-h-i-j) forming Rows 1 to 30.
- Looking closely at the actual board's lettering, the **bottom-most hole is usually 'a', the one above it 'e'**, skipping the center gap, and the **top-most hole is 'j'**. (See diagram below)

```text
       1  2  3  4  5    (Column Number, Left to Right)
  (Blue line)  - - - - - - - - - - -  ← Top Blue Line (-)
  (Red line)   + + + + + + + + + + +  ← Top Red Line (+)
        ──────────────── 
      j o  o  o  o  o
      i o  o  o  o  o
      h o  o  o  o  o   ← Top Center Group (f~j)
      g o  o  o  o  o
      f o  o  o  o  o
        -------------   ← Center Gap 
      e o  o  o  o  o
      d o  o  o  o  o
      c o  o  o  o  o   ← Bottom Center Group (a~e)
      b o  o  o  o  o
      a o  o  o  o  o
        ──────────────── 
  (Blue line)  - - - - - - - - - - -  ← Bottom Blue Line (-)
  (Red line)   + + + + + + + + + + +  ← Bottom Red Line (+)
```

## 1. Power Rail Allocation (Rules) - ⚡ NEVER BREAK THESE RULES! ⚡

If 12V power enters 3.3V components, they will be instantly destroyed. We must **strictly separate the usage of the top and bottom power rails**.

- **[Top Line] 3.3V ADC / 3.3V Only**:
  1. **Top Blue Line (-)**: `AGND` (Analog Ground - for 3.3V)
  2. **Top Red Line (+)**: `3V3_DIG` (**Pure 3.3V Input from Arduino ONLY**)
- **[Bottom Line] 12V Motor/Relay Only**:
  3. **Bottom Blue Line (-)**: `12V GND` (Ground for Motor/Relay) -> *Only used later in Step 6!*
  4. **Bottom Red Line (+)**: `12V+` (12V Adapter Power) -> *Only used later in Step 6!*

> [!CAUTION]
> **NEVER connect the Arduino to the bottom red line (12V) or put 12V onto the top red line.**
> Similarly, the top `-` rail (AGND) and bottom `-` rail (12V GND) should NOT be directly linked indiscriminately (rely on Star Ground principles).

---

## 🗺️ Master Chessboard Layout (Top-Down View)
The table below illustrates how components are placed across Rows (1~32) of the 60-column Perma-Proto board. (Bottom group is a~e, Top group is f~j)

| Row | Function / Label | [f, g, h, i, j] (Top Group) | [a, b, c, d, e] (Bottom Group) | Connection Notes |
|:---:|:---|:---|:---|:---|
| **1** | **AGND** Extra | **Jumper**(Top Blue➡️1j), **0.1µF**(1i), **1µF**(1h) | 🔴 To **I+** Post (Wire) | GND Node (Jumper Link) |
| **2** | [Empty] | (Capacitor bodies bridge across ⬇️) | ⚫ To **I-** Post (Wire) | Gap for component legs |
| **3** | **3V3_A** | **10Ω**(Top Red➡️3j), **0.1µF**(3i), **1µF**(3h) | (Empty) | Purified 3.3V Node (Step 2) |
| **4** | **IN0** | **IN0 Wire from external BAT54** | **[ADS1220 AIN0]** ➡️ Jumper to Row 8(AIN0) | V+ Sense Line Standby |
| **5** | **IN1** | **IN1 Wire from external BAT54** | **[ADS1220 AIN1]** ➡️ Jumper to Row 9(AIN1) | V- Sense Line Standby |
| **6** | [Input] | **1kΩ**(↑), 🟢 To **V-** Post (Wire) | **1kΩ**(↑), 🔵 To **V+** Post (Wire) | Post Input & Resistor |
| **7** | ADS_Pin1,16 | **[ADS VDD]** ➡️ Jumper to Row 3(3V3_A) | **[ADS AVSS]**(Unused/Internal GND) | 3.3V Power Link |
| **8** | ADS_Pin2,15 | **[ADS DRDY]** ➡️ Arduino D9 | **[ADS AIN0]** ➡️ Jumper to Row 4(IN0) | Data Ready / Sense+ |
| **9** | ADS_Pin3,14 | **[ADS CS]** ➡️ Arduino D10 | **[ADS AIN1]** ➡️ Jumper to Row 5(IN1) | Chip Select / Sense- |
| **10** | ADS_Pin4,13 | **[ADS SCLK]** ➡️ Arduino D13 | **[ADS AIN2]** ➡️ Jumper to Row 21(Shunt+) | Clock / Shunt+ |
| **11** | ADS_Pin5,12 | **[ADS DIN(MOSI)]** ➡️ Arduino D11 | **[ADS AIN3]** ➡️ Jumper to Row 22(Shunt-) | Data IN / Shunt- |
| **12** | ADS_Pin6,11 | **[ADS DOUT(MISO)]** ➡️ Arduino D12 | **[ADS AVDD]**(Unused/Internal VDD) | Data OUT / Analog VDD |
| **13** | ADS_Pin7,10 | **[ADS GND]** ➡️ Jumper to Row 1(GND) | **[ADS REFP]**(Unused) | Main Ground / Ext Ref+ |
| **14** | ADS_Pin8,9 | **[ADS AVSS]**(Unused/Internal GND) | **[ADS REFN]**(Unused) | Analog GND / Ext Ref- |
| **15** | [Empty] | (Empty) | (Empty) | |
| **16** | [Empty] | (Empty) | (Empty) | |
| **17** | [Empty] | (Empty) | (Empty) | |
| **18** | [Empty] | (Empty) | (Empty) | |
| **19** | [Curr Src]| (Empty) | (Empty) | ⬇️ **LM334 Area** ⬇️ |
| **20** | V+ | | **LM334(V+)** ➡️ Jumper to 3V3_A | LM334 Power |
| **21** | R / Sh+ | ➡️ Jumper to Row 10(AIN2) | **LM334(R)**, **Rset(68.1Ω)**(↓) | Rset Network & Shunt+ |
| **22** | OUT/Sh-| ➡️ Jumper to Row 11(AIN3) | **LM334(V-)**, **Rset**(↑), **100Ω**(↓) | Constant Curr Out & Shunt- |
| **23** | S_COM | | **100Ω**(↑), **DPDT_COM_A**(Jumper wire) | Post 100Ω to Relay |
| **24** | [Empty] | (Empty) | (Empty) | ⬇️ **Relay/12V (Isolated)** ⬇️|
| **25** | RLY_COM| **DPDT COM_B** ➡️ Jumper to AGND | **DPDT COM_A** ⬅️ Jumper from Row 23 | Relay IN terminal |
| **26** | RLY_NO | **DPDT NO_B** ➡️ Jumper to Row 1(I+) | **DPDT NO_A** ➡️ Jumper to Row 2(I-) | Reverse (Cross Swap) |
| **27** | RLY_NC | **DPDT NC_B** ➡️ Jumper to Row 2(I-) | **DPDT NC_A** ➡️ Jumper to Row 1(I+) | Forward (Default) |
| **28** | Coil+ | **1N4148 (Cathode)** | **DPDT Coil 1**, **12V+**(Bot Red) Jumper| Coil Drive Power |
| **29** | Coil- | **1N4148 (Anode)** | **DPDT Coil 2**, **PN2222(Collector)**| Transistor Switching |
| **30** | BASE | **10kΩ**(↓Pull-down) | **PN2222(Base)**, **1kΩ**(↓) | Arduino Signal IN |
| **31** | EMITTER| **1kΩ**(↑)➡️Arduino / **10kΩ**(↑)➡️GND | **PN2222(Emitter)** ➡️ Jumper to 12V GND | TR Ground & Control Net |

*(※ The chessboard diagram above perfectly reflects the pin layout of your CJMCU-1220 module.)*

---

## ♟️ Assembly Progress: Step 1 & 2 - Power Rails & Filters

Initial critical setup steps for those assembling from scratch.

### Step 1: Labeling & Preparation

- [ ] Attach **I+, V+, V-, I-** labels to the panel binding posts.
- [ ] Mark test point locations on the stripboard.
- [ ] Solder BAT54A and BAT54C onto SOT23→DIP adapters. (Mind pin orientation!)

> [!TIP]
> **SOT23 ↔ DIP Adapter Pin Mapping & Soldering Guide**
>
> 1. **BAT54 Orientation (SOT-23)**:
>    Looking down at the part, one side has 1 pin, the opposite side has 2 pins.
>    If you place the 2-pin side on the left, **top-left is Pin 1, bottom-left is Pin 2, and the solo right pin is Pin 3**.
>    ```text
>          ┌───┐
>       1 ─┤   ├─ 3
>          │   │
>       2 ─┤   ├
>          └───┘
>    ```
>    - **BAT54A**: pin1=Cathode1, pin2=Cathode2, pin3=Common Anode
>    - **BAT54C**: pin1=Anode1, pin2=Anode2, pin3=Common Cathode
>    
> 2. **DIP Adapter Board Numbering**:
>    - The adapter has 3 small SOT23 surface pads.
>    - The through-holes (DIP pins) corresponding to pads 1, 2, and 3 are often unlabeled.
>    - **Mandatory Pre-solder Step**: Use a multimeter in **Continuity mode (beep)** to map which through-hole connects to SOT23 pad 1, 2, and 3.
>    - Once identified, **write 1, 2, 3 next to the holes with a sharpie** to avoid confusion later.
>
> 3. **SMD Soldering Tip**:
>    - First, **apply a tiny bit of solder to just ONE** of the 3 pads on the adapter.
>    - Using tweezers, align the component perfectly and melt that single pad to **tack it in place (temporary hold)**.
>    - Check the alignment. If straight, solder the remaining legs.

### Step 2: Power Filter Assembly (Board A & B)

> [!TIP]
> **Wiring Guide (Color & Gauge Recs)**
> - **GND (Ground)**: Always use **Black** or **Blue** wire. (AWG 22 recommended)
> - **3.3V Power**: Always use **Red** or **Orange** wire. (AWG 22 recommended)
> - Use bare **Solid wire** for *short jumpers on the stripboard*, and **Stranded wire** for *connections going off-board or between modules*.

Assembly (Ref. Layout Plot):

1.  **Arduino Power Links (Using wire)**:
    - [ ] `Arduino 3V3` pin ➡️ **Stripboard Column 2 (3V3_DIG)**: Link with **Red** wire
    - [ ] `Arduino GND` pin ➡️ **Stripboard Column 1 (AGND)**: Link with **Black** wire
2.  **Power Filter Components (No wire needed, plug legs directly)**:
    - [ ] **10Ω Resistor ([BOM #28])**: One leg in `Col 2(3V3_DIG)`, the other in `Col 3(3V3_A)`. (Horizontal, e.g., Row 3)
    - [ ] **0.1µF Ceramic Cap ([BOM #30])**: One leg in `Col 1(AGND)`, the other in `Col 3(3V3_A)`. (Horizontal, e.g., Row E)
    - [ ] **1µF Ceramic Cap ([BOM #29])**: Similarly, connect between `Col 1(AGND)` and `Col 3(3V3_A)`. (Horizontal, e.g., Row F)

**Verification (Multimeter DC Voltage Mode)**:
```text
1. Plug a USB cable into the Arduino to supply power.
2. Hold the black probe (COM) firmly on 'Col 1 (AGND)':
   - Touch red probe to 'Col 2 (3V3_DIG)': Expect 3.3V ± 0.1V ✓
   - Touch red probe to 'Col 3 (3V3_A)': Expect 3.3V ± 0.1V ✓ (Should be nearly identical to Col 2)
```

---

## ♟️ Assembly Progress: Step 3 - ADS1220 ADC Module (BOM #2)

Mount the CJMCU-1220 horizontally so it bridges across the center gap of the breadboard according to its specific pinout.

### 3.1 ADS1220 16-Pin Custom Placement

Press the module firmly so its dual-row header pins slide into **[Column d]** and **[Column h]** (or g) holes. (Uses Rows 7 to 14)

```text
       1  2  3  4  5    (Column Number)
         (Top power/filters omitted)
        ---│--│--│------   ← Center Gap 
      ...
(Row 7) h [VDD ] ├───┤ [AVSS] d
(Row 8) h [DRDY] ├───┤ [IN0 ] d
(Row 9) h [ CS ] ├───┤ [IN1 ] d
(Row10) h [SCLK] ├───┤ [IN2 ] d
(Row11) h [DIN ] ├───┤ [IN3 ] d
(Row12) h [DOUT] ├───┤ [AVDD] d
(Row13) h [GND ] ├───┤ [REFP] d
(Row14) h [AVSS] ├───┤ [REFN] d
        ──────────────── 
           ▼  ▼  ▼
```

### 3.2 ADS1220 Power Wiring (Unifying AVDD/AVSS)

This specific module type does NOT internally bridge its analog power (AVDD/AVSS) and digital power (VDD/GND). Therefore, you must make a total of 4 power/ground connections!

1. **Digital Power Connection**:
    - `VDD` Pin (Row 7, top empty hole) ↔ **[Row 3, 3V3_A]** Jumper
    - `GND` Pin (Row 13, top empty hole) ↔ **[Row 1, Main GND]** Jumper
2. **Analog Power Connection (Left-Layout Optimization)**:
    - `AVDD` Pin (Row 12, Left side) ➡️ **`12c` ↔ `3d`** Jumper (Direct short path to purified 3V3_A on Row 3)
    - `AVSS` Pin (Row 7, Left side) ➡️ **`7c` ↔ `1c`** Jumper (Direct short path to purified AGND on Row 1)
*(※ Both VDD and AVDD must receive 3.3V for the internal circuits to fully wake up!)*

### 3.3 Arduino ↔ ADS1220 SPI Communication Wiring

Run long jumper wires from the 'h' column side directly to the **Arduino's digital pins**.

- [x] Module **`SCLK`** Pin (Row 10) ➡️ Arduino **`D13`** `[Yellow Wire]` ✅
- [x] Module **`DIN` (MOSI)** Pin (Row 11) ➡️ Arduino **`D11`** `[Orange Wire]` ✅
- [x] Module **`DOUT` (MISO)** Pin (Row 12) ➡️ Arduino **`D12`** `[White Wire]` ✅
- [x] Module **`CS`** Pin (Row 9) ➡️ Arduino **`D10`** `[Brown Wire]` ✅
- [x] Module **`DRDY`** Pin (Row 8) ➡️ Arduino **`D9`** `[Purple Wire]` ✅

> **Use Stranded wire (Dupont cables) for SPI lines.** Being digital signals, they are resilient to noise and much easier to route long distances to the Arduino.

### 🧪 Verification (Solder/Power Integrity Check)
1. Plug USB into Arduino.
2. Probe **VDD (Row 7)** and **AVDD (Row 12, col d)** with multimeter. Both must show 3.3V.
3. Upload `firmware/debug/ads1220_spi_test/ads1220_spi_test.ino` and open the Serial Monitor.
4. **Write/Read Verification**: Writing `0x6A` to a register and reading it back out successfully proves SPI communication is fully operational.

> [!IMPORTANT]
> **The default register values for the ADS1220 are ALL `0x00`!** (Not `0x08`!)
> Therefore, simply reading a `0x00` does not confirm success.
> You must verify using a **Write → Read Back** pattern.

✅ **2026-02-20 Verification Completed**: `Reg0 = 0x6A` Write/Read match confirmed. SPI comms normal.

---

## ♟️ Assembly Progress: Step 4 - LM334 Constant Current Source

Utilize the empty space beneath the ADS1220 (Rows 20~23) to assemble the 1mA Constant Current Source, the beating heart of resistance measurement.

### 4.0 Preparation (Check BOM)
Locate these exact three components before assembly.
1. **[BOM #3] LM334Z/NOPB (Constant Current Source IC)**:
   - Black half-cylinder (TO-92 Package)
   - Marked `LM334Z`.
2. **[BOM #4] 68.1Ω Resistor (0.1% Precision)**:
   - Blue body (Precision)
   - Color bands: **[Blue - Gray - Brown - Gold - Violet]** or marked `68R1`.
   - The core component (Rset) generating the 1mA current.
3. **[BOM #6] 100Ω Resistor (0.1% Precision, Shunt)**:
   - Blue body (Precision)
   - Color bands: **[Brown - Black - Black - Black - Violet]** or marked `100R`.
   - The shunt resistor used to monitor the *actual* amount of current flowing.

### 4.1 Placement Guide (Bottom Group, Columns a~e)

Use the **bottom-right of the board (Cols a~e)** based on the master layout.

```text
       1  2  3  4  5    (Column Num)
       a  b  c  d  e    (Alpha)
      ...
(Row20) [LM_V+] ───Jumper───► (Row 7, VDD)  ← ⚠️ Row 3 is too crowded, pull from here!
(Row21) [LM_R ] ─────────┐ 
(Row22) [LM_V-] ───┐     │ (Rset 68.1Ω)
                   │     │ 
(Row23) [S_COM] ───┴─────┴ (100Ω Shunt)
```

### 4.2 Detailed Insertion Order (User-Optimized Layout!)

> 🚨 **Ultra-Precision Note**: With the flat face (printed side) of the half-cylinder LM334 facing you, the pins are 1, 2, and 3 from left to right.

1. **Insert LM334 (#3)**:
   - Pin 1 (V+) ➡️ Hole **20b**
   - Pin 2 (R)  ➡️ Hole **21b**
   - Pin 3 (V-) ➡️ Hole **22b**
2. **Insert Rset Resistor (68.1Ω, #4)**:
   - Leg 1 ➡️ Hole **21c**
   - Leg 2 ➡️ Hole **22c**
   > 💡 **Variable Measurement Range (Hot-Swap)**: Since you've already soldered a **[BOM #17] Female Header** into 21c and 22c, you can easily use tweezers to swap resistors (plug and play) according to the target material.
   > - **With [BOM #4] 68.1Ω (approx. 1mA)**: Rec. Range **~10 kΩ/sq or lower**. (Low resistance like ITO films)
   > - **With [BOM #5] 681Ω (approx. 100µA)**: Rec. Range **1 kΩ/sq ~ 100 kΩ/sq**. (High resistance like PEDOT:PSS)
   > *(This is a safe operating range calculated considering the ADC limit and the LM334's ~2.2V dropout voltage headroom.)*
3. **Insert 100Ω Shunt (#6)**:
   - Leg 1 ➡️ Hole **22d**
   - Leg 2 ➡️ Hole **23d**

*(※ Inserted this way, the components will align vertically in a very neat column.)*

### 4.3 Jumper Wiring (Power & Sensing)

The power routing issue was beautifully solved using the user's **"Row 3 Center Bridge"** idea!

1. **Routing Power to LM334 (Completed)**:
   - Bridge Jumper across the gap **3f ↔ 3e**.
   - Relocated the old AVDD pin to **3d** to free up space.
   - Long Jumper **3a ↔ 20a** drops the power down. (Clean 3.3V successfully delivered to LM334 Pin 20b.)
2. **Connecting ADS1220 Current Monitor Lines (Your Next Task!)**:
   - Now, to actually measure the true current flowing from the source, we run two wires up to the ADC.
   - **Sense Wire 1 (Blue Rec 🔵)**: Drop in **Row 21** (e.g., hole 21e) ➡️ Run up and solder into **Row 10 (MUST be on the 'd' col side!)** (Connects mapping AIN2 / `IN2`)
   - **Sense Wire 2 (Green Rec 🟢)**: Drop in **Row 22** (e.g., hole 22e) ➡️ Run up and solder into **Row 11 (MUST be on the 'd' col side!)** (Connects mapping AIN3 / `IN3`)
   - *(※ The `IN2` and `IN3` labels on the module match perfectly with the `AIN2` and `AIN3` (Analog Input) pins from the datasheet!)*
   - > 🚨 **CRITICAL**: The opposite 'h' column side of Rows 10 and 11 contains the Yellow (SCLK) and Orange (DIN) SPI digital comm lines. These must NEVER touch or mix! The sensing lines must strictly be soldered on the **lower 'd' column side (Analog pin side)**.

### 🧪 4.4 1st Stage Multimeter Verification (Mandatory)
Before powering on the Arduino, use a multimeter to check the solder joints!

1. Set Multimeter to Ω (Resistance) mode.
2. Touch the two probes to the silver solder joints of **Row 21** and **Row 22**.
   - ➡️ Screen shows around **~68.1Ω** (67.5 ~ 68.5) = Success!
3. Now, probe **Row 22** and **Row 23**.
   - ➡️ Screen shows around **~100Ω** (99.5 ~ 100.5) = Success!

---

## ♟️ Assembly Progress: Step 5 - BAT54 Input Protection (Board B Finalization)

Since the analog board's (Board B) space from Rows 25~31 is empty, we build a dual-clamping Zener protection circuit here to clamp any over-voltages coming from the probe's micro-voltages (`V+`, `V-`) before they hit the delicate ADC.
We create an invincible shield utilizing the user's combination idea: **BAT54A(Common Anode) + BAT54C(Common Cathode)**.

### 5.1 Essential Bridges (Crossing the Center Gap)
To utilize the purified power (Rows 1 and 3) on the left side (a~e) of the board, add bridge jumpers.
- **[3.3V_A Bridge]**: Jumper `3e` ↔ `3f` (Likely already done)
- **[AGND Bridge]**: Jumper `1e` ↔ `1f` (New addition!)

### 5.2 Component Insertion (SOT-23 Modules)
Insert the two modules into the right side (f~j) in a zig-zag pattern and hook up power.

1. **Insert BAT54A (`Rows 25~27 Area`)**:
   - `27f`: Pin 1 (Cathode 1) ➡️ [Future **V+ Channel**]
   - `25f`: Pin 2 (Cathode 2) ➡️ [Future **V- Channel**]
   - `26e`: Pin 3 (Common Anode) ➡️ Jumper to **`1d` (Purified AGND)**!

2. **Insert BAT54C (`Rows 29~31 Area`)**:
   - `31f`: Pin 1 (Anode 1) ➡️ [Partner for V+ at 27f]
   - `29f`: Pin 2 (Anode 2) ➡️ [Partner for V- at 25f]
   - `30c`: Pin 3 (Common Cathode) ➡️ Jumper to **`3c` (Purified 3.3V_A)**!

### 5.3 Creating the Perfect 1kΩ Input Terminals (Using Rows 35, 37)
> 🌟 **[Full-Board Layout Optimization]** The empty bottom-right space (Rows 35~37) becomes a dedicated terminal zone solely for probe sensing input and the 1kΩ defensive line.

- **[V- Channel Defense Line (Row 35)]**:
  1. Insert external Orange (V-) probe wire down into **`35a`** (Later).
  2. Jumper the **1kΩ resistor** across the center gap, dropping legs into **`35c` and `35i`**.
  3. Send the filtered, safe voltage up to the diode channel via vertical jumper **`35j` ↔ `25j`**.
- **[V+ Channel Defense Line (Row 37)]**:
  1. Insert external Purple (V+) probe wire down into **`37a`** (Later).
  2. Jumper the **1kΩ resistor** across the center gap, dropping legs into **`37c` and `37i`**.
  3. Send the filtered, safe voltage up to the diode channel via vertical jumper **`37j` ↔ `27j`**.

### 5.4 Binding Diode Pairs and Sending to ADC
Finally, we bind the now-safe voltages from the diode zone (Rows 25~31) and pipe them up to the ADC.

- **[Bind Diode Bridges]**: Jumper `31g` ↔ `27g` (V+ Pair), `29g` ↔ `25g` (V- Pair)
- **[Pipe to ADC]**: Long jumper from protected terminal **`27h`** ➡️ Up-left to **`8b` (AIN0)**. Long jumper from terminal **`25h`** ➡️ Up-left to **`9b` (AIN1)**.

> 🎉 **With this, 100% of the soldering for the 3.3V Analog Base Board (Board B) is complete!** 
> It is highly recommended to designate one extra zone to ground the silver shield wires from the external probe later.
> - **[Dedicated Shield Zone (e.g., Row 36)]**: Run one long jumper from the left AGND (Row 1 Blue or 1d) to **`36c`**. Later, twist the V+ and V- shield wires together and plug them into **`36a` or `36b`**, routing noise immediately into the ground away from the board!

---

## ♟️ Assembly Progress: Step 6 - DPDT Relay Drive Circuit (Independent Board!)

> 🌟 **[New Architecture Deployed]** To maximize noise isolation and system stability, from here on out we abandon the old analog breadboard and assemble independently on a **completely new breadboard or perfboard (Board C: 12V Switching Board)**!

This is a 12V Relay switching circuit designed to swap the direction of the 1mA constant current source back and forth (Reversal) into the sample's I+ and I- terminals. We utilize a **PN2222A Transistor** so the weak 3.3V digital signal from the Arduino can reliably flick the beefy 12V relay on and off.

### 6.0 Prep List
1. **[BOM #7] DPDT Relay (12V)** (Panasonic TX2-12V / 255-1002-5-ND)
2. **[BOM #8] PN2222A Transistor** (NPN, TO-92 Package)
3. **[BOM #9] 1N4148 Diode** (Glass tube type, Black stripe is Cathode)
4. **[BOM #10] 1kΩ Resistor x 2** (Base protection and pull-down)
5. **[BOM #14, #15] 12V SMPS Wall Adapter** (Isolated fresh power source)
6. **[BOM #25] DC Barrel Jack (Panel Mount)** (External power connector)
7. **[BOM #26, #27] Inline blade fuse holder & 5A fuse** (Mandatory safety and fire prevention)

### 6.1 Independent Board (Board C) Insertion Sequence

Grab any breadboard and wire exactly according to these principles. (Row numbers are arbitrary, place freely.)

1. **Place PN2222A Transistor**:
   - Looking face-on at the flat side, pins from left to right are **E, B, C**.
2. **Connect 1N4148 Flyback Diode**:
   - Wire the diode in parallel across the two Relay Coil pins.
   - ⚠️ **Direction Check**: The diode's **Black Stripe (Cathode)** MUST connect to the 12V(+) power side. The stripeless side (Anode) connects to the Transistor's C (Collector).
3. **Connect Two 1kΩ Resistors**:
   - **Base Resistor**: Arduino Control Signal ➡️ 1kΩ Resistor ➡️ Transistor B (Base) pin.
   - **Pull-down Resistor**: Transistor B (Base) pin ➡️ 1kΩ Resistor ➡️ 12V Ground (GND).
4. **Transistor Power/Ground**:
   - Transistor E (Emitter) pin ➡️ 12V Ground (GND).
   - Transistor C (Collector) pin ➡️ Diode (Anode) and one side of the Relay Coil.
5. **Relay Power**:
   - Diode Black Stripe (Cathode) side Coil pin ➡️ External 12V(+) Power Source.

### 6.2 💎 3-Board Core Interface Wiring (Crucial)

These are the 3 "lifeline" wires linking all three independently functioning boards.

1. **[Common GND]**:
   - Board A (Arduino) GND ➡️ **MUST** be inextricably tied via a single wire to Board C (Relay Board)'s 12V GND rail.
2. **[Control Signal]**:
   - Board A (Arduino) Control Pin (e.g., `D8`) ➡️ Tip of Board C's 1kΩ Base resistor.
3. **[1mA Current Supply]**:
   - Board B (Analog Board)'s "Row 23 (End of 100Ω, S_COM)" ➡️ Long jumper connecting directly to the **COM A pin** on the Relay body on Board C.

---

## ♟️ Assembly Progress: Step 7 - 4-Point Probe Final Connection 

Once all circuits and panel assembly are finished, final step is directly terminating the actual **Signatone 4-Point Probe Head's banana plugs (or terminal wires) to the panel**.

### 7.1 Verify 4-Point Probe Pin Arrangement
The 4 pins of a Signatone probe head (especially SP4 series) are arranged linearly. (Pins 1, 2, 3, 4 from the left). Following standard wiring norms:

*   **Pin 1 (Outer edge)** ➡️ **I+ (Current Positive, Red Post)**
*   **Pin 2 (Inner)** ➡️ **V+ (Voltage Positive, Blue Post)**
*   **Pin 3 (Inner)** ➡️ **V- (Voltage Negative, Green Post)**
*   **Pin 4 (Outer edge)** ➡️ **I- (Current Negative, Black Post)**

*(If your specific probe cable colors differ, absolutely verify which tip matches which cable end using a multimeter's continuity mode.)*

### 7.2 Binding Post Connection Method
1. Fully loosen the nuts (screw heads) of the binding posts mounted on the panel by turning them counter-clockwise.
2. Insert the probe cable's terminal pin (or bare stripped wire) deeply into the lateral cross-hole exposed in the metal post shaft.
   *(If using Banana Plugs, ignore the screw entirely and just firmly stab the plug directly into the hole on the front face of the post.)*
3. Twist the nut tightly clockwise to secure. If this connection is loose or flimsy, it is the #1 cause of wildly jumping resistance values.

> 🎉 **Hardware and Wiring Assembly Complete!** Now prepare your sample, upload the code to your Arduino, and commence real-world measurements! You now possess a setup capable of the most ideal and highly precise electrical hardware measurements.
