import requests
from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import time
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
RTDB_URL = "https://farhan-exe-default-rtdb.asia-southeast1.firebasedatabase.app/api_hits/profile_card.json"
MAIN_API_URL = "https://raw.thug4ff.com/info?uid={}&key=thug4ff"
FONT_PATH = "DejaVuSans.ttf"

def fetch_ff_data(uid):
    """Directly fetch from the raw source API"""
    try:
        response = requests.get(MAIN_API_URL.format(uid), timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Fetch Error: {e}")
    return None

def log_to_firebase(uid):
    """Log hit to Firebase RTDB"""
    try:
        log_data = {
            'uid': uid,
            'timestamp': int(time.time() * 1000),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        requests.post(RTDB_URL, json=log_data, timeout=2)
    except:
        pass

def load_remote_image(url):
    """Load image from URL for Pillow"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10, stream=True)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except:
        return None

@app.route('/api/profile_card')
def profile_card():
    uid = request.args.get('uid')
    if not uid:
        return "UID is required", 400

    # Logging
    log_to_firebase(uid)
    
    # Fetch Data
    data = fetch_ff_data(uid)
    if not data or 'basicInfo' not in data:
        return "Player not found or API down", 404

    # Extracting Data
    nickname = data['basicInfo'].get('nickname', 'Unknown')
    level = data['basicInfo'].get('level', '0')
    clan = data.get('clanBasicInfo', {}).get('clanName', 'No Clan')
    banner_id = data['basicInfo'].get('bannerId', '900000014')
    head_pic = data['basicInfo'].get('headPic', '902000001')

    # Assets URLs
    banner_url = f"https://images0.netlify.app/id/{banner_id}.png"
    default_banner = "https://images0.netlify.app/id/900000014.png"
    # Free Fire official asset URL for headPic
    avatar_url = f"https://freefiremobile-a.akamaihd.net/common/as_png/head/{head_pic}.png"

    # --- Canvas Creation ---
    # Size: 280x60
    canvas = Image.new('RGBA', (280, 60), (0, 0, 0, 0))
    
    # 1. Background/Banner (Position: 60,0 | Size: 220x60)
    bn = load_remote_image(banner_url) or load_remote_image(default_banner)
    if bn:
        bn = bn.resize((220, 60), Image.Resampling.LANCZOS)
        canvas.paste(bn, (60, 0))

    # 2. Avatar (Position: 0,0 | Size: 60x60)
    av = load_remote_image(avatar_url)
    if av:
        av = av.resize((60, 60), Image.Resampling.LANCZOS).transpose(Image.FLIP_LEFT_RIGHT)
        canvas.paste(av, (0, 0), av)

    # 3. Draw Text
    draw = ImageDraw.Draw(canvas)
    try:
        font_main = ImageFont.truetype(FONT_PATH, 14)
        font_sub = ImageFont.truetype(FONT_PATH, 11)
        
        # Shadow/Outline for better visibility
        draw.text((76, 9), nickname, fill="black", font=font_main) # Shadow
        draw.text((75, 8), nickname, fill="white", font=font_main)
        
        draw.text((75, 34), clan, fill="white", font=font_sub)
        draw.text((230, 34), f"Lv.{level}", fill="white", font=font_sub)
    except:
        # Fallback fonts
        draw.text((75, 10), nickname, fill="white")
        draw.text((75, 38), clan, fill="white")
        draw.text((220, 38), f"Lv.{level}", fill="white")

    # Save to buffer
    img_io = io.BytesIO()
    canvas.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
