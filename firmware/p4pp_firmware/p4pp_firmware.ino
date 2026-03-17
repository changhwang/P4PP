#include <AccelStepper.h>
#include <SPI.h>

// -----------------------------------------------------------------------------
// Pin Definitions (Arduino Nano 33 IoT)
// -----------------------------------------------------------------------------
// ADS1220 SPI
const int ADS1220_CS_PIN = 10;
const int ADS1220_DRDY_PIN = 9;

// Relay Control
const int RELAY_PIN = 2; // Digital pin to control the DPDT relay (PN2222A base)

// Stepper Motor & Limit Switch
const int ROT_STEP_PIN = 3;
const int ROT_DIR_PIN = 4;
const int LIN_STEP_PIN = 5;
const int LIN_DIR_PIN = 6;
const int LIMIT_SW_LIN_PIN = 7;
const int LIMIT_SW_ROT_PIN = 8;
const int ROT_EN_PIN = A1; // Pull LOW to enable Rotation Driver
const int LIN_EN_PIN = A0; // Pull LOW to enable Linear Driver

AccelStepper rotMotor(AccelStepper::DRIVER, ROT_STEP_PIN, ROT_DIR_PIN);
AccelStepper linMotor(AccelStepper::DRIVER, LIN_STEP_PIN, LIN_DIR_PIN);

// Movement Debugging (set true only when debugging)
const bool DEBUG_MOVEMENT = false;

// -----------------------------------------------------------------------------
// Constants & Settings
// -----------------------------------------------------------------------------
// ADS1220 Commands
const uint8_t RESET_CMD = 0x06;
const uint8_t START_CMD = 0x08;
const uint8_t WREG_CMD = 0x40;
const uint8_t RREG_CMD = 0x20;
const uint8_t RDATA_CMD = 0x10;

// Relay States
const bool RELAY_FORWARD = LOW;
const bool RELAY_REVERSE = HIGH;

// Measurement Settings
const int SETTLING_TIME_MS =
    100; // Wait time after switching relay before taking a reading
const float MIN_VALID_CURRENT_MA = 0.005f; // Supports 681-ohm (~100 uA) mode
const long HOMING_MAX_STEPS = 30000;
const int LIN_HOME_CLEAR_STEPS = 800;         // After first switch hit
const int LIN_HOME_FINAL_BACKOFF_STEPS = 250; // After second switch hit
const int ROT_HOME_CLEAR_STEPS = 200;         // After first switch hit
const int ROT_HOME_FINAL_BACKOFF_STEPS = 70;  // After second switch hit
// Motion conversion baseline (17HS08-1004S + TMC2209 default 1/8 microstep)
const float ROT_STEPS_PER_DEG = 4.444444f; // 400 steps ~= 90 deg
const float LIN_STEPS_PER_MM = 200.0f;     // 8 mm lead, 4-start screw

// ADS1220 MUX/Gain settings used in measurement
const uint8_t ADS_MUX_CURRENT = 0x50;
const uint8_t ADS_MUX_VOLTAGE = 0x00;
const uint8_t ADS_GAIN_CURRENT = 0;
const uint8_t ADS_GAIN_VOLTAGE = 2;

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {
  } // Wait up to 3 seconds for Serial

  // Initialize Pins
  pinMode(ADS1220_CS_PIN, OUTPUT);
  digitalWrite(ADS1220_CS_PIN, HIGH);
  pinMode(ADS1220_DRDY_PIN, INPUT_PULLUP);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_FORWARD); // Start in Forward direction

  pinMode(LIMIT_SW_LIN_PIN, INPUT_PULLUP);
  pinMode(LIMIT_SW_ROT_PIN, INPUT_PULLUP);

  pinMode(ROT_EN_PIN, OUTPUT);
  digitalWrite(ROT_EN_PIN, LOW); // Enable rot driver by default
  pinMode(LIN_EN_PIN, OUTPUT);
  digitalWrite(LIN_EN_PIN, LOW); // Enable lin driver by default

  // Stepper Initialization
  rotMotor.setMaxSpeed(1000.0);
  rotMotor.setAcceleration(500.0);

  linMotor.setMaxSpeed(1000.0);
  linMotor.setAcceleration(500.0);

  // Initialize SPI
  SPI.begin();

  Serial.println(F("\n--- P4PP Firmware Starting ---"));

  // Initialize ADS1220
  resetADS1220();
  delay(10);

  // Configure Registers for P4PP operation
  configADS1220();

  Serial.println(F("System Ready."));
}

void setMuxAndGain(uint8_t mux, uint8_t gain, bool bypass_pga) {
  uint8_t reg0_val = mux | (gain << 1) | (bypass_pga ? 0x01 : 0x00);
  writeRegister(0x00, reg0_val);
  delay(5); // Allow internal MUX to settle
}

void dbgPrint(const __FlashStringHelper *label, int value) {
  if (!DEBUG_MOVEMENT)
    return;
  Serial.print(label);
  Serial.println(value);
}

bool parseOneInt(const String &cmd, int &a) {
  int firstSpace = cmd.indexOf(' ');
  if (firstSpace < 0)
    return false;
  a = cmd.substring(firstSpace + 1).toInt();
  return true;
}

bool parseTwoInts(const String &cmd, int &a, int &b) {
  int firstSpace = cmd.indexOf(' ');
  if (firstSpace < 0)
    return false;
  int secondSpace = cmd.indexOf(' ', firstSpace + 1);
  if (secondSpace < 0)
    return false;
  a = cmd.substring(firstSpace + 1, secondSpace).toInt();
  b = cmd.substring(secondSpace + 1).toInt();
  return true;
}

int getSampleCount(const String &cmd, int defaultCount) {
  int value = defaultCount;
  int firstSpace = cmd.indexOf(' ');
  if (firstSpace >= 0) {
    value = cmd.substring(firstSpace + 1).toInt();
  }
  if (value < 1)
    value = 1;
  if (value > 1000)
    value = 1000;
  return value;
}

void setDriverEnable(int enPin, bool enable) {
  // enable=true -> LOW, enable=false -> HIGH
  digitalWrite(enPin, enable ? LOW : HIGH);
}

void parseCommand(String cmd) {
  if (cmd.equals("MEASURE")) {
    executeMeasurement();
  } else if (cmd.equals("HOME_LIN")) {
    homeLinearStepper();
  } else if (cmd.equals("HOME_ROT")) {
    homeRotationStepper();
  } else if (cmd.startsWith("MOVE_LIN ")) {
    long target = cmd.substring(9).toInt();
    linMotor.moveTo(target);
    dbgPrint(F("DBG MOVE_LIN DIR pin: "), digitalRead(LIN_DIR_PIN));
    Serial.print(F("OK LIN_TARGET: "));
    Serial.println(target);
  } else if (cmd.startsWith("MOVE_ROT ")) {
    long target = cmd.substring(9).toInt();
    rotMotor.moveTo(target);
    Serial.print(F("OK ROT_TARGET: "));
    Serial.println(target);
  } else if (cmd.equals("DBG_LIMIT")) {
    dbgPrint(F("DBG LIMIT_LIN: "), digitalRead(LIMIT_SW_LIN_PIN));
    dbgPrint(F("DBG LIMIT_ROT: "), digitalRead(LIMIT_SW_ROT_PIN));
  } else if (cmd.equals("DBG_DIR")) {
    dbgPrint(F("DBG DIR_LIN: "), digitalRead(LIN_DIR_PIN));
    dbgPrint(F("DBG DIR_ROT: "), digitalRead(ROT_DIR_PIN));
  } else if (cmd.startsWith("SET_LIN_DIR ")) {
    int val = 0;
    if (!parseOneInt(cmd, val)) {
      Serial.println(F("ERR SET_LIN_DIR needs 0/1"));
      return;
    }
    digitalWrite(LIN_DIR_PIN, val ? HIGH : LOW);
    dbgPrint(F("DBG LIN_DIR set: "), digitalRead(LIN_DIR_PIN));
  } else if (cmd.startsWith("SET_ROT_DIR ")) {
    int val = 0;
    if (!parseOneInt(cmd, val)) {
      Serial.println(F("ERR SET_ROT_DIR needs 0/1"));
      return;
    }
    digitalWrite(ROT_DIR_PIN, val ? HIGH : LOW);
    dbgPrint(F("DBG ROT_DIR set: "), digitalRead(ROT_DIR_PIN));
  } else if (cmd.startsWith("EN_LIN ")) {
    int val = 0;
    if (!parseOneInt(cmd, val)) {
      Serial.println(F("ERR EN_LIN needs 0/1"));
      return;
    }
    setDriverEnable(LIN_EN_PIN, val != 0);
    dbgPrint(F("DBG LIN_EN pin: "), digitalRead(LIN_EN_PIN));
  } else if (cmd.startsWith("EN_ROT ")) {
    int val = 0;
    if (!parseOneInt(cmd, val)) {
      Serial.println(F("ERR EN_ROT needs 0/1"));
      return;
    }
    setDriverEnable(ROT_EN_PIN, val != 0);
    dbgPrint(F("DBG ROT_EN pin: "), digitalRead(ROT_EN_PIN));
  } else if (cmd.startsWith("STEP_LIN ")) {
    int steps = 0;
    int delayUs = 0;
    if (!parseTwoInts(cmd, steps, delayUs)) {
      Serial.println(F("ERR STEP_LIN needs <steps> <delay_us>"));
      return;
    }
    steps = abs(steps);
    for (int i = 0; i < steps; i++) {
      manualStep(LIN_STEP_PIN, (unsigned int)delayUs);
    }
    Serial.print(F("OK STEP_LIN "));
    Serial.println(steps);
  } else if (cmd.startsWith("STEP_ROT ")) {
    int steps = 0;
    int delayUs = 0;
    if (!parseTwoInts(cmd, steps, delayUs)) {
      Serial.println(F("ERR STEP_ROT needs <steps> <delay_us>"));
      return;
    }
    steps = abs(steps);
    for (int i = 0; i < steps; i++) {
      manualStep(ROT_STEP_PIN, (unsigned int)delayUs);
    }
    Serial.print(F("OK STEP_ROT "));
    Serial.println(steps);
  } else if (cmd.equals("ADS_REG_DUMP")) {
    dumpADS1220Registers();
    Serial.println(F("OK ADS_REG_DUMP"));
  } else if (cmd.startsWith("ADC_RAW_CURR")) {
    int n = getSampleCount(cmd, 1);
    setMuxAndGain(ADS_MUX_CURRENT, ADS_GAIN_CURRENT, true);
    for (int i = 0; i < n; i++) {
      int32_t raw = readADC();
      Serial.print(F("RAW_CURR["));
      Serial.print(i);
      Serial.print(F("]: "));
      Serial.println(raw);
    }
    Serial.println(F("OK ADC_RAW_CURR"));
  } else if (cmd.startsWith("ADC_RAW_VOLT")) {
    int n = getSampleCount(cmd, 1);
    setMuxAndGain(ADS_MUX_VOLTAGE, ADS_GAIN_VOLTAGE, true);
    for (int i = 0; i < n; i++) {
      int32_t raw = readADC();
      Serial.print(F("RAW_VOLT["));
      Serial.print(i);
      Serial.print(F("]: "));
      Serial.println(raw);
    }
    Serial.println(F("OK ADC_RAW_VOLT"));
  } else if (cmd.startsWith("ADC_RAW_BOTH")) {
    int n = getSampleCount(cmd, 1);
    for (int i = 0; i < n; i++) {
      setMuxAndGain(ADS_MUX_CURRENT, ADS_GAIN_CURRENT, true);
      int32_t rawCurr = readADC();
      setMuxAndGain(ADS_MUX_VOLTAGE, ADS_GAIN_VOLTAGE, true);
      int32_t rawVolt = readADC();
      Serial.print(F("RAW_BOTH["));
      Serial.print(i);
      Serial.print(F("] I: "));
      Serial.print(rawCurr);
      Serial.print(F(" V: "));
      Serial.println(rawVolt);
    }
    Serial.println(F("OK ADC_RAW_BOTH"));
  } else if (cmd.startsWith("MEASURE_N")) {
    int n = getSampleCount(cmd, 5);
    executeMeasurementMulti(n);
  } else if (cmd.startsWith("MEASURE_DBG")) {
    int n = getSampleCount(cmd, 4);
    executeMeasurementDebug(n);
  } else if (cmd.equals("RELAY_FWD")) {
    digitalWrite(RELAY_PIN, RELAY_FORWARD);
    Serial.println(F("OK RELAY_FWD"));
  } else if (cmd.equals("RELAY_REV")) {
    digitalWrite(RELAY_PIN, RELAY_REVERSE);
    Serial.println(F("OK RELAY_REV"));
  } else if (cmd.equals("GET_POS")) {
    Serial.print(F("POS LIN: "));
    Serial.print(linMotor.currentPosition());
    Serial.print(F(" ROT: "));
    Serial.println(rotMotor.currentPosition());
  } else if (cmd.equals("ZERO")) {
    linMotor.setCurrentPosition(0);
    rotMotor.setCurrentPosition(0);
    Serial.println(F("OK ZEROED"));
  } else if (cmd.equals("STATUS")) {
    Serial.println(F("OK READY"));
  } else {
    Serial.print(F("ERR Unknown command: "));
    Serial.println(cmd);
  }
}

// Helper: pulse the STEP pin manually at a given interval
void manualStep(int stepPin, unsigned int stepDelayUs) {
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(2);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(stepDelayUs);
}

void homeLinearStepper() {
  Serial.println(F("HOMING_LIN_START"));
  dbgPrint(F("DBG LIMIT_LIN initial: "), digitalRead(LIMIT_SW_LIN_PIN));
  dbgPrint(F("DBG LIN_DIR initial: "), digitalRead(LIN_DIR_PIN));

  // Confirmed baseline: LIN DIR=1 is forward, so homing must use DIR=0.
  const int HOMING_DIR = LOW;
  const int RETREAT_DIR = HIGH;
  dbgPrint(F("DBG HOMING_DIR: "), HOMING_DIR);

  // If already pressed, back off first
  if (digitalRead(LIMIT_SW_LIN_PIN) == LOW) {
    digitalWrite(LIN_DIR_PIN, RETREAT_DIR);
    dbgPrint(F("DBG LIN_DIR set RETREAT_DIR: "), RETREAT_DIR);
    while (digitalRead(LIMIT_SW_LIN_PIN) == LOW) {
      manualStep(LIN_STEP_PIN, 1500);
    }
    // Move a bit more to clear the switch
    for (int i = 0; i < 400; i++)
      manualStep(LIN_STEP_PIN, 1500);
  }

  // 1. Move towards switch - FAST
  digitalWrite(LIN_DIR_PIN, HOMING_DIR);
  dbgPrint(F("DBG LIN_DIR set HOMING_DIR: "), HOMING_DIR);
  long seekSteps = 0;
  while (digitalRead(LIMIT_SW_LIN_PIN) == HIGH) {
    if (++seekSteps > HOMING_MAX_STEPS) {
      Serial.println(F("ERR HOME_LIN seek timeout"));
      return;
    }
    manualStep(LIN_STEP_PIN, 800);
  }

  // 2. Back off 800 steps
  digitalWrite(LIN_DIR_PIN, RETREAT_DIR);
  for (int i = 0; i < LIN_HOME_CLEAR_STEPS; i++)
    manualStep(LIN_STEP_PIN, 1500);

  // 3. Approach again SLOWLY for precision
  digitalWrite(LIN_DIR_PIN, HOMING_DIR);
  seekSteps = 0;
  while (digitalRead(LIMIT_SW_LIN_PIN) == HIGH) {
    if (++seekSteps > HOMING_MAX_STEPS) {
      Serial.println(F("ERR HOME_LIN refine timeout"));
      return;
    }
    manualStep(LIN_STEP_PIN, 4000);
  }

  // 4. Back off slightly to safe zero
  digitalWrite(LIN_DIR_PIN, RETREAT_DIR);
  for (int i = 0; i < LIN_HOME_FINAL_BACKOFF_STEPS; i++)
    manualStep(LIN_STEP_PIN, 1500);

  // Reset AccelStepper position to 0
  linMotor.setCurrentPosition(0);
  Serial.println(F("OK HOMING_LIN_COMPLETE"));
}

void homeRotationStepper() {
  Serial.println(F("HOMING_ROT_START"));

  // rotMotor has NO setPinsInverted so:
  //   MOVE_ROT 100 (positive) -> DIR pin goes HIGH physically
  //   So homing (opposite) -> DIR pin goes LOW
  const int HOMING_DIR = LOW;   // Opposite of MOVE_ROT positive
  const int RETREAT_DIR = HIGH; // Same as MOVE_ROT positive

  // If already pressed, back off first
  if (digitalRead(LIMIT_SW_ROT_PIN) == LOW) {
    digitalWrite(ROT_DIR_PIN, RETREAT_DIR);
    while (digitalRead(LIMIT_SW_ROT_PIN) == LOW) {
      manualStep(ROT_STEP_PIN, 1500);
    }
    for (int i = 0; i < 400; i++)
      manualStep(ROT_STEP_PIN, 1500);
  }

  // 1. Move towards switch - FAST
  digitalWrite(ROT_DIR_PIN, HOMING_DIR);
  long seekSteps = 0;
  while (digitalRead(LIMIT_SW_ROT_PIN) == HIGH) {
    if (++seekSteps > HOMING_MAX_STEPS) {
      Serial.println(F("ERR HOME_ROT seek timeout"));
      return;
    }
    manualStep(ROT_STEP_PIN, 800);
  }

  // 2. Back off 200 steps
  digitalWrite(ROT_DIR_PIN, RETREAT_DIR);
  for (int i = 0; i < ROT_HOME_CLEAR_STEPS; i++)
    manualStep(ROT_STEP_PIN, 1500);

  // 3. Approach again SLOWLY for precision
  digitalWrite(ROT_DIR_PIN, HOMING_DIR);
  seekSteps = 0;
  while (digitalRead(LIMIT_SW_ROT_PIN) == HIGH) {
    if (++seekSteps > HOMING_MAX_STEPS) {
      Serial.println(F("ERR HOME_ROT refine timeout"));
      return;
    }
    manualStep(ROT_STEP_PIN, 4000);
  }

  // 4. Back off slightly to safe zero
  digitalWrite(ROT_DIR_PIN, RETREAT_DIR);
  for (int i = 0; i < ROT_HOME_FINAL_BACKOFF_STEPS; i++)
    manualStep(ROT_STEP_PIN, 1500);

  // Reset AccelStepper position to 0
  rotMotor.setCurrentPosition(0);
  Serial.println(F("OK HOMING_ROT_COMPLETE"));
}

void loop() {
  // Stepper drivers must be called continuously
  rotMotor.run();
  linMotor.run();

  // Non-blocking serial command interface
  static String inputString = "";
  while (Serial.available() > 0) {
    char inChar = (char)Serial.read();
    if (inChar == '\n' || inChar == '\r') {
      if (inputString.length() > 0) {
        inputString.trim();
        parseCommand(inputString);
        inputString = ""; // Reset for next command
      }
    } else {
      inputString += inChar;
    }
  }
}

void executeMeasurement() {
  int32_t current_fwd = 0, voltage_fwd = 0;
  int32_t current_rev = 0, voltage_rev = 0;

  digitalWrite(RELAY_PIN, RELAY_FORWARD);
  delay(SETTLING_TIME_MS);

  setMuxAndGain(ADS_MUX_CURRENT, ADS_GAIN_CURRENT, true);
  current_fwd = readADC();

  setMuxAndGain(ADS_MUX_VOLTAGE, ADS_GAIN_VOLTAGE, true);
  voltage_fwd = readADC();

  digitalWrite(RELAY_PIN, RELAY_REVERSE);
  delay(SETTLING_TIME_MS);

  setMuxAndGain(ADS_MUX_CURRENT, ADS_GAIN_CURRENT, true);
  current_rev = readADC();

  setMuxAndGain(ADS_MUX_VOLTAGE, ADS_GAIN_VOLTAGE, true);
  voltage_rev = readADC();

  Serial.println(F("--- Delta Cycle Data ---"));

  float i_fwd_mA = ((current_fwd * 2.048) / 8388608.0) * 1000.0 / 100.0;
  float v_fwd_mV =
      (((voltage_fwd * 2.048) / 8388608.0) / 4.0) * 1000.0; // Gain = 4
  float i_rev_mA = ((current_rev * 2.048) / 8388608.0) * 1000.0 / 100.0;
  float v_rev_mV =
      (((voltage_rev * 2.048) / 8388608.0) / 4.0) * 1000.0; // Gain = 4

  Serial.print(F("I_fwd: "));
  Serial.print(i_fwd_mA, 4);
  Serial.println(F(" mA"));
  Serial.print(F("V_fwd: "));
  Serial.print(v_fwd_mV, 4);
  Serial.println(F(" mV"));
  Serial.print(F("I_rev: "));
  Serial.print(i_rev_mA, 4);
  Serial.println(F(" mA"));
  Serial.print(F("V_rev: "));
  Serial.print(v_rev_mV, 4);
  Serial.println(F(" mV"));

  float delta_v_mV = (v_fwd_mV - v_rev_mV) / 2.0;
  // Relay reversal flips shunt polarity, so average current magnitudes.
  float test_i_mA = (fabs(i_fwd_mA) + fabs(i_rev_mA)) / 2.0;

  Serial.println(F("- - - - - - - - - - - - "));
  Serial.print(F("Delta_V: "));
  Serial.print(delta_v_mV, 4);
  Serial.println(F(" mV"));
  Serial.print(F("Test_I:  "));
  Serial.print(test_i_mA, 4);
  Serial.println(F(" mA"));

  if (fabs(test_i_mA) > MIN_VALID_CURRENT_MA) {
    float r_sheet = 4.532 * (delta_v_mV / test_i_mA);
    Serial.print(F("Raw R_sheet: "));
    Serial.print(r_sheet, 4);
    Serial.println(F(" Ohm/sq"));
  }

  Serial.println(F("========================\n"));
  Serial.println(F("OK MEASURE_COMPLETE"));
}

// ---------------------------------------------------------------------------
// Multi-cycle measurement: N complete fwd/rev delta cycles with avg & std
// ---------------------------------------------------------------------------
void executeMeasurementMulti(int cycles) {
  if (cycles < 1)
    cycles = 1;
  if (cycles > 20)
    cycles = 20;

  Serial.print(F("--- Multi-Cycle Measurement (N="));
  Serial.print(cycles);
  Serial.println(F(") ---"));

  float rs_values[20];
  float sum = 0.0;

  for (int c = 0; c < cycles; c++) {
    // Forward
    digitalWrite(RELAY_PIN, RELAY_FORWARD);
    delay(SETTLING_TIME_MS);
    setMuxAndGain(ADS_MUX_CURRENT, ADS_GAIN_CURRENT, true);
    int32_t current_fwd = readADC();
    setMuxAndGain(ADS_MUX_VOLTAGE, ADS_GAIN_VOLTAGE, true);
    int32_t voltage_fwd = readADC();

    // Reverse
    digitalWrite(RELAY_PIN, RELAY_REVERSE);
    delay(SETTLING_TIME_MS);
    setMuxAndGain(ADS_MUX_CURRENT, ADS_GAIN_CURRENT, true);
    int32_t current_rev = readADC();
    setMuxAndGain(ADS_MUX_VOLTAGE, ADS_GAIN_VOLTAGE, true);
    int32_t voltage_rev = readADC();

    float i_fwd = ((current_fwd * 2.048) / 8388608.0) * 1000.0 / 100.0;
    float v_fwd = (((voltage_fwd * 2.048) / 8388608.0) / 4.0) * 1000.0;
    float i_rev = ((current_rev * 2.048) / 8388608.0) * 1000.0 / 100.0;
    float v_rev = (((voltage_rev * 2.048) / 8388608.0) / 4.0) * 1000.0;

    float delta_v = (v_fwd - v_rev) / 2.0;
    // Relay reversal flips shunt polarity, so average current magnitudes.
    float test_i = (fabs(i_fwd) + fabs(i_rev)) / 2.0;

    float rs = 0.0;
    if (fabs(test_i) > MIN_VALID_CURRENT_MA) {
      rs = 4.532 * (delta_v / test_i);
    }
    rs_values[c] = rs;
    sum += rs;

    Serial.print(F("CYCLE:"));
    Serial.print(c + 1);
    Serial.print(F(" Rs:"));
    Serial.println(rs, 4);
  }

  float avg = sum / cycles;

  // Compute std dev
  float sq_sum = 0.0;
  for (int c = 0; c < cycles; c++) {
    float diff = rs_values[c] - avg;
    sq_sum += diff * diff;
  }
  float std_dev = (cycles > 1) ? sqrt(sq_sum / (cycles - 1)) : 0.0;

  Serial.print(F("AVG:"));
  Serial.print(avg, 4);
  Serial.print(F(" STD:"));
  Serial.println(std_dev, 4);

  // Also emit the standard result line for backward compat
  Serial.print(F("Raw R_sheet: "));
  Serial.print(avg, 4);
  Serial.println(F(" Ohm/sq"));

  Serial.println(F("OK MEASURE_COMPLETE"));
}

int32_t readADCAveraged(int samples, int discardFirst) {
  if (samples < 1)
    samples = 1;
  int64_t sum = 0;
  int count = 0;
  for (int i = 0; i < samples + discardFirst; i++) {
    int32_t raw = readADC();
    if (i < discardFirst)
      continue;
    sum += raw;
    count++;
  }
  if (count == 0)
    return 0;
  return (int32_t)(sum / count);
}

void executeMeasurementDebug(int samples) {
  const int discardFirst = 1;

  Serial.println(F("--- MEASURE_DBG START ---"));
  Serial.print(F("DBG samples: "));
  Serial.println(samples);
  Serial.print(F("DBG discard_first: "));
  Serial.println(discardFirst);

  digitalWrite(RELAY_PIN, RELAY_FORWARD);
  delay(SETTLING_TIME_MS);

  setMuxAndGain(ADS_MUX_CURRENT, ADS_GAIN_CURRENT, true);
  int32_t current_fwd = readADCAveraged(samples, discardFirst);
  setMuxAndGain(ADS_MUX_VOLTAGE, ADS_GAIN_VOLTAGE, true);
  int32_t voltage_fwd = readADCAveraged(samples, discardFirst);

  digitalWrite(RELAY_PIN, RELAY_REVERSE);
  delay(SETTLING_TIME_MS);

  setMuxAndGain(ADS_MUX_CURRENT, ADS_GAIN_CURRENT, true);
  int32_t current_rev = readADCAveraged(samples, discardFirst);
  setMuxAndGain(ADS_MUX_VOLTAGE, ADS_GAIN_VOLTAGE, true);
  int32_t voltage_rev = readADCAveraged(samples, discardFirst);

  Serial.print(F("RAW I_fwd: "));
  Serial.println(current_fwd);
  Serial.print(F("RAW V_fwd: "));
  Serial.println(voltage_fwd);
  Serial.print(F("RAW I_rev: "));
  Serial.println(current_rev);
  Serial.print(F("RAW V_rev: "));
  Serial.println(voltage_rev);

  float i_fwd_mA = ((current_fwd * 2.048) / 8388608.0) * 1000.0 / 100.0;
  float v_fwd_mV =
      (((voltage_fwd * 2.048) / 8388608.0) / 4.0) * 1000.0; // Gain = 4
  float i_rev_mA = ((current_rev * 2.048) / 8388608.0) * 1000.0 / 100.0;
  float v_rev_mV =
      (((voltage_rev * 2.048) / 8388608.0) / 4.0) * 1000.0; // Gain = 4

  float delta_v_mV = (v_fwd_mV - v_rev_mV) / 2.0;
  // Relay reversal flips shunt polarity, so average current magnitudes.
  float test_i_mA = (fabs(i_fwd_mA) + fabs(i_rev_mA)) / 2.0;

  Serial.print(F("DBG I_fwd(mA): "));
  Serial.println(i_fwd_mA, 6);
  Serial.print(F("DBG V_fwd(mV): "));
  Serial.println(v_fwd_mV, 6);
  Serial.print(F("DBG I_rev(mA): "));
  Serial.println(i_rev_mA, 6);
  Serial.print(F("DBG V_rev(mV): "));
  Serial.println(v_rev_mV, 6);
  Serial.print(F("DBG Delta_V(mV): "));
  Serial.println(delta_v_mV, 6);
  Serial.print(F("DBG Test_I(mA): "));
  Serial.println(test_i_mA, 6);

  if (fabs(test_i_mA) > MIN_VALID_CURRENT_MA) {
    float r_sheet = 4.532 * (delta_v_mV / test_i_mA);
    Serial.print(F("DBG Raw R_sheet: "));
    Serial.println(r_sheet, 6);
  } else {
    Serial.print(F("DBG Raw R_sheet: skipped (|I| <= "));
    Serial.print(MIN_VALID_CURRENT_MA, 3);
    Serial.println(F("mA)"));
  }

  Serial.println(F("OK MEASURE_DBG"));
}

void resetADS1220() {
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE1));
  digitalWrite(ADS1220_CS_PIN, LOW);
  delayMicroseconds(1);
  SPI.transfer(RESET_CMD);
  delayMicroseconds(1);
  digitalWrite(ADS1220_CS_PIN, HIGH);
  SPI.endTransaction();
  Serial.println(F("ADS1220 Reset Command Sent."));
}

void writeRegister(uint8_t reg, uint8_t data) {
  uint8_t opcode = 0x40 | (reg << 2);
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE1));
  digitalWrite(ADS1220_CS_PIN, LOW);
  delayMicroseconds(1);
  SPI.transfer(opcode);
  SPI.transfer(data);
  delayMicroseconds(1);
  digitalWrite(ADS1220_CS_PIN, HIGH);
  SPI.endTransaction();
}

uint8_t readRegister(uint8_t reg) {
  uint8_t opcode = 0x20 | (reg << 2);
  uint8_t data = 0;
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE1));
  digitalWrite(ADS1220_CS_PIN, LOW);
  delayMicroseconds(1);
  SPI.transfer(opcode);
  data = SPI.transfer(0xFF);
  delayMicroseconds(1);
  digitalWrite(ADS1220_CS_PIN, HIGH);
  SPI.endTransaction();
  return data;
}

void dumpADS1220Registers() {
  Serial.println(F("ADS1220 Register Dump:"));
  for (int i = 0; i < 4; i++) {
    uint8_t val = readRegister(i);
    Serial.print(F("Reg "));
    Serial.print(i);
    Serial.print(F(": 0x"));
    if (val < 0x10)
      Serial.print(F("0"));
    Serial.println(val, HEX);
  }
}

void configADS1220() {
  Serial.println(F("Configuring ADS1220..."));
  writeRegister(0x00, 0xAA);
  writeRegister(0x01, 0x00);
  writeRegister(0x02, 0x20);
  writeRegister(0x03, 0x00);
  Serial.println(F("Configuration written. Reading back:"));
  dumpADS1220Registers();
}

int32_t readADC() {
  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE1));
  digitalWrite(ADS1220_CS_PIN, LOW);
  delayMicroseconds(1);
  SPI.transfer(START_CMD);
  delayMicroseconds(1);
  digitalWrite(ADS1220_CS_PIN, HIGH);
  SPI.endTransaction();

  unsigned long startTime = millis();
  while (digitalRead(ADS1220_DRDY_PIN) == HIGH) {
    if (millis() - startTime > 100) {
      Serial.println(F("ERROR: DRDY Timeout!"));
      return 0;
    }
  }

  SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE1));
  digitalWrite(ADS1220_CS_PIN, LOW);
  delayMicroseconds(1);
  SPI.transfer(RDATA_CMD);
  uint8_t msb = SPI.transfer(0xFF);
  uint8_t mid = SPI.transfer(0xFF);
  uint8_t lsb = SPI.transfer(0xFF);
  delayMicroseconds(1);
  digitalWrite(ADS1220_CS_PIN, HIGH);
  SPI.endTransaction();

  int32_t result =
      ((int32_t)msb << 24) | ((int32_t)mid << 16) | ((int32_t)lsb << 8);
  result = result >> 8;

  return result;
}
