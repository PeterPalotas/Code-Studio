# Code-Studio


**Code Studio** is a local development environment designed for practicing algorithmic problems. It bridges the gap between browser based coding and real world engineering by allowing developers to solve practice problems directly in **VS Code** with automated local test cases, and it works OFFLINE.

My main inspiration for this project came while traveling; I wanted to practice algorithmic problems on flights and other travel without relying on network connections, so I built a tool that caches problems locally.

![Python](https://img.shields.io/badge/Python-3.13%2B-blue) ![Flask](https://img.shields.io/badge/Backend-Flask-green) ![VS Code](https://img.shields.io/badge/Editor-VS_Code-007acc) ![License](https://img.shields.io/badge/License-MIT-lightgrey)

<img width="2467" height="1078" alt="image" src="https://github.com/user-attachments/assets/14c3c78c-0062-4bd2-a8f1-3b27158c28e7" />

## Overview

Code Studio creates a bridge between problem definitions and your local IDE. Instead of copy pasting code into a browser, it can be done all in one locally hosted page.

The local hosting allows for offline access to pre downloaded problems, which come with solutions and test cases; which allows you to solve them without network access.

**Current features:**
* **One Click Workspace:** Instantly generates Python boilerplate and launches VS Code.
* **Local Test Runner:** Executes test cases against your solution using a custom built Python harness, **independent** of external servers. (This means you can solve problems offline)
* **Ground Truth Verification:** Compares your output against community verified solutions to ensure correctness.

## TODO:
If/When I next choose to work on the project. Below are the planned features and improvements:

### Core Functionality
- [ ] **Multi-Language Support:** Add support for **JavaScript/Node.js** execution (currently Python only).
- [ ] **Dynamic Problem Fetching:** Remove hardcoded "Blind 75" slugs and allow fetching any problem by URL or ID.
- [ ] **Search & Filtering:** Add a search bar and filter problems by Difficulty (Easy/Med/Hard) or Topic (DP, Graphs, Arrays).
- [ ] **Custom Test Cases:** Add the ability for users to input their own custom test cases via the UI to cover edge cases not provided by the default set.


## 📦 Installation

I have primarily tested this on **Arch Linux** with **Hyprland**. Windows support is included in the code but is currently experimental. (Can be found in `code_client.py`)

1.  **Clone the repository**
    ```bash
    git clone https://github.com/PeterPalotas/Code-Studio.git
    cd Code-Studio
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**
    ```bash
    python3 app.py
    ```

4.  **Open the Studio**
    * Navigate to `http://127.0.0.1:5000`
    * Select a problem from the sidebar to begin.
## 🔧 Prerequisites

* **Python 3.13+**
* **VS Code** (must be in your system PATH as `code`).
    * *Note:* The application attempts to auto-detect your OS (Windows/Linux) to launch the editor correctly BUT I have only tested it on Linux.


## 🛠️ Architecture

The application is built with a **Flask** backend that powers the entire workflow:
* **Offline Caching:** Checks the local `code_workspace` for problem data before attempting network requests.

* **Quick deployment:** Flask allows the project to be deployed in seconds with relative ease, and work on all machines 


## ⚠️ Disclaimer

This project is for **educational purposes only**. It is a local interface for practicing algorithms and is not affiliated with, endorsed by, or connected to any specific coding platform. All code is executed locally on your machine. Users are responsible for complying with the Terms of Service of any third-party data sources accessed by this tool.
