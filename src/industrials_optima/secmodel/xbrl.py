"""Minimal XBRL instance-document parser.

Parses the raw XBRL instance ``.xml`` filed with each 10-K / 10-Q and returns
a flat list of :class:`Fact` records carrying their period and dimensional
context (e.g. segment = United States vs International).  This is what lets the
model report *segment* figures, which the aggregated ``companyfacts`` API
strips out.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from lxml import etree


@dataclass
class Fact:
    concept: str  # local name, e.g. "OperatingIncomeLoss"
    prefix: str  # namespace prefix, e.g. "us-gaap", "cprt"
    value: Optional[float]
    unit: Optional[str]
    start: Optional[str]  # duration start (YYYY-MM-DD) or None for instant
    end: Optional[str]  # duration end or instant date
    is_instant: bool
    # dimension local-name -> member local-name
    dims: dict = field(default_factory=dict)

    @property
    def dim_key(self) -> tuple:
        return tuple(sorted(self.dims.items()))


_XBRLI = "http://www.xbrl.org/2003/instance"
_XBRLDI = "http://xbrl.org/2006/xbrldi"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _prefix_for(qname: str, nsmap: dict) -> str:
    """Turn a ``prefix:Local`` QName (from an attribute value) into its prefix's
    local alias, falling back to the raw prefix text."""
    if ":" in qname:
        return qname.split(":", 1)[0]
    return ""


def parse_instance(xml_text: str) -> list[Fact]:
    """Parse an XBRL instance document into a list of :class:`Fact`."""
    parser = etree.XMLParser(recover=True, huge_tree=True)
    root = etree.fromstring(xml_text.encode("utf-8"), parser=parser)
    if root is None:
        return []

    # ---- 1. contexts: id -> {period, dims} ---------------------------- #
    contexts: dict[str, dict] = {}
    for ctx in root.iter("{%s}context" % _XBRLI):
        cid = ctx.get("id")
        if cid is None:
            continue
        info: dict = {"dims": {}, "start": None, "end": None, "instant": None}
        period = ctx.find("{%s}period" % _XBRLI)
        if period is not None:
            inst = period.find("{%s}instant" % _XBRLI)
            if inst is not None and inst.text:
                info["instant"] = inst.text.strip()
            else:
                s = period.find("{%s}startDate" % _XBRLI)
                e = period.find("{%s}endDate" % _XBRLI)
                if s is not None and s.text:
                    info["start"] = s.text.strip()
                if e is not None and e.text:
                    info["end"] = e.text.strip()
        # explicit dimension members live in entity/segment (occasionally scenario)
        for member in ctx.iter("{%s}explicitMember" % _XBRLDI):
            dim = member.get("dimension")
            mem = (member.text or "").strip()
            if dim and mem:
                info["dims"][_local_qname(dim)] = _local_qname(mem)
        contexts[cid] = info

    # ---- 2. units: id -> measure ------------------------------------- #
    units: dict[str, str] = {}
    for unit in root.iter("{%s}unit" % _XBRLI):
        uid = unit.get("id")
        measures = [m.text for m in unit.iter("{%s}measure" % _XBRLI) if m.text]
        if uid:
            units[uid] = "/".join(_local_qname(m) for m in measures)

    # ---- 3. facts ----------------------------------------------------- #
    facts: list[Fact] = []
    for el in root.iter():
        cref = el.get("contextRef")
        if not cref:
            continue
        ctx = contexts.get(cref)
        if ctx is None:
            continue
        tag = el.tag
        if not isinstance(tag, str):
            continue
        ns = tag.split("}", 0)[0]
        prefix = _prefix_from_tag(tag, el.nsmap)
        val = _to_float(el.text, el.get("sign"), el.get("scale"), el.get("decimals"))
        uref = el.get("unitRef")
        facts.append(
            Fact(
                concept=_local(tag),
                prefix=prefix,
                value=val,
                unit=units.get(uref, uref),
                start=ctx["start"],
                end=ctx["end"] or ctx["instant"],
                is_instant=ctx["instant"] is not None,
                dims=dict(ctx["dims"]),
            )
        )
    return facts


def _local_qname(qname: str) -> str:
    """``us-gaap:OperatingIncomeLoss`` -> ``OperatingIncomeLoss``."""
    return qname.split(":", 1)[-1] if ":" in qname else qname


def _prefix_from_tag(tag: str, nsmap: dict) -> str:
    if "}" not in tag:
        return ""
    ns_uri = tag[1:].split("}", 1)[0]
    for pfx, uri in (nsmap or {}).items():
        if uri == ns_uri and pfx:
            return pfx
    # fall back to a short label derived from the URI
    if "us-gaap" in ns_uri:
        return "us-gaap"
    if "/srt" in ns_uri or ns_uri.endswith("srt"):
        return "srt"
    if "dei" in ns_uri:
        return "dei"
    return "cprt"


def _to_float(
    text: Optional[str], sign: Optional[str], scale: Optional[str], decimals: Optional[str]
) -> Optional[float]:
    if text is None:
        return None
    t = text.strip().replace(",", "")
    if t == "" or t.lower() in ("true", "false"):
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    # inline-XBRL style scale (rare in plain instances) — applied if present
    if scale:
        try:
            v *= 10 ** int(scale)
        except ValueError:
            pass
    if sign == "-":
        v = -v
    return v
