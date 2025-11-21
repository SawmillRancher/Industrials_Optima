"""Command-line interface for hazardous waste analysis."""

import argparse
import asyncio
import logging
import sys
from datetime import datetime

from .analyzer import WasteAnalyzer
from .pricing import PricingCollector
from .waste_codes import INCINERATION_WASTE_CODES, LANDFILL_WASTE_CODES, get_waste_code_info


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def cmd_report(args):
    """Generate market analysis report."""
    setup_logging(args.verbose)
    analyzer = WasteAnalyzer()
    report = analyzer.generate_report(include_pricing=True)
    print(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"\nReport saved to: {args.output}")


def cmd_pricing(args):
    """Show pricing data."""
    setup_logging(args.verbose)
    collector = PricingCollector()

    if args.code:
        comparison = collector.get_price_comparison(args.code)
        info = get_waste_code_info(args.code)

        print(f"\nWaste Code: {args.code}")
        print(f"Description: {info['description']}")
        print(f"Requires Incineration: {'Yes' if info['requires_incineration'] else 'No'}")
        print(f"Can Landfill: {'Yes' if info['can_landfill'] else 'No'}")
        print()

        if comparison["incineration"]:
            inc = comparison["incineration"]
            print(f"Incineration: ${inc['min']:.2f} - ${inc['max']:.2f} {inc['unit']}")
            if inc.get("notes"):
                print(f"  Note: {inc['notes']}")

        if comparison["landfill"]:
            land = comparison["landfill"]
            print(f"Landfill:     ${land['min']:.2f} - ${land['max']:.2f} {land['unit']}")
            if land.get("notes"):
                print(f"  Note: {land['notes']}")

        if comparison["price_differential"]:
            diff = comparison["price_differential"]
            print(f"\nIncineration Premium: ${diff['premium_per_lb']:.2f}/lb ({diff['premium_pct']:.1f}%)")
    else:
        # Show pricing for common codes
        codes = ["D001", "D002", "D003", "D008", "F001", "F003", "F005"]
        print(collector.generate_pricing_report(codes))


def cmd_codes(args):
    """List waste codes."""
    setup_logging(args.verbose)

    if args.incineration:
        print("\nWaste Codes Requiring Incineration:")
        print("=" * 50)
        for code in INCINERATION_WASTE_CODES[:50]:
            info = get_waste_code_info(code)
            print(f"  {code}: {info['description']}")
    elif args.landfill:
        print("\nWaste Codes Eligible for Landfill:")
        print("=" * 50)
        for code in LANDFILL_WASTE_CODES:
            info = get_waste_code_info(code)
            print(f"  {code}: {info['description']}")
    else:
        print("\nUse --incineration or --landfill to list specific codes")
        print(f"Total incineration codes: {len(INCINERATION_WASTE_CODES)}")
        print(f"Total landfill codes: {len(LANDFILL_WASTE_CODES)}")


def cmd_facilities(args):
    """List major disposal facilities."""
    from .pricing import MAJOR_FACILITIES

    print("\n" + "=" * 60)
    print("MAJOR HAZARDOUS WASTE DISPOSAL FACILITIES")
    print("=" * 60)

    print("\nIncinerators:")
    print("-" * 40)
    for f in MAJOR_FACILITIES["incinerators"]:
        print(f"  {f['name']} - {f['state']}")

    print("\nHazardous Waste Landfills:")
    print("-" * 40)
    for f in MAJOR_FACILITIES["landfills"]:
        print(f"  {f['name']} - {f['state']}")


async def cmd_volumes_async(args):
    """Fetch volume data from EPA eManifest."""
    setup_logging(args.verbose)
    analyzer = WasteAnalyzer()

    codes = args.codes.split(",") if args.codes else INCINERATION_WASTE_CODES[:5]

    print(f"Fetching volume data for: {', '.join(codes)}")
    print("(This requires EPA API access or public data)")

    if args.method == "incineration":
        analyses = await analyzer.analyze_incineration_volumes(
            waste_codes=codes,
            months_back=args.months,
            state_code=args.state,
        )
    else:
        analyses = await analyzer.analyze_landfill_volumes(
            waste_codes=codes,
            months_back=args.months,
            state_code=args.state,
        )

    for analysis in analyses:
        print(f"\n{analysis.waste_code}: {analysis.waste_description}")
        print(f"  Total Volume: {analysis.total_volume:,.0f} kg")
        print(f"  Monthly Avg: {analysis.average_monthly_volume:,.0f} kg")
        print(f"  Trend: {analysis.trend_direction} ({analysis.percent_change:+.1f}%)")


def cmd_volumes(args):
    """Fetch volume data."""
    asyncio.run(cmd_volumes_async(args))


def main():
    """Main entry point for hazwaste CLI."""
    parser = argparse.ArgumentParser(
        description="Hazardous Waste Analysis Tool - EPA eManifest Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hazwaste report                    Generate market analysis report
  hazwaste pricing -c D001           Get pricing for specific waste code
  hazwaste pricing                   Show pricing comparison
  hazwaste codes --incineration      List incineration-required codes
  hazwaste facilities                List major disposal facilities
  hazwaste volumes -c D001,F001      Fetch volume data from EPA
        """,
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate analysis report")
    report_parser.add_argument("-o", "--output", help="Output file path")
    report_parser.add_argument("-v", "--verbose", action="store_true")

    # Pricing command
    pricing_parser = subparsers.add_parser("pricing", help="Show pricing data")
    pricing_parser.add_argument("-c", "--code", help="Specific waste code")
    pricing_parser.add_argument("-v", "--verbose", action="store_true")

    # Codes command
    codes_parser = subparsers.add_parser("codes", help="List waste codes")
    codes_parser.add_argument("--incineration", action="store_true", help="Show incineration codes")
    codes_parser.add_argument("--landfill", action="store_true", help="Show landfill codes")
    codes_parser.add_argument("-v", "--verbose", action="store_true")

    # Facilities command
    facilities_parser = subparsers.add_parser("facilities", help="List disposal facilities")

    # Volumes command
    volumes_parser = subparsers.add_parser("volumes", help="Fetch EPA volume data")
    volumes_parser.add_argument("-c", "--codes", help="Comma-separated waste codes")
    volumes_parser.add_argument("-m", "--months", type=int, default=12, help="Months of data")
    volumes_parser.add_argument("-s", "--state", help="State code (e.g., TX, CA)")
    volumes_parser.add_argument(
        "--method",
        choices=["incineration", "landfill"],
        default="incineration",
        help="Disposal method",
    )
    volumes_parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.command == "report":
        cmd_report(args)
    elif args.command == "pricing":
        cmd_pricing(args)
    elif args.command == "codes":
        cmd_codes(args)
    elif args.command == "facilities":
        cmd_facilities(args)
    elif args.command == "volumes":
        cmd_volumes(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
