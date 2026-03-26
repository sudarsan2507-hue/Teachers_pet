# 📝 CLAS: Cognitive Learning Analytics System

**CLAS** (Cognitive Learning Analytics System) is a high-integrity, AI-driven classroom platform designed to bridge the gap between attendance and actual conceptual understanding. It leverages a **Hybrid AI Engine** (powered by Groq Llama 3.1) to provide real-time pedagogical insights while enforcing strict academic honesty.

## 🚀 Key Features

### For Teachers (Teacher Dashboard)
*   **Live Analytics**: Real-time gauges for class understanding, engagement, and mean plagiarism.
*   **Honesty & AI Alerts**: Instant notifications for plagiarism, peer-copying, and AI-generated responses (ChatGPT/Claude).
*   **Pedagogical Closure Reports**: Automatically generates a "Mentor Report" at the end of every session, identifying class-wide misconceptions and suggesting teaching strategies.
*   **Visual Transparency**: Submission tables with gradient highlighting based on plagiarism risk.

### For Students (Student Portal)
*   **Conceptual Evaluation**: Moving beyond keyword matching, the AI verifies technically sound explanations even if vocabulary differs.
*   **Personalized AI Feedback**: Unique, student-specific **Study Tips** and **Conceptual Gaps** generated for every response.
*   **Zero-Tolerance Mimicry Defense**: Robust fuzzy-matching logic catches students who copy the question text, even if they change punctuation or casing.

## 🧠 Hybrid AI Architecture
The system employs a multi-stage evaluation pipeline:
1.  **Stage 1: Keyword Clustering (TF-IDF)**: Rapidly identifies technical term coverage.
2.  **Stage 2: Fuzzy Mimicry Detection**: Locates word-for-word question copying.
3.  **Stage 3: Groq LLM Verification**: Uses Llama 3.1 (8B) to authenticate conceptual depth, detect AI tonal signatures, and generate personalized feedback.

## 🛠️ Easy Clone & Run Setup

Everything you need to run the application (including the pre-trained ML models) is already included in the repository! Simply clone, provide your Groq API key, and you're good to go!

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/sudarsan2507-hue/Teachers_pet.git
    cd Teachers_pet
    ```

2.  **Install Dependencies**:
    The `requirements.txt` file is pre-configured with all necessary packages, including `streamlit`, `groq`, `scikit-learn`, and `plotly`.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables (Crucial for AI Features)**:
    Create a `.env` file in the root directory:
    ```env
    GROQ_API_KEY=your_groq_api_key_here
    ```

4.  **Run the Applications**:
    *   **Teacher Dashboard**: `streamlit run teacher_app.py --server.port 8501`
    *   **Student App**: `streamlit run student_app.py --server.port 8502`

## 📊 Evaluation Metrics
*   **Engaged (Green)**: Score > 75% | Deep conceptual coverage.
*   **Partially Engaged (Yellow)**: Score 50%-75% | Shallow or surface-level keywords.
*   **Disengaged (Red)**: Score < 50% | Plagiarism, Mimicry, or missing key technical nuances.

---
*Developed for high-integrity, data-driven learning.*
