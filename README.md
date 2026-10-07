# Duchesne School Assistant ❤️ Charger Pride

[![Duchesne Academy of the Sacred Heart](https://img.shields.io/badge/Duchesne%20Academy-Sacred%20Heart-C8102E.svg)](https://www.duchesne.org)
[![Cross-Platform](https://img.shields.io/badge/Platform-Claude%20%7C%20Gemini%20%7C%20ChatGPT-blue.svg)](#installation--setup)
[![Zero Password](https://img.shields.io/badge/Privacy-Zero--Password%20Guarantee-success.svg)](#-privacy--security-the-zero-password-guarantee)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Welcome to the Duchesne School Assistant!**  
> An intelligent, parent-friendly companion designed exclusively for families of **Duchesne Academy of the Sacred Heart** in Houston, Texas. Whether your daughter is in Lower School (PK3–Grade 4), Middle School (Grades 5–8), or Upper School (Grades 9–12), this assistant keeps your family organized, informed, and connected with zero stress.

---

## 🌟 What the Assistant Does for Busy Parents

* ⏰ **Bell Schedules & Dismissals:** Get instant answers on morning drop-off, daily start times, lunch periods (including PK4 lunch at 10:55 AM), and division dismissal times.
* 👗 **Dress Code & Uniform Guidance:** Clarifies Mills Uniform standards, formal dress liturgy days, and Friday spirit wear rules with ease.
* 🥗 **Dining & Nutrislice Menus:** Direct links and info for Sage Dining daily menus across all divisions.
* 🛍️ **Spirit Store Recommendations:** Find official Friday spirit shirts, outerwear, uniforms, and Charger pride gear at the Duchesne Spirit Store.
* 📧 **Email & Newsletter Digest:** Paste long Friday letters or division emails to extract immediate takeaways, key dates, and actionable to-do lists.
* 📱 **Social Media Central:** Stay updated with all 12 official Duchesne social channels (athletics, arts, dance, alumnae, admissions, and campus life).
* 📅 **1-Tap Calendar Subscriptions:** Sync all school holidays and events directly to your phone or laptop calendar.

---

## 🚀 Installation & Setup

Choose the setup method that works best for you. **No coding or terminal experience is needed!**

### Method 1: Direct Sync via GitHub Link (Easiest — Under 1 Minute)

Sync the assistant directly to your favorite AI platform using this repository link:  
```
https://github.com/dvmorris/duchesne-school-assistant
```

#### 🟣 For Anthropic Claude (Web & Desktop)
1. In Claude, navigate to **Settings** > **Customize** (or **Plugins** / **Personal plug-in**).
2. Select **Add from repository** or **Add marketplace**.
3. Paste the repository URL: `https://github.com/dvmorris/duchesne-school-assistant`
4. Click **Sync**, then click **+** to enable the Duchesne School Assistant.

#### 🔵 For Google Gemini
1. Open Gemini and go to **Settings / Plugins** (or **Gem Manager**).
2. Select **Add from repository**.
3. Paste the repository URL: `https://github.com/dvmorris/duchesne-school-assistant`
4. Click **Add Skill** to install.

#### 🟢 For OpenAI ChatGPT
1. Open ChatGPT and navigate to **Skills / Customizations** (or **Explore GPTs** > **Create**).
2. Select **Import from Repository / URL**.
3. Paste the repository URL: `https://github.com/dvmorris/duchesne-school-assistant`
4. Confirm to import the assistant profile.

---

### Method 2: Drag-and-Drop / Upload ZIP (No URL Needed)

If your AI tool supports uploading project files or knowledge documents:

1. Click the green **Code** button at the top of this GitHub repository and click **Download ZIP**.
2. Extract the ZIP file on your computer.
3. Drag and drop the files (or specifically [`distribution/common/duchesne_knowledge_base.md`](distribution/common/duchesne_knowledge_base.md)) into your Claude Project, ChatGPT Custom GPT, or Gemini Gem workspace.
4. Alternatively, copy and paste the single universal prompt from [`distribution/web/universal_parent_prompt.md`](distribution/web/universal_parent_prompt.md) directly into your chat! (See our complete [Web Chat Setup Guide](distribution/web/setup_guide.md)).

---

### Method 3: 1-Tap Mobile & Laptop Calendar Subscriptions

Keep your family's personal calendar in sync with school holidays, early dismissals, and campus celebrations:

* 🍏 **Apple Calendar (iPhone, iPad & Mac):**  
  [**Subscribe in Apple Calendar (1-Click webcal://)**](webcal://portals.veracross.com/duchesne/subscribe/all_school.ics)  
  *Tap the link above on your Apple device to automatically prompt calendar subscription.*

* 📅 **Google Calendar (Android, Chromebook & Web):**  
  [**Subscribe in Google Calendar (1-Click)**](https://calendar.google.com/calendar/r?cid=https%3A%2F%2Fportals.veracross.com%2Fduchesne%2Fsubscribe%2Fall_school.ics)  
  *Opens Google Calendar and adds the live Duchesne feed to "Other calendars".*

* ✉️ **Microsoft Outlook (Desktop & Web):**  
  [**Add to Microsoft Outlook**](https://outlook.office.com/calendar/addcalendar)  
  *Select **Subscribe from web** and paste:* `https://portals.veracross.com/duchesne/subscribe/all_school.ics`

*For instructions on subscribing to personalized, student-specific family calendars, see [`distribution/common/calendar_links.md`](distribution/common/calendar_links.md).*

---

### Method 4: Advanced CLI / Developer Setup

For power users, developers, or local offline automations, the assistant includes a standalone Python suite built exclusively with the **Python standard library** (zero `pip` dependencies required):

```bash
# Clone the repository
git clone https://github.com/dvmorris/duchesne-school-assistant.git
cd duchesne-school-assistant

# Run the Veracross multi-division scanner
python3 scripts/veracross_scanner.py

# Run the school assistant system check
python3 scripts/duchesne_check.py

# Aggregate recent updates from all 12 official social channels
python3 scripts/social_aggregator.py

# Check current featured items from the Duchesne Spirit Store
python3 scripts/spirit_store_crawler.py

# Run automated distribution and manifest test suite
PYTHONPATH=. python3 -m unittest discover -s tests
```

---

## 🔒 Privacy & Security: The Zero-Password Guarantee

Your family's privacy and online security are paramount. The Duchesne School Assistant operates under a strict, non-negotiable **Zero-Password Policy**:

1. **Never Share Passwords:** The assistant will **NEVER** ask for, accept, or store your Veracross, Toddle, or Magnus Health passwords.
2. **No Automated Credential Access:** The assistant does not execute background logins or scrape protected student academic records behind authenticated portals.
3. **Safe Content Summarization:** To review personalized communications (such as a teacher's message or Friday letter), simply copy and paste the text directly into your conversation.
4. **Local & Secure:** All configuration options and local tools run entirely on your device with no unauthorized data transmission.

---

## 🏫 Duchesne Quick Reference

### Campus Information
* **Address:** 10202 Memorial Dr, Houston, TX 77024
* **Main Office Phone:** (713) 468-8211
* **Website:** [duchesne.org](https://www.duchesne.org)
* **Sacred Heart Goals:**
  1. A personal and active faith in God
  2. A deep respect for intellectual values
  3. A social awareness which impels to action
  4. The building of community as a Christian value
  5. Personal growth in an atmosphere of wise freedom

### Essential Portals
* 🌐 **Veracross Parent Portal:** [portals.veracross.com/duchesne/parent](https://portals.veracross.com/duchesne/parent)
* ⚙️ **Communication Settings:** [Veracross Email & Notification Preferences](https://portals.veracross.com/duchesne/parent) *(Profile > Manage School Communication)*
* 🎒 **Toddle LMS (Lower School):** [web.toddleapp.com](https://web.toddleapp.com)
* 🍽️ **Nutrislice Menus (Sage Dining):** [duchesne.nutrislice.com](https://duchesne.nutrislice.com/)
* 🛍️ **Duchesne Spirit Store:** [duchesnespiritstore.square.site](https://duchesnespiritstore.square.site/)
* 👗 **Mills Uniform Company:** [millswear.com](https://www.millswear.com) *(School Code: 3550)*

### Official Social Media Channels (12 Channels)
* **Instagram:**
  * Main Campus: [@duchesnehouston](https://www.instagram.com/duchesnehouston)
  * Athletics: [@duchesneathletics](https://www.instagram.com/duchesneathletics)
  * Charger Girls Dance: [@chargergirlsdance](https://www.instagram.com/chargergirlsdance/)
  * Fine Arts: [@duchesne_arts](https://www.instagram.com/duchesne_arts/)
  * Upper School: [@duchesneupperschool](https://www.instagram.com/duchesneupperschool)
  * Admissions: [@duchesneadmissions](https://www.instagram.com/duchesneadmissions/)
  * Alumnae: [@duchesnealumnae](https://www.instagram.com/duchesnealumnae)
* **LinkedIn:** [Duchesne Academy of the Sacred Heart](https://www.linkedin.com/school/duchesne-academy-of-the-sacred-heart/)
* **Facebook:**
  * Official School: [Duchesne Academy Houston](https://www.facebook.com/DuchesneAcademyHouston)
  * Athletics & Campus Life: [Duchesne Athletics](https://www.facebook.com/profile.php?id=100079069373448)
  * Alumnae Association: [Duchesne Houston Alums](https://www.facebook.com/DuchesneHoustonAlums)
* **YouTube:** [@duchesneacademyofthesacred1409](https://www.youtube.com/@duchesneacademyofthesacred1409)

---

## 📄 License & Community Support

Created with ❤️ by Duchesne Academy parents for the Duchesne community. Distributed under the MIT License.
