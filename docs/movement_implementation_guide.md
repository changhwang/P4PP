# Movement Implementation Guide (P4PP System)

This document is a comprehensive guide covering the **final hardware wiring, mechanical considerations, tuning settings, and firmware logic** for implementing the motor control (sample rotation, linear movement) in the P4PP system.

> [!NOTE]
> **Mechanical Design Precautions**
> This guide focuses on the **electronic circuit control, wiring, and firmware** between the Arduino and the motor drivers. The **mechanical design**—such as the brackets for mounting the motors, the Z-axis carriage for lowering the 4-Point Probe vertically, and the rotational stage for placing the sample—must be **custom-made according to the user's specific setup environment**.

---

## 1. Hardware Setup & Wiring

### 1-1. Core Components
*   **Motors**: StepperOnline 17HS08-1004S (NEMA 17, 1.0A/Phase, 1.8°/step) x 2
*   **Motor Drivers**: Adafruit TMC2209 Breakout Board (#33) x 2
*   **Power Protection (Mandatory)**: 470µF (or 100µF+) electrolytic capacitor x 2
*   **Limit Switches**: Micro switch (NO, C terminals used) x 2

### 1-2. Pin Assignments (Arduino Nano 33 IoT)
This is the final confirmed mapping, resolving all pin conflicts.

| Module | Signal | Arduino Pin | Notes |
| :--- | :--- | :--- | :--- |
| **Rotation** | `STEP` | **D3** | |
| | `DIR` | **D4** | |
| | `ENABLE` | **A1** | Active LOW, cuts power (standby) when HIGH |
| | `Limit SW` | **D8** | Uses internal pullup (`INPUT_PULLUP`). Switch connects to GND. |
| **Linear** | `STEP` | **D5** | |
| | `DIR` | **D6** | |
| | `ENABLE` | **A0** | Active LOW, cuts power (standby) when HIGH |
| | `Limit SW` | **D7** | Uses internal pullup (`INPUT_PULLUP`). Switch connects to GND. |

### 1-3. Motor Driver (Board D) Wiring Guide
The Adafruit TMC2209 driver features terminal blocks for the high-voltage side (12V and motor coils), while only the logic pins (3.3V) are plugged into the breadboard.

1. **Power Distribution (Star Topology)**: To minimize electromagnetic noise, distribute power in a parallel (Star) configuration rather than series. Split the 12V adapter power using WAGO connectors and wire them directly to each terminal block (VM, GND). The Arduino 3.3V/GND should also be distributed to the VDD/GND pins.
   - ⚠️ **[CRITICAL] Decoupling Capacitor Installation**: To prevent the driver from immediately burning out due to voltage spikes when power is applied, a **470µF electrolytic capacitor** must be connected in parallel to the 12V terminals (VMOT and GND). (Overlap the wire insulation and the capacitor legs, and screw them down tightly together. **Mind the polarity!**)
2. **Common Ground**: All 12V GNDs from the boards and the 3.3V/Arduino GND must meet at a single point (e.g., Board C) to form a common ground. The C terminal of the limit switches also ties into this ground network.
3. **Motor Coil Wiring (Linear Direction Patch)**: To prevent software calculation conflicts, the **1A and 1B wires of the Linear motor terminal have been physically crossed/swapped** (exchanged positions of the black and green wires). This ensures both motors share the same DIR logic (HIGH = Forward/Depart, LOW = Reverse/Homing).

---

## 2. Driver Tuning (Vref & Current Adjustment)

To prevent stuttering and overheating, the output current of the TMC2209 must be tuned.
*   **Motor Specs (I_max)**: 1.0A 
*   **Recommended Operating Current**: 70~80% of max
*   **Target Tuning Voltage (Vref)**: **0.75V ~ 0.8V** 
    *(Use a multimeter to measure the voltage between the driver board's metal potentiometer screw (+) and the GND terminal while making fine adjustments.)*

---

## 3. Firmware Homing Logic

To fundamentally prevent internal directional conflict errors in the `AccelStepper` engine, the homing function was implemented using low-level, direct hardware control.

### 3-1. Manual Step Function
Pulses are sent directly using `delayMicroseconds()`.
```cpp
void manualStep(int stepPin, unsigned int stepDelayUs) {
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(2);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(stepDelayUs);
}
```

### 3-2. 2-Pass Homing Sequence
1. **Safety Retreat (Optional)**: If the switch is already depressed when the command is sent, the motor moves in `RETREAT_DIR (HIGH)` to clear the switch and create an additional safety margin.
2. **1st Fast Approach**: Approaches rapidly (800us pulse interval) in the `HOMING_DIR (LOW)` direction until the switch is triggered.
3. **1st Retreat**: Bounces back upon collision by stopping and retreating a set number of steps (Linear: 800, Rotation: 200) in the `RETREAT_DIR (HIGH)` direction.
4. **2nd Precision Approach**: Approaches slowly (4000us pulse interval) back in the `HOMING_DIR (LOW)` direction. Upon triggering, it immediately sets this as the target.
5. **Safety Margin & Zero Point Setting**: Retreats slightly (50 steps) in the `RETREAT_DIR` to fully clear the switch lever, and then firmly establishes that position as `setCurrentPosition(0)`.

### 3-3. Non-blocking Serial
The current firmware employs an asynchronous architecture that reads one character at a time from `Serial.read()` into an array buffer during each loop iteration. This structure does not interfere with the motor pulse intervals, perfectly guaranteeing noiseless StealthChop operation.
