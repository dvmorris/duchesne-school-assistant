import csv
import io
import os
import re
from dataclasses import dataclass
from typing import List, Dict, Union, Any

@dataclass
class ParentContact:
    first_name: str
    last_name: str
    email: str
    phone: str
    child_name: str
    child_grade: str
    address: str = ""

def parse_directory_roster(roster_data: Union[List[Dict[str, Any]], str]) -> List[ParentContact]:
    contacts = []
    if isinstance(roster_data, list):
        for entry in roster_data:
            contacts.append(ParentContact(
                first_name=entry.get("first_name", "").strip(),
                last_name=entry.get("last_name", "").strip(),
                email=entry.get("email", "").strip(),
                phone=entry.get("phone", "").strip(),
                child_name=entry.get("child_name", "").strip(),
                child_grade=entry.get("child_grade", "").strip(),
                address=entry.get("address", "").strip()
            ))
    elif isinstance(roster_data, str):
        # Fallback HTML parser looking for parent cards
        parent_cards = re.findall(r'<div class="parent-entry"[^>]*>(.*?)</div>', roster_data, re.DOTALL)
        for card in parent_cards:
            fn = re.search(r'class="first-name">([^<]+)', card)
            ln = re.search(r'class="last-name">([^<]+)', card)
            em = re.search(r'mailto:([^\"]+)', card)
            ph = re.search(r'tel:([^\"]+)', card)
            ch = re.search(r'class="student-name">([^<]+)', card)
            gr = re.search(r'class="grade">([^<]+)', card)
            if fn and ln:
                contacts.append(ParentContact(
                    first_name=fn.group(1).strip(),
                    last_name=ln.group(1).strip(),
                    email=em.group(1).strip() if em else "",
                    phone=ph.group(1).strip() if ph else "",
                    child_name=ch.group(1).strip() if ch else "",
                    child_grade=gr.group(1).strip() if gr else ""
                ))
    return contacts

def generate_vcard_content(contacts: List[ParentContact]) -> str:
    cards = []
    for c in contacts:
        card = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{c.first_name} {c.last_name}".strip(),
            f"N:{c.last_name};{c.first_name};;;",
            f"EMAIL;TYPE=INTERNET,HOME:{c.email}" if c.email else "",
            f"TEL;TYPE=CELL:{c.phone}" if c.phone else "",
            "ORG:Duchesne Academy of the Sacred Heart",
            f"TITLE:Parent of {c.child_name} ({c.child_grade})" if c.child_name else "TITLE:Duchesne Parent",
            f"NOTE:Student: {c.child_name} | Grade: {c.child_grade} | Duchesne Academy Parent Directory",
            f"ADR;TYPE=HOME:;;{c.address};;;;" if c.address else "",
            "END:VCARD"
        ]
        cards.append("\n".join([line for line in card if line]))
    return "\n\n".join(cards) + "\n"

def generate_google_contacts_csv(contacts: List[ParentContact]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Given Name", "Family Name",
        "E-mail 1 - Type", "E-mail 1 - Value",
        "Phone 1 - Type", "Phone 1 - Value",
        "Organization 1 - Name", "Organization 1 - Title",
        "Notes", "Address 1 - Formatted"
    ])

    for c in contacts:
        writer.writerow([
            f"{c.first_name} {c.last_name}".strip(),
            c.first_name,
            c.last_name,
            "Home", c.email,
            "Mobile", c.phone,
            "Duchesne Academy of the Sacred Heart",
            f"Parent of {c.child_name} ({c.child_grade})" if c.child_name else "Duchesne Parent",
            f"Student: {c.child_name} | Grade: {c.child_grade}",
            c.address
        ])
    return output.getvalue()

def export_contacts(contacts: List[ParentContact], vcf_path: str, csv_path: str) -> None:
    vcf_content = generate_vcard_content(contacts)
    parent_dir_vcf = os.path.dirname(os.path.abspath(vcf_path))
    if parent_dir_vcf:
        os.makedirs(parent_dir_vcf, exist_ok=True)
    with open(vcf_path, "w", encoding="utf-8") as f:
        f.write(vcf_content)

    csv_content = generate_google_contacts_csv(contacts)
    parent_dir_csv = os.path.dirname(os.path.abspath(csv_path))
    if parent_dir_csv:
        os.makedirs(parent_dir_csv, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
