# Power wiring notes (simplified, always-on)

- The Pi is now powered directly (always on). No MOSFET high-side switch is used.
- The ESP32 no longer monitors a Pi “alive” GPIO signal.
- Keep all grounds common between the Pi, ESP32, and power supply.

This project no longer uses any shutdown or power-hold wiring. Remove any MOSFET, gate resistor, or GPIO7 alive signal connections if they were previously installed.
