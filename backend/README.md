# AI-Powered Interview System

A complete, prototype virtual interview automation platform with
real-time proctoring, AI-generated questions, automated speech-to-text
evaluation, webcam monitoring, and a full analytics dashboard.

------------------------------------------------------------------------

#  Table of Contents

1.  Overview\
2.  Features\
3.  System Architecture\
4.  Technology Stack\
5.  Folder Structure\
6.  Installation Guide\
7.  How to Run the Application\
8.  How the System Works (Detailed)\
9.  Database Schema\
10. API Endpoints\
11. Frontend Workflow\
12. Known Requirements & Browser Notes\
13. Troubleshooting\
14. Future Enhancements

------------------------------------------------------------------------

#  1. Overview

This AI-powered interview system automates the entire interview
lifecycle---from candidate registration to real-time recording, question
generation, proctoring, answer capture, and admin dashboard analytics.

It uses:

-   **Flask backend**\
-   **Speech Recognition (browser-based)**\
-   **Webcam-based proctoring (optional face detection)**\
-   **SQLite database**\
-   **Dynamic AI or fallback local question generator**\
-   **Structured Q&A storage for evaluation**

------------------------------------------------------------------------

#  2. Features

###  Candidate Registration

Users register with name, email, and subject. A unique session ID is
created.

### Dynamic Question Generation

Questions are fetched from: - `question_generator.py` (if available)\
- OR a fallback question bank (`question_bank.json`)

### Automated AI Interview Flow

-   Countdown timer\
-   Auto-speech playback of questions\
-   Live speech-to-text transcription\
-   Next-question automation\
-   Retry, repeat, and playback controls

###  Real-Time Proctoring

Every few seconds, snapshots are sent to the server for: - Face
detection (if module exists)\
- Snapshot saving for auditing

###  Admin Dashboard

-   List of all interview sessions\
-   All answers given by candidates\
-   Download webcam snapshots\
-   Time history of each answer

###  Robust Error Handling

-   Missing files auto-generated\
-   Database auto-initialized\
-   Fallback question list\
-   JSON/Form flexible parsing to avoid frontend errors

------------------------------------------------------------------------

#  3. System Architecture

     ┌───────────────────────────────┐
     │           Frontend            │
     │  HTML + CSS + JavaScript      │
     │  - SpeechRecognition API       │
     │  - Webcam (getUserMedia)       │
     │  - Proctoring Snapshots        │
     └──────────────┬────────────────┘
                    │ AJAX (Fetch API)
     ┌──────────────┴────────────────┐
     │             Flask API          │
     │  - /register                   │
     │  - /interview/<session_id>     │
     │  - /get_question               │
     │  - /submit_answer              │
     │  - /proctor                    │
     │  - /dashboard                  │
     └──────────────┬────────────────┘
                    │ SQLite
     ┌──────────────┴────────────────┐
     │           Database             │
     │ sessions, questions, answers   │
     └───────────────────────────────┘

------------------------------------------------------------------------

#  4. Technology Stack

### Backend

-   Python 3.x\
-   Flask\
-   SQLite\
-   Optional: OpenAI or custom question generator\
-   Optional: OpenCV + Face Detection

### Frontend

-   HTML, CSS\
-   JavaScript\
-   Web Speech API\
-   MediaDevices API

------------------------------------------------------------------------

#  5. Folder Structure

    project/
    │── app.py
    │── question_bank.json
    │── data.db
    │── uploads/                # Proctoring snapshots
    │── templates/
    │     ├── register.html
    │     ├── interview.html
    │     └── dashboard.html
    │── static/
    │     ├── css/
    │     └── js/



-----------------------------------------------------------------------------


## **6. Installation Guide**

### **Prerequisites**

Ensure the following software is installed on your system:

* **Python 3.10+**
* **pip** (Python package manager)
* **Flask** and required dependencies
* **SQLite3** (preinstalled on most systems)
* A modern browser (Chrome or Edge recommended)

### **Environment Setup**

1. Clone or download the project.
2. Open the project folder in your terminal:

   ```bash
   cd AI_Interview_System
   ```
3. Create a virtual environment:

   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:

   * Windows:

     ```bash
     venv\Scripts\activate
     ```
   * Mac/Linux:

     ```bash
     source venv/bin/activate
     ```
5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### **Database Setup**

The system automatically creates the SQLite database and required tables when first executed.
No manual setup is required unless tables need resetting.

---

## **7. How to Run the Application**

1. Activate the virtual environment (if not already activated).
2. Run the Flask server:

   ```bash
   python app.py
   ```
3. Open your browser and navigate to:

   ```
   http://127.0.0.1:5000/
   ```
4. Log in or register to access the dashboard.
5. Start a new interview session.

The server also handles:

* Question rendering
* Voice recognition pipeline
* AI follow-up question generation
* Result storage
* Session evaluation & summary generation

---

## **8. How the System Works (Detailed)**

**1. Session Initialization**

* A unique interview session ID is generated.
* Candidate details (name, subject, date/time) are stored.
* The system automatically fetches the first question.

**2. Question Delivery**

* The interviewer panel shows questions one at a time.
* The system supports:

  * Play question audio (Text-to-Speech)
  * Repeat question
  * Retry answer

 **3. Voice Recording & Speech-to-Text**

* When the user clicks **Start Recording**, the system:

  * Activates the microphone
  * Shows a blinking red indicator
  * Displays a live waveform animation
  * Streams audio to the browser’s SpeechRecognition engine

* Transcription happens in real time:

  * Interim transcript → shows partial results
  * Final transcript → saved as final answer

 **4. Automatic Follow-Up Question Generation**

After each answer:

* The backend sends (Question + Answer) to the AI engine.
* The AI analyzes:

  * Clarity
  * Technical correctness
  * Confidence level
  * Missing points
* If needed, the AI generates a **follow-up question**, which appears instantly.

**5. Completion & Submission**

* After the final question, the system:

  * Stores all Q&A in the database
  * Generates a summary
  * Creates an interview score (optional)
  * Redirects the candidate to the dashboard

 **6. Client-Side Security**

* Tab-switch detection (optional enhancement)
* Malpractice flag (eye movement, silence alerts, etc.)
* Prevent recording without user consent
* Browser compatibility checks

----------

## **9. Database Schema**

### **Table: candidates**

| Column     | Type         | Description               |
| ---------- | ------------ | ------------------------- |
| id         | INTEGER (PK) | Auto-increment            |
| name       | TEXT         | Candidate Name            |
| subject    | TEXT         | Interview Subject         |
| session_id | TEXT         | Unique session identifier |
| created_at | TIMESTAMP    | Session start time        |

### **Table: questions**

| Column      | Type         |
| ----------- | ------------ |
| id          | INTEGER (PK) |
| session_id  | TEXT         |
| question    | TEXT         |
| answer      | TEXT         |
| is_followup | BOOLEAN      |
| created_at  | TIMESTAMP    |

### **Table: logs (optional)**

Records system events such as:

* Recording started/stopped
* Browser tab switched
* Noisy environment detected

---

## **10. API Endpoints**

### **POST /get_question**

Fetches next question for the session.

**Request:**

```json
{
  "session_id": "ABC123",
  "index": 0
}
```

**Response:**

```json
{
  "question": "Explain polymorphism in OOP.",
  "done": false
}
```

---

### **POST /submit_answer**

Stores the answer for a question.

**Request:**

```json
{
  "session_id": "ABC123",
  "question": "What is AI?",
  "answer": "AI is..."
}
```

---

### **POST /generate_followup**

Creates an AI-generated follow-up question.

**Request:**

```json
{
  "session_id": "ABC123",
  "question": "...",
  "answer": "...",
  "history": ["Q1", "A1"]
}
```

---

### **GET /dashboard**

Returns candidate summary and past sessions.

---

### **GET /interview/{session_id}**

Loads the interview panel.

---

### **Optional APIs**

* **/flag_malpractice** – logs suspicious behavior
* **/validate_browser** – checks version & capabilities

---


# **11. Frontend Workflow**

The frontend of the system manages the user interface for conducting AI-based interview sessions. It communicates with the backend through REST APIs and provides real-time interaction using browser-native technologies such as Web Speech API for speech recognition and speech synthesis. The workflow below explains how each part functions:

---

## **1. Page Load & Session Initialization**

* When the interview page loads, the frontend retrieves the `SESSION_ID` (generated on the backend).
* A call is immediately made to:
  **POST → `/get_question`**
  This returns the first interview question based on the session index (`index = 0`).
* The question is displayed inside the question card.
* Automatically, the system uses **SpeechSynthesis** to *speak* the question aloud for the candidate.

---

## **2. Showing Interview Questions**

* Questions are fetched **one at a time** using the backend’s `/get_question` endpoint.
* If the backend returns `"done": true`, the frontend replaces the UI with a “Interview Completed” message.
* Otherwise, the question text is shown, and the audio playback begins.

---

## **3. Text-to-Speech (TTS) Flow**

When a question is received:

1. A `SpeechSynthesisUtterance` is created using the question string.
2. Browser TTS speaks the question automatically.
3. A manual **Speak Again** button lets the user replay the question if needed.

---

## **4. Speech-to-Text (STT) Answer Recording**

The frontend uses **Web Speech Recognition** (Chrome-only recommended) to capture interview answers.

**Recording flow:**

1. User clicks **Start Recording**.
2. Button changes to **Stop Recording**, and recording status updates.
3. A red blinking indicator + waveform animation show that speech capture is active.
4. As the user speaks:

   * **Interim results** show partial text.
   * **Final results** are appended to the answer box.
5. When the user clicks **Stop Recording** or the recognition ends:

   * Recording stops gracefully.
   * Status is updated.
   * The button switches back to **Start Recording**.

If the browser does not support STT:

* The system displays a compatibility warning.

---

## **5. Manual Answer Typing**

Users can edit or directly type answers in the text box.
Speech-to-text is optional; the system supports hybrid input.

---

## **6. Submitting an Answer**

When the user clicks **Next →**:

1. The answer text is collected from the answer box.
2. A `POST` request is sent to:
   **POST → `/submit_answer`**
3. Payload includes:

   * `session_id`
   * `question`
   * `answer`
4. Backend stores the answer in the database.
5. Frontend:

   * Clears the answer input box.
   * Increments `currentIndex`.
   * Automatically loads the next question using `loadQuestion()`.

---

## **7. UI State Handling**

The frontend manages several state variables:

| State Variable    | Purpose                                  |
| ----------------- | ---------------------------------------- |
| `currentIndex`    | Tracks which question to request next    |
| `currentQuestion` | Stores the current question text         |
| `recognizing`     | Whether STT is active                    |
| `finalTranscript` | Stores finalized speech recognition text |

These states ensure the interview continues smoothly question by question.

---

## **8. Error Handling**

The frontend gracefully handles:

* Speech recognition failures (microphone denied, unsupported browser)
* Failed API calls
* Missing session ID
* Empty answers

Errors are shown in the UI through the status bar.

---

## **9. End of Interview Flow**

Once all questions are answered:

* The backend responds with `{ "done": true }`.
* The frontend replaces the question card with a completion message.
* Recording buttons are disabled.
* No further actions can be taken.

---

#  This section is fully ready to paste into your README file.

If you want, I can also prepare:
✔ A README template
✔ Proper markdown formatting
✔ Full documentation + diagrams (flowchart, sequence diagram)
✔ Installation + environment setup block

-----

## **12. Known Requirements & Browser Notes**

### **Supported Browsers**

| Feature            | Supported Browsers                  |
| ------------------ | ----------------------------------- |
| SpeechRecognition  | Chrome, Edge                        |
| Camera access      | All modern browsers                 |
| TTS                | Chrome, Firefox, Edge               |
| Waveform animation | All browsers with Web Audio support |

### **Important Notes**

* Safari **does not fully support** Web Speech API.
* Chrome/Edge recommended for stable voice recognition.
* Microphone permissions **must be granted**.
* VPN/Antivirus may block mic access.
* On Windows, set default microphone from Sound Settings.

---

## **13. Troubleshooting**

### **1. Recording not starting**

✔ Ensure microphone access is allowed
✔ Try restarting the browser
✔ Check if another app is using the microphone

---

### **2. “SpeechRecognition not supported”**

Use:

* Google Chrome
* Microsoft Edge (latest version)

---

### **3. Waveform not showing**

Possible reasons:

* Browser blocked microphone
* AudioContext couldn't start
* Permission not granted

---

### **4. AI follow-up questions not generating**

Check backend logs for:

* Missing API key
* Token quota exceeded
* Bad JSON response

---

### **5. Camera not working**

✔ Make sure no other site/app is using the camera
✔ Allow video permission
✔ Disable VPN if camera routing fails

---

### **6. UI buttons not updating**

Likely issue:

* JavaScript file not refreshed (browser cached old version)

Solution:

* Hard refresh → **Ctrl + Shift + R**
* Clear browser cache
* Ensure `/static/js/interview.js` is updated



# 14 Future Enhancements

# 1. Advanced Malpractice & Anomaly Detection

Enhancing the proctoring system can significantly improve the credibility and reliability of the interview process.

Potential Improvements:

Real-time monitoring for multiple faces
Detect if more than one person appears on the camera during the interview.

Background movement or additional voice detection
Alert the system if someone else speaks or enters the frame.

Phone usage detection
Recognize whether the candidate looks downward repeatedly, indicating possible phone use.

Eye-movement tracking
Detect suspicious gaze patterns that indicate reading answers or checking external sources.

Automatic flagging of unusual behavior
The system can generate a "Proctoring Score" for each candidate based on detected anomalies.

# 2. Tab-Switch & Window-Focus Restriction

To ensure the candidate remains within the interview window:

Possible Enhancements:

Detect tab changes or switching to another application
If the candidate leaves the interview tab, a warning can be shown or the session can be marked.

Lock-screen mode
Prevents the user from opening new tabs while the interview is active.

Timer penalties or session termination
Repeated tab-switch attempts can automatically end the interview or be logged in the activity report.

# 3. AI Counter-Questioning and Dynamic Follow-Ups

Currently, the system records answers but does not evaluate content.

Future Improvements:

AI-generated follow-up questions
Based on the candidate's answer, the AI can instantly generate a deeper or more contextual question.

Semantic answer evaluation
The system can rate answers based on clarity, depth, correctness, and communication skills.

Personalized interview paths
The interview can dynamically adjust difficulty based on candidate performance.

# 4. Candidate Personality & Communication Scoring

A more comprehensive evaluation system can be introduced:

Confidence score using speech patterns (tone, pitch, pace)

Sentiment analysis to understand communication style (positive, assertive, neutral)

Language fluency scoring

Content richness evaluation using NLP models

# 5. Improved User Interface for Admin Panel

Enhancements for the dashboard to make data more useful:

Graphical analytics
Charts for candidate scores, timelines, and performance comparisons.

Session heatmaps
Identify interview portions with low/no audio, unusual pauses, or multiple warnings.

Downloadable PDF reports
Auto-generate a complete proctoring + answer transcript report per candidate.

# 6. Audio Quality & Environment Detection

Introduce checks for sound environment:

Low-noise requirement detection

Echo or background noise alerts

Microphone quality check before starting the interview

# 7. Cloud Deployment & Scalability

To make the system production-ready:

Deploy on AWS/GCP/Azure with autoscaling

Use managed SQLite → PostgreSQL migration

Add caching (Redis) for high traffic

Implement rate limiting for security

# 8. Authentication & Role-Based Access

Enhance system security and manageability:

Separate roles for Admin, HR, Interviewer

Multi-factor authentication (MFA)

Logged access trails for transparency

# 9. Enhanced Question Bank & LLM Integration

Future advancements:

Auto-update question bank using AI

Difficulty-level categorization

Domain-specific interview modes (AI/ML, Web Dev, Finance, HR, etc.)

Randomization to prevent repeatability and memorization