# CollabIQ: A Retrospective on Building an AI-Powered Automation System

**Date:** November 29, 2025
**Project:** CollabIQ (Automated Collaboration Tracking)

---

## Introduction

When we started CollabIQ, the goal was deceptively simple: *Stop manually copying data from emails to Notion.*

It sounded like a weekend script. Read an email, ask AI what's in it, and paste it into a database. But as we peeled back the layers, we discovered that "simple" automation is actually an engineering challenge in disguise.

This document chronicles our journey from a basic prototype to a production-grade cloud system. It explains the technical hurdles we faced—and how we solved them—in language designed for the whole team.

---

## The Journey: From "Script" to "System"

### Phase 1: The "Happy Path" (Late October 2025)
Our first version was what engineers call a "Happy Path" implementation. It assumed everything would go right:
1. Emails would always be perfectly formatted.
2. The AI would always understand us.
3. Notion would always be available to save data.

We built a system that could read an email, use Google's Gemini AI to extract names and dates, and print them out. It worked! ...Until it didn't.

### Phase 2: Reality Sets In (Early November)
As soon as we threw real-world data at it, things broke.
- **The "Signature" Problem**: The AI would read email signatures and think the sender was the "Person in Charge" of the collaboration.
- **The "Notion" Surprise**: Just as we started integrating, Notion updated their API (the language computers use to talk to each other), breaking our code.
- **The "Duplicate" Disaster**: If you ran the script twice, you got two copies of every entry.

**The Fix**: We introduced **Sanitization** (cleaning email text before the AI sees it) and **Idempotency** (a fancy word for "making sure doing the same thing twice doesn't break anything").

### Phase 3: Making it Smart (Mid-November)
We realized that relying on one AI provider (Gemini) was risky. Sometimes it was down, sometimes it refused to answer (safety filters), and sometimes it just hallucinated.

**The Fix**: We built an **"Orchestrator"**. Think of it like a traffic controller. If Gemini is busy or confused, it automatically reroutes the work to Claude (Anthropic) or GPT-4 (OpenAI). We also added **Fuzzy Matching**—so if an email says "Samsung," our system knows to link it to "Samsung Electronics Co., Ltd." in our database.

### Phase 4: Going Pro (Late November)
The final hurdle was moving from "running on my laptop" to "running 24/7 in the cloud." This meant packaging the app into a **Container** (Docker) and deploying it to Google Cloud Run.

---

## Key Challenges & Engineering Concepts

Here are the specific technical challenges we solved, explained simply.

### 1. The "Flaky AI" Problem
**The Challenge**: AI models are probabilistic, not deterministic. Ask them "2+2" and they usually say "4", but sometimes they might say "Four" or "I can't do math right now."
**The Solution**: **Multi-LLM Orchestration**.
We stopped relying on a single "brain." We created a system that checks the health of our AI providers.
- *Concept*: **Circuit Breakers**. Just like in your house, if a service draws too much "power" (errors), we flip a switch and stop using it for a while to prevent a fire (system crash).

### 2. "Computer says No" (API Reliability)
**The Challenge**: Services like Gmail and Notion limit how fast you can work. If you try to read 1,000 emails in a second, they block you.
**The Solution**: **Exponential Backoff**.
If Notion rejects our request, we don't just give up. We wait 1 second and try again. If that fails, we wait 2 seconds, then 4, then 8. This politeness allows our system to recover automatically from temporary glitches without human intervention.

### 3. The "Notion" Migration
**The Challenge**: Midway through development, Notion changed how they identify databases (moving from "Databases" to "Data Sources").
**The Solution**: **Abstraction**.
Instead of writing code that says "Talk to Notion v1," we wrote a layer in the middle that says "Talk to *a* database." When Notion updated, we only had to fix that one middle layer, not the whole application. This saved us days of rewriting.

### 4. "It Works on My Machine"
**The Challenge**: Code that runs on a developer's MacBook often crashes on a cloud server because of missing files or different settings.
**The Solution**: **Containerization (Docker)**.
We packaged our code, its settings, and even the specific version of Python it needs into a "container." This container is like a sealed shipping box. If it works on my laptop, it is guaranteed to work on Google Cloud, because we ship the whole box, not just the code inside.

---

## What We Learned (And What We'd Do Differently)

### 1. Test Earlier
We wrote most of our comprehensive tests in Phase 15. In hindsight, we should have written them in Phase 2. We spent a lot of time manually checking if things worked, which is slow and error-prone.
*Lesson*: **Automated Testing** is not a luxury; it's a speed multiplier.

### 2. Secrets Management is Critical
We started by passing passwords around in text files. This is dangerous. We moved to **Infisical**, a tool that securely manages our secrets (API keys).
*Lesson*: Security cannot be an afterthought.

### 3. Async is Worth the Pain
We initially wrote code that did one thing at a time (read email -> wait -> extract -> wait -> save). We refactored it to be **Asynchronous** (read email -> start extracting -> immediately read next email). This made the system 5x faster but was much harder to debug.
*Lesson*: For high-volume data, **Parallel Processing** is essential, but it adds complexity.

---

## The Future

We have built a Ferrari engine. Now we need to build the dashboard.
- **Next Steps**: Building automated reports and analytics. We have the data; now we need to visualize it to see trends in our collaboration network.

CollabIQ is now a robust, self-healing system. It doesn't just "run scripts"; it manages its own health, chooses the best AI for the job, and recovers from errors automatically. That is the difference between a prototype and a product.
