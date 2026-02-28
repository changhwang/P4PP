#include <SPI.h>

// ADS1220 핀 세팅 (Arduino Nano 33 IoT)
const int CS_PIN = 10;
const int DRDY_PIN = 9;

SPISettings ADS1220_SPI(100000, MSBFIRST, SPI_MODE1);

void ads_cmd(byte cmd) {
  SPI.beginTransaction(ADS1220_SPI);
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(cmd);
  digitalWrite(CS_PIN, HIGH);
  SPI.endTransaction();
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }

  Serial.println("\n=== ADS1220 WRITE/READ Verification ===");
  Serial.println("[INFO] ADS1220 기본값은 0x00 입니다 (0x08이 아닙니다!)");

  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);
  pinMode(DRDY_PIN, INPUT_PULLUP);

  SPI.begin();
  delay(500);

  // 1. 리셋
  Serial.println("\n1. RESET...");
  ads_cmd(0x06);
  delay(100);

  // 2. 리셋 직후 기본값 읽기 (0x00이 나와야 정상!)
  Serial.println("2. Reading defaults (should be 0x00)...");
  byte before[4];
  SPI.beginTransaction(ADS1220_SPI);
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(0x23); // RREG: reg0부터 4개
  for(int i=0; i<4; i++) before[i] = SPI.transfer(0xFF);
  digitalWrite(CS_PIN, HIGH);
  SPI.endTransaction();

  for(int i=0; i<4; i++) {
    Serial.print("  Reg"); Serial.print(i); Serial.print("=0x");
    if(before[i]<0x10) Serial.print("0");
    Serial.println(before[i], HEX);
  }

  // 3. 레지스터 0에 0x6A를 직접 써넣기 (WREG: 0100_0000 = 0x40)
  byte testVal = 0x6A; // MUX=0110, GAIN=101, PGA=0
  Serial.print("\n3. Writing 0x"); Serial.print(testVal, HEX);
  Serial.println(" to Register 0...");

  SPI.beginTransaction(ADS1220_SPI);
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(0x40); // WREG: reg0에 1바이트 쓰기
  SPI.transfer(testVal);
  digitalWrite(CS_PIN, HIGH);
  SPI.endTransaction();

  delay(10);

  // 4. 다시 읽어서 변했는지 확인!
  Serial.println("4. Reading back Register 0...");
  byte after;
  SPI.beginTransaction(ADS1220_SPI);
  digitalWrite(CS_PIN, LOW);
  SPI.transfer(0x20); // RREG: reg0 1바이트 읽기
  after = SPI.transfer(0xFF);
  digitalWrite(CS_PIN, HIGH);
  SPI.endTransaction();

  Serial.print("  Reg0 = 0x");
  if(after<0x10) Serial.print("0");
  Serial.println(after, HEX);

  // 5. 최종 판정
  Serial.println("\n========== VERDICT ==========");
  if (after == testVal) {
    Serial.println("[SUCCESS] SPI 통신 완벽!! 칩이 살아있습니다!!");
    Serial.print("  0x"); Serial.print(testVal, HEX);
    Serial.print(" 을 보냈고, 칩이 0x"); Serial.print(after, HEX);
    Serial.println(" 을 정확히 되돌려줬습니다.");
  } else if (after == 0x00) {
    Serial.println("[FAIL] 레지스터가 변하지 않았습니다. 칩이 명령을 못 받고 있습니다.");
  } else {
    Serial.print("[PARTIAL] 뭔가 반응은 있습니다! 0x");
    Serial.println(after, HEX);
  }
}

void loop() {}
