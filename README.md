# mens X machina — Website Content Guide

## File Structure

```
mensxmachina/
├── index.html            ← main page (don't edit unless changing layout)
├── data/
│   ├── news.json         ← ✏️  ADD NEWS HERE
│   ├── team.json         ← ✏️  ADD TEAM MEMBERS HERE
│   └── projects.json     ← ✏️  ADD PROJECTS HERE
└── photos/               ← 📷  DROP MEMBER PHOTOS HERE
```

---

## ➕ Adding a Project

Open `data/projects.json` and add a new object to the array:

```json
{
  "id": "proj-009",
  "title": "Project Title",
  "subtitle": "Short descriptive subtitle",
  "status": "current",
  "period": "2024 – 2027",
  "funder": "European Commission / Horizon",
  "description": "2–3 sentence description of the project goals and methods.",
  "url": "https://project-website.eu",
  "tags": ["AutoML", "Causal Discovery", "ERC"]
}
```

**`status` options:**
- `"current"` — appears in the Current tab (blue badge)
- `"past"` — appears in the Past tab (grey badge)

Both always appear in the **All** tab.

---

## ➕ Adding a News Item

Open `data/news.json` and add a new object:

```json
{
  "id": "news-006",
  "date": "2025-03-15",
  "title": "Your news title here",
  "excerpt": "A short summary of the news item (1–3 sentences).",
  "category": "general",
  "link": "#"
}
```

**`category` options:** `"general"` | `"awards"` | `"positions"`

News items are **automatically sorted newest-first** by `date`.

---

## ➕ Adding a Team Member

Open `data/team.json` and add:

```json
{
  "id": "lastname",
  "name": "Dr. Firstname Lastname",
  "role": "Postdoc Researcher",
  "group": "staff",
  "photo": "photos/lastname.jpg",
  "email": "email@example.com",
  "url": "https://their-website.com",
  "bio": "Short bio.",
  "initials": "FL",
  "color": "#1a4a7a"
}
```

**`group` options:** `"faculty"` | `"phd"` | `"staff"` | `"alumni"`

### 📷 Photos
- Drop the file into `photos/` with the exact name from the `"photo"` field
- Recommended: **200×200 px** square, JPG or PNG
- Missing photo? Falls back to a coloured initials avatar automatically

---

## 📚 Publications (BibSonomy — Automatic)

Edit these lines in the `<script>` block of `index.html`:

```javascript
const BIBSONOMY_USER = 'mensxmachina';   // ← your BibSonomy username
const BIBSONOMY_TAG  = 'mensxmachina';   // ← tag on your publications
const PUB_LIMIT      = 8;               // how many to show on homepage
```

Tag any publication in BibSonomy with your lab tag → it appears on the site automatically.

---

## 🚀 Running Locally

```bash
cd mensxmachina/
python -m http.server 8000
# open http://localhost:8000
```

---

## 🎨 Colors

All colors are CSS variables at the top of `index.html`:

```css
:root {
  --blue:   #1a4a7a;   /* primary accent */
  --blue2:  #1d5491;   /* hover states */
  --blue3:  #e8f0f9;   /* light tint backgrounds */
  --dark:   #1a2433;   /* nav, headings */
  --accent: #1a6eb5;   /* links */
}
```
