# Duchesne Academy Portals & Integration Details

## Portal URLs & Authentication Types

### 1. Veracross Parent Dashboard
- **URL:** `https://portals.veracross.com/duchesne/parent`
- **Auth:** Veracross Parent Account / Google Workspace SSO.
- **Key Sections:**
  - `div.announcements-wrapper`: Weekly division and all-school announcements.
  - Friday Morning Letter from Head of School: Typically published under General Announcements at ~9:00 AM Central on Fridays.
  - All-school calendar: Feed and list views for holidays, liturgies, and parent meetings.

### 2. Lower School Dashboard
- **URL:** `https://portals.veracross.com/duchesne/parent/pages/ls-page`
- **Auth:** Inherits Veracross Parent session.
- **Key Sections:**
  - Letter from Head of Lower School.
  - Lower School rolling calendar and special events (Mass days, Dress Uniform days).
  - Reminders: Uniform guidelines, drop-off/pick-up adjustments.

### 3. Toddle Learning Management System (LMS)
- **Base Course URL:** `https://web.toddleapp.com/platform/116643011487614044/courses`
- **Target Classroom:** `PK4 Homeroom (PK4HR-01)`
- **Key Tabs:**
  - **Home Tab:** Primary anchor. Contains the weekly classroom newsletter (often formatted as an infographic, image, or PDF).
    - *Sophie's Space:* Sacred Heart Goals (I: Personal and active faith in God; II: Deep respect for intellectual values; III: Social awareness which impels to action; IV: Building of community as a Christian value; V: Personal growth in an atmosphere of wise freedom).
    - *Learning Focus:* Weekly academic topics (Numbers/Counting, Science/Social Studies, Literacy/Phonics).
    - *Important Reminders:* Photo requests (4x6 family photo), library days (return books/checkout), special events.
  - **Announcements Tab:** Direct teacher announcements.
  - **Portfolio Tab:** Photo updates of student projects and daily activities.

### 4. Nutrislice Lunch Menus
- **URL:** `https://duchesne.nutrislice.com/menu/lower-school/lunch`
- **API Endpoint:** `https://duchesne.nutrislice.com/menu/api/weeks/school/lower-school/menu-type/lunch/YYYY/MM/DD/`
- **Auth:** None (Public).
- **Data Extracted:** Daily entrees, sides, vegetarian options, and allergen flags.

### 5. Supplemental Portals
- **Fine Arts Dashboard:** `https://portals.veracross.com/duchesne/parent/pages/fa-page`
- **Extended Programs Dashboard:** `https://portals.veracross.com/duchesne/parent/pages/ep-page`
- **Instagram:** `https://www.instagram.com/duchesnehouston`
