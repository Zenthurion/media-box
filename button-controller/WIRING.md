# Power wiring notes (Pi + ESP32 + P‑channel MOSFET)

- **Goal:** High-side switch the Pi’s 5V with a P-channel MOSFET; Pi reports “alive” on GPIO7 to ESP32 GPIO18; ESP32 drives MOSFET gate on GPIO5. Common ground stays tied.

## P-channel MOSFET (high-side)
- Source → 5V input (USB 5V).
- Drain → 5V to Raspberry Pi.
- Gate → ESP32 GPIO5 through ~220 Ω.
- Pull-up → 100 kΩ from gate to 5V (defaults OFF).
- Logic: gate HIGH ≈ 5V = OFF; gate LOW ≈ 0V = ON. ESP32 drives LOW to power Pi, releases to turn off.

## “Alive” signal from Pi
- Pi GPIO7 → ESP32 GPIO18 (input).
- Configure ESP32 pin as `INPUT_PULLDOWN` or add ~100 kΩ pulldown to GND so it reads LOW when Pi is off.
- Pi runs `power-hold` service to drive GPIO7 HIGH while running, LOW on shutdown.

## Grounds
- All grounds (Pi, ESP32, supply, MOSFET source/drain returns) stay common. Do **not** switch ground with the MOSFET.

## Optional protections
- Gate resistor: ~220 Ω already listed (helps tame transients).
- Optional gate-source Zener (~5.6 V) if you ever drive gate above 5 V (not needed with 3.3 V logic).

## Notes
- Use a logic-level P-channel FET with low Rds(on) at Vgs = –3 to –4.5 V (examples: AO3407A, IRLML6402, PMV48XP).
- Keep the MOSFET close to the Pi’s 5V feed; keep grounds thick/short.***
