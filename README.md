A simple Python automation script that uses **Selenium** and **Chromedriver** to open [Monkeytype](https://monkeytype.com/), handle login, and interact with the site automatically.  

## 📦 Requirements
- Python 3.9 or later  
- Google Chrome installed  
- Chromedriver (must match your Chrome version)  

Install dependencies:
\`\`\`bash
py -m pip install -r requirements.txt
\`\`\`

## 🚀 Usage
1. Place \`chromedriver.exe\` in the same folder as \`main.py\`.  
2. Run the script:
\`\`\`bash
py main.py
\`\`\`

## ⚙️ Configuration
- Update \`main.py\` with your Monkeytype login credentials.  
- Run Chrome in headless mode by editing:
\`\`\`python
chrome_options.add_argument(\"--headless=new\")
\`\`\`

## 🐞 Troubleshooting
- SSL handshake errors → ignore  
- Pip not recognized → use \`py -m pip install -r requirements.txt\`  
- Chromedriver not found → ensure it's in the same folder as \`main.py\`  

## 📜 License
MIT License
