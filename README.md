# 🏆 Project: The AI Marketing Co-pilot

![BigQuery](https://img.shields.io/badge/Google_Cloud-BigQuery-4285F4?style=for-the-badge&logo=google-cloud)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python)
![Gemini](https://img.shields.io/badge/Gemini-8E77D3?style=for-the-badge&logo=google-gemini)

A sophisticated, hybrid AI agent that empowers business users to have a natural language conversation with their BigQuery data warehouse to get instant insights from structured data, text, and images.

---

## 🎥 Demo Video

[![The AI Marketing Co-pilot Demo](https://img.youtube.com/vi/8myGbj3fxpw/0.jpg)](https://youtu.be/8myGbj3fxpw)

*(Click the image above for a 3-minute video demonstration of the project in action)*

---

## 🎯 The Challenge & Our Solution

Modern retailers struggle to get quick insights from their vast and varied data (transactions, reviews, images). The **AI Marketing Co-pilot** solves this by providing an intelligent, conversational interface to BigQuery. It allows non-technical users to ask complex questions in plain English and receive comprehensive, multimodal answers in seconds, dramatically accelerating the insight-to-action cycle.

---

## ✨ Key Features

* **Natural Language to SQL Engine:** Translates user questions into complex, multi-table SQL queries on the fly.
* **Hybrid AI Core:** Strategically combines native **BigQuery ML** (for scalable K-Means clustering) with the **Gemini API** (for dynamic reasoning and generation).
* **Multimodal Perception:** Can analyze product **images** in conjunction with text **reviews** and structured **transaction data** to provide a complete 360-degree view.
* **BQML Integration:** Intelligently generates and executes `ML.PREDICT` commands to leverage the pre-trained customer segmentation model.
* **Secure & Reproducible:** Uses Kaggle Secrets for Service Account authentication, ensuring the notebook is secure and easy for judges to run.

---

## 🏗️ Architecture

![Architecture Diagram](architecture.png)
*(This diagram illustrates the flow from a user's natural language prompt to the final, synthesized report, showcasing the interaction between the Kaggle Notebook, the Gemini API, and the various services within BigQuery.)*

---

## 🚀 How to Run This Notebook

This notebook is designed to be run in the Kaggle environment.

### **Prerequisites:**
* A Google Cloud Project.
* A Google AI Studio API Key for the Gemini API.

### **Setup Instructions:**
1.  **Create a Service Account** in your GCP project with `BigQuery User` and `BigQuery Data Viewer` roles. Download the JSON key.
2.  **Configure Kaggle Secrets:** Go to **Add-ons > Secrets** in the notebook editor. Create a new secret named `GCP_SA_KEY` and paste the entire content of your Service Account JSON file.
3.  **Run the Notebook:** Execute the first cell and enter your personal **Google AI Studio API Key** when prompted. Then, run the remaining cells.

---

## 🗣️ Prompts to Try with the Co-pilot

* **Basic Query:** `"Show me the 10 most expensive products in the store."`
* **BQML Command:** `"Which cluster does customer 17490 belong to?"`
* **Complex Hybrid Query:** `"What are the top 3 countries for customers who are in cluster 5?"`
* **Grand Finale (Multimodal):** `"Show me the reviews and analyze the image for the 'SET OF 3 REGENCY CAKE TINS'."`
