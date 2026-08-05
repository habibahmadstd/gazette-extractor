# Gazette Result Extractor — Web App

Upload gazette + roll numbers → get results in one click. No Python needed for users.

---

## How to Deploy (One Time Setup)

### Step 1 — Create a free GitHub account
- Go to https://github.com
- Sign up with your email
- Verify your email

### Step 2 — Create a new GitHub repository
- Click the **+** button (top right) → **New repository**
- Name it: `gazette-extractor`
- Set it to **Public**
- Click **Create repository**

### Step 3 — Upload the files
In your new repository, click **Add file → Upload files** and upload:
- `app.py`
- `requirements.txt`
- `README.md`

Click **Commit changes**.

### Step 4 — Deploy on Streamlit Cloud
- Go to https://streamlit.io/cloud
- Sign in with your GitHub account
- Click **New app**
- Select your repository: `gazette-extractor`
- Main file path: `app.py`
- Click **Deploy**

Wait 1-2 minutes. You will get a public link like:
`https://yourname-gazette-extractor.streamlit.app`

**Share this link with anyone — they just open it in a browser!**

---

## How Users Use It

1. Open the link in any browser (Chrome, Edge, Firefox)
2. Upload the gazette file (PDF or Excel)
3. Upload the roll numbers Excel file (roll numbers in column A)
4. If needed, adjust "Columns per student" in the sidebar (default 5)
5. Click **Extract Results**
6. View results on screen and click **Download Results as Excel**

---

## Files in This Project

| File | Purpose |
|------|---------|
| `app.py` | The web application code |
| `requirements.txt` | Libraries Streamlit Cloud will install automatically |
| `README.md` | This guide |
