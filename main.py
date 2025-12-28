import requests
from flask import Flask, request, send_file, Response
from PIL import Image, ImageDraw, ImageFont
import io
import time
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
RTDB_URL = "https://farhan-exe-default-rtdb.asia-southeast1.firebasedatabase.app/api_hits/profile_card.json"
FONT_PATH = "DejaVuSans.ttf" # Ensure this file is in your project folder

def fetch_data(url):
    try:
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        return response.json()
    except:
        return {}

def load_remote_image(url):
    try:
        response = requests.get(url, timeout=10, stream=True)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except:
        return None

def log_to_firebase(uid):
    try:
        log_data = {
            'uid': uid,
            'timestamp': int(time.time() * 1000),
            'date': datetime.now().strftime("%Y-%m-%d %H:i:s")
        }
        requests.post(RTDB_URL, json=log_data, timeout=2)
    except:
        pass

@app.route('/api/profile_card')
def profile_card():
    uid = request.args.get('uid')
    if not uid:
        return "UID is required", 400

    # Firebase Logging
    log_to_firebase(uid)

    # Fetch Data
    abimg = fetch_data(f"https://farhanexe.kesug.com/apis/abimg?uid={uid}")
    info = fetch_data(f"https://farhanexe.kesug.com/apis/info?uid={uid}")

    banner_id = abimg.get('bannerId', '900000014')
    head_pic = abimg.get('headPic')
    nickname = info.get('basicInfo', {}).get('nickname', 'Unknown')
    level = info.get('basicInfo', {}).get('level', '0')
    clan = info.get('clanBasicInfo', {}).get('clanName', 'No Clan')

    # URLs
    banner_url = f"https://images0.netlify.app/id/{banner_id}.png"
    default_banner = "https://images0.netlify.app/id/900000014.png"
    avatar_url = f"https://farhanexe.kesug.com/apis/averterimg?id={head_pic}" if head_pic else None

    # Canvas Setup (280x60)
    canvas = Image.new('RGBA', (280, 60), (0, 0, 0, 0))
    
    # Load and Paste Banner (Position: 60,0; Size: 220x60)
    bn = load_remote_image(banner_url) or load_remote_image(default_banner)
    if bn:
        bn = bn.resize((220, 60))
        canvas.paste(bn, (60, 0))

    # Load and Paste Avatar (Position: 0,0; Size: 60x60)
    if avatar_url:
        av = load_remote_image(avatar_url)
        if av:
            av = av.resize((60, 60)).transpose(Image.FLIP_LEFT_RIGHT)
            canvas.paste(av, (0, 0), av if av.mode == 'RGBA' else None)

    # Drawing Text
    draw = ImageDraw.Draw(canvas)
    try:
        # Load fonts
        font_main = ImageFont.truetype(FONT_PATH, 14)
        font_sub = ImageFont.truetype(FONT_PATH, 11)
        
        draw.text((75, 8), nickname, fill="white", font=font_main)
        draw.text((75, 34), clan, fill="white", font=font_sub)
        draw.text((230, 34), f"Lv.{level}", fill="white", font=font_sub)
    except:
        # Fallback if font file is missing
        draw.text((75, 10), nickname, fill="white")
        draw.text((75, 38), clan, fill="white")
        draw.text((220, 38), f"L.{level}", fill="white")

    # Output Image
    img_io = io.BytesIO()
    canvas.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
