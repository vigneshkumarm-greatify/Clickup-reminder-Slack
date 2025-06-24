# 🚀 Free Deployment Guide

## 🆓 Best Free Options (Ranked by Ease)

### **1. 🚀 Railway (Recommended - Easiest)**
**Free tier**: 500 hours/month + $5 credit monthly

**Steps:**
1. **Push to GitHub** (ensure `.env` is in `.gitignore`)
2. **Deploy**:
   - Go to [Railway](https://railway.app)
   - Click "New Project" → "Deploy from GitHub"
   - Select your repository
3. **Add Environment Variables** in Railway dashboard:
   ```
   OPENAI_API_KEY=your_openai_key
   SLACK_BOT_TOKEN=xoxb-your-slack-token
   SLACK_CHANNEL_ID=C1234567890
   CLICKUP_API_KEY=your_clickup_key
   CLICKUP_TEAM_ID=your_team_id (if using multi-list)
   ```
4. **Setup Cron**:
   - Add **Cron** plugin to your project
   - Schedule: `0 9 * * 1-5` (weekdays 9 AM UTC)
   - Command: `python main.py`
5. **Deploy** and monitor logs

---

### **2. 🐙 GitHub Actions (100% Free)**
**Free tier**: 2000 minutes/month (unlimited for public repos)

**Steps:**
1. **Add secrets** to your GitHub repo:
   - Go to Settings → Secrets and variables → Actions
   - Add all environment variables as secrets

2. **Create workflow file** `.github/workflows/clickup-reminder.yml`:
   ```yaml
   name: ClickUp Reminder Bot
   
   on:
     schedule:
       - cron: '0 9 * * 1-5'  # Weekdays 9 AM UTC
     workflow_dispatch:  # Manual trigger
   
   jobs:
     run-bot:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
             
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
             
         - name: Run ClickUp Bot
           env:
             OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
             SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
             SLACK_CHANNEL_ID: ${{ secrets.SLACK_CHANNEL_ID }}
             CLICKUP_API_KEY: ${{ secrets.CLICKUP_API_KEY }}
             CLICKUP_TEAM_ID: ${{ secrets.CLICKUP_TEAM_ID }}
           run: python main.py
   ```

3. **Push and test**:
   - Commit the workflow file
   - Test manually: Actions → ClickUp Reminder Bot → Run workflow

---

### **3. 🟢 Render (Good Alternative)**
**Free tier**: 750 hours/month

**Steps:**
1. **Create account** at [Render](https://render.com)
2. **Deploy**:
   - New → Cron Job
   - Connect GitHub repository
   - Command: `python main.py`
   - Schedule: `0 9 * * 1-5`
3. **Add environment variables** in Render dashboard
4. **Deploy**

---

### **4. ☁️ Heroku Scheduler (Limited)**
**Free tier**: Discontinued for new users, but existing users get 550-1000 hours

**Steps** (if you have access):
1. **Deploy to Heroku**:
   ```bash
   heroku create your-clickup-bot
   git push heroku main
   ```
2. **Add environment variables**:
   ```bash
   heroku config:set OPENAI_API_KEY=your_key
   heroku config:set SLACK_BOT_TOKEN=your_token
   # ... add all variables
   ```
3. **Add Heroku Scheduler addon**:
   ```bash
   heroku addons:create scheduler:standard
   heroku addons:open scheduler
   ```
4. **Configure job**: `python main.py` at `0 9 * * 1-5`

---

### **5. 🔥 Firebase Functions (Advanced)**
**Free tier**: 2M invocations/month

**Setup** (requires modification):
- Convert to Cloud Function
- Use Cloud Scheduler for cron
- More complex but very reliable

---

## 📋 **Quick Setup Checklist**

### **For Railway (Easiest)**:
- [ ] Code pushed to GitHub
- [ ] `.env` in `.gitignore`
- [ ] Railway account created
- [ ] Project deployed from GitHub
- [ ] Environment variables added
- [ ] Cron plugin added with `0 9 * * 1-5`
- [ ] First run tested

### **For GitHub Actions (Most Reliable)**:
- [ ] All environment variables added as GitHub secrets
- [ ] Workflow file created in `.github/workflows/`
- [ ] Workflow tested manually
- [ ] Schedule verified (runs weekdays only)

---

## 🔧 **Post-Deployment**

### **Test Your Deployment**:
1. **Manual trigger** (if available)
2. **Check logs** for errors
3. **Verify Slack message** arrives
4. **Monitor for a few days**

### **Monitor Performance**:
- **Railway**: View logs in dashboard
- **GitHub Actions**: Check Actions tab
- **Render**: Monitor in dashboard

### **Troubleshooting**:
- **No messages**: Check environment variables
- **API errors**: Verify all tokens are correct
- **Wrong time**: Confirm timezone (use UTC in cron)
- **Weekend runs**: Ensure weekday logic is working

---

## 💰 **Cost Comparison**

| Platform | Free Tier | Best For |
|----------|-----------|----------|
| **Railway** | 500hrs + $5/month | Easiest setup |
| **GitHub Actions** | 2000 min/month | Most reliable |
| **Render** | 750 hours/month | Good alternative |
| **Heroku** | Limited availability | Legacy projects |

**Recommendation**: Start with **Railway** for ease, switch to **GitHub Actions** if you need more reliability or hit limits. 