# 🧠 Memoraid — AI Memory Support for People with Dementia

 
> An AI-powered assistive tool that helps dementia patients recognize faces and stay on top of daily reminders — built with empathy, designed for the elderly.

---

## 📸 Screenshots

### Patient View — Face Recognition
![Patient Assistant](screenshots/Patient%20assistant.png)

### Caregiver Login
![Caregiver Login](screenshots/caregiver%20login.png)

---

## 🧩 What is Memoraid?

Dementia affects over **55 million people worldwide**. One of its earliest and most distressing symptoms is the inability to recognize familiar faces — family members, friends, and caregivers become strangers.

**Memoraid** solves this with a two-interface system:

- 🧓 **Patient View** — A large, calm, warm interface that uses the device camera to recognize people walking in and announces who they are out loud via voice assistant.
- 👩‍⚕️ **Caregiver Dashboard** — A simple portal for caregivers and family members to register known faces and set daily reminders (medication, meals, calls).

---

## ✨ Features

### Patient Interface
- 📷 Live camera feed with AI face scanning animation
- 👤 Large identity card showing recognized person's **name**, **relationship badge**, and **match confidence**
- 🔊 **Voice announcement** — speaks the person's name and relationship aloud automatically
- ⏰ Upcoming reminders shown inline, polled every 30 seconds
- 🔔 Pop-up notification + voice when a reminder is due

### Caregiver Dashboard
- 🔒 Password-protected login from patient view
- 📤 Add a person via **photo upload** (drag & drop supported)
- 📷 Add a person via **live camera capture**
- 🔔 Add, view, and delete **scheduled reminders**
- ✅ Toast notifications instead of browser alerts
- 📅 Past reminders highlighted in red

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, FastAPI, Uvicorn |
| **Face Recognition** | DeepFace (Facenet model, cosine similarity) |
| **Image Processing** | OpenCV, NumPy |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Fonts** | Google Fonts — Nunito |
| **Storage** | JSON files (`faces_db.json`, `reminders.json`) |
| **Voice** | Web Speech API (browser-native TTS) |
| **Templates** | Jinja2 |

---

## 📁 Project Structure

```
memoraid2/
│
├── main_logic/
│   ├── __init__.py
│   ├── face_logic.py          # DeepFace recognition & face DB management
│   ├── reminder_logic.py      # CRUD operations for reminders
│   ├── faces_db.json          # Registered faces metadata
│   └── reminders.json         # Saved reminders
│
├── Static/
│   ├── script.js              # All frontend JS (recognition, reminders, UI)
│   └── style.css              # Full design system (warm, dementia-friendly)
│
├── templates/
│   ├── index.html             # Patient recognition page
│   └── dashboard.html         # Caregiver dashboard
│
├── faces/                     # Stored face images (created at runtime)
├── uploads/                   # Temporary upload buffer (cleared after processing)
├── screenshots/
│   ├── patient assistant.png
│   └── caregiver login.png
│
├── server.py                  # FastAPI app — all routes
├── requirements.txt
└── venv/
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.9 or higher
- A working webcam
- Windows / Linux / macOS

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/memoraid2.git
cd memoraid2
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Note:** DeepFace will automatically download the Facenet model weights on first run (~90MB). Make sure you have an internet connection the first time.

### 4. Run the Server

```bash
python server.py
```

### 5. Open in Browser

```
http://localhost:8001
```

---

## 🔑 Default Caregiver Password

```
@dmin123
```

> To change it, edit the `CAREGIVER_PASSWORD` variable in `server.py` line ~20.

---

## 🚀 How to Use

### As a Caregiver — Setting Up

1. Open `http://localhost:8001`
2. Click **Caregiver** in the top right and enter the password
3. On the dashboard:
   - **Add Person** — upload a clear photo of the person, enter their name and relationship (e.g. *Priya, Daughter*)
   - **Add Reminder** — set the patient's name, date/time, and a message (e.g. *Take blood pressure tablet*)
4. Log out — the patient view is now ready

### As a Patient — Using the App

1. Open `http://localhost:8001`
2. Press **▶ Start Camera**
3. Point the camera at someone — Memoraid will:
   - Show their **name and relationship** in the card on the right
   - **Speak their name aloud** ("This is Priya, your Daughter")
   - Auto-scan every **4 seconds**
4. Press **📸 Capture Now** for an immediate scan
5. Reminders appear as pop-ups with voice announcements when they are due

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Patient recognition page |
| `GET` | `/dashboard` | Caregiver dashboard |
| `POST` | `/login` | Caregiver authentication |
| `POST` | `/recognize` | Submit a frame for face recognition |
| `POST` | `/add_person` | Register a new face |
| `GET` | `/get_reminders` | Fetch all reminders |
| `POST` | `/add_reminder` | Create a new reminder |
| `POST` | `/delete_reminder` | Delete reminder by ID |

---

## 🧠 How Face Recognition Works

```
Camera Frame (JPEG)
        ↓
  Sent to /recognize via FormData (POST)
        ↓
  OpenCV decodes image → NumPy array
        ↓
  DeepFace.verify() called against every
  registered face in faces_db.json
        ↓
  Facenet model extracts 128-d face embedding
  Cosine distance calculated per face
        ↓
  Matches (distance < threshold) sorted by confidence
        ↓
  Top 3 matches returned as JSON
        ↓
  Frontend displays Name + Relationship
  Browser TTS speaks the announcement
```

---

## 🎨 Design Philosophy

Memoraid's UI was designed specifically for **elderly users with cognitive impairment**:

- **Large fonts** (16px minimum, 26px for names) — reduced reading difficulty
- **Warm cream palette** — avoids clinical coldness; reduces anxiety
- **Maximum 3 buttons** on the patient screen — minimizes cognitive load
- **Emoji in relationship badges** — faster visual parsing than text alone
- **Voice feedback** with animated bars — confirms something is happening
- **High contrast** between text and backgrounds — supports low vision
- **No dark mode** — warm white is more comforting for dementia patients

---

## 🗺️ Roadmap

| Priority | Feature | Status |
|---|---|---|
| 🔴 High | Voice announcement on recognition | ✅ Done |
| 🔴 High | Reminder notifications with TTS | ✅ Done |
| 🟡 Medium | SQLite database migration | 🔲 Planned |
| 🟡 Medium | Recognition history / logs | 🔲 Planned |
| 🟡 Medium | Family tree view | 🔲 Planned |
| 🟢 Future | Medication tracker with dosage | 🔲 Planned |
| 🟢 Future | Daily briefing ("Good morning, Ramesh") | 🔲 Planned |
| 🟢 Future | Emergency SOS button | 🔲 Planned |
| 🟢 Future | Mobile app (React Native) | 🔲 Planned |

---

## ⚠️ Known Limitations

- Face database is stored in JSON — suitable for prototyping, not production scale
- Recognition accuracy depends on photo quality and lighting
- No user session management — caregiver login is per-tab only
- `faces/` folder must not be deleted (it holds the registered face images)

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---


---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- [DeepFace](https://github.com/serengil/deepface) — face recognition framework
- [FastAPI](https://fastapi.tiangolo.com/) — modern Python web framework
- [Google Fonts — Nunito](https://fonts.google.com/specimen/Nunito) — accessible, rounded typeface
- [OpenCV](https://opencv.org/) — image processing

---

<div align="center">
  <strong>Memoraid</strong> — Because every face deserves to be remembered. 🧠💛
</div>
