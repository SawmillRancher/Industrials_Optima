"""EPA eManifest API client for hazardous waste data."""

import logging
from datetime import datetime, timedelta
from typing import Optional
import aiohttp
from dataclasses import dataclass, field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@dataclass
class ManifestRecord:
    """Represents a hazardous waste manifest record."""
    manifest_tracking_number: str
    generator_id: str
    generator_name: str
    generator_state: str
    tsdf_id: str  # Treatment, Storage, Disposal Facility
    tsdf_name: str
    tsdf_state: str
    waste_codes: list[str]
    quantity: float
    quantity_unit: str
    management_method: str  # Incineration, Landfill, etc.
    shipped_date: Optional[datetime] = None
    received_date: Optional[datetime] = None


@dataclass
class WasteVolumeSummary:
    """Summary of waste volumes by code and disposal method."""
    waste_code: str
    waste_description: str
    period_start: datetime
    period_end: datetime
    total_quantity: float
    quantity_unit: str
    manifest_count: int
    disposal_method: str
    facilities: list[str] = field(default_factory=list)


class EManifestClient:
    """Client for EPA RCRAInfo eManifest API.

    API Documentation: https://rcrainfo.epa.gov/rcrainfoprod/action/secured/api
    Public Data: https://rcrapublic.epa.gov/rcrainfoweb/action/main-menu/view
    """

    # EPA eManifest API endpoints
    BASE_URL = "https://rcrainfo.epa.gov/rcrainfoprod/rest/api/v1"
    PUBLIC_URL = "https://rcrapublic.epa.gov/rcrainfo/rest/api/v1"

    # Management method codes for incineration and landfill
    INCINERATION_METHODS = ["H040", "H061", "H050", "H039"]  # Various incineration codes
    LANDFILL_METHODS = ["H101", "H102", "H103", "H131", "H132"]  # Landfill codes

    def __init__(self, api_id: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize client with optional API credentials.

        For public data, credentials are not required.
        For detailed manifest data, register at https://rcrainfo.epa.gov/
        """
        self.api_id = api_id
        self.api_key = api_key
        self.token = None
        self.token_expiry = None

    async def _get_auth_token(self, session: aiohttp.ClientSession) -> Optional[str]:
        """Authenticate and get bearer token."""
        if not self.api_id or not self.api_key:
            return None

        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token

        try:
            async with session.get(
                f"{self.BASE_URL}/auth/{self.api_id}/{self.api_key}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data.get("token")
                    self.token_expiry = datetime.now() + timedelta(minutes=20)
                    return self.token
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
        return None

    def _get_headers(self) -> dict:
        """Get request headers."""
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_manifests(
        self,
        state_code: Optional[str] = None,
        site_id: Optional[str] = None,
        waste_code: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        management_method: Optional[str] = None,
    ) -> list[dict]:
        """Search for manifests with filters.

        Args:
            state_code: Two-letter state code (e.g., 'TX', 'CA')
            site_id: EPA site ID
            waste_code: Hazardous waste code (e.g., 'D001', 'F001')
            start_date: Start of date range
            end_date: End of date range
            management_method: Treatment method code
        """
        params = {}
        if state_code:
            params["stateCode"] = state_code
        if site_id:
            params["siteId"] = site_id
        if waste_code:
            params["wasteCode"] = waste_code
        if start_date:
            params["startDate"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["endDate"] = end_date.strftime("%Y-%m-%d")
        if management_method:
            params["managementMethod"] = management_method

        async with aiohttp.ClientSession() as session:
            await self._get_auth_token(session)

            url = f"{self.BASE_URL}/emanifest/search" if self.token else f"{self.PUBLIC_URL}/emanifest/search"

            async with session.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Manifest search failed: {response.status}")
                    return []

    async def get_manifest_details(self, manifest_tracking_number: str) -> Optional[dict]:
        """Get detailed manifest information."""
        async with aiohttp.ClientSession() as session:
            await self._get_auth_token(session)

            url = f"{self.BASE_URL}/emanifest/manifest/{manifest_tracking_number}"

            async with session.get(
                url,
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None

    async def get_site_details(self, site_id: str) -> Optional[dict]:
        """Get details about a TSDF or generator site."""
        async with aiohttp.ClientSession() as session:
            await self._get_auth_token(session)

            async with session.get(
                f"{self.BASE_URL}/site-details/{site_id}",
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None

    async def get_incineration_volumes(
        self,
        waste_codes: list[str],
        start_date: datetime,
        end_date: datetime,
        state_code: Optional[str] = None,
    ) -> list[WasteVolumeSummary]:
        """Get waste volumes sent to incineration by waste code."""
        summaries = []

        for waste_code in waste_codes:
            for method in self.INCINERATION_METHODS:
                manifests = await self.search_manifests(
                    waste_code=waste_code,
                    start_date=start_date,
                    end_date=end_date,
                    management_method=method,
                    state_code=state_code,
                )

                if manifests:
                    total_qty = sum(m.get("quantity", 0) for m in manifests)
                    facilities = list(set(m.get("tsdfName", "") for m in manifests))

                    summaries.append(WasteVolumeSummary(
                        waste_code=waste_code,
                        waste_description=get_waste_code_description(waste_code),
                        period_start=start_date,
                        period_end=end_date,
                        total_quantity=total_qty,
                        quantity_unit="KG",
                        manifest_count=len(manifests),
                        disposal_method=f"Incineration ({method})",
                        facilities=facilities,
                    ))

        return summaries

    async def get_landfill_volumes(
        self,
        waste_codes: list[str],
        start_date: datetime,
        end_date: datetime,
        state_code: Optional[str] = None,
    ) -> list[WasteVolumeSummary]:
        """Get waste volumes sent to hazardous waste landfills."""
        summaries = []

        for waste_code in waste_codes:
            for method in self.LANDFILL_METHODS:
                manifests = await self.search_manifests(
                    waste_code=waste_code,
                    start_date=start_date,
                    end_date=end_date,
                    management_method=method,
                    state_code=state_code,
                )

                if manifests:
                    total_qty = sum(m.get("quantity", 0) for m in manifests)
                    facilities = list(set(m.get("tsdfName", "") for m in manifests))

                    summaries.append(WasteVolumeSummary(
                        waste_code=waste_code,
                        waste_description=get_waste_code_description(waste_code),
                        period_start=start_date,
                        period_end=end_date,
                        total_quantity=total_qty,
                        quantity_unit="KG",
                        manifest_count=len(manifests),
                        disposal_method=f"Landfill ({method})",
                        facilities=facilities,
                    ))

        return summaries


def get_waste_code_description(code: str) -> str:
    """Get description for a waste code."""
    from .waste_codes import WASTE_CODE_DESCRIPTIONS
    return WASTE_CODE_DESCRIPTIONS.get(code, f"Waste Code {code}")
