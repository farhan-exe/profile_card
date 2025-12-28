import requests
from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import time
from datetime import datetime
import urllib3

# SSL warning disable korar jonno (InsecureRequestWarning bondho hobe)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- Configuration ---
RTDB_URL = "https://farhan-exe-default-rtdb.asia-southeast1.firebasedatabase.app/api_hits/profile_card.json"
MAIN_API_URL = "https://raw.thug4ff.com/info?uid={}&key=thug4ff"
FONT_PATH = "DejaVuSans.ttf"

def fetch_ff_data(uid):
    """Directly fetch from the raw source API with SSL bypass"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    try:
        url = MAIN_API_URL.format(uid)
        # verify=False deya hoyeche jate SSL error na dey
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Fetch Error: {e}")
        return None

def log_to_firebase(uid):
    try:
        log_data = {
            'uid': uid,
            'timestamp': int(time.time() * 1000),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        requests.post(RTDB_URL, json=log_data, timeout=3)
    except:
        pass

def load_remote_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10, stream=True, verify=False)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except:
        return None

@app.route('/api/profile_card')
def profile_card():
    uid = request.args.get('uid')
    if not uid:
        return "UID is required", 400

    # Firebase-e hit count log hobe
    log_to_firebase(uid)
    
    # API theke data niye asha
    data = fetch_ff_data(uid)
    
    # Data check
    if not data or 'basicInfo' not in data:
        return f"Error: Player not found for UID {uid} or API is down.", 404

    # Data extracting based on your provided JSON structure
    basic = data.get('basicInfo', {})
    clan_info = data.get('clanBasicInfo', {})
    
    nickname = basic.get('nickname', 'Unknown')
    level = basic.get('level', '0')
    clan = clan_info.get('clanName', 'No Clan')
    banner_id = basic.get('bannerId', '900000014')
    head_pic = basic.get('headPic', '902000001')

    # Image URLs
    banner_url = f"https://images0.netlify.app/id/{banner_id}.png"
    default_banner = "https://images0.netlify.app/id/900000014.png"
    avatar_url = f"https://freefiremobile-a.akamaihd.net/common/as_png/head/{head_pic}.png"

    # --- Image Processing with Pillow ---
    canvas = Image.new('RGBA', (280, 60), (0, 0, 0, 0))
    
    # 1. Load Banner
    bn = load_remote_image(banner_url) or load_remote_image(default_banner)
    if bn:
        bn = bn.resize((220, 60), Image.Resampling.LANCZOS)
        canvas.paste(bn, (60, 0))

    # 2. Load Avatar
    av = load_remote_image(avatar_url)
    if av:
        # Resize and Flip
        av = av.resize((60, 60), Image.Resampling.LANCZOS).transpose(Image.FLIP_LEFT_RIGHT)
        canvas.paste(av, (0, 0), av)

    # 3. Text Rendering
    draw = ImageDraw.Draw(canvas)
    try:
        font_main = ImageFont.truetype(FONT_PATH, 13)
        font_sub = ImageFont.truetype(FONT_PATH, 10)
        
        # Text with subtle shadow for better readability
        draw.text((76, 9), nickname, fill=(0,0,0,150), font=font_main) # Shadow
        draw.text((75, 8), nickname, fill="white", font=font_main)
        
        draw.text((75, 36), clan, fill="white", font=font_sub)
        draw.text((230, 36), f"Lv.{level}", fill="white", font=font_sub)
    except:
        # Fallback fonts
        draw.text((75, 10), nickname, fill="white")
        draw.text((75, 38), clan, fill="white")
        draw.text((220, 38), f"Lv.{level}", fill="white")

    # Serve the image
    img_io = io.BytesIO()
    canvas.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    # Render automatically sets PORT environment variable
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
