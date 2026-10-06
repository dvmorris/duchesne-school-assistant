import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

DIVISION_MAP = {
    "pk3": "lower_school", "pk4": "lower_school", "k": "lower_school", "kindergarten": "lower_school",
    "1": "lower_school", "2": "lower_school", "3": "lower_school", "4": "lower_school",
    "ls": "lower_school", "lower": "lower_school", "lower_school": "lower_school",
    "5": "middle_school", "6": "middle_school", "7": "middle_school", "8": "middle_school",
    "ms": "middle_school", "middle": "middle_school", "middle_school": "middle_school",
    "9": "upper_school", "10": "upper_school", "11": "upper_school", "12": "upper_school",
    "us": "upper_school", "upper": "upper_school", "upper_school": "upper_school"
}

@dataclass
class ChildProfile:
    first_name: str
    last_name: str
    division: str
    grade: str
    homeroom_advisor: str = ""
    student_id: str = ""
    lms: str = "toddle"
    toddle_class_id: Optional[str] = None

@dataclass
class FamilyProfile:
    family_id: str = ""
    children: List[ChildProfile] = field(default_factory=list)
    active_dashboards: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=lambda: {
        "include_lunch_menus": True,
        "include_athletics": True,
        "include_fine_arts": True,
        "auto_audit_communications": True
    })

def normalize_division(grade_or_div: str) -> str:
    cleaned = grade_or_div.strip().lower()
    return DIVISION_MAP.get(cleaned, "lower_school")

def infer_dashboards_for_divisions(divisions: List[str], preferences: Optional[Dict[str, Any]] = None) -> List[str]:
    prefs = preferences or {}
    dashboards = ["all_school", "parent_association"]
    norm_divisions = {normalize_division(d) for d in divisions}

    for div in norm_divisions:
        if div not in dashboards:
            dashboards.append(div)

    if prefs.get("include_fine_arts", True) and "fine_arts" not in dashboards:
        dashboards.append("fine_arts")
    if prefs.get("include_athletics", True) and "athletics" not in dashboards:
        dashboards.append("athletics")
    if prefs.get("include_extended_programs", False) and "extended_programs" not in dashboards:
        dashboards.append("extended_programs")

    return dashboards

def save_profile(profile: FamilyProfile, filepath: str) -> None:
    dirname = os.path.dirname(os.path.abspath(filepath))
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    data = asdict(profile)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_profile(filepath: str) -> FamilyProfile:
    if not os.path.exists(filepath):
        return FamilyProfile()
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    children = [ChildProfile(**c) for c in data.get("children", [])]
    return FamilyProfile(
        family_id=data.get("family_id", ""),
        children=children,
        active_dashboards=data.get("active_dashboards", []),
        preferences=data.get("preferences", {})
    )
