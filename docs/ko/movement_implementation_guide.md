# Movement Implementation Guide (P4PP System)

이 문서는 P4PP 시스템의 모터 제어(샘플 회전, 선형 이동) 기능 구현을 위한 **최종 하드웨어 배선, 기구적 유의사항, 튜닝 설정 및 펌웨어 로직**을 총망라한 가이드입니다.

> [!NOTE]
> **기구 설계(Mechanical Design) 관련주의사항**
> 이 가이드는 아두이노와 모터 드라이버 간의 **전자 회로 제어 및 배선/펌웨어**에 집중합니다. 실제 모터를 장착할 브라켓, 4-Point Probe가 수직으로 하강하는 Z축 이송 장치, 그리고 샘플이 놓일 회전 스테이지 등의 **기구적 설계(Mechanical Design)는 사용자의 셋업 환경에 맞춰 Custom 제작**되어야 합니다.

---

## 1. 하드웨어 구성 및 배선 (Hardware Setup & Wiring)

### 1-1. 핵심 부품
*   **모터**: StepperOnline 17HS08-1004S (NEMA 17, 1.0A/Phase, 1.8°/step) x 2개
*   **모터 드라이버**: Adafruit TMC2209 Breakout Board (#33) x 2개
*   **전원 보호 (필수)**: 470µF (또는 100µF 이상) 전해 캐패시터 x 2개
*   **리미트 스위치**: 마이크로 스위치 (NO, C 단자 사용) x 2개

### 1-2. 핀 할당 (Pin Assignments - Arduino Nano 33 IoT)
모든 핀 충돌을 해결하고 최종 확정된 맵핑입니다.

| 모듈 | 신호 (Signal) | Arduino 핀 | 비고 |
| :--- | :--- | :--- | :--- |
| **Rotation (회전)** | `STEP` | **D3** | |
| | `DIR` | **D4** | |
| | `ENABLE` | **A1** | LOW일 때 활성화, HIGH일 때 전력 차단 (대기) |
| | `Limit SW` | **D8** | 내부 풀업(INPUT_PULLUP) 사용. 스위치는 GND와 연결. |
| **Linear (선형)** | `STEP` | **D5** | |
| | `DIR` | **D6** | |
| | `ENABLE` | **A0** | LOW일 때 활성화, HIGH일 때 전력 차단 (대기) |
| | `Limit SW` | **D7** | 내부 풀업(INPUT_PULLUP) 사용. 스위치는 GND와 연결. |

### 1-3. 모터 드라이버(Board D) 배선 가이드
Adafruit TMC2209 드라이버는 고전압(12V 및 모터 코일) 쪽이 터미널 블록으로 빠져있고, 로직 핀(3.3V)들만 빵판에 꽂히는 구조입니다. 

1. **전원 분배 (Star Topology)**: 전자파 노이즈 최소화를 위해 직렬이 아닌 병렬(Star)로 전원을 분배합니다. 12V 어댑터 전원을 WAGO 등으로 쪼개어 각각의 터미널 블록(VM, GND)에 직접 물립니다. 아두이노 3.3V/GND 역시 VDD/GND 핀에 분배합니다.
   - ⚠️ **[매우 중요] 디커플링 캐패시터 장착**: 모터 드라이버 전원 투입 시 발생하는 전압 스파이크로 인해 드라이버가 즉각 타버리는(Burn-out) 현상을 막기 위해, 12V 터미널(VMOT 및 GND)에 **470µF 전해 캐패시터**를 반드시 병렬로 물려주어야 합니다. (전선 피복과 캐패시터 다리를 겹쳐서 나사로 함께 단단히 조이세요. **극성 주의!**)
2. **공통 접지 (Common Ground)**: 모든 보드의 12V GND와 3.3V/아두이노 GND는 한 점(Board C 등)에서 만나 공통 접지를 이루어야 합니다. 리미트 스위치의 C 단자 역시 이 접지망에 물립니다.
3. **모터 코일 배선 (Linear 방향 패치)**: 소프트웨어 내부 연산 충돌 방지를 위해 **Linear 모터의 터미널 1A와 1B 선을 물리적으로 교차 교환**했습니다. (검정색과 초록색 위치 교환). 이로써 양쪽 모터가 동일한 DIR 논리(HIGH=정방향/출발, LOW=역방향/호밍)를 가집니다.

---

## 2. 드라이버 튜닝 (Vref & Current Adjustment)

탈조(Stuttering) 및 발열을 방지하기 위해 TMC2209의 출력 전류를 튜닝해야 합니다.
*   **모터 스펙 (I_max)**: 1.0A 
*   **권장 운용 전류**: 최대치의 70~80% 수준
*   **튜닝 목표 전압 (Vref)**: **0.75V ~ 0.8V** 
    *(멀티미터로 보드 위 금속 가변저항 십자나사(+극)와 GND 단자 간 전압을 측정하며 미세 조정합니다.)*

---

## 3. 펌웨어 호밍 로직 (Firmware Homing Logic)

`AccelStepper` 라이브러리의 엔진 내부 방향 충돌 에러를 원천 차단하기 위해, 가장 로우레벨의 하드웨어 직접 제어 방식으로 호밍 함수를 구현했습니다.

### 3-1. 수동 스텝 함수 (Manual Step)
`delayMicroseconds()`를 활용해 직접 펄스를 쏩니다.
```cpp
void manualStep(int stepPin, unsigned int stepDelayUs) {
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(2);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(stepDelayUs);
}
```

### 3-2. 2-Pass(2차 접근) 호밍 시퀀스
1. **안전 후퇴 (Optional)**: 명령 시 이미 스위치가 눌려있다면 `RETREAT_DIR (HIGH)`로 스위치를 벗어난 후 추가 안전거리를 만듭니다.
2. **1차 고속 접근**: `HOMING_DIR (LOW)` 방향으로 스위치가 눌릴 때까지 빠른 속도(펄스 간격 800us)로 다가갑니다.
3. **1차 후퇴**: 충돌 시 정지 후 튕겨나가는 동작으로, `RETREAT_DIR (HIGH)` 방향으로 일정 스텝 (Linear: 800, Rotation: 200) 후퇴합니다.
4. **2차 정밀 접근**: 다시 `HOMING_DIR (LOW)` 방향으로 느린 속도(펄스 간격 4000us)로 접근해 눌리면 즉각 타겟으로 삼습니다.
5. **안전거리 및 0점 세팅**: 레버가 온전히 비키도록 `RETREAT_DIR` 방향으로 살짝(50 스텝) 뺀 뒤 거기를 `setCurrentPosition(0)`으로 확정합니다.

### 3-3. 비동기 통신 (Non-blocking Serial)
현재 펌웨어는 루프 매 바퀴마다 `Serial.read()`로 문자를 배열 버퍼에 하나씩 쌓는 비동기 아키텍처를 채택했습니다. 이는 모터 펄스 간격에 영향을 미치지 않아 무소음 스텔스 구동(StealthChop)을 완벽히 보장합니다.
