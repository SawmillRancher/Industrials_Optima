"""Hazardous waste disposal pricing data collector.

Collects pricing data from public sources, industry reports, and facility data
for incineration and landfill disposal fees by waste code.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class DisposalPrice:
    """Represents a disposal price data point."""
    waste_code: str
    disposal_method: str  # 'incineration' or 'landfill'
    price_per_unit: float
    unit: str  # 'lb', 'kg', 'ton', 'drum', 'gal'
    facility_name: Optional[str] = None
    facility_state: Optional[str] = None
    source: str = ""
    date_collected: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None


@dataclass
class PricingTrend:
    """Pricing trend over time."""
    waste_code: str
    disposal_method: str
    data_points: list[tuple[datetime, float]] = field(default_factory=list)
    unit: str = "per_lb"
    average_price: float = 0.0
    min_price: float = 0.0
    max_price: float = 0.0
    trend_direction: str = "stable"  # 'up', 'down', 'stable'
    percent_change: float = 0.0


# Known industry pricing sources and typical ranges
# These are approximate ranges based on industry data
TYPICAL_PRICING_RANGES = {
    "incineration": {
        "general": {"min": 0.50, "max": 3.00, "unit": "per_lb"},
        "D001": {"min": 0.75, "max": 2.50, "unit": "per_lb", "notes": "Ignitable waste"},
        "D003": {"min": 1.00, "max": 4.00, "unit": "per_lb", "notes": "Reactive waste"},
        "F001": {"min": 0.80, "max": 3.50, "unit": "per_lb", "notes": "Halogenated solvents"},
        "F002": {"min": 0.80, "max": 3.50, "unit": "per_lb", "notes": "Halogenated solvents"},
        "F003": {"min": 0.60, "max": 2.00, "unit": "per_lb", "notes": "Non-halogenated solvents"},
        "F004": {"min": 0.70, "max": 2.50, "unit": "per_lb", "notes": "Non-halogenated solvents"},
        "F005": {"min": 0.80, "max": 3.00, "unit": "per_lb", "notes": "Spent solvents"},
        "F020": {"min": 2.00, "max": 8.00, "unit": "per_lb", "notes": "Dioxin waste - premium pricing"},
        "K-listed": {"min": 0.75, "max": 4.00, "unit": "per_lb"},
        "P-listed": {"min": 1.50, "max": 6.00, "unit": "per_lb", "notes": "Acute hazardous"},
        "U-listed": {"min": 0.60, "max": 3.00, "unit": "per_lb"},
        "PCBs": {"min": 1.50, "max": 5.00, "unit": "per_lb", "notes": "TSCA regulated"},
    },
    "landfill": {
        "general": {"min": 0.15, "max": 0.75, "unit": "per_lb"},
        "D002": {"min": 0.20, "max": 0.60, "unit": "per_lb", "notes": "Corrosive - needs neutralization"},
        "D004": {"min": 0.25, "max": 0.80, "unit": "per_lb", "notes": "Arsenic"},
        "D005": {"min": 0.20, "max": 0.60, "unit": "per_lb", "notes": "Barium"},
        "D006": {"min": 0.30, "max": 0.90, "unit": "per_lb", "notes": "Cadmium"},
        "D007": {"min": 0.25, "max": 0.75, "unit": "per_lb", "notes": "Chromium"},
        "D008": {"min": 0.25, "max": 0.85, "unit": "per_lb", "notes": "Lead"},
        "D009": {"min": 0.40, "max": 1.20, "unit": "per_lb", "notes": "Mercury - special handling"},
        "D010": {"min": 0.25, "max": 0.70, "unit": "per_lb", "notes": "Selenium"},
        "D011": {"min": 0.20, "max": 0.60, "unit": "per_lb", "notes": "Silver"},
        "stabilized": {"min": 0.10, "max": 0.40, "unit": "per_lb", "notes": "Pre-treated/stabilized waste"},
    },
}

# Major hazardous waste facilities
MAJOR_FACILITIES = {
    "incinerators": [
        {"name": "Clean Harbors Deer Park", "state": "TX", "type": "incineration"},
        {"name": "Clean Harbors El Dorado", "state": "AR", "type": "incineration"},
        {"name": "Clean Harbors Aragonite", "state": "UT", "type": "incineration"},
        {"name": "Veolia ES Technical Solutions", "state": "TX", "type": "incineration"},
        {"name": "Heritage Thermal Services", "state": "OH", "type": "incineration"},
        {"name": "Ross Incineration Services", "state": "OH", "type": "incineration"},
        {"name": "Tradebe Treatment and Recycling", "state": "CT", "type": "incineration"},
        {"name": "US Ecology", "state": "TX", "type": "incineration"},
        {"name": "Stericycle Environmental Solutions", "state": "UT", "type": "incineration"},
    ],
    "landfills": [
        {"name": "Clean Harbors Buttonwillow", "state": "CA", "type": "landfill"},
        {"name": "Clean Harbors Lone Mountain", "state": "OK", "type": "landfill"},
        {"name": "US Ecology Idaho", "state": "ID", "type": "landfill"},
        {"name": "US Ecology Nevada", "state": "NV", "type": "landfill"},
        {"name": "US Ecology Texas", "state": "TX", "type": "landfill"},
        {"name": "Waste Control Specialists", "state": "TX", "type": "landfill"},
        {"name": "Chemical Waste Management", "state": "AL", "type": "landfill"},
        {"name": "Wayne Disposal", "state": "MI", "type": "landfill"},
    ],
}


class PricingCollector:
    """Collects hazardous waste disposal pricing data."""

    # Public data sources for pricing information
    SOURCES = {
        "epa_biennial": "https://rcrapublic.epa.gov/rcrainfoweb/",
        "state_data": "https://www.epa.gov/hwgenerators/hazardous-waste-management-facilities-and-units",
    }

    def __init__(self, data_dir: str = "./data/pricing"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.prices: list[DisposalPrice] = []

    def get_typical_price(
        self,
        waste_code: str,
        disposal_method: str,
    ) -> Optional[dict]:
        """Get typical pricing range for a waste code and disposal method."""
        method_prices = TYPICAL_PRICING_RANGES.get(disposal_method.lower(), {})

        # Check for specific waste code
        if waste_code in method_prices:
            return method_prices[waste_code]

        # Check by waste code prefix (K-listed, P-listed, U-listed)
        prefix = waste_code[0] + "-listed"
        if prefix in method_prices:
            return method_prices[prefix]

        # Return general pricing
        return method_prices.get("general")

    async def fetch_facility_data(self) -> list[dict]:
        """Fetch facility information from EPA."""
        facilities = []

        # Return known facilities as base data
        for category, facility_list in MAJOR_FACILITIES.items():
            for facility in facility_list:
                facilities.append(facility)

        return facilities

    def add_price_data(
        self,
        waste_code: str,
        disposal_method: str,
        price: float,
        unit: str,
        facility_name: Optional[str] = None,
        facility_state: Optional[str] = None,
        source: str = "manual",
        notes: Optional[str] = None,
    ):
        """Add a price data point."""
        self.prices.append(DisposalPrice(
            waste_code=waste_code,
            disposal_method=disposal_method,
            price_per_unit=price,
            unit=unit,
            facility_name=facility_name,
            facility_state=facility_state,
            source=source,
            notes=notes,
        ))

    def save_prices(self, filename: str = "pricing_data.json"):
        """Save collected prices to JSON."""
        filepath = self.data_dir / filename
        data = [
            {
                "waste_code": p.waste_code,
                "disposal_method": p.disposal_method,
                "price_per_unit": p.price_per_unit,
                "unit": p.unit,
                "facility_name": p.facility_name,
                "facility_state": p.facility_state,
                "source": p.source,
                "date_collected": p.date_collected.isoformat(),
                "notes": p.notes,
            }
            for p in self.prices
        ]
        filepath.write_text(json.dumps(data, indent=2))
        logger.info(f"Saved {len(self.prices)} price records to {filepath}")

    def load_prices(self, filename: str = "pricing_data.json") -> list[DisposalPrice]:
        """Load prices from JSON."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            return []

        data = json.loads(filepath.read_text())
        self.prices = [
            DisposalPrice(
                waste_code=d["waste_code"],
                disposal_method=d["disposal_method"],
                price_per_unit=d["price_per_unit"],
                unit=d["unit"],
                facility_name=d.get("facility_name"),
                facility_state=d.get("facility_state"),
                source=d.get("source", ""),
                date_collected=datetime.fromisoformat(d["date_collected"]),
                notes=d.get("notes"),
            )
            for d in data
        ]
        return self.prices

    def get_price_comparison(
        self,
        waste_code: str,
    ) -> dict:
        """Compare incineration vs landfill pricing for a waste code."""
        incineration = self.get_typical_price(waste_code, "incineration")
        landfill = self.get_typical_price(waste_code, "landfill")

        result = {
            "waste_code": waste_code,
            "incineration": incineration,
            "landfill": landfill,
            "price_differential": None,
        }

        if incineration and landfill:
            inc_avg = (incineration["min"] + incineration["max"]) / 2
            land_avg = (landfill["min"] + landfill["max"]) / 2
            result["price_differential"] = {
                "incineration_avg": inc_avg,
                "landfill_avg": land_avg,
                "premium_pct": ((inc_avg - land_avg) / land_avg * 100) if land_avg > 0 else None,
                "premium_per_lb": inc_avg - land_avg,
            }

        return result

    def calculate_trend(
        self,
        waste_code: str,
        disposal_method: str,
        prices: Optional[list[DisposalPrice]] = None,
    ) -> PricingTrend:
        """Calculate pricing trend from historical data."""
        prices = prices or self.prices

        # Filter relevant prices
        relevant = [
            p for p in prices
            if p.waste_code == waste_code and p.disposal_method.lower() == disposal_method.lower()
        ]

        if not relevant:
            return PricingTrend(
                waste_code=waste_code,
                disposal_method=disposal_method,
            )

        # Sort by date
        relevant.sort(key=lambda p: p.date_collected)

        data_points = [(p.date_collected, p.price_per_unit) for p in relevant]
        prices_only = [p.price_per_unit for p in relevant]

        avg_price = sum(prices_only) / len(prices_only)
        min_price = min(prices_only)
        max_price = max(prices_only)

        # Calculate trend
        if len(prices_only) >= 2:
            first_price = prices_only[0]
            last_price = prices_only[-1]
            percent_change = ((last_price - first_price) / first_price * 100) if first_price > 0 else 0

            if percent_change > 5:
                trend_direction = "up"
            elif percent_change < -5:
                trend_direction = "down"
            else:
                trend_direction = "stable"
        else:
            percent_change = 0.0
            trend_direction = "stable"

        return PricingTrend(
            waste_code=waste_code,
            disposal_method=disposal_method,
            data_points=data_points,
            unit=relevant[0].unit if relevant else "per_lb",
            average_price=avg_price,
            min_price=min_price,
            max_price=max_price,
            trend_direction=trend_direction,
            percent_change=percent_change,
        )

    def generate_pricing_report(self, waste_codes: list[str]) -> str:
        """Generate a text report of pricing data."""
        lines = [
            "=" * 70,
            "HAZARDOUS WASTE DISPOSAL PRICING REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 70,
            "",
        ]

        for code in waste_codes:
            comparison = self.get_price_comparison(code)
            lines.append(f"\n{code}: {comparison.get('waste_code', 'Unknown')}")
            lines.append("-" * 40)

            if comparison["incineration"]:
                inc = comparison["incineration"]
                lines.append(f"  Incineration: ${inc['min']:.2f} - ${inc['max']:.2f} {inc['unit']}")
                if inc.get("notes"):
                    lines.append(f"    Note: {inc['notes']}")

            if comparison["landfill"]:
                land = comparison["landfill"]
                lines.append(f"  Landfill:     ${land['min']:.2f} - ${land['max']:.2f} {land['unit']}")
                if land.get("notes"):
                    lines.append(f"    Note: {land['notes']}")

            if comparison["price_differential"]:
                diff = comparison["price_differential"]
                lines.append(f"  Premium: ${diff['premium_per_lb']:.2f}/lb ({diff['premium_pct']:.1f}% higher for incineration)")

        lines.append("\n" + "=" * 70)
        lines.append("Major Facilities:")
        lines.append("-" * 40)

        lines.append("\nIncinerators:")
        for f in MAJOR_FACILITIES["incinerators"]:
            lines.append(f"  - {f['name']} ({f['state']})")

        lines.append("\nLandfills:")
        for f in MAJOR_FACILITIES["landfills"]:
            lines.append(f"  - {f['name']} ({f['state']})")

        return "\n".join(lines)
