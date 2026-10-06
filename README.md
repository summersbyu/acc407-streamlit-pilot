# Your first shareable accounting app

This pilot is for the instructor to experience the entire workflow before students use it. It includes fictional data, requires no AI API key, and makes no persistent writes. This folder is intended to become its own GitHub repository; it is separate from TeachLab.

## Three tools, three jobs

| Tool | Its job | Everyday comparison |
|---|---|---|
| GitHub repository | Saves code and its revision history | The project folder with a history of changes |
| GitHub Codespaces | Runs a development computer in your browser | Your workshop |
| Streamlit | Turns Python into an interactive app | The app's interface |
| Streamlit Community Cloud | Hosts the published app | The public storefront |

The Codespaces preview is for development. The public Streamlit app URL is the one students submit and share. Visitors use the app through a browser without installing Python. Once deployed, the app runs separately from the Codespace, so students can stop their Codespace.

## First: put these files on GitHub

Create a new repository called `acc407-streamlit-pilot`. For this fictional-data demonstration, a public repository is appropriate. Upload this folder's **contents** to the repository root, preserving `.devcontainer/devcontainer.json` and `.gitignore`; do not upload the entire course workspace. `app.py` and `requirements.txt` must be visible at the root. A repository template can be enabled later after the pilot works.

## Second: open the workshop

1. On the repository page, choose **Code → Codespaces → Create codespace on main**.
2. Wait for the browser editor and package installation to finish.
3. In its terminal, enter:

   ```bash
   python -m streamlit run app.py
   ```

4. Open the forwarded port 8501 in the **Ports** panel if the preview does not open automatically. Keep the development port private; public sharing will use Community Cloud.
5. Try all vendors, then Canyon Equipment, then the weekend checkbox.

## Third: make one change and save it

### Optional: use Codex in the Codespace

The container configuration includes Node.js 22, which supplies `npm`. For a Codespace created before this was added, first save your files, run `git pull --ff-only`, then open the Command Palette (F1) and choose **Codespaces: Rebuild Container**. When it reconnects, open a new terminal and run `npm --version`.

Install Codex with `npm install -g @openai/codex`, then sign in using `codex login --device-auth`. Device-code login and Codex access must be allowed for the ChatGPT account/workspace. Start with `codex` and ask it to explain `app.py` without changing it. Next, request one small change and ask it to run `python check_pilot.py`. Review and preview before committing/pushing. This account-authentication path remains to be verified in the instructor and student accounts.

Change `APP_TITLE` near the top of `app.py` to a title of your choosing. Save the file and check the preview. Then use the editor's Source Control panel to stage the change, commit it with a short description, and sync/push to GitHub. Saving in Codespaces alone does not update the published app: the change must reach GitHub.

Suggested AI request:

> Explain this app to me as an accounting instructor learning Python. Then change its title to Payment Review Dashboard. Preserve the SQL, integer-cent calculations, and strict greater-than threshold. Tell me how to confirm that your change did not alter the results.

## Fourth: publish the storefront

1. Open https://share.streamlit.io/ and sign in/connect your GitHub account. Complete account agreements yourself if prompted.
2. Choose **Create app** and the option to deploy from GitHub.
3. Select your repository, branch `main`, and entrypoint `app.py`.
4. In Advanced settings, choose Python 3.12 if offered to match this pilot's Codespace.
5. Choose an available app subdomain and deploy. Wait for the build to finish.
6. Confirm the app is public in its sharing/settings controls.
7. Open the resulting `https://....streamlit.app` URL in a signed-out/private browser window and on your phone. Confirm visitors can use it without your account.

The cloud installs packages from `requirements.txt`. This pilot uses a version range while exploring; freeze the tested package versions before distributing the course template. Free hosting can sleep or hit resource limits, so a URL is not a promise of permanent uptime. Retain the source repository and a brief recorded demonstration for assessment.

## Check these known answers

| Selection | Expected count | Expected total |
|---|---:|---:|
| All vendors; threshold $0; weekend off | 8 | $74,250.01 |
| Canyon Equipment; threshold $0; weekend off | 3 | $35,500.00 |
| All vendors; threshold $0; weekend on | 4 | $28,000.00 |
| All vendors; threshold $10,000; weekend off | 3 | $50,000.01 |
| All vendors; threshold $10,000; weekend on | 1 | $15,000.00 |
| All vendors; threshold $100,000; weekend off | 0 | $0.00 |

At $10,000, payments exactly equal to $10,000 must be excluded. The download must reflect the current filters. Display uses dollar formatting; stored amounts and totals use integer cents.

## What students would submit

- Public app URL, tested while signed out.
- GitHub repository URL and the commit identifier submitted for grading.
- Short description of the business problem, implemented rules, test results, and limitations.
- Brief recorded demonstration as a fallback if hosting is unavailable.

Use fictional or approved public data in this public portfolio. Keep student grades, credentials, and real client information out of both repository and app. This pilot has no upload feature and no secrets.

## When finished working

Commit and push your changes, then explicitly stop the Codespace at https://github.com/codespaces. Closing its browser tab is not the same as stopping it. Codespaces usage is metered; check the personal account's allowance before the class rollout.

## Official references

- Deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Codespaces stop/start: https://docs.github.com/en/codespaces/developing-in-a-codespace/stopping-and-starting-a-codespace
- Codespaces billing: https://docs.github.com/en/billing/concepts/product-billing/github-codespaces

Status: public repository created at https://github.com/summersbyu/acc407-streamlit-pilot. Local checks passed using Python 3.14.2 and Streamlit 1.65.0: six accounting cases, CSV row counts, interactive threshold/weekend filtering, and empty results. Run `python check_pilot.py` to repeat. Codespaces startup with Python 3.12 and Community Cloud deployment remain unverified.
