import os
import tempfile
import unittest
from scripts.directory_exporter import (
    ParentContact,
    parse_directory_roster,
    generate_vcard_content,
    generate_google_contacts_csv,
    export_contacts
)

class TestDirectoryExporter(unittest.TestCase):
    def test_generate_vcard_content(self):
        contact = ParentContact(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="(713) 555-0123",
            child_name="Clara Davis",
            child_grade="PK4",
            address="10202 Memorial Dr, Houston, TX 77024"
        )
        vcard = generate_vcard_content([contact])
        self.assertIn("BEGIN:VCARD", vcard)
        self.assertIn("VERSION:3.0", vcard)
        self.assertIn("FN:Jane Doe", vcard)
        self.assertIn("N:Doe;Jane;;;", vcard)
        self.assertIn("EMAIL;TYPE=INTERNET,HOME:jane.doe@example.com", vcard)
        self.assertIn("TEL;TYPE=CELL:(713) 555-0123", vcard)
        self.assertIn("ORG:Duchesne Academy of the Sacred Heart", vcard)
        self.assertIn("TITLE:Parent of Clara Davis (PK4)", vcard)
        self.assertIn("NOTE:Student: Clara Davis | Grade: PK4 | Duchesne Academy Parent Directory", vcard)
        self.assertIn("ADR;TYPE=HOME:;;10202 Memorial Dr;Houston;TX;77024;USA", vcard)
        self.assertIn("END:VCARD", vcard)

    def test_escape_vcard(self):
        from scripts.directory_exporter import escape_vcard
        self.assertEqual(escape_vcard("Hello, World; Testing\\Slash\nNewline"), "Hello\\, World\\; Testing\\\\Slash\\nNewline")
        self.assertEqual(escape_vcard(""), "")

    def test_format_vcard_adr(self):
        from scripts.directory_exporter import format_vcard_adr
        # Full standard address
        self.assertEqual(
            format_vcard_adr("10202 Memorial Dr, Houston, TX 77024"),
            "ADR;TYPE=HOME:;;10202 Memorial Dr;Houston;TX;77024;USA"
        )
        # Address with apartment/suite
        self.assertEqual(
            format_vcard_adr("10202 Memorial Dr, Suite 200, Houston, TX 77024"),
            "ADR;TYPE=HOME:;;10202 Memorial Dr\\, Suite 200;Houston;TX;77024;USA"
        )
        # Fallback simple street
        self.assertEqual(
            format_vcard_adr("10202 Memorial Dr"),
            "ADR;TYPE=HOME:;;10202 Memorial Dr;;;;"
        )

    def test_generate_vcard_content_escaping(self):
        contact = ParentContact(
            first_name="Jane, Jr.",
            last_name="Doe; Smith",
            email="jane@example.com",
            phone="123",
            child_name="Clara\nLily",
            child_grade="PK4"
        )
        vcard = generate_vcard_content([contact])
        self.assertIn("FN:Jane\\, Jr. Doe\\; Smith", vcard)
        self.assertIn("N:Doe\\; Smith;Jane\\, Jr.;;;", vcard)
        self.assertIn("NOTE:Student: Clara\\nLily | Grade: PK4 | Duchesne Academy Parent Directory", vcard)

    def test_generate_vcard_content_minimal(self):
        contact = ParentContact(
            first_name="John",
            last_name="Smith",
            email="",
            phone="",
            child_name="",
            child_grade=""
        )
        vcard = generate_vcard_content([contact])
        self.assertIn("BEGIN:VCARD", vcard)
        self.assertIn("VERSION:3.0", vcard)
        self.assertIn("FN:John Smith", vcard)
        self.assertIn("N:Smith;John;;;", vcard)
        self.assertIn("TITLE:Duchesne Parent", vcard)
        self.assertNotIn("EMAIL;", vcard)
        self.assertNotIn("TEL;", vcard)
        self.assertNotIn("ADR;", vcard)
        self.assertIn("END:VCARD", vcard)

    def test_generate_google_contacts_csv(self):
        contact = ParentContact(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="(713) 555-0123",
            child_name="Clara Davis",
            child_grade="PK4",
            address="10202 Memorial Dr, Houston, TX 77024"
        )
        csv_content = generate_google_contacts_csv([contact])
        self.assertIn("Given Name,Family Name", csv_content)
        self.assertIn("Jane,Doe", csv_content)
        self.assertIn("jane.doe@example.com", csv_content)
        self.assertIn("(713) 555-0123", csv_content)
        self.assertIn("Parent of Clara Davis (PK4)", csv_content)
        self.assertIn("10202 Memorial Dr, Houston, TX 77024", csv_content)

    def test_parse_directory_roster_dict_list(self):
        roster_data = [
            {
                "first_name": "  Jane  ",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
                "phone": "(713) 555-0123",
                "child_name": "Clara Davis",
                "child_grade": "PK4",
                "address": "10202 Memorial Dr"
            },
            {
                "first_name": "Bob",
                "last_name": "Smith",
                "email": "bob@example.com",
                "phone": "",
                "child_name": "",
                "child_grade": ""
            }
        ]
        contacts = parse_directory_roster(roster_data)
        self.assertEqual(len(contacts), 2)
        self.assertEqual(contacts[0].first_name, "Jane")
        self.assertEqual(contacts[0].last_name, "Doe")
        self.assertEqual(contacts[0].email, "jane.doe@example.com")
        self.assertEqual(contacts[0].child_name, "Clara Davis")
        self.assertEqual(contacts[1].first_name, "Bob")
        self.assertEqual(contacts[1].address, "")

    def test_parse_directory_roster_html(self):
        html_data = """
        <div class="directory-list">
            <div class="parent-entry">
                <span class="first-name">Jane</span>
                <span class="last-name">Doe</span>
                <a href="mailto:jane.doe@example.com">Email</a>
                <a href="tel:7135550123">Phone</a>
                <span class="student-name">Clara Davis</span>
                <span class="grade">PK4</span>
            </div>
            <div class="parent-entry">
                <span class="first-name">Alice</span>
                <span class="last-name">Wonder</span>
                <a href="mailto:alice@example.com">Email</a>
            </div>
        </div>
        """
        contacts = parse_directory_roster(html_data)
        self.assertEqual(len(contacts), 2)
        self.assertEqual(contacts[0].first_name, "Jane")
        self.assertEqual(contacts[0].last_name, "Doe")
        self.assertEqual(contacts[0].email, "jane.doe@example.com")
        self.assertEqual(contacts[0].phone, "7135550123")
        self.assertEqual(contacts[0].child_name, "Clara Davis")
        self.assertEqual(contacts[0].child_grade, "PK4")

        self.assertEqual(contacts[1].first_name, "Alice")
        self.assertEqual(contacts[1].last_name, "Wonder")
        self.assertEqual(contacts[1].email, "alice@example.com")
        self.assertEqual(contacts[1].phone, "")

    def test_export_contacts(self):
        contact = ParentContact(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone="(713) 555-0123",
            child_name="Clara Davis",
            child_grade="PK4",
            address="10202 Memorial Dr"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            vcf_path = os.path.join(tmpdir, "contacts.vcf")
            csv_path = os.path.join(tmpdir, "contacts.csv")

            export_contacts([contact], vcf_path, csv_path)

            self.assertTrue(os.path.exists(vcf_path))
            self.assertTrue(os.path.exists(csv_path))

            with open(vcf_path, "r", encoding="utf-8") as f:
                vcf_text = f.read()
            self.assertIn("BEGIN:VCARD", vcf_text)
            self.assertIn("FN:Jane Doe", vcf_text)

            with open(csv_path, "r", encoding="utf-8") as f:
                csv_text = f.read()
            self.assertIn("Jane,Doe", csv_text)

if __name__ == "__main__":
    unittest.main()
