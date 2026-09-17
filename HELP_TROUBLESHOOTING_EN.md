# 🛠 Troubleshooting & AI Support (Auto-Repair)

If you encounter errors during installation (`setup.bat`) or music generation, do not panic. This project comes with a built-in diagnostic system. You don't need to be a programmer to fix it: a free AI agent can do it for you.

The distribution includes a system file called `SUPPORT_AGENT.md`. This is a strict playbook for an AI assistant that knows the architecture of this build and can automatically fix issues[cite: 5].

Follow the steps below to run the AI mechanic on your PC for free.

## Step 1. Install a free AI environment (Verdent)
We recommend **Verdent** — an AI coding assistant that provides access to free models without requiring a credit card.

1. Go to the official website: [verdent.ai](https://www.verdent.ai/).
2. Download and install the Windows client.
3. Sign up for a free account (Free Trial). You will get access to fast models like **GLM-5.3-Flash**, which is more than capable of diagnosing script errors.

## Step 2. Open the project and run diagnostics
1. Launch Verdent.
2. Click **"Open Folder"** and select the ROOT folder where you extracted YuE2 LITE (the folder containing `setup.bat`). This is crucial so the AI can read all system logs.
3. Open the **Chat** (or Agent) tab in the sidebar.
4. Make sure a free model (e.g., `GLM-5.3-Flash`) is selected in the model dropdown.
5. Copy the prompt below, paste it into the AI chat, and hit send:

> **Prompt to copy & paste:**
> "Hi. I encountered an error while running YuE2 LITE. 
> Your instructions and diagnostic matrix are located in the `SUPPORT_AGENT.md` file. Please read this file, check my logs in the current workspace, and tell me which playbook scenario (F1-F6) applies to my issue, or fix it automatically if your instructions allow it."

The AI will analyze your logs (like `setup_log.txt` or `hardware_report.txt`) and provide the exact solution or run the necessary patch directly[cite: 5].