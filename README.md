# 🏨 GuestDiary → 🐵 Mailchimp Sync

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?logo=githubactions&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

> 🔁 **Automate guest list sync from GuestDiary.com to your Mailchimp audience.**  
> This script runs daily via GitHub Actions, keeping your email marketing list fresh—without exposing your API keys.

---

## ✨ Features

- ✅ Fetches **checked‑out guests** from GuestDiary’s Diary API
- 🧹 Filters out **temporary / proxy emails** (e.g., `@guest.booking.com`)
- 📬 **Upserts** contacts to Mailchimp using **Batch Operations**
- 🔐 **Zero credentials in code** – all keys passed as GitHub Secrets
- ⏰ Scheduled daily (or manually triggered) via **GitHub Actions**
- 📋 Detailed logging for monitoring and debugging

---

## 📦 Project Structure

```
.
├── sync_guests.py          # Main Python script
├── requirements.txt        # Python dependencies
├── .github/
│   └── workflows/
│       └── sync.yml        # GitHub Actions workflow
└── README.md               # You are here!
```

---

## 🚀 Quick Start (Local Testing)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/guestdiary-mailchimp-sync.git
   cd guestdiary-mailchimp-sync
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables** (use a `.env` file or export directly)
   ```bash
   export GUESTDIARY_API_URL="https://api.guestdiary.com/v1/..."
   export GUESTDIARY_API_KEY="your_guestdiary_key"
   export MAILCHIMP_API_KEY="your_mailchimp_key"
   export MAILCHIMP_SERVER_PREFIX="us19"
   export MAILCHIMP_AUDIENCE_ID="abc123def456"
   # Optional: how many days back to fetch
   export DAYS_BACK="1"
   ```

4. **Run the script**
   ```bash
   python sync_guests.py
   ```

---

## ⚙️ Configuration (GitHub Actions)

All sensitive values are stored as **GitHub Secrets**.

| Secret Name | Description |
|-------------|-------------|
| `GUESTDIARY_API_URL` | Full endpoint URL for your property’s reservations |
| `GUESTDIARY_API_KEY` | API key / token from GuestDiary Dashboard |
| `MAILCHIMP_API_KEY` | Mailchimp API key (starts with a server suffix, e.g. `...-us19`) |
| `MAILCHIMP_SERVER_PREFIX` | Server prefix (e.g., `us19`) – part of your Mailchimp URL |
| `MAILCHIMP_AUDIENCE_ID` | Unique ID of your Mailchimp audience/list |
| *(Optional)* `DAYS_BACK` | **Repository variable** – number of past days to fetch (default: `1`) |

### 🔧 Setting Up Secrets

1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret** and add each key/value pair.
3. (Optional) Add `DAYS_BACK` as a **Repository variable**.

---

## 🕒 Automation Schedule

The GitHub Actions workflow (`sync.yml`) is configured to run:

- **Every day at 2:00 AM UTC** (`cron: '0 2 * * *'`)
- **Manually** via the **Actions** tab → `Run workflow`

You can change the schedule by editing the `cron` expression in `.github/workflows/sync.yml`.

---

## 🛠️ Customization & Troubleshooting

### 🔍 GuestDiary API Response Format

The script assumes a JSON response like:
```json
{
  "data": [
    {
      "email_address": "guest@example.com",
      "first_name": "John",
      "last_name": "Doe"
    }
  ]
}
```

If your API uses different field names or pagination logic, adjust the parsing in `fetch_guestdiary_guests()`.

### 📧 Mailchimp Merge Fields

By default, the script uses `FNAME` and `LNAME`. If your audience uses custom merge tags, modify the `merge_fields` dictionary in `create_mailchimp_batch()`.

### 🧪 Filtering Emails

Temporary email domains are blocked by default:
- `guest.booking.com`
- `expedia.com`
- `guest.expedia.com`

You can extend the `BLOCKED_DOMAINS` set in the script to add others.

### 🪵 Viewing Logs

All script output appears in the **GitHub Actions log** for each run. You can also enable debug logging by changing the log level to `DEBUG` in `sync_guests.py`.

---

## 📄 License

MIT – Feel free to use, modify, and share.

---

## 🙌 Acknowledgements

- [GuestDiary.com](https://guestdiary.com) – Property management system
- [Mailchimp API](https://mailchimp.com/developer/) – Email marketing platform
- [Requests](https://docs.python-requests.org/) – HTTP library for Python

---

**Happy syncing!** 🎉  
*Questions or improvements? Open an issue or submit a PR.*