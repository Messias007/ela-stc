"""Data model for the ELA-STC tool.

All currents in amperes (A) at nominal bus voltage, capacities in ampere-hours (Ah),
times in minutes. Values in the example data files are ILLUSTRATIVE PLACEHOLDERS and
must be replaced with data from type certificate holder and equipment installation manuals.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PHASES = ("ground", "start", "taxi", "takeoff_climb", "cruise", "landing", "emergency")


@dataclass
class Battery:
    capacity_ah: float          # nameplate capacity at the 1-hour rate
    chemistry: str = "lead-acid"
    peukert_n: float = 1.2      # lead-acid 1.1-1.25, AGM 1.05-1.15
    rated_hours: float = 1.0    # rating time base H of the nameplate capacity
    soh: float = 1.0            # state of health: deliverable capacity of the fully charged battery / rated capacity
    soc: float = 1.0            # state of charge at alternator loss (CASA AC 21-38 4.5.12.6 assumes 0.90)
    temp_factor: float = 1.0    # capacity factor at the analysis temperature (1.0 = rating reference, +20..25 degC)
    capacity_scenarios: bool = False  # True: sensitivity varies capacity among documented alternatives (bat_capacity_factor)

    def __post_init__(self):
        if self.capacity_ah <= 0:
            raise ValueError("battery capacity_ah must be > 0")
        for name in ("soh", "soc", "temp_factor"):
            v = getattr(self, name)
            if not 0 < v <= 1.0:
                raise ValueError(f"battery {name} must be in (0, 1], got {v}")
        if not 1.0 <= self.peukert_n <= 1.6:
            raise ValueError(f"battery peukert_n outside plausible range 1.0-1.6: {self.peukert_n}")
        if self.rated_hours <= 0:
            raise ValueError("battery rated_hours must be > 0")


@dataclass
class Bus:
    name: str
    essential: bool = False     # remains powered after load shed (battery only)


@dataclass
class Aircraft:
    model: str
    tcds: str
    cert_basis: str             # e.g. "CAR 3" or "14 CFR 23 amdt 23-xx"
    voltage: float              # 14 or 28
    alternator_a: float         # nameplate continuous rating
    battery: Battery
    buses: list[Bus]
    required_endurance_min: float = 30.0
    battery_v: float = 0.0      # nominal battery voltage on emergency (12 or 24); 0 = same as bus
    baseline_loads: list["Load"] = field(default_factory=list)
    source: str = "PLACEHOLDER: replace with TC holder data"

    def __post_init__(self):
        if self.alternator_a <= 0:
            raise ValueError(f"{self.model}: alternator_a must be > 0")
        if self.voltage <= 0:
            raise ValueError(f"{self.model}: voltage must be > 0")
        if not self.battery_v:
            self.battery_v = self.voltage
        names = [l.name for l in self.baseline_loads]
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            raise ValueError(f"{self.model}: duplicate load names {sorted(dup)}")
        buses = {b.name for b in self.buses}
        for l in self.baseline_loads:
            if buses and l.bus not in buses:
                raise ValueError(f"{self.model}: load '{l.name}' on unknown bus '{l.bus}'")


@dataclass
class Load:
    name: str
    bus: str
    current_a: float = 0.0      # current at nominal voltage (continuous or RMS for intermittent)
    breaker_a: float | None = None
    duty: dict[str, float] = field(default_factory=dict)  # phase -> duty factor 0..1
    wire_awg: int | None = None
    wire_length_ft: float | None = None
    source: str = "PLACEHOLDER"
    current_by_v: dict[float, float] | None = None   # e.g. {14: 2.5, 28: 1.2}; overrides current_a
    breaker_by_v: dict[float, float] | None = None   # breaker rating per bus voltage
    typical_by_v: dict[float, float] | None = None   # typical current per voltage (manufacturer ELA procedure)
    cls: str = "continuous"     # "continuous" or "intermittent" (AC 43.13-1B 11-35; Cessna 1976 "running load")
    current_batt_a: float | None = None   # current at battery voltage when published (Cessna 172RMM 24 V column)
    constant_power: bool | None = None    # None -> True for avionics bus loads
    circuit: str | None = None  # protective-device group; loads on one breaker share it (None = own circuit)
    radio: str | None = None    # pairs a receive row with its transmit row: states are mutually exclusive

    def __post_init__(self):
        if self.constant_power is None:
            self.constant_power = self.bus == "avionics"
        if self.cls not in ("continuous", "intermittent"):
            raise ValueError(f"load '{self.name}': cls must be continuous or intermittent")
        if self.current_a < 0:
            raise ValueError(f"load '{self.name}': negative current")
        for d in (self.current_by_v, self.typical_by_v, self.breaker_by_v):
            if d and any(float(v) < 0 for v in d.values()):
                raise ValueError(f"load '{self.name}': negative value in per-voltage table")
        for ph, k in self.duty.items():
            if ph not in PHASES:
                raise ValueError(f"load '{self.name}': unknown phase '{ph}'")
            if not 0.0 <= float(k) <= 1.0:
                raise ValueError(f"load '{self.name}': duty for {ph} must be in [0, 1], got {k}")

    def at_voltage(self, volts: float, use_typical: bool = False) -> "Load":
        """Copy of this load with current_a (and breaker_a) resolved for the bus voltage.

        use_typical=True takes typical_by_v when given (manufacturer net-change procedure)."""
        from dataclasses import replace

        def pick(d, label):
            t = {float(k): float(v) for k, v in d.items()}
            if float(volts) not in t:
                raise ValueError(f"load '{self.name}': no {label} given for {volts} V")
            return t[float(volts)]

        out = self
        src = self.typical_by_v if (use_typical and self.typical_by_v) else self.current_by_v
        if src:
            out = replace(out, current_a=pick(src, "current"))
        if self.breaker_by_v:
            out = replace(out, breaker_a=pick(self.breaker_by_v, "breaker"))
        return out

    def k(self, phase: str) -> float:
        return float(self.duty.get(phase, 0.0))


@dataclass
class Installation:
    name: str
    added: list[Load] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)   # names of baseline loads removed (all models)
    removed_by_model: dict[str, list[str]] = field(default_factory=dict)  # model -> extra removals

    def removed_for(self, model: str) -> list[str]:
        return list(self.removed) + list(self.removed_by_model.get(model, []))
