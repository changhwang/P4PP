# Final Bill of Materials (BOM) - P4PP System

이 목록은 P4PP 시스템 구축에 최종적으로 투입된 **"BOM 최종 완성본(P4PP_BOM_Final.csv)"** 기준 부품 리스트입니다. 각 부품 번호는 모든 가이드 문서의 참조 번호(`BOM #번호`)와 1:1로 정확하게 일치합니다.

## 1. 컨트롤러 & ADC (Core)
| 번호 | 개수 | 카테고리 | 부품명 (Item) | 비고 / 용도 |
| :---: | :---: | :--- | :--- | :--- |
| **1** | 1 | Core / Controller | Arduino Nano 33 IoT (3.3V) | 메인 컨트롤러 및 SPI 마스터 |
| **2** | 1 | Core / ADC | ADS1220 24-bit ADC breakout | 전압/전류 정밀 측정용 |

## 2. 1mA 측정 아날로그 회로 & 릴레이 스위칭 
| 번호 | 개수 | 카테고리 | 부품명 (Item) | 비고 / 용도 |
| :---: | :---: | :--- | :--- | :--- |
| **3** | 1 | Current Source | Adjustable current source IC (TO-92) | LM334 정전류원 |
| **4** | 1 | Current Source | Rset for 1.0 mA (68.1Ω, 0.1%) | ITO 등 일반 측정용 |
| **5** | 1 | Current Source | Rset for 100 µA (681Ω, 0.1%) | PEDOT 등 고저항 교체용 |
| **6** | 1 | Current Sense | Shunt resistor for current monitor (100Ω, 0.1%)| 전류 감시 션트저항 |
| **7** | 1 | Current Reversal | DPDT relay, 12V coil (through-hole) | 델타 모드 반전 릴레이 |
| **8** | 1 | Relay Driver | NPN transistor (TO-92) | 릴레이 구동 차폐 스위치 (PN2222A) |
| **9** | 1 | Relay Driver | Flyback diode for relay coil | 릴레이 역기전력 방어 (1N4148) |
| **10** | 2 | Relay Driver | Base resistor (1kΩ, 0.1% / 1%) | 베이스 보호 및 풀다운 용도 |

## 3. 프로브 보호회로 및 단자 (Input Protection & Connectors)
| 번호 | 개수 | 카테고리 | 부품명 (Item) | 비고 / 용도 |
| :---: | :---: | :--- | :--- | :--- |
| **11** | 1 | ADC Input Protection | Diode Array Common Anode 30V 200mA (BAT54A) | V+, V- 방어 |
| **12** | 1 | ADC Input Protection | Diode Array Common Cathode 30V 200mA (BAT54C)| V+, V- 짝꿍 방어 |
| **13** | 2 | ADC Input Protection | SOT23 TO DIP ADAPTER | SMD 다이오드 변환 단자 |
| **18** | 1 | Connectors (Probe) | CONN BIND POST KNURLED BLACK | Binding Post |
| **19** | 1 | Connectors (Probe) | Binding Post Connector RED | Binding Post |
| **20** | 1 | Connectors (Probe) | Binding Post Connector GREEN | Binding Post |
| **21** | 1 | Connectors (Probe) | CONN BIND POST KNURLED BLUE | Binding Post |

## 4. 메인 전원, 보호회로 및 필터 소자 (Power, Protection & Filters)
| 번호 | 개수 | 카테고리 | 부품명 (Item) | 비고 / 용도 |
| :---: | :---: | :--- | :--- | :--- |
| **14** | 1 | Power | 12V wall adapter, 60W (12V/5A), 2.5mm | 12V 메인 어댑터 |
| **15** | 1 | Power | Power Cord | 어댑터 전원 코드 |
| **25** | 1 | Power (DC input) | DC barrel jack, Panel Mount | 12V 어댑터 꽂는 케이스 단자 |
| **26** | 1 | Power Protection | Inline blade fuse holder (ATC/ATO) | 합선 방어용 인라인 퓨즈 홀더 |
| **27** | 1 | Power Protection | ATC/ATO blade fuse, 5A, 32V | 블레이드 퓨즈 |
| **28** | 1 | Stabilizing | 10 Ohms 1% 0.25W Resistor | 3.3V Low-Pass 필터용 전원 노이즈 제거 |
| **29** | 1 | Stabilizing | 1 µF 10% 16V Ceramic Capacitor | 메인 전원 디커플링 |
| **30** | 1 | Stabilizing | 0.1 µF 10% 50V Ceramic Capacitor | 3.3V 전원망 고주파 필터링 |
| **31** | 1 | Power Decoupling | Bulk electrolytic capacitor, 470uF 25V | TMC2209 드라이버 파손 방지 필수 |

## 5. 기구 동작 (Linear Motion & Switches)
| 번호 | 개수 | 카테고리 | 부품명 (Item) | 비고 / 용도 |
| :---: | :---: | :--- | :--- | :--- |
| **24** | 2 | Switch | SWITCH SNAP ACTION SPDT 15A 250V | 호밍용 (회전/선형) 마이크로 리미트 스위치 |
| **33** | 2 | Linear Motion | TMC2209 Stepper Motor Driver | 선형/회전 모터 구동 드라이버 |
| **36** | 2 | Linear Motion | Stepper Motor (NEMA 17) | 회전/수직 하강 스테퍼 모터 |

## 6. 기판, 헤더, 배선 및 기타 자재 (Boards & Accessories)
| 번호 | 개수 | 카테고리 | 부품명 (Item) | 비고 / 용도 |
| :---: | :---: | :--- | :--- | :--- |
| **16** | 1 | Headers | Male header, 1x40, 2.54mm | 아두이노 조립 베이스 등 |
| **17** | 1 | Headers | Female header, 1x40, 2.54mm | Rset(가변전류 조절) 핀헤더 소켓 등 |
| **22** | 1 | EMI / Noise control | Ferrite clamp (snap-on) | 모터 노이즈 제어용 코어 |
| **23** | 1 | Wiring | Shielded wire 22AWG | 쉴드 케이블 |
| **32** | 1 | Cables | Micro-USB cable | Arduino Nano PC 연결망 |
| **34** | 1 | Breadboard | Perma-Proto Full-sized Breadboard PCB | 측정부 (Board A, B) 납땜용 |
| **35** | 3 | Breadboard | Perma-Proto Mint Tin Size Breadboard PCB | 스위칭(Board C), 모터용(Board D) 기판 |

---
*모든 가이드 상병합 및 동기화 처리 완료.*
