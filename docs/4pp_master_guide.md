# 4-Point Probe Surface Resistance Measurement System Comprehensive Guide

> **Version**: 1.1 | **Date**: 2026-02-03 | **BOM**: P4PP_BOM_Final.csv

---

## 📋 Table of Contents

1. [System Overview](#1-system-overview)
2. [Core Design Principles](#2-core-design-principles)
3. [BOM Details](#3-bom-details)
4. [Detailed Circuit Design](#4-detailed-circuit-design)
5. [Stripboard Layout Overview](#5-stripboard-layout-overview)
6. [Assembly Sequence (Bring-up)](#6-assembly-sequence-bring-up)
7. [Software Implementation](#7-software-implementation)
8. [Verification and Debugging](#8-verification-and-debugging)
9. [Measurement Formulas & Correction](#9-measurement-formulas--correction)
10. [Checklist](#10-checklist)

---

## 1. System Overview

### 1.1 Objective

Implement a PoC system to measure the **Sheet Resistance (Rs, Ω/□)** of ITO and thin films using a Signatone SP4-40085TFJ 4-point probe head.

### 1.2 Scope

| INCLUDED | EXCLUDED |
|----------|----------|
| Power (12V + USB) | Stepper Motors/Drivers |
| Constant Curr Src (LM334)| Limit Switches |
| Voltage Msmt (ADS1220)| Motor Cabling |
| Input Protect (Clamps)| |
| Current Reversal (Relays)| |
| **(IN BOM) Linear Motion**| **Tier 2: Automation (Excluded in PoC)**|

> [!CAUTION]
> **Mandatory Probe Usage Precautions**
> - Always **verify sample levelness** and lower the probe **perfectly vertically**.
> - Signatone probe tips are extremely sharp and sensitive; lowering them at an angle risks severe damage.
> - **Probe Pressure Spec**: The model `085` denotes **85g per tip**.
>   - Total load across 4 tips: Approx. **340g**
>   - The Z-axis mechanism must support this load and descend smoothly without overshoot.
>   - Absolute prohibition against horizontal dragging! It directly destroys tip lifespan.

### 1.3 Block Diagram (3-Board Modular Architecture)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        System 3-Board Architecture                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    USB     ┌──────────────────┐                           │
│  │    PC    │◄─────────►│ [Board A]         │                           │
│  │ (Serial) │            │ Arduino Nano      │                           │
│  └──────────┘            │ 33 IoT (3.3V)     │                           │
│                          └────────┬──────────┘                           │
│                                   │ SPI / GPIO                           │
│                     ┌─────────────┴─────────────┐                        │
│                     ▼                           ▼                        │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐        │
│  │ [Board B]                   │  │ [Board C]                   │        │
│  │ Analog Precision Board      │  │ High-Voltage (12V) Switch   │        │
│  │  ┌─────────────────────┐   │  │  ┌─────────────────────┐   │        │
│  │  │      ADS1220        │   │  │  │   DPDT Relay         │   │        │
│  │  │  (24-bit ΔΣ ADC)    │   │  │  │ (Current Reversal)   │   │        │
│  │  └──────────┬──────────┘   │  │  │ Pole A: Source Swap  │   │        │
│  │             │              │  │  │ Pole B: Return Swap  │   │        │
│  │  ┌──────────┴──────────┐   │  │  └──────────┬──────────┘   │        │
│  │  │ Input Protection    │   │  │             │              │        │
│  │  │ (1kΩ + BAT54A/C)    │   │  │  ┌──────────┴──────────┐   │        │
│  │  └──────────┬──────────┘   │  │  │ PN2222A + 1N4148     │   │        │
│  │             │              │  │  │ (Relay Driver)       │   │        │
│  │  ┌──────────┴──────────┐   │  │  └─────────────────────┘   │        │
│  │  │ LM334 Source        │   │  │                           │        │
│  │  │ + 100Ω Shunt        │   │  │ ⚠️ Isolated 12V Power!    │        │
│  │  └──────────┬──────────┘   │  │                           │        │
│  └─────────────┼─────────────┘  └─────────────┬─────────────┘        │
│                │ (1mA Supply)                 │                          │
│                └──────────────────────────────┘                          │
│                               │                                          │
│                               ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐         │
│  │                    Panel Binding Posts                      │         │
│  │              [I+] [V+] [V-] [I-]                            │         │
│  └─────────────────────────────────────────────────────────────┘         │
│                              │                                           │
│                              ▼                                           │
│                    ┌─────────────────┐                                   │
│                    │  Signatone 4PP  │                                   │
│                    │    Probe Head   │                                   │
│                    └─────────────────┘                                   │
│                              ▼                                           │
│                    ┌─────────────────┐                                   │
│                    │   ITO Sample    │                                   │
│                    └─────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Core Module Descriptions

| Module | Function | Key Parts |
|:---:|---|---|
| **MCU** | Master control, PC comms, ADC data acqusition | Arduino Nano 33 IoT |
| **ADS1220** | Precision voltage read (24-bit). Reads microvolts | ADS1220 (TI) |
| **Input Protection** | Guards delicate ADC from overvoltage/ESD | BAT54S (Diode), 1kΩ |
| **LM334 Current Src** | Injects constant current (1mA/100µA) | LM334, Rset, Shunt |
| **DPDT Relay** | Physically swaps current direction for Delta Mode | Panasonic TQ2-12V |
| **Relay Driver** | Drives 12V relay using 3.3V Arduino signal | PN2222A (Transistor) |
| **Power Filter** | Filters noise out of power lines (Clean 3.3V) | 10Ω, 1µF, 0.1µF |

---

## 2. Core Design Principles

> [!IMPORTANT]
> The following 5 principles MUST be strictly adhered to for accurate measurements.

### 2.1 Keep ADC Inputs Within Rails

```
ADS1220 Safe Input Range (when PGA is bypassed):
AVSS − 0.1V  ~  AVDD + 0.1V
   ↓              ↓
 -0.1V          3.4V  (Assuming 3.3V supply)
```

**Solution**: Tie the constant current source to the 3.3V rail → Keeps sample potential within 0~3.3V.

### 2.2 Use Actual Measured Current, Not Assumed Value

> [!CAUTION]
> The LM334 has **temperature dependency (+0.33%/°C)**, meaning current drifts.
> You must physically measure the injected current using the 100Ω shunt.

```
I_actual = V_shunt / 100Ω
R_sample = V_sense / I_actual  ← The only way to guarantee accuracy.
```

### 2.3 Eliminate Offsets via Current Reversal (Delta Mode)

This is the **most effective method** for canceling Thermal EMF and ADC offsets:

```
1. Inject Forward Curr → (Wait for settle) → Measure V_fwd
2. Swap Curr Dir via Relay → (Wait for settle) → Measure V_rev
3. V_corrected = (V_fwd - V_rev) / 2
4. Rs = Correction_Factor × (V_corrected / I_actual)
```

> [!TIP]
> **Settle Time**
> - Recommend waiting **100~300ms** after relay switching.
> - Discarding the first 1~2 samples right after switching stabilizes averages.

### 2.4 Modular Physical Board Separation (3-Board System)

To maximize noise isolation and maintainability, the system is wholly separated into **three physically distinct boards**.

| Board Name | Role | Circuits Included | Power Used |
|-----------|------|-----------|-----------|
| **Board A** | Brain/Controller | Arduino Nano 33 IoT | 5V (USB) → Outputs 3.3V |
| **Board B** | Analog Baseboard | RC filter, ADS1220, LM334, BAT54 | 3.3V (From Board A) |
| **Board C** | Switch/Relay Board | DPDT Relay, PN2222A, Flyback | 12V (Separate Wall Adapter) |

| **If Operating Motors** | - | **Must turn Motor Driver EN=OFF during measurements (Crucial)** |
 
 → **Physical isolation is absolute**. Only essential interface wires cross boundaries.

### 2.5 LM334 Headroom limits (Dropout Warning)

> [!WARNING]
> **Check this when measuring high-resistance samples!**
> 
> Due to the 3.3V power ceiling, if the sample resistance gets too high (**several kΩ or more**), the LM334 cannot maintain its target current (Dropout).

```
LM334 Operating Condition:
  V_headroom = V_supply - V_sample - V_shunt - V_LM334(min)
             = 3.3V - (I × R_sample) - (I × 100Ω) - 0.9V

  ↓ If R_sample grows too large ↓
  V_headroom < 0 → LM334 Dropout → I_actual plummets!
```

**Software monitoring required**:
- Calculate `I_actual = V_shunt / 100 ohm` every cycle.
- Output warnings if current drops by **10% or more** against target.

**Estimated operating guidance**:
- `68.1 ohm Rset` (`~1 mA`): best for lower-resistance samples, but dropout starts sooner.
- `681 ohm Rset` (`~100 uA`, default bring-up mode): safer for higher-resistance samples, but produces a smaller sense voltage on low-resistance films.

**Estimated Limits (at 1mA)**:
```
R_sample_max ~= (3.3V - 0.1V_shunt - 0.9V_LM) / 1mA ~= 2.3kOhm
```

### 2.6 Star Ground Topology

```
                    ┌─────────────────┐
                    │ Arduino GND Pin │ ← Head Station (Star Point)
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
      ┌──────────┐    ┌──────────┐    ┌──────────┐
      │ ADC AGND │    │  3V3_A   │    │ 12V GND  │
      │(Closest) │    │ Decoup.  │    │(Farthest)│
      └──────────┘    └──────────┘    └──────────┘
```

---

## 3. BOM Details (Refer to Master CSV)

> Please refer to the final `BOM_final.md` document for the detailed, synchronized BOM list. All component numbering references `BOM #N` match that finalized file.

---

## 4. Detailed Circuit Design

### 4.1 Power Filter (Generating 3V3_A)

```
Arduino 3V3 ──┬── 3V3_DIG
              │
             10Ω
              │
              ├── 3V3_A ──┬── ADS1220 AVDD/VDD
              │           │
             0.1µF       1µF
              │           │
              └─────┬─────┘
                    │
                  AGND
```

### 4.2 ADC Input Protection Circuit

```
                        3V3_A
                          │
                     ┌────┴────┐
                     │ BAT54C  │
                     │ pin3    │
                     └────┬────┘
                    pin1  │  pin2
                      │   │   │
   V+ ──── 1kΩ ───────┴───┼───┴─────── 1kΩ ──── V-
   Post                   │                     Post
                          │
              ┌───────────┴───────────┐
              │                       │
          IN0_NODE               IN1_NODE
              │                       │
              ▼                       ▼
          ADS1220                 ADS1220
           AIN0                    AIN1
              │                       │
              │     ┌────┬────┐       │
              └─────┤pin1│pin2├───────┘
                    │ BAT54A  │
                    └────┬────┘
                         │ pin3
                         │
                       AGND
```

### 4.3 Constant Current Source (LM334)

```
       3V3_A
         │
         ▼
    ┌─────────┐
    │  LM334  │
    │         │
    │ V+   R  ├──── Rset (68.1Ω or 681Ω)
    │         │         │
    │    V-   ├─────────┘
    └────┬────┘
         │
        100Ω (Shunt) ← V_shunt measurement node
         │
         ▼
    SHUNT_LO (Current output)
```

> [!CAUTION]
> **Crucial DPDT Wiring Correction**
> 
> A DPDT must utilize **BOTH Poles (both COMs)** to successfully reverse the current flow!
> You must cross-swap **Pole A** (Source side) and **Pole B** (Return side) simultaneously.

### 4.4 DPDT Current Reversal Circuit (Critical!)

```
              ┌─────────────────────────────────────────────┐
              │              DPDT Relay (TQ2-12V)           │
              │                                             │
              │   Pole A (Source Side)      Pole B (Return) │
              │   ┌───────────┐        ┌───────────┐        │
              │   │           │        │           │        │
   SHUNT_LO ──┼──►│   COM_A   │        │   COM_B   │◄───AGND│
              │   │     │     │        │     │     │        │
              │   │  ┌──┴──┐  │        │  ┌──┴──┐  │        │
              │   │ NC_A  NO_A│        │ NC_B  NO_B│        │
              │   │  │     │  │        │  │     │  │        │
              │   └──┼─────┼──┘        └──┼─────┼──┘        │
              └─────┼─────┼──────────────┼─────┼────────────┘
                    │     │              │     │
                    │     └──────────────┼─────┼──► I- Post
                    │                    │     │
                    └────────────────────┼─────┘
                                         │
                                         ▼
                                       I+ Post
```

**Relay Wiring (Orthodox Setup)**:

| Pole | Pin | Connection |
|------|-----|------------|
| **A** | COM_A | SHUNT_LO (LM334 Output, post-shunt) |
| **A** | NC_A | I+ Post (Red) |
| **A** | NO_A | I- Post (Black) |
| **B** | COM_B | AGND (Current Return Route) |
| **B** | NC_B | I- Post (Black) |
| **B** | NO_B | I+ Post (Red) |

**Operational Principle**:
- **Relay OFF (NC Contacts)**: SHUNT_LO→I+, AGND→I- → **Forward Current**
- **Relay ON (NO Contacts)**: SHUNT_LO→I-, AGND→I+ → **Reverse Current**

### 4.5 Relay Driver Circuit

```
Arduino ──── 1kΩ ────┬──── PN2222A Base
  GPIO               │
                     │      ┌────────┐
                    10kΩ    │ DPDT   │
                     │      │ Relay  │
                   GND      │  Coil  │
                            └───┬────┘
                                │
                     ┌──────────┼──────────┐
                     │          │          │
               ┌─────┴─────┐  0.1µF  ┌─────┴─────┐
               │  1N4148   │   │     │  Optional │
               │ (Flyback) │   │     │ Snubber   │
               └─────┬─────┘   │     └───────────┘
                     │         │
        PN2222A ─────┴─────────┘
        Collector               │
                               12V
        Emitter ─────── 12V GND
```

### 4.6 Shunt Current Monitor (ADS1220 2nd Channel)

```
LM334 Output ──── Shunt 100Ω ──┬──── To Relay
                             │
              ┌──────────────┴──────────────┐
              │                              │
          Shunt+                         Shunt-
              │                              │
             1kΩ                            1kΩ
              │                              │
              ▼                              ▼
          ADS1220                        ADS1220
           AIN2                           AIN3
```

---

### 4.7 12V Input Protection (Power Protection)

> [!WARNING]
> Protecting the 12V line is mandatory! Relay/Motor spikes can cascade and damage the ADC.

```
       DC Barrel Jack (#25)                To Stripboard #2
            │                                  │
            ▼                                  ▼
  ┌──────────────────────────────────────────────────────┐
  │                                                      │
  │  12V+  ────[FUSE #26+#27]──── 5A ────┬── 12V_FUSED   │
  │    IN                                │               │
  │                           ┌──────────┴──────────┐    │
  │                           │     SMBJ15A         │    │
  │                           │  (TVS Unidir)       │    │
  │                           │  Cathode → 12V      │    │
  │                           │  Anode → GND        │    │
  │                           └──────────┬──────────┘    │
  │                                      │               │
  │  GND  ───────────────────────────────┴── 12V_GND    │
  │                                                      │
  └──────────────────────────────────────────────────────┘
```

---

## 5. Stripboard Layout Overview

> [!NOTE]
> For highly detailed step-by-step soldering and wiring instructions for the Analog (Board B, C) section, refer to **[`analog_wiring_guide.md`](./analog_wiring_guide.md)**.
> For the Stepper Motor and logic details (Board D), refer to **[`movement_implementation_guide.md`](./movement_implementation_guide.md)**.

> [!WARNING]
> **Leakage Current Mitigation**
> - The IN0/IN1 strips (V+/V-) MUST be cleaned with flux remover to maximize insulation resistance.
> - **Even nA of leakage current** will cause massive mV measurement errors.
> - **Flux cleaning is mandatory!** Use IPA (Isopropyl Alcohol) and a brush after soldering.

---

### 5.6 Physical Topology Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Metal Enclosure (EMI Shield)                       │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                                                                   │  │
│  │   ┌──────────────────┐               ┌──────────────────┐         │  │
│  │   │   [Board B]      │ ◀──ISOLATION──▶ │   [Board C]      │         │  │
│  │   │ Analog/ADC (3.3V)│               │ Relay Drv (12V)  │         │  │
│  │   │  ┌────────────┐  │               │  ┌────────────┐  │         │  │
│  │   │  │  ADS1220   │  │               │  │DPDT Relay  │  │         │  │
│  │   │  └────────────┘  │               │  └────────────┘  │         │  │
│  │   └────────▲─────────┘               └────────▲─────────┘         │  │
│  │            │ SPI cable (7-wire)                 │ Ctrl wire (2)       │  │
│  │            │                                  │                   │  │
│  │            └─────────┬──────────────┬─────────┘                   │  │
│  │                      ▼              ▼                             │  │
│  │                   ┌────────────────────┐                          │  │
│  │                   │     [Board A]      │                          │  │
│  │                   │ Arduino Nano 33 IoT│                          │  │
│  │                   └────────────────────┘                          │  │
│  │                                                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     Panel Binding Posts                         │    │
│  │                                                                 │    │
│  │      🔴 I+      🔵 V+      🟢 V-      ⚫ I-                     │    │
│  │     (Red)     (Blue)    (Green)   (Black)                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Enclosure Case → Tied to AGND (At exactly ONE point)                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Assembly Sequence (Bring-up)

Go to **`analog_wiring_guide.md`** and follow the 7 sequential guide steps listed in that document.

---

## 7. Software Implementation

### 7.1 Recommended ADS1220 Settings

```cpp
// ADS1220 Register Setup
// Config Register 0
//   MUX = AIN0/AIN1 (Differential)
//   GAIN = 1 (PGA bypass) → Circumvents VCM restrictions, simplifies circuit.
//   PGA_BYPASS = 1 (Maximizes input headroom)
byte config0 = 0b00000001; // MUX=00, GAIN=000, PGA_BYPASS=1

// Config Register 1
//   - DR[2:0] = 000 → 20 SPS (Normal mode)
//   - MODE[1:0] = 00 → Normal mode  
//   - CM = 1 → Continuous conversion
byte config1 = 0b00000100;

// Config Register 2
//   VREF=00 (Internal 2.048V) ← Recommended for PoC!
byte config2 = 0b00010000; 

// Config Register 3
byte config3 = 0b00000000;
```

### 7.2 Delta Mode Reversal Routine

```cpp
struct Measurement {
  float V_corrected;
  float I_actual;
  float R_sample;
  float Rs;
};

Measurement measureWithReversal() {
  Measurement m;
  
  // 1. Forward Current
  digitalWrite(RELAY_PIN, LOW);
  delay(500);  // Settle time
  
  float V_fwd = readVoltage(0x00);  // V sense
  float V_shunt_fwd = readVoltage(0x30);  // Shunt
  
  // 2. Reverse Current
  digitalWrite(RELAY_PIN, HIGH);
  delay(500);  // Settle time
  
  float V_rev = readVoltage(0x00);  // V sense
  float V_shunt_rev = readVoltage(0x30);  // Shunt
  
  // 3. Math
  m.V_corrected = (V_fwd - V_rev) / 2.0;
  
  // Average the current (More accurate)
  float I_fwd = V_shunt_fwd / SHUNT_R;
  float I_rev = abs(V_shunt_rev) / SHUNT_R; 
  m.I_actual = (I_fwd + I_rev) / 2.0;
  
  m.R_sample = m.V_corrected / m.I_actual;
  
  // Geometric Correction Factor F
  // Based on NBS Standard for 1-inch target centered.
  float F_GEOM = 4.47044;  
  
  m.Rs = F_GEOM * m.R_sample;  // Sheet Resistance
  
  // 4. Return relay to default
  digitalWrite(RELAY_PIN, LOW);
  
  return m;
}
```

---

## 8. Verification and Debugging

### 8.1 Common Problems & Solutions

| Symptom | Cause | Solution |
|------|------------|--------|
| ADS1220 values jump wildly| Lack of decoupling, Gnd Loop | Add 0.1µF, verify Star Ground |
| Current wildly deviates | Wrong Rset, LM334 blown | Check Rset, replace LM334 |
| V sense clips at rail | Clamp activation, Overvoltage | Check contact, lower the current |
| Rs changes vs varied current | Non-ohmic contact | Increase pressure, clean tips |
| Values drift slowly | Thermal EMF buildup | Use Delta Mode Reversal, let settle |
| Noise when switching relay| 12V/3.3V coupling | Full physical separation, wire routing |

---

## 9. Measurement Formulas & Correction

### 9.1 Basic Math

```
Resistance:
  R_sample = V_sense / I_actual

Sheet Resistance (Infinite Sheet Approx):
  Rs = (π / ln2) × R_sample
     = 4.532 × R_sample  [Ω/□]
```

### 9.2 Current Reversal Correction (Delta Mode)

```
V_corrected = (V_fwd - V_rev) / 2

Benefits:
  - Eliminates ADC offset
  - Eliminates Thermal EMF voltages
  - Compensates for contact asymmetry
```

### 9.3 Sample Size Correction Factor (CF)

> [!WARNING]
> **Important**: The `4.532` multiplier is ONLY valid **when sample size > 40x the probe spacing**.

```
Probe Spacing: s = 40 mil = 1.016 mm
Minimum sample radius: 40 × 1.016 mm ≈ 40 mm

Smaller samples demand a Correction Factor (CF):
  Rs = CF × (π / ln2) × (V / I)
```

**NBS/NIST TN 199 Standard (Circular, centered)**:
- 1-inch sample / 40mil probe spacing (d/s ≈ 25)
- **F = 4.47044** (CF ≈ 0.986)
- This guide fixes this value in code. Adjust if using differently sized samples.

---

## 10. Checklist

### 10.1 Pre-Assembly
- [ ] Arduino Nano 33 IoT blinks and connects to PC.
- [ ] ADS1220 pin headers soldered.
- [ ] BAT54A/C SOT23→DIP soldered accurately.
- [ ] Confirm Resistor bands (68.1Ω, 681Ω, 100Ω, 1kΩ, 10Ω).

### 10.2 Post-Assembly Final Eval
- [ ] Measure a standard known resistor to verify absolute accuracy.
- [ ] Measure an ITO sample (Expect <5% repeatability variance).
- [ ] Current Reversal confirms `V_fwd ≈ -V_rev`.

### 10.3 Flux Cleaning (Critical!)
> [!CAUTION]
> To prevent nano-ampere leakage currents spanning across the stripboard, you MUST clean all flux.

- [ ] Use IPA (Isopropyl Alcohol) and a stiff ESD brush to aggressively scrub the back of the soldered board.

---

## 📚 References

- [ADS1220 Datasheet (TI)](https://www.ti.com/product/ADS1220)
- [LM334 Datasheet (TI)](https://www.ti.com/product/LM334)
- [BAT54 Datasheet (ON Semi)](https://www.onsemi.com/products/discrete-power-modules/schottky-diodes/bat54a)
- [SEMI MF84 - Four-Point Probe Standard](https://store.semi.org/products/mf08400-semi-mf84)
- Smits, F.M. "Measurement of Sheet Resistivities with the Four-Point Probe" Bell System Technical Journal, 1958

---

> **Next Steps**: Having digested this master overview, proceed with the actual build by strictly following **`analog_wiring_guide.md`** and **`movement_implementation_guide.md`**.

