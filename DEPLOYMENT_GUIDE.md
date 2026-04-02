# Deployment Guide — AI-Pass Analysis Studio

This guide walks you through pushing the project to GitHub and deploying it live on Streamlit Community Cloud. Follow each step in order.

---

## Part 1: Push to GitHub

### Step 1 — Install Git (if not already installed)

```bash
git --version
```

If not installed, download from https://git-scm.com/downloads

### Step 2 — Create a GitHub Repository

1. Go to https://github.com/new
2. Repository name: `AI-pass-Analysis-Studio`
3. Set it to **Public**
4. Do NOT initialize with README (we already have one)
5. Click **Create repository**

### Step 3 — Initialize and Push

Open your terminal, navigate to the project folder, and run:

```bash
cd /path/to/AI-pass_Uday

# Initialize git
git init

# Add all files
git add .

# Create the first commit
git commit -m "Initial commit: AI-Pass Analysis Studio - complete Streamlit app"

# Set the main branch
git branch -M main

# Add your GitHub repo as remote (replace YOUR_USERNAME with your actual GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/AI-pass-Analysis-Studio.git

# Push to GitHub
git push -u origin main
```

If prompted for credentials, use your GitHub username and a **Personal Access Token** (not your password).

### How to Create a Personal Access Token (if needed)

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name like "AI-Pass Deploy"
4. Select scopes: `repo` (full control)
5. Click "Generate token"
6. Copy the token — use it as your password when pushing

---

## Part 2: Deploy on Streamlit Community Cloud

### Step 1 — Go to Streamlit Cloud

1. Open https://share.streamlit.io
2. Click **Sign in with GitHub**
3. Authorize Streamlit to access your GitHub account

### Step 2 — Create a New App

1. Click **"New app"** (top-right button)
2. Fill in the form:
   - **Repository**: `YOUR_USERNAME/AI-pass-Analysis-Studio`
   - **Branch**: `main`
   - **Main file path**: `app.py`
3. Click **"Deploy!"**

### Step 3 — Wait for Deployment

- Streamlit will install the packages from `requirements.txt` automatically
- Build usually takes 2-5 minutes
- Once done, you get a live URL like: `https://your-app-name.streamlit.app`

### Step 4 — Verify

1. Open the live URL
2. Click "Load Sample Dataset" on the Home page
3. Navigate through all sections: Data Profiling, Analysis Engine, Insights, Visualizations, Export
4. Try uploading a different CSV to confirm it works with custom data too

---

## Part 3: Update the README with Live Links

After deployment, go back to your GitHub repo and edit `README.md`:

1. Replace `_[Add your Streamlit Cloud URL here after deployment]_` with your actual Streamlit app URL
2. Replace `_[Add your GitHub repo URL here]_` with your GitHub repo URL
3. Commit the change

You can do this directly on GitHub's web interface or via terminal:

```bash
# Edit README.md with your URLs, then:
git add README.md
git commit -m "Add live demo and repo links to README"
git push
```

---

## Troubleshooting

**"ModuleNotFoundError" on Streamlit Cloud:**
- Make sure `requirements.txt` is in the root of your repo (not inside a subfolder)
- Check that all package names are spelled correctly

**App crashes on load:**
- Check the Streamlit Cloud logs (click "Manage app" → "Logs" in the bottom-right corner)
- Most common issue: a file path that works locally but not on the cloud. The app already uses relative paths, so this should not happen.

**"No module named streamlit":**
- This means requirements.txt wasn't found. Verify it's committed and at the repo root.

**Data file not found:**
- Make sure the `data/` folder and `sample_energy_data.csv` are committed to git
- Run `git status` to check if they're tracked

**App is slow to load:**
- First load after deploy takes longer (cold start). Subsequent loads are faster.
- The app uses `@st.cache_data` for data loading, so repeated interactions are fast.

---

## What to Submit

Once deployed, submit these three things:

1. **Live app link**: `https://your-app-name.streamlit.app`
2. **GitHub repo link**: `https://github.com/YOUR_USERNAME/AI-pass-Analysis-Studio`
3. **README**: Already included in the repo with all required sections

---

That's it! The project is complete and ready for review.
