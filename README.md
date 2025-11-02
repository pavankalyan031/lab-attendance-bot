# 📌 Lab Attendance Bot

🤖 A **Telegram bot** that automates lab attendance submissions by directly sending responses to a **Google Form**.
Built with **Python** and **python-telegram-bot**.

---

## 🚀 Features

* Collects:

  * Full Name
  * Roll Number
  * Gender
  * Batch
  * Phone Number
  * Date (Auto-increment for multi-day submissions)
  * Time In / Out
  * Remarks
* Submits responses directly to Google Forms.
* Multi-day attendance with **automatic date increment**.
* Options to **Edit, Cancel, or Confirm** before submission.
* Created by: **Vairagade Pavan Kalyan 🚀**

---

## 🛠️ Tech Stack

* [Python 3.11+](https://www.python.org/)
* [python-telegram-bot](https://python-telegram-bot.org/)
* [Requests](https://docs.python-requests.org/)

---

## 📂 Project Structure

```
lab-attendance-bot/
 ├── main.py
 ├── requirements.txt
 ├── Procfile
 └── submissions.json   # auto-created by bot
```

---

## ⚙️ Installation (Local)

1. Clone the repository:

   ```bash
   git clone https://github.com/vaira/lab-attendance-bot.git
   cd lab-attendance-bot
   ```
2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Linux/Mac
   venv\Scripts\activate      # On Windows
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Run the bot:

   ```bash
   python main.py
   ```

---

## 🌍 Deployment

This project is ready to deploy on **Render** (free hosting).

1. Push your code to GitHub.
2. Go to [Render](https://render.com/).
3. Create a **New Web Service** → Connect to this repo.
4. Add environment variable:

   * `BOT_TOKEN = your-telegram-bot-token`
5. Set **Start Command**:

   ```bash
   python main.py
   ```
6. Deploy 🚀

---

## 🔑 Environment Variables

| Key        | Value (example)                                  |
| ---------- | ------------------------------------------------ |
| BOT\_TOKEN | `your-telegram-bot-token` |

---

## 📜 License

This project is licensed under the **MIT License**.
Feel free to use and modify with attribution.

---

## ✨ Author

👨‍💻 **Pavan Kalyan**
🚀 Telegram Lab Automation Bot Developer
