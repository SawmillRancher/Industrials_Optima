"""Hazardous waste volume and pricing trend analyzer."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
import json

from .emanifest_client import EManifestClient, WasteVolumeSummary
from .pricing import PricingCollector, PricingTrend
from .waste_codes import INCINERATION_WASTE_CODES, LANDFILL_WASTE_CODES, get_waste_code_info

logger = logging.getLogger(__name__)


@dataclass
class VolumeDataPoint:
    """A single data point for volume tracking."""
    period_start: datetime
    period_end: datetime
    waste_code: str
    disposal_method: str
    total_quantity: float
    quantity_unit: str
    manifest_count: int


@dataclass
class BacklogAnalysis:
    """Analysis of waste backlog/volume trends."""
    waste_code: str
    waste_description: str
    disposal_method: str
    periods: list[VolumeDataPoint] = field(default_factory=list)
    total_volume: float = 0.0
    average_monthly_volume: float = 0.0
    trend_direction: str = "stable"
    percent_change: float = 0.0
    capacity_utilization: Optional[float] = None


@dataclass
class MarketAnalysis:
    """Combined volume and pricing market analysis."""
    waste_code: str
    waste_description: str
    volume_analysis: Optional[BacklogAnalysis] = None
    incineration_pricing: Optional[PricingTrend] = None
    landfill_pricing: Optional[PricingTrend] = None
    market_outlook: str = ""
    supply_demand_indicator: str = "balanced"  # tight, balanced, loose


class WasteAnalyzer:
    """Analyzes hazardous waste volumes and pricing trends."""

    def __init__(
        self,
        emanifest_api_id: Optional[str] = None,
        emanifest_api_key: Optional[str] = None,
        data_dir: str = "./data/hazwaste",
    ):
        self.emanifest = EManifestClient(
            api_id=emanifest_api_id,
            api_key=emanifest_api_key,
        )
        self.pricing = PricingCollector(data_dir=f"{data_dir}/pricing")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def analyze_incineration_volumes(
        self,
        waste_codes: Optional[list[str]] = None,
        months_back: int = 12,
        state_code: Optional[str] = None,
    ) -> list[BacklogAnalysis]:
        """Analyze incineration waste volumes over time."""
        waste_codes = waste_codes or INCINERATION_WASTE_CODES[:20]  # Top 20 codes
        analyses = []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)

        for code in waste_codes:
            try:
                volumes = await self.emanifest.get_incineration_volumes(
                    waste_codes=[code],
                    start_date=start_date,
                    end_date=end_date,
                    state_code=state_code,
                )

                if volumes:
                    info = get_waste_code_info(code)
                    total = sum(v.total_quantity for v in volumes)
                    manifest_count = sum(v.manifest_count for v in volumes)

                    analysis = BacklogAnalysis(
                        waste_code=code,
                        waste_description=info["description"],
                        disposal_method="incineration",
                        total_volume=total,
                        average_monthly_volume=total / months_back if months_back > 0 else 0,
                    )

                    # Add volume data points
                    for v in volumes:
                        analysis.periods.append(VolumeDataPoint(
                            period_start=v.period_start,
                            period_end=v.period_end,
                            waste_code=code,
                            disposal_method=v.disposal_method,
                            total_quantity=v.total_quantity,
                            quantity_unit=v.quantity_unit,
                            manifest_count=v.manifest_count,
                        ))

                    analyses.append(analysis)

            except Exception as e:
                logger.error(f"Error analyzing {code}: {e}")

        return analyses

    async def analyze_landfill_volumes(
        self,
        waste_codes: Optional[list[str]] = None,
        months_back: int = 12,
        state_code: Optional[str] = None,
    ) -> list[BacklogAnalysis]:
        """Analyze landfill waste volumes over time."""
        waste_codes = waste_codes or LANDFILL_WASTE_CODES[:20]
        analyses = []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)

        for code in waste_codes:
            try:
                volumes = await self.emanifest.get_landfill_volumes(
                    waste_codes=[code],
                    start_date=start_date,
                    end_date=end_date,
                    state_code=state_code,
                )

                if volumes:
                    info = get_waste_code_info(code)
                    total = sum(v.total_quantity for v in volumes)

                    analysis = BacklogAnalysis(
                        waste_code=code,
                        waste_description=info["description"],
                        disposal_method="landfill",
                        total_volume=total,
                        average_monthly_volume=total / months_back if months_back > 0 else 0,
                    )

                    for v in volumes:
                        analysis.periods.append(VolumeDataPoint(
                            period_start=v.period_start,
                            period_end=v.period_end,
                            waste_code=code,
                            disposal_method=v.disposal_method,
                            total_quantity=v.total_quantity,
                            quantity_unit=v.quantity_unit,
                            manifest_count=v.manifest_count,
                        ))

                    analyses.append(analysis)

            except Exception as e:
                logger.error(f"Error analyzing {code}: {e}")

        return analyses

    def get_market_analysis(self, waste_code: str) -> MarketAnalysis:
        """Get combined market analysis for a waste code."""
        info = get_waste_code_info(waste_code)

        analysis = MarketAnalysis(
            waste_code=waste_code,
            waste_description=info["description"],
        )

        # Get pricing data
        if info["requires_incineration"] or "Incineration" in info["disposal_methods"]:
            inc_pricing = self.pricing.get_typical_price(waste_code, "incineration")
            if inc_pricing:
                analysis.incineration_pricing = PricingTrend(
                    waste_code=waste_code,
                    disposal_method="incineration",
                    average_price=(inc_pricing["min"] + inc_pricing["max"]) / 2,
                    min_price=inc_pricing["min"],
                    max_price=inc_pricing["max"],
                    unit=inc_pricing["unit"],
                )

        if info["can_landfill"]:
            land_pricing = self.pricing.get_typical_price(waste_code, "landfill")
            if land_pricing:
                analysis.landfill_pricing = PricingTrend(
                    waste_code=waste_code,
                    disposal_method="landfill",
                    average_price=(land_pricing["min"] + land_pricing["max"]) / 2,
                    min_price=land_pricing["min"],
                    max_price=land_pricing["max"],
                    unit=land_pricing["unit"],
                )

        # Generate market outlook
        if info["requires_incineration"]:
            analysis.market_outlook = (
                f"{waste_code} requires incineration disposal. "
                "Limited facility capacity nationwide typically results in premium pricing. "
                "Monitor Clean Harbors and Veolia capacity utilization for pricing trends."
            )
            analysis.supply_demand_indicator = "tight"
        elif info["can_landfill"]:
            analysis.market_outlook = (
                f"{waste_code} can be disposed via landfill after treatment. "
                "More disposal options available, generally lower pricing."
            )
            analysis.supply_demand_indicator = "balanced"
        else:
            analysis.market_outlook = "Consult specific regulations for disposal options."

        return analysis

    def generate_report(
        self,
        waste_codes: Optional[list[str]] = None,
        include_pricing: bool = True,
    ) -> str:
        """Generate a comprehensive analysis report."""
        waste_codes = waste_codes or INCINERATION_WASTE_CODES[:10]

        lines = [
            "=" * 80,
            "HAZARDOUS WASTE MARKET ANALYSIS REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 80,
            "",
            "EXECUTIVE SUMMARY",
            "-" * 40,
            "This report analyzes hazardous waste disposal trends for waste codes",
            "requiring incineration, including volume trends and pricing data.",
            "",
        ]

        # Incineration-only waste codes
        lines.append("\nINCINERATION-REQUIRED WASTE CODES")
        lines.append("-" * 40)

        for code in waste_codes[:10]:
            info = get_waste_code_info(code)
            if info["requires_incineration"]:
                lines.append(f"\n{code}: {info['description']}")
                analysis = self.get_market_analysis(code)

                if analysis.incineration_pricing:
                    p = analysis.incineration_pricing
                    lines.append(f"  Pricing: ${p.min_price:.2f} - ${p.max_price:.2f} {p.unit}")

                lines.append(f"  Market: {analysis.supply_demand_indicator}")

        # Pricing comparison
        if include_pricing:
            lines.append("\n\nPRICING COMPARISON: INCINERATION VS LANDFILL")
            lines.append("-" * 40)

            comparison_codes = ["D001", "D002", "D008", "F001", "F003"]
            for code in comparison_codes:
                comparison = self.pricing.get_price_comparison(code)
                lines.append(f"\n{code}:")

                if comparison["incineration"]:
                    inc = comparison["incineration"]
                    lines.append(f"  Incineration: ${inc['min']:.2f} - ${inc['max']:.2f}/lb")

                if comparison["landfill"]:
                    land = comparison["landfill"]
                    lines.append(f"  Landfill:     ${land['min']:.2f} - ${land['max']:.2f}/lb")

                if comparison["price_differential"]:
                    diff = comparison["price_differential"]
                    lines.append(f"  Incineration Premium: {diff['premium_pct']:.0f}%")

        # Key facilities
        lines.append("\n\nKEY DISPOSAL FACILITIES")
        lines.append("-" * 40)
        lines.append("\nMajor Incinerators:")
        from .pricing import MAJOR_FACILITIES
        for f in MAJOR_FACILITIES["incinerators"][:5]:
            lines.append(f"  - {f['name']} ({f['state']})")

        lines.append("\nMajor Hazardous Waste Landfills:")
        for f in MAJOR_FACILITIES["landfills"][:5]:
            lines.append(f"  - {f['name']} ({f['state']})")

        lines.append("\n" + "=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def save_report(self, filename: str = "hazwaste_report.txt"):
        """Save report to file."""
        report = self.generate_report()
        filepath = self.data_dir / filename
        filepath.write_text(report)
        logger.info(f"Report saved to {filepath}")
        return str(filepath)
