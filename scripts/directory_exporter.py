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

def escape_vcard(text: str) -> str:
    if not text:
        return ""
    s = str(text)
    s = s.replace("\\", "\\\\")
    s = s.replace(";", "\\;")
    s = s.replace(",", "\\,")
    s = s.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
    return s

def format_vcard_adr(address: str) -> str:
    if not address:
        return ""
    addr = address.strip()
    m = re.match(r'^(.*?),\s*([^,]+),\s*([A-Za-z]{2,})\s+([0-9]{5}(?:-[0-9]{4})?)(?:,\s*(.*))?$', addr)
    if m:
        street = escape_vcard(m.group(1).strip())
        city = escape_vcard(m.group(2).strip())
        state = escape_vcard(m.group(3).strip())
        zip_code = escape_vcard(m.group(4).strip())
        country = escape_vcard(m.group(5).strip()) if m.group(5) else "USA"
        return f"ADR;TYPE=HOME:;;{street};{city};{state};{zip_code};{country}"

    parts = [p.strip() for p in addr.split(",")]
    if len(parts) >= 3:
        street = escape_vcard(parts[0])
        city = escape_vcard(parts[1])
        state_zip = parts[2].split()
        if len(state_zip) >= 2:
            state = escape_vcard(state_zip[0])
            zip_code = escape_vcard(" ".join(state_zip[1:]))
        else:
            state = escape_vcard(parts[2])
            zip_code = ""
        country = escape_vcard(parts[3]) if len(parts) > 3 else "USA"
        return f"ADR;TYPE=HOME:;;{street};{city};{state};{zip_code};{country}"

    return f"ADR;TYPE=HOME:;;{escape_vcard(addr)};;;;"

def generate_vcard_content(contacts: List[ParentContact]) -> str:
    cards = []
    for c in contacts:
        fn = escape_vcard(f"{c.first_name} {c.last_name}".strip())
        n_last = escape_vcard(c.last_name)
        n_first = escape_vcard(c.first_name)
        org = escape_vcard("Duchesne Academy of the Sacred Heart")
        title_text = f"Parent of {c.child_name} ({c.child_grade})" if c.child_name else "Duchesne Parent"
        title = escape_vcard(title_text)
        note_text = f"Student: {c.child_name} | Grade: {c.child_grade} | Duchesne Academy Parent Directory"
        note = escape_vcard(note_text)
        adr_line = format_vcard_adr(c.address) if c.address else ""

        card = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{fn}",
            f"N:{n_last};{n_first};;;",
            f"EMAIL;TYPE=INTERNET,HOME:{c.email}" if c.email else "",
            f"TEL;TYPE=CELL:{c.phone}" if c.phone else "",
            f"ORG:{org}",
            f"TITLE:{title}",
            f"NOTE:{note}",
            adr_line,
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
