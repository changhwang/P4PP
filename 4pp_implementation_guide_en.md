# 4-Point Probe Surface Resistance Measurement System - Implementation Guide

> **Version**: 1.1 | **Date**: 2026-02-09 | **BOM**: 4pp_BOM_v5.xlsx

---

## 📋 Table of Contents

1. [System Overview](#1-system-overview)
2. [Key Design Principles](#2-key-design-principles)
3. [BOM Details](#3-bom-details)
4. [Detailed Circuit Design](#4-detailed-circuit-design)
5. [Stripboard Layout](#5-stripboard-layout)
6. [Assembly Sequence (Bring-up)](#6-assembly-sequence-bring-up)
7. [Software Implementation](#7-software-implementation)
8. [Verification and Debugging](#8-verification-and-debugging)
9. [Formulas and Correction](#9-formulas-and-correction)
10. [Checklist](#10-checklist)

---

## 1. System Overview

### 1.1 Goal

Implement a PoC system to measure **Sheet Resistance (Rs, Ω/□)** of ITO and thin films using a Signatone SP4-40085TFJ 4-point probe head.

### 1.2 Scope

| Included | Excluded |
|----------|----------|
| Power (12V + USB) | Stepper Motor/Driver |
| Current Source (LM334) | Limit Switches |
| Voltage Measurement (ADS1220) | Motor Cabling |
| Input Protection (Clamp) | |
| Current Reversal (DPDT Relay) | |
| **(In BOM) Linear Motion** | **Tier 2: Automation (Excluded from PoC)** |

> [!CAUTION]
> **Essential Precautions for Probe Usage** (Gemini Feedback)
> - Always **verify sample leveling** before measurement and lower the probe **vertically**.
> - Signatone probe tips are very sharp and sensitive; lowering them at an angle risks damage.
> - **Probe Pressure Spec** (ChatGPT Feedback): Model `085` implies **85g per tip**.
>   - Total load for 4 tips: Approx. **340g**
>   - The Z-axis mechanism must support this load and lower smoothly without overshoot.
>   - **ABSOLUTELY NO horizontal movement (dragging)** while in contact! This directly affects tip life.

### 1.3 Block Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           System Architecture                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    USB     ┌──────────────────┐                          │
│  │    PC    │◄─────────►│  Arduino Nano    │                          │
│  │ (Serial) │            │   33 IoT (3.3V)  │                          │
│  └──────────┘            └────────┬─────────┘                          │
│                                   │ SPI                                │
│                     ┌─────────────┴─────────────┐                      │
│                     ▼                           ▼                      │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐      │
│  │  Analog/ADC Zone (3.3V_A)   │  │   Noise Zone (12V only)      │      │
│  │  ┌─────────────────────┐   │  │  ┌─────────────────────┐   │      │
│  │  │      ADS1220        │   │  │  │    DPDT Relay       │   │      │
│  │  │  (24-bit ΔΣ ADC)    │   │  │  │ (Current Reversal)  │   │      │
│  │  └──────────┬──────────┘   │  │  │ Pole A: Source Swap │   │      │
│  │             │              │  │  │ Pole B: Return Swap │   │      │
│  │  ┌──────────┴──────────┐   │  │  └──────────┬──────────┘   │      │
│  │  │ Input Protection    │   │  │             │              │      │
│  │  │ (1kΩ + BAT54A/C)    │   │  │  ┌──────────┴──────────┐   │      │
│  │  └──────────┬──────────┘   │  │  │  PN2222A + 1N4148   │   │      │
│  │             │              │  │  │   (Relay Driver)    │   │      │
│  │  ┌──────────┴──────────┐   │  │  └─────────────────────┘   │      │
│  │  │ LM334 Current Src   │   │  │                           │      │
│  │  │ + 100Ω Shunt        │   │  │  ⚠️ Coil only is 12V!     │      │
│  │  └──────────┬──────────┘   │  │    LM334/Shunt not here   │      │
│  └─────────────┼─────────────┘  └─────────────────────────────┘      │
│                │                              │                      │
│                ▼                              ▼                      │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │                    Panel Binding Posts                      │      │
│  │              [I+] [V+] [V-] [I-]                            │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                              │                                        │
│                              ▼                                        │
│                    ┌─────────────────┐                                │
│                    │  Signatone 4PP  │                                │
│                    │    Probe Head   │                                │
│                    └────────┬────────┘                                │
│                             ▼                                         │
│                    ┌─────────────────┐                                │
│                    │   ITO Sample    │                                │
│                    └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Design Principles

> [!IMPORTANT]
> You must adhere to these 5 principles for accurate measurements.

### 2.1 Keep ADC Input Voltage within Rails

```
ADS1220 Input Safety Range (PGA bypass):
AVSS − 0.1V  ~  AVDD + 0.1V
   ↓              ↓
 -0.1V          3.4V  (Based on 3.3V supply)
```

**Solution**: Build the Current Source based on the 3.3V rail → Sample potential stays within 0~3.3V.

### 2.2 Use Measured Current, Not Assumed

> [!CAUTION]
> LM334 has **temperature dependence (+0.33%/°C)**, causing current drift.
> You MUST measure the actual current using the 100Ω shunt and use it for calculation.

```
I_actual = V_shunt / 100Ω
R_sample = V_sense / I_actual  ← This is accurate
```

### 2.3 Remove Offset with Current Reversal (Delta Mode)

The **most effective way** to remove Thermal EMF and ADC Offset:

```
1. Apply Forward Current → (wait for settle) → Measure V_fwd
2. Switch Relay (Reverse) → (wait for settle) → Measure V_rev
3. V_corrected = (V_fwd - V_rev) / 2
4. Rs = 4.532 × (V_corrected / I)
```

> [!TIP]
> **Settle Time** (ChatGPT Feedback)
> - Recommend waiting **100~300ms** after relay switching.
> - Discarding **1~2 samples** immediately after switching yields more stable results.

### 2.4 Zone Separation (Analog vs Digital/Relay)

| Zone | Power | Components |
|------|-------|------------|
| **Analog Zone** | 3.3V only | ADS1220, Input Protection, 100Ω shunt |
| **Noisy Zone** | 12V | Relay Coil, Future Motor Drivers |

| **When Driving Motors** | - | **Driver EN=OFF (Essential) during measurement** |

→ **Physically Separate** (2 Stripboards or keep distance)

### 2.5 LM334 Headroom Limit (Dropout Warning)

> [!WARNING]
> **Critical Check for High-Resistance Samples** (Gemini Feedback)
> 
> Due to the 3.3V supply, if sample resistance exceeds **a few kΩ**, 
> LM334 may fail to maintain constant current (Dropout).

```
LM334 Operating Condition:
  V_headroom = V_supply - V_sample - V_shunt - V_LM334(min)
             = 3.3V - (I × R_sample) - (I × 100Ω) - 0.9V

  ↓ If R_sample is too high ↓
  V_headroom < 0 → LM334 Dropout → I_actual drops sharply!
```

**Software Monitoring Essential**:
- Calculate `I_actual = V_shunt / 100Ω` every measurement.
- If it drops by **>10%** vs target: Output "Headroom Warning!"
- Example: Target 1mA, Measured 0.85mA → Warning.

**Estimated Limit** (at 1mA):
```
R_sample_max ≈ (3.3V - 0.1V_shunt - 0.9V_LM) / 1mA ≈ 2.3kΩ
```

### 2.6 Star Ground

```
                    ┌─────────────────┐
                    │ Arduino GND Pin │ ← Central Station (Star Point)
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
      ┌──────────┐    ┌──────────┐    ┌──────────┐
      │ ADC AGND │    │  3V3_A   │    │ 12V GND  │
      │ (Closest)│    │ Decoupling │    │ (Farthest)│
      └──────────┘    └──────────┘    └──────────┘
```

---

## 3. BOM Details (Based on 4pp_BOM_v5.xlsx)

> [!NOTE]
> **BOM Scope Warning**: **Linear Motion (Stepper, Rails, etc.)** items in `4pp_BOM_v5.xlsx` are for **Tier 2 Automation**. They are **NOT used** in this **Tier 0 Manual PoC**.

> Part numbers `#N` refer to Item # column in 4pp_BOM_v5.xlsx.

### 3.1 Core Components

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **1** | Arduino Nano 33 IoT | 3 | ABX00027 | MCU | 3.3V Logic, USB Power |
| **2** | ADS1220 24-bit ADC Breakout | 3 | BB-ADS1220 | Voltage Measure | SPI, Olimex |

### 3.2 Current Source

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **3** | LM334Z/NOPB | 10 | LM334Z/NOPB | Current Src IC | TO-92, I=67.7mV/Rset |
| **4** | Rset 68.1Ω 0.1% | 25 | YR1B68R1CC | 1mA Setting | I ≈ 0.994mA @25°C |
| **5** | Rset 681Ω 0.1% | 25 | YR1B681RCC | 100µA Setting | I ≈ 99.4µA @25°C |
| **6** | 100Ω Shunt 0.1% | 25 | MFP-25BRD52-100R | Current Monitor | V_shunt = I × 100Ω |

### 3.3 Current Reversal

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **7** | DPDT Relay 12V | 3 | TQ2-12V | Reversal | Panasonic, Through-hole |
| **8** | PN2222A NPN | 10 | PN2222ABU | Relay Driver | TO-92 |
| **9** | 1N4148 Diode | 20 | 1N4148FS | Flyback | EMF Protection |
| **10** | Base Resistor 1kΩ 0.1% | 25 | YR1B1K0CC | Transistor Base | GPIO → Base |
| **48** | Pulldown Resistor 10kΩ | 10 | - | Transistor Base | Prevents Glitch (Step 6) |

### 3.4 Input Protection

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **11** | BAT54A (Common Anode) | 10 | BAT54ACT | Clamp → AGND | SOT-23 |
| **12** | BAT54C (Common Cathode) | 10 | BAT54CTR | Clamp → 3V3_A | SOT-23 |
| **13** | SOT23→DIP Adapter | 10 | 00717 | SMD→DIP | For BAT54 mounting |
| **14** | 1kΩ Series Resistor 1% | 50 | 1.00KXBK | Input Protection | Current Limiting |

### 3.5 Power Supply

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **15** | 12V Adapter 60W (5A) | 1 | - | Relay/Motor Power | 2.5mm Center+ |
| **16** | Power Cord | 1 | TL868 | AC Cord | |
| **33** | DC Barrel Jack (PCB) | 2 | SC1863 | 12V Input | 5.5x2.5mm |

### 3.6 Power Protection

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **17** | 500mA Fuse (5x20mm) | 10 | 0215.500MXEP | Circuit Protection | Slow-blow |
| **18** | Fuse Holder (PCB) | 5 | - | For 5x20mm | PCB Clip Type |
| **34** | Inline Blade Fuse Holder | 5 | F3209 | For ATC/ATO | Splash Cover |
| **35** | 5A Blade Fuse | 10 | 0287005.U | 12V Main Protect | 32V ATC |
| **36** | 3A Blade Fuse | 10 | F11061 | Spare | 32V ATC |
| **37** | SMBJ15A TVS | 10 | SMBJ15ALFCT | 12V Spike Absorb | Uni-dir, DO-214AA |

### 3.7 Power Control (Optional)

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **19** | Toggle Switch SPST | 3 | SW-T3-1A-A-A3-S1 | Power ON/OFF | Panel Mount |
| **20** | Power LED (3mm Red) | 50 | LED3RED | Indicator | Through-hole |

### 3.8 Decoupling Capacitors

> [!IMPORTANT]
> **Distinguish between Essential and Optional!**
> - **Essential (Right next to ADS1220 pins)**: #40 + #41 Ceramic
> - **Optional (Bulk/Stabilization)**: #21 Electrolytic, #22 Film

#### 🔴 Essential — Next to ADS1220 Power Pins (3V3_A ↔ AGND)

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **40** | 1µF Ceramic X7R 16V | 50 | FK24X7R1C105KN000 | **Mid-freq Decoupling** | Radial, Essential |
| **41** | 0.1µF Ceramic X7R 50V | 50 | RDER71H104K0M1H03A | **High-freq Decoupling** | Radial, Essential |

#### 🟡 Optional — Bulk/Aux Caps (Improves PoC Quality)

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **21** | 10µF Electrolytic 25V | 10 | EEA-GA1E100H | Bulk Cap | Add on 12V or 3V3_A |
| **22** | 0.1µF Film Cap 100V | 10 | R82EC3100DQ70J | Aux Stabilization | ⚠️ Cannot replace Ceramic |

#### Other Power Parts

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **38** | 470µF Electrolytic 25V | 10 | P14418 | 12V Bulk | Radial, Essential |
| **39** | 10Ω Resistor 1% | 25 | MFR-25FTF52-10R | 3V3_DIG → 3V3_A Filter | 1/4W |

### 3.9 Connectors & Wiring

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **23** | Male Header 1x40 | 10 | HDR100IMP40M | Arduino/ADC | 2.54mm |
| **24** | Female Header 1x40 | 10 | HDR100IMP40F | Arduino/ADC Socket | 2.54mm |
| **25** | Binding Post (Black) | 2 | 501-1094 | **I-** | ⚫ |
| **26** | Binding Post (Red) | 2 | 501-1095 | **I+** | 🔴 |
| **27** | Binding Post (Green) | 2 | 501-1506 | **V-** | 🟢 |
| **28** | Binding Post (Blue) | 2 | 501-1650 | **V+** | 🔵 |
| **30** | Shielded Wire 22AWG | 25ft | Belden 9461 | V+/V- Sense Line | ⚠️ See below |

> [!IMPORTANT]
> **Shield Grounding Principle** (ChatGPT Feedback)
> - Ground Shield **ONLY at one point (ADC AGND side)**.
> - Keep Shield **OPEN (Floating)** at the Probe Head side.
> - Grounding both ends creates a Ground Loop → Noise!

| **42** | Terminal Block 2P | 30 | 2138 | Wiring Convenience | 0.1" pitch |
| **43** | Micro-USB Cable | 5 | 2185 | Arduino↔PC | |
| **45** | 22AWG Stranded Set | 1 | - | Internal Wiring | 10 colors |
| **46** | 22AWG Solid Set | 1 | - | Stripboard Jumpers | 10 colors |

### 3.10 EMI/Noise Control (Optional)

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **29** | Ferrite Clamp | 10 | 1934-1375 | EMI Attenuation | Snap-on |

### 3.11 Misc/Tools

| # | Part | Qty | Mfr P/N | Usage | Note |
|:-:|------|:-:|---------|-------|------|
| **31** | Desoldering Braid | 1 | 60-5-5 | Correction | |
| **32** | Snap Switch SPDT | 10 | SW1249 | Limit Switch (Motor) | 15A 250V |
| **47** | PCB Vise | 1 | - | Workbench | |

---

**Panel Post Color Assignment** (4pp_BOM_v5 #25~28):
```
┌─────────────────────────────────────────┐
│              Panel Front                │
│                                         │
│   🔴 I+     🔵 V+     🟢 V-     ⚫ I-    │
│   #26      #28      #27      #25       │
│   (Red)    (Blue)   (Green)  (Black)   │
│                                         │
│   Current   Voltage  Voltage   Current  │
│   (HIGH)    (HIGH)    (LOW)     (LOW)   │
└─────────────────────────────────────────┘
```

---

## 4. Detailed Circuit Design

### 4.1 Power Filter (3V3_A Generation)

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

### 4.3 Current Source (LM334)

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
        100Ω (Shunt) ← Vshunt Measurement Point
         │
         ▼
    SHUNT_LO (Current Output)
```

> [!CAUTION]
> **Critical DPDT Wiring** (ChatGPT Feedback)
> 
> You MUST use **both Poles (COM A & B)** of the DPDT relay to truly reverse current!
> **Pole A** (Source side) and **Pole B** (Return side) must swap in a crossover pattern.

### 4.4 DPDT Current Reversal Circuit

```
              ┌─────────────────────────────────────────────┐
              │             DPDT Relay (TQ2-12V)            │
              │                                             │
              │  Pole A (Source Side)  Pole B (Return Side) │
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

**Relay Wiring (Standard)**:

| Pole | Pin | Connection |
|------|-----|------------|
| **A** | COM_A | SHUNT_LO (LM334 Output) |
| **A** | NC_A | I+ Post (Red) |
| **A** | NO_A | I- Post (Black) |
| **B** | COM_B | AGND (Current Return) |
| **B** | NC_B | I- Post (Black) |
| **B** | NO_B | I+ Post (Red) |

**Operation Logic**:
- **Relay OFF (NC)**: SHUNT_LO→I+, AGND→I- → **Forward Current**
- **Relay ON (NO)**: SHUNT_LO→I-, AGND→I+ → **Reverse Current**

**LM334 Pinout**:
- **V+ (pin 1)**: 3V3_A Input
- **R (pin 2)**: One side of Rset
- **V- (pin 3)**: Other side of Rset + Current Output

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

> [!TIP]
> **Gemini Feedback**: Adding a **0.1µF ceramic cap (#41)** in parallel with the relay coil 
> helps suppress high-frequency spikes better than the diode alone.

### 4.6 Shunt Current Monitor (ADS1220 2nd Channel)

```
LM334 Out ───── Shunt 100Ω ──┬──── To Relay
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
> 12V line protection is mandatory! Relay spikes can damage the ADC.

```
       DC Barrel Jack (#33)             To Stripboard #2
            │                                  │
            ▼                                  ▼
  ┌──────────────────────────────────────────────────────┐
  │                                                      │
  │  12V+  ────[FUSE #34+#35]──── 5A ────┬── 12V_FUSED  │
  │    IN                                │              │
  │                           ┌──────────┴──────────┐   │
  │                           │     SMBJ15A #37     │   │
  │                           │  (TVS Uni-dir)       │   │
  │                           │  Cathode → 12V      │   │
  │                           │  Anode → GND        │   │
  │                           └──────────┬──────────┘   │
  │                                      │              │
  │  GND  ───────────────────────────────┴── 12V_GND   │
  │                                                      │
  └──────────────────────────────────────────────────────┘
```

**12V Protection Parts (See BOM)**:

| BOM# | Part | Usage |
|:-:|------|-------|
| #33 | DC Barrel Jack | 12V Input Connector |
| #34 | Inline Fuse Holder | ATC/ATO Fuse Holder |
| #35 | 5A Blade Fuse | Overcurrent Protection |
| #37 | SMBJ15A TVS | Spike Absorption (15V Clamp) |
| #38 | 470µF 25V Electrolytic | Bulk Decoupling |
| #41 | 0.1µF Ceramic | High-freq Decoupling |

### 4.8 Power Control (Optional)

```
         12V_FUSED
             │
       ┌─────┴─────┐
       │ Toggle SW │ (#19)
       │   SPST    │
       └─────┬─────┘
             │
             ├───────[1kΩ]─────●──── LED (#20) ───── GND
             │                 │
             ▼                 │
        12V_SWITCHED ─────────┘
             │
        (To Relay Coil)
```

---

## 5. Stripboard Layout

> [!NOTE]
> Copper strips run **vertically (Columns)**.
> Coordinates: **Horizontal = Row (A, B, C...)**, **Vertical = Column (1, 2, 3...)** — Like a chessboard.
> Designed **without track cuts**.

> [!WARNING]
> **Leakage Current Management** (Gemini Feedback)
> - For IN0/IN1 strips (Col 5, 6), ensure separation from others or **physically scrape** the holes between them to maximize insulation.
> - **nA level leakage** causes errors in mV measurements.
> - **Flux Cleaning Essential!** Use IPA after soldering.

---

### 5.1 Node Definition - Stripboard #1 (ADC/3.3V)

| Col | Node Name | Usage |
|:-:|-----------|-------|
| 1 | AGND | ⚫ Analog Ground (Star Point) |
| 2 | 3V3_DIG | 🔴 Arduino 3V3 Input |
| 3 | 3V3_A | 🟠 ADC 3.3V (Filtered) |
| 4 | - | Gap |
| 5 | IN0 | 🔵 V+ Sense (ADS1220 AIN0) |
| 6 | IN1 | 🟢 V- Sense (ADS1220 AIN1) |
| 7 | - | Gap |
| 8 | V+_RAW | 🔵 Panel V+ Input |
| 9 | V-_RAW | 🟢 Panel V- Input |
| 10 | - | Gap |
| 11 | LM_V+ | 🟠 LM334 V+ Input |
| 12 | LM_R | 🟣 LM334 R Pin |
| 13 | LM_OUT | 🟡 LM334 V- Output |
| 14 | - | Gap |
| 15 | SHUNT_LO | 🟡 Shunt Low → Relay |

---

### 5.2 Stripboard #1: ADC/Power/Protection/Current

#### 5.2.1 Left Zone (Col 1~7: Power/ADC/Protection)

```
         ║  1    │  2    │  3    │  4   │  5    │  6    │  7   ║
         ║ AGND  │3V3_DIG│3V3_A  │  -   │ IN0   │ IN1   │  -   ║
═════════╬═══════╪═══════╪═══════╪══════╪═══════╪═══════╪══════║
    A    ║ GND★  │ 3V3   │       │      │       │       │      ║
         ║       │ ←Ard  │       │      │       │       │      ║
─────────╫───────┼───────┼───────┼──────┼───────┼───────┼──────║
    B    ║       │       │       │      │       │       │      ║
─────────╫───────┼───────┼───────┼──────┼───────┼───────┼──────║
    C    ║       │ 10Ω───────→   │      │       │       │      ║
─────────╫───────┼───────┼───────┼──────┼───────┼───────┼──────║
    D    ║       │       │       │      │       │       │      ║
─────────╫───────┼───────┼───────┼──────┼───────┼───────┼──────║
    E    ║ 0.1µF─────→   │       │      │       │       │      ║
─────────╫───────┼───────┼───────┼──────┼───────┼───────┼──────║
    F    ║ 1µF───────→   │       │      │       │       │      ║
─────────╫───────┼───────┼───────┼──────┼───────┼───────┼──────║
    G    ║       │       │       │      │       │       │      ║
─────────╫───────┼───────┼───────┼──────┼───────┼───────┼──────║
    H    ║       │       │       │      │ AIN0  │ AIN1  │      ║
         ║       │       │       │      │ ADS   │ ADS   │      ║
─────────╫───────┼───────┼───────┼──────┼───────┼───────┼──────║
    I    ║ ADS   │       │ ADS   │      │       │       │      ║
         ║ VSS   │       │ VDD   │      │       │       │      ║
─────────╫───────┼───────┼───────┼──────┼───────┼───────┼──────║
    J    ║BAT54A │       │BAT54C │      │BAT54A │BAT54A │      ║
         ║  p3   │       │  p3   │      │  p1   │  p2   │      ║
─────────╫───────┼───────┼───────┼──────┼───────┼───────┼──────║
    K    ║       │       │       │      │BAT54C │BAT54C │      ║
         ║       │       │       │      │  p1   │  p2   │      ║
═════════╩═══════╧═══════╧═══════╧══════╧═══════╧═══════╧══════╝
```

#### 5.2.2 Right Zone (Col 8~15: Sense/Current)

> [!TIP]
> **Variable Current Tip (1mA ↔ 100µA)**: Instead of soldering the resistor directly at `Rset` (LM_R ↔ LM_OUT), solder a **1x2 Female Header (#24 cut)**. You can then swap the resistor to measure high-resistance samples like PEDOT:PSS.

```
         ║  8    │  9    │ 10   │ 11   │ 12   │ 13   │ 14  │ 15   ║
         ║ V+_RAW│ V-_RAW│  -   │LM_V+ │LM_R  │LM_OUT│  -  │SH_LO ║
═════════╬═══════╪═══════╪══════╪══════╪══════╪══════╪═════╪══════║
    A    ║ 🔵V+  │ 🟢V-  │      │ ←Jmp │      │      │     │      ║
         ║ Post  │ Post  │      │(A3→) │      │      │     │      ║
─────────╫───────┼───────┼──────┼──────┼──────┼──────┼─────┼──────║
    B    ║       │       │      │LM334 │      │      │     │      ║
         ║       │       │      │ V+   │      │      │     │      ║
─────────╫───────┼───────┼──────┼──────┼──────┼──────┼─────┼──────║
    C    ║       │       │      │      │LM334 │      │     │      ║
         ║       │       │      │      │  R   │      │     │      ║
─────────╫───────┼───────┼──────┼──────┼──────┼──────┼─────┼──────║
    D    ║       │       │      │      │      │LM334 │     │      ║
         ║       │       │      │      │      │ V-   │     │      ║
─────────╫───────┼───────┼──────┼──────┼──────┼──────┼─────┼──────║
    E    ║       │       │      │      │Rset──────→  │     │      ║
─────────╫───────┼───────┼──────┼──────┼──────┼──────┼─────┼──────║
    F    ║ 1kΩ───────→   │      │      │      │      │     │      ║
         ║(→IN0) │       │      │      │      │      │     │      ║
─────────╫───────┼───────┼──────┼──────┼──────┼──────┼─────┼──────║
    G    ║       │ 1kΩ───────→  │      │      │      │     │      ║
         ║       │(→IN1) │      │      │      │      │     │      ║
─────────╫───────┼───────┼──────┼──────┼──────┼──────┼─────┼──────║
    H    ║       │       │      │      │      │100Ω──────→       ║
─────────╫───────┼───────┼──────┼──────┼──────┼──────┼─────┼──────║
    I    ║       │       │      │      │      │      │     │→DPDT ║
         ║       │       │      │      │      │      │     │COM_A ║
─────────╫───────┼───────┼──────┼──────┼──────┼──────┼─────┼──────║
    J    ║       │       │      │      │      │      │     │      ║
─────────╫───────┼───────┼──────┼──────┼──────┼──────┼─────┼──────║
    K    ║       │       │      │      │      │      │     │      ║
═════════╩═══════╧═══════╧══════╧══════╧══════╧══════╧═════╧══════╝
```

**Component Wiring Summary** (See BOM):

| BOM# | Part | Loc | Connection |
|:-:|------|------|------------|
| #39 | 10Ω Resistor | C2 → C3 | 3V3_DIG → 3V3_A (Filter) |
| #41 | 0.1µF Ceramic ⭐Essential | E1 ↔ E3 | AGND ↔ 3V3_A (High-freq Decap) |
| #40 | 1µF Ceramic ⭐Essential | F1 ↔ F3 | AGND ↔ 3V3_A (Mid-freq Decap) |
| #21 | 10µF Electrolytic 🟡Opt | (Add near I3) | 3V3_A Bulk (Optional) |
| #14 | 1kΩ (V+) | F8 → F5 | V+_RAW → IN0 (Protection) |
| #14 | 1kΩ (V-) | G9 → G6 | V-_RAW → IN1 (Protection) |
| #11 | BAT54A | J1(p3), J5(p1), J6(p2) | GND Clamp (+#13 Adapter) |
| #12 | BAT54C | J3(p3), K5(p1), K6(p2) | 3V3 Clamp (+#13 Adapter) |
| #2 | ADS1220 | I1(VSS), I3(VDD), H5(AIN0), H6(AIN1) | ADC |
| #3 | LM334 | B11(V+), C12(R), D13(V-) | Current Source |
| #4/#5 | Rset | E12 → E13 | 68.1Ω(1mA) or 681Ω(100µA) |
| #6 | 100Ω Shunt | H13 → H15 | Current Monitor |
| #46 | Jumper Wire | A3 → A11 | 3V3_A → LM_V+ |

---

### 5.3 Stripboard #2: Relay/12V

```
         ║  1   │  2   │  3   │  4   │  5   │  6   │  7   │  8   │  9   │ 10  ║
         ║ GND  │ 12V+ │ COIL │  -   │ COM  │  NC  │  NO  │  -   │  I+  │ I-  ║
═════════╬══════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╪══════╪═════║
    A    ║ GND★ │ 12V  │      │      │ ←SH  │      │      │      │ 🔴I+ │ ⚫I-║
         ║      │  IN  │      │      │      │      │      │      │ Post │Post ║
─────────╫──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼─────║
    B    ║      │      │ RLY+ │      │      │→wire────────────────→     │     ║
         ║      │      │      │      │      │      │      │      │      │     ║
─────────╫──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼─────║
    C    ║      │      │      │      │      │      │→wire─────────────→     ║
         ║      │      │      │      │      │      │      │      │      │     ║
─────────╫──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼─────║
    D    ║470µF─────→  │      │      │      │      │      │      │      │     ║
         ║  -   │  +   │      │      │      │      │      │      │      │     ║
─────────╫──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼─────║
    E    ║0.1µF─────→  │      │      │      │      │      │      │      │     ║
         ║      │      │      │      │      │      │      │      │      │     ║
─────────╫──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼─────║
    F    ║PN E  │      │PN C  │      │      │      │      │      │      │     ║
         ║      │      │      │      │      │      │      │      │      │     ║
─────────╫──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼─────║
    G    ║      │ 1kΩ  │      │      │      │      │      │      │      │     ║
         ║      │  ↓   │      │      │      │      │      │      │      │     ║
─────────╫──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼─────║
    H    ║      │ GPIO │      │      │      │      │      │      │      │     ║
         ║      │ ←Ard │      │      │      │      │      │      │      │     ║
─────────╫──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼─────║
    I    ║      │PN B  │      │      │      │      │      │      │      │     ║
         ║      │ 1kΩ↑ │      │      │      │      │      │      │      │     ║
─────────╫──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼─────║
    J    ║1N4148│      │1N4148│      │      │      │      │      │      │     ║
         ║ cath │      │ anod │      │      │      │      │      │      │     ║
─────────╫──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼─────║
    K    ║      │→12V  │ RLY- │      │      │      │      │      │      │     ║
         ║      │      │      │      │      │      │      │      │      │     ║
═════════╩══════╧══════╧══════╧══════╧══════╧══════╧══════╧══════╧══════╧═════╝
```

**Component Wiring Summary**:

| BOM# | Part | Loc | Connection |
|:-:|------|------|------------|
| #33 | DC Barrel Jack | (Ext) | 12V Input (To PCB or Panel) |
| #34+#35 | Inline Fuse + 5A | (Ext) | 12V Input Protection |
| #37 | SMBJ15A TVS | D1-D2 | 12V Spike Absorption |
| #38 | 470µF Electrolytic | D1(-) ↔ D2(+) | 12V Bulk Decap |
| #41 | 0.1µF Ceramic | E1 ↔ E2 | 12V Spike Absorption |
| #8 | PN2222A | F1(E), F3(C), I2(B) | Relay Switch |
| #10 | 1kΩ Base | G2 → I2 | GPIO → Base |
| #48 | 10kΩ Pulldown | I2(Base) → I1(GND) | Prevention (Step 6) |
| #1 | Arduino GPIO | H2 | Relay Control (Use D7) |
| #9 | 1N4148 | J1(cath) ↔ J3(anode) | Flyback Diode |
| #7 | DPDT Relay | B3(+), K3(-), A5(COM), B6(NC), C7(NO) | TQ2-12V |
| #26 | I+ Post (Red) | A9 | 🔴 Current Output |
| #25 | I- Post (Black) | A10 | ⚫ Current Return |
| #19 | Toggle Switch (Opt) | (Panel) | 12V ON/OFF |
| #20 | Power LED (Opt) | (Panel) | Power Ind, 1kΩ Series |

### 5.3.1 Off-board Wiring

> [!TIP]
> **Toggle Switch, Fuse, Barrel Jack** are connected via **Air Wiring** or Panel Wiring, sending only final **12V wires** to the board.

```
[DC Adapter]
    ║
    ▼
[DC Barrel Jack]
   (+) Pin ─────── [Fuse Holder] ─────── [Toggle Switch] ───────┐
    │                                               │
    │                                         (12V_SWITCHED)
    │                                               │
    │                 ┌── [1kΩ] ── (+) [LED] ───────┤ (Option)
    │                 │                             │
   (-) Pin ───┬────────┴──────── (-) [LED] ──────────┼───→ Stripboard #2 [A2: 12V+]
             │                                      │
             └──────────────────────────────────────┴───→ Stripboard #2 [A1: GND]
```

---

### 5.4 Board-to-Board Connections

```
┌───────────────────────────┐              ┌───────────────────────┐
│     Stripboard #1          │              │    Stripboard #2       │
│   (ADC/3.3V Zone)          │              │   (Relay/12V Zone)     │
│                           │              │                       │
│  I15 (SHUNT_LO) ───────wire──────────────→ A5 (COM)             │
│                           │              │                       │
│  A1 (AGND) ─────────Star Point───────────→ A1 (GND)             │
│               (From Arduino GND)          │                       │
│                           │              │                       │
│  A8 (V+_RAW) ←──────────── Panel 🔵 V+ Post                      │
│  A9 (V-_RAW) ←──────────── Panel 🟢 V- Post                      │
│                           │              │                       │
└───────────────────────────┘              │  A9 ←── 🔴 I+ Post   │
                                           │  A10 ←── ⚫ I- Post   │
           Keep 5cm Distance                └───────────────────────┘
```

---

### 5.5 Track Cuts

> [!TIP]
> **No Track Cuts Needed (If Mounted Vertically)**
> Each node is assigned a unique column (1~15). If modules are mounted **vertically**, no cuts are required.

> [!CAUTION]
> **Check Module Orientation**
> - If you must mount horizontally:
>   1. **Cut tracks** under the module pins (between pins).
>   2. **Test Continuity** between adjacent pins.

---

### 5.6 Physical Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Metal Case (EMI Shielding)                       │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                                                                   │  │
│  │   ┌──────────────────┐    5cm+    ┌──────────────────┐           │  │
│  │   │  Stripboard #1     │ ◀───────▶ │  Stripboard #2     │           │  │
│  │   │  (ADC/3.3V)       │           │  (Relay/12V)      │           │  │
│  │   │  ┌────────────┐   │           │  ┌────────────┐   │           │  │
│  │   │  │  Arduino   │   │           │  │DPDT Relay  │   │           │  │
│  │   │  └────────────┘   │           │  └────────────┘   │           │  │
│  │   │  ┌────────────┐   │           │                   │           │  │
│  │   │  │  ADS1220   │   │           │                   │           │  │
│  │   │  └────────────┘   │           │                   │           │  │
│  │   └──────────────────┘           └──────────────────┘           │  │
│  │                                                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                       Panel (Posts)                              │    │
│  │      🔴 I+      🔵 V+      🟢 V-      ⚫ I-                     │    │
│  │     (Red)     (Blue)    (Green)   (Black)                      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Case → AGND Connection (One Point Only)                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Assembly Sequence (Bring-up)

> [!TIP]
> **Core Principle**: Test in small increments → Easier debugging.

### Step 1: Labeling & Prep

- [ ] Label Panel Posts **I+, V+, V-, I-**
- [ ] Mark Test Points on Stripboard
- [ ] Solder BAT54A/C to Adapter (Check Pinout)

**BAT54A/C Pinout**:
```
SOT-23 Package
      ┌───┐
   1 ─┤   ├─ 3
      │   │
   2 ─┤   ├
      └───┘

BAT54A: pin1=Cathode1, pin2=Cathode2, pin3=Common Anode
BAT54C: pin1=Anode1, pin2=Anode2, pin3=Common Cathode

⚠️ Verify with Datasheet!
```

### Step 2: Power Filter Assembly

Assembly (Layout 5.2.1):
- [ ] 10Ω Resistor: Col 2(3V3_DIG) ↔ Col 3(3V3_A) (Row C)
- [ ] 0.1µF: Col 1(AGND) ↔ Col 3(3V3_A) (Row E)
- [ ] 1µF: Col 1(AGND) ↔ Col 3(3V3_A) (Row F)
- [ ] Arduino 3V3 → Col 2(3V3_DIG), Arduino GND → Col 1(AGND)

**Verify**:
```
1. Connect Arduino USB
2. Measure:
   - B1 (3V3_DIG): 3.3V ± 0.1V ✓
   - C3 (3V3_A): 3.3V ± 0.1V ✓
```

### Step 3: ADS1220 SPI Check

Connection:
- [ ] ADS1220 VDD/AVDD → Col 3 (3V3_A)
- [ ] ADS1220 GND/AVSS → Col 1 (AGND)
- [ ] SPI: SCK, MOSI, MISO, CS, DRDY → Arduino Pins

**Verification Code**: (Same as Step 3 in KR guide, use `Config Reg 0: 0x00` check)

### Step 4: Input Protection

Assembly:
- [ ] 1kΩ: Col 8(V+_RAW) → Col 5(IN0) (Row F)
- [ ] 1kΩ: Col 9(V-_RAW) → Col 6(IN1) (Row G)
- [ ] BAT54A: pin3→Col 1(AGND), pin1/2→Col 5/6 (IN0/IN1)
- [ ] BAT54C: pin3→Col 3(3V3_A), pin1/2→Col 5/6 (IN0/IN1)
- [ ] ADS1220 AIN0 → Col 5(IN0), AIN1 → Col 6(IN1)

**Verify**:
```
1. Short V+ & V- Posts → Read ~0V
2. Apply 3.3V via 1kΩ → IN0 ~3.3V (Safe)
3. Apply GND via 1kΩ → IN0 ~0V
```

### Step 5: Current Source (Dummy Load Test)

Assembly:
- [ ] LM334: V+ → Col 3(3V3_A), R → Col 12, V- → Col 13
- [ ] Rset: Col 12(LM_R) ↔ Col 13(LM_OUT)
  - **Recommended**: Use **1x2 Female Header** socket (Easy swap for 100µA)
- [ ] 100Ω Shunt: Col 13(LM_OUT) ↔ Col 15(SHUNT_LO)
  > [!WARNING]
  > Don't confuse **100Ω** (Brown-Black-Black-Black-Brown) with 10Ω!
- [ ] Connect Dummy Load (1kΩ)

**Verify**:
```
Expected I = 67.7mV / 681Ω ≈ 99.4µA
Shunt V = I × 100Ω ≈ 9.94mV
Dummy V ≈ 0.1V
```

> [!NOTE]
> **Headroom Check**:
> - @100µA: 2.29V margin
> - @1mA: 2.20V margin

### Step 6: Relay Driver (12V)

Assembly:
- [ ] Relay Coil → 12V / PN2222A Collector
- [ ] 1N4148 Flyback
- [ ] PN2222A Base → 1kΩ → GPIO
- [ ] (Rec.) PN2222A Base → 10kΩ → GND (Pulldown)
- [ ] PN2222A Emitter → 12V GND
- [ ] 470µF & 0.1µF Caps

**Verify**:
- Relay Click Sound test.
- Check for ADC spikes during switching.

### Step 7: Final Connect

- [ ] **Start with 1mA** (ITO Standard)
  - Default: 68.1Ω in socket
- [ ] **For High Resistance (PEDOT:PSS)**:
  - Swap to 681Ω (100µA)
  - Update `CURRENT_SETTING` in code

---

## 7. Software Implementation

### 7.1 ADS1220 Settings

```cpp
// ADS1220 Config
// Config0: MUX=AIN0/AIN1, GAIN=1 (PGA Bypass)
byte config0 = 0b00000001; 

// Config1: DR=20SPS, Continuous, Normal Mode
byte config1 = 0b00000100;

// Config2: VREF=Internal 2.048V, 50/60Hz Rej
byte config2 = 0b00010000;

// Config3: Default
byte config3 = 0b00000000;
```

### 7.2 Current Reversal Routine (Delta Mode)

```cpp
#include <SPI.h>

#define CS_PIN 10
#define DRDY_PIN 9
#define RELAY_PIN 2
#define SHUNT_R 100.0  // Ohms

// ... ADS1220 functions ...

float readVoltage(byte mux) {
  // Update MUX (Config0)
  byte cfg0 = (config0 & 0x1F) | mux; 
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(0x40); // WREG
  SPI.transfer(cfg0);
  digitalWrite(CS_PIN, HIGH);
  
  // START/SYNC
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(0x08);
  digitalWrite(CS_PIN, HIGH);
  
  // DRDY Wait (Timeout Protected)
  unsigned long start = millis();
  while (digitalRead(DRDY_PIN) == HIGH) {
    if (millis() - start > 100) { 
       Serial.println("Error: DRDY Timeout!");
       return 0.0;
    }
  }
  
  // Read Data
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(0x10); // RDATA
  long raw = 0;
  raw |= (long)SPI.transfer(0x00) << 16;
  raw |= (long)SPI.transfer(0x00) << 8;
  raw |= (long)SPI.transfer(0x00);
  digitalWrite(CS_PIN, HIGH);
  
  // Sign extension
  if (raw & 0x800000) raw |= 0xFF000000;
  
  // Convert to Voltage (VREF 2.048V)
  return (float)raw * 2.048 / 8388608.0;
}

struct Measurement {
  float V_corrected;
  float I_actual;
  float R_sample;
  float Rs;
};

Measurement measureWithReversal() {
  Measurement m;
  
  // 1. Forward
  digitalWrite(RELAY_PIN, LOW);
  delay(500);
  
  float V_fwd = readVoltage(0x00);
  float V_shunt_fwd = readVoltage(0x30);
  
  // 2. Reverse
  digitalWrite(RELAY_PIN, HIGH);
  delay(500);
  
  float V_rev = readVoltage(0x00);
  float V_shunt_rev = readVoltage(0x30);
  
  // 3. Calculation
  m.V_corrected = (V_fwd - V_rev) / 2.0;
  
  float I_fwd = V_shunt_fwd / SHUNT_R;
  float I_rev = abs(V_shunt_rev) / SHUNT_R;
  m.I_actual = (I_fwd + I_rev) / 2.0;
  
  m.R_sample = m.V_corrected / m.I_actual;
  
  // Correction Factor (Geom Factor)
  // For 1-inch Sample, Center Measurement (NBS Standard)
  // F = 4.47044 (CF ≈ 0.986)
  float F_GEOM = 4.47044;  
  
  m.Rs = F_GEOM * m.R_sample;
  
  // Reset Relay
  digitalWrite(RELAY_PIN, LOW);
  
  return m;
}
```

### 7.3 Ohmic Contact Verification

(Same logic as KR version: measure at multiple currents if possible, check linearity)

### 7.4 Serial Output

(Same format as KR version)

---

## 8. Verification & Debugging

### 8.1 Checkpoints

| Step | Item | Expected | Pass Criteria |
|------|------|----------|---------------|
| 2 | 3V3_A | 3.3V | ±0.1V |
| 3 | ADS1220 Reg0 | 0x00 | Exact |
| 4 | Input Short | 0V | ±50µV |
| 5 | Shunt V (100µA) | ~10mV | ±2mV |
| 5 | Shunt V (1mA) | ~100mV | ±10mV |
| 6 | Relay | Click Sound | Audible |
| 7 | ITO Measure | 10~100 Ω/□ | Repeatable ±5% |

### 8.2 Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| Unstable voltage | Decoupling/GND Loop | Add 0.1µF, Check Star GND |
| Wrong Current | Rset/LM334 bad | Check Rset, Swap LM334 |
| V sense near Rail | Clamp active | Check contact, Reduce current |
| Non-ohmic behavior | Probe contact | Increase pressure, Clean tips |
| Drift | Temp/EMF | Use Reversal Mode |
| Relay Noise | 12V/3.3V Coupling | Separate Zones, Add Caps |

---

## 9. Formulas & Correction

### 9.1 Basic

```
Rs = (π / ln2) × R_sample = 4.532 × R_sample
```

### 9.2 Current Reversal (Delta Mode)

```
V_corr = (V_fwd - V_rev) / 2
```
Removes Offset and Thermal EMF.

### 9.3 Correction Factor (CF)

> [!WARNING]
> 4.532 is valid only for infinite sheets (Sample > 40x Probe Spacing).

**NBS/NIST TN 199 Standard (Circular, Center)**:
- 1-inch Sample / 40mil Probe (d/s ≈ 25)
- **F = 4.47044** (CF ≈ 0.986)
- This guide uses this fixed value.

> [!NOTE]
> Use this F value for 1-inch square samples as a first approximation.

---

## 10. Checklist

### 10.1 Components
- [ ] Arduino Blink Check
- [ ] ADS1220 Header Soldered
- [ ] BAT54 Solder Check
- [ ] Resistor Values Checked

### 10.2 Assembly
- [ ] Step 2 Power OK
- [ ] Step 3 SPI OK
- [ ] Step 4 Input Short OK
- [ ] Step 5 Shunt V OK
- [ ] Step 6 Relay OK

### 10.3 Final
- [ ] Resistor Measure Check
- [ ] ITO Sample Check
- [ ] Reversal Mode Check

### 10.4 EMI (Recommended)
- [ ] Metal Case
- [ ] Shield Grounded at ADC side only

### 10.5 Flux Cleaning (Essential!)
- [ ] Clean with IPA + Brush
- [ ] Dry completely

---

## 📚 References
- ADS1220 Datasheet
- LM334 Datasheet
- NBS Technical Note 199
- Smits 1958

---

> **Next Step**: Upload the code in [Section 7](#7-software-implementation) and build!
