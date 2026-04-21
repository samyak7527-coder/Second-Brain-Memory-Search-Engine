import re

file_path = "combined.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace DESIGN TOKENS
tokens_replacement = """:root {
  /* canvas */
  --bg:       #F9FAFB;
  --bg2:      #F3F4F6;
  --bg3:      #E5E7EB;
  --surface:  #ffffff;
  --glass:    rgba(255,255,255,0.8);

  /* ink */
  --ink:      #111827;
  --ink2:     #374151;
  --ink3:     #4B5563;
  --ink4:     #9CA3AF;

  /* sidebar */
  --sb:       #F9FAFB;
  --sb2:      #F3F4F6;
  --sb3:      #E5E7EB;
  --sb4:      #D1D5DB;
  --sb5:      #9CA3AF;
  --sbt:      #111827;
  --sbt2:     #374151;
  --sbt3:     #6B7280;

  /* accents (Blue primary) */
  --amber:    #2563EB;
  --amber-l:  #DBEAFE;
  --amber-m:  #60A5FA;
  --amber-d:  #1D4ED8;

  /* accents (Purple accent) */
  --teal:     #7C3AED;
  --teal-l:   #EDE9FE;
  --teal-m:   #A78BFA;

  --rose:     #EF4444;
  --rose-l:   #FEE2E2;
  --rose-m:   #F87171;

  --sky:      #0EA5E9;
  --sky-l:    #E0F2FE;
  --sky-m:    #7DD3FC;

  --plum:     #8B5CF6;
  --plum-l:   #EDE9FE;
  --plum-m:   #C4B5FD;

  /* radii */
  --r-sm:  8px;
  --r:     12px;
  --r-lg:  16px;
  --r-xl:  24px;

  /* shadows */
  --sh-xs:  0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --sh-sm:  0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
  --sh-md:  0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --sh-lg:  0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
}"""
content = re.sub(r':root\s*\{.*?(?=/\*\s*════════════════════════════════════════════════════════\s*GLOBAL RESET & BASE)', tokens_replacement + '\n\n', content, flags=re.DOTALL)

# Replace stApp background
stapp_replacement = """.stApp {
  background: var(--bg) !important;
}"""
content = re.sub(r'\.stApp\s*\{[^\}]+\}', stapp_replacement, content, flags=re.DOTALL)

# Replace Sidebar shadow
content = content.replace("box-shadow: 2px 0 24px rgba(0,0,0,0.25) !important;", "box-shadow: var(--sh-sm) !important;")

# Fix radio button styling in sidebar
radio_replacement = """[data-testid="stSidebar"] .stRadio > div { gap: 4px !important; }
[data-testid="stSidebar"] .stRadio label {
  background: transparent !important;
  border-radius: var(--r-sm) !important;
  padding: 8px 12px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
  color: var(--sbt2) !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
  background: var(--sb3) !important;
  color: var(--sbt) !important;
}
[data-testid="stSidebar"] .stRadio [data-checked="true"] > label,
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked) {
  background: var(--amber-l) !important;
  color: var(--amber-d) !important;
  box-shadow: none !important;
  border-left: 4px solid var(--amber) !important;
}"""
content = re.sub(r'\[data-testid="stSidebar"\] \.stRadio > div \{.*?(?=\[data-testid="stSidebar"\] \.stRadio \[data-baseweb="radio"\])', radio_replacement + '\n', content, flags=re.DOTALL)

# Fix stTextArea and stTextInput
inputs_replacement = """[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] .stTextInput input {
  background: var(--surface) !important;
  border: 1px solid var(--sb4) !important;
  border-radius: var(--r-sm) !important;
  color: var(--ink) !important;
  font-family: 'Outfit', sans-serif !important;
  font-size: 14px !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stSidebar"] .stTextArea textarea:focus,
[data-testid="stSidebar"] .stTextInput input:focus {
  border-color: var(--amber) !important;
  box-shadow: 0 0 0 3px var(--amber-l) !important;
}"""
content = re.sub(r'\[data-testid="stSidebar"\] \.stTextArea textarea,\s*\[data-testid="stSidebar"\] \.stTextInput input\s*\{.*?(?=\[data-testid="stSidebar"\] \.stTextArea textarea::placeholder)', inputs_replacement + '\n', content, flags=re.DOTALL)

# Fix sidebar buttons
sidebar_btn_replacement = """[data-testid="stSidebar"] .stButton > button {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  border-radius: var(--r) !important;
  padding: 10px 16px !important;
  transition: all 0.2s ease !important;
  background: var(--surface) !important;
  border: 1px solid var(--sb4) !important;
  color: var(--sbt) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--bg2) !important;
  color: var(--teal) !important;
  border-color: var(--teal) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: var(--amber) !important;
  border-color: transparent !important;
  color: #fff !important;
  box-shadow: var(--sh-sm) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
  background: var(--teal) !important;
  transform: translateY(-1px) !important;
}"""
content = re.sub(r'\[data-testid="stSidebar"\] \.stButton > button\s*\{.*?(?=\[data-testid="stSidebar"\] \[data-testid="stFileUploader"\])', sidebar_btn_replacement + '\n\n/* sidebar file uploader */\n', content, flags=re.DOTALL)

# Main area buttons
main_btn_replacement = """.main .stButton > button, section.main .stButton > button {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  border-radius: var(--r) !important;
  padding: 10px 20px !important;
  transition: all 0.2s ease !important;
  border: 1px solid var(--bg3) !important;
  background: var(--surface) !important;
  color: var(--ink2) !important;
  box-shadow: var(--sh-xs) !important;
}
.main .stButton > button:hover {
  background: var(--bg) !important;
  border-color: var(--teal) !important;
  color: var(--teal) !important;
  box-shadow: var(--sh-sm) !important;
}
.main .stButton > button:active { transform: translateY(0) !important; }
.main .stButton > button[kind="primary"] {
  background: var(--amber) !important;
  border-color: transparent !important;
  color: #fff !important;
  box-shadow: var(--sh-sm) !important;
}
.main .stButton > button[kind="primary"]:hover {
  background: var(--teal) !important;
  box-shadow: var(--sh-md) !important;
  transform: translateY(-1px) !important;
}"""
content = re.sub(r'\.main \.stButton > button, section\.main \.stButton > button\s*\{.*?(?=/\*\s*════════════════════════════════════════════════════════\s*CHAT MESSAGES)', main_btn_replacement + '\n\n', content, flags=re.DOTALL)

# Fix Chat Messages
chat_replacement = """[data-testid="stChatMessage"] {
  background: var(--surface) !important;
  border: 1px solid var(--bg3) !important;
  border-radius: var(--r-lg) !important;
  padding: 16px 20px !important;
  margin-bottom: 16px !important;
  font-size: 15px !important;
  box-shadow: var(--sh-sm) !important;
  transition: box-shadow 0.2s !important;
  animation: msg-in 0.25s ease !important;
}
@keyframes msg-in {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
[data-testid="stChatMessage"]:hover { box-shadow: var(--sh-md) !important; }
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  background: var(--bg2) !important;
  border-color: var(--bg3) !important;
}
[data-testid="stChatInput"] > div {
  background: var(--surface) !important;
  border: 1px solid var(--bg3) !important;
  border-radius: var(--r-lg) !important;
  box-shadow: var(--sh-md) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stChatInput"] > div:focus-within {
  border-color: var(--amber) !important;
  box-shadow: 0 0 0 3px var(--amber-l), var(--sh-md) !important;
}
[data-testid="stChatInput"] textarea {
  font-family: 'Outfit', sans-serif !important;
  font-size: 15px !important;
  color: var(--ink) !important;
}"""
content = re.sub(r'\[data-testid="stChatMessage"\]\s*\{.*?(?=/\*\s*════════════════════════════════════════════════════════\s*METRICS)', chat_replacement + '\n\n', content, flags=re.DOTALL)

# Fix random gradients
content = content.replace("background: linear-gradient(135deg, var(--amber), var(--amber-d))", "background: var(--amber)")
content = content.replace("background: linear-gradient(135deg, #e09410, var(--amber))", "background: var(--teal)")
content = content.replace("background: linear-gradient(135deg, var(--amber-l) 0%, var(--surface) 70%)", "background: var(--bg2)")

# Fix main input focus
content = content.replace("box-shadow: 0 0 0 3px rgba(212,134,10,0.12), var(--sh-xs) !important;", "box-shadow: 0 0 0 3px var(--amber-l), var(--sh-sm) !important;")

# Fix logo
content = content.replace("color: #e8e2d8 !important;", "color: var(--sbt) !important;")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated successfully.")
