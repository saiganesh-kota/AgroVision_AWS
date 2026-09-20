# 🌾 AgroVision AI v3 — Intelligent Crop Disease Detection Platform

> AI-powered crop diagnosis, treatment recommendations, farm intelligence, and government-scheme discovery — deployed live on AWS.

[![Backend](https://img.shields.io/badge/backend-Flask%20%2B%20Python-3776AB)]()
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)]()
[![AWS](https://img.shields.io/badge/AWS-Amplify%20%7C%20ECS%20%7C%20S3%20%7C%20ECR-orange)]()
[![Status](https://img.shields.io/badge/status-hackathon%20build-brightgreen)]()

**🌐 Live Application:**  
https://main.d3dq67cpjcc46t.amplifyapp.com/

**💻 GitHub:**  
https://github.com/saiganesh-kota/AgroVision_AWS

**🎥 Demo Video:**  
https://youtu.be/fRkSd7u9ZTw?si=Xv0TzClp-VyILFDA

---

## 🎯 Problem

Farmers often lack quick access to reliable crop-health information, disease identification, treatment guidance, weather intelligence, and relevant agricultural schemes.

AgroVision AI combines computer vision, environmental information, geospatial intelligence, and AI assistance into a single platform that helps farmers understand crop health and take informed action.

---

## 💡 Solution

AgroVision AI provides:

- 🍃 AI-powered crop disease detection
- 📊 Disease confidence and severity analysis
- 🌦️ Weather and environmental intelligence
- 🌱 Soil and crop-health insights
- 💊 Treatment recommendations
- 🏛️ Government scheme discovery
- 📅 Crop calendar
- 💰 Yield and profit estimation
- 🗺️ Geo-intelligence and disease hotspots
- 🤖 RaithuMitra AI assistant
- 📈 Scan history and farm dashboard
- 🔄 Feedback and adaptive model improvement

---

# ☁️ AWS Architecture

```mermaid
flowchart LR

    Farmer["👨‍🌾 Farmer"]

    subgraph AWS["☁️ AWS Cloud"]
        Amplify["AWS Amplify Hosting<br/>React + Vite"]

        ECS["Amazon ECS / Fargate<br/>ECS Express Mode<br/>Flask API"]

        ECR["Amazon ECR<br/>Docker Image"]

        S3["Amazon S3<br/>Uploads · Data · Models"]
    end

    ML["🧠 ML Pipeline<br/>Disease Detection"]

    Gemini["🤖 Gemini API<br/>RaithuMitra"]

    Farmer --> Amplify
    Amplify -->|"HTTPS / REST"| ECS
    ECR -->|"Container Image"| ECS
    ECS --> ML
    ECS <--> S3
    ECS --> Gemini
