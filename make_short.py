import os, random, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS

OUT = Path("output")
OUT.mkdir(exist_ok=True)
W, H = 720, 1280
FONT_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",

    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]
FONT = next((p for p in FONT_PATHS if Path(p).exists()), None)

# Starter content only. Replace/add original topics before using regularly.
TOPICS = [
    ("प्रकृति का कमाल", "एक छोटा सा बीज सही मिट्टी, पानी और रोशनी पाकर पौधा बन सकता है।\nप्रकृति हमें धैर्य और देखभाल का महत्व सिखाती है।", "आज एक पौधे की देखभाल ज़रूर करें 🌱"),
    ("समुद्र की दुनिया", "समुद्र में कई तरह के जीव रहते हैं।\nउनके रहने की जगह और साफ पानी की रक्षा करना हम सबकी ज़िम्मेदारी है।", "प्रकृति को साफ रखें 🌊"),
    ("छोटी सी सीख", "हर दिन कुछ नया सीखने की कोशिश करें।\nछोटे कदम भी समय के साथ बड़ा बदलाव ला सकते हैं।", "आज क्या नया सीखोगे? ✨"),
    ("अंतरिक्ष की जिज्ञासा", "अंतरिक्ष बहुत विशाल है और वैज्ञानिक लगातार नई चीज़ें सीख रहे हैं।\nजिज्ञासा ही खोज की शुरुआत है।", "सवाल पूछते रहो 🚀"),
]
random.seed(int(os.environ.get("GITHUB_RUN_NUMBER", "1")))
topic = random.choice(TOPICS)
slides = [
    (topic[0], "30 सेकंड में एक छोटी सी बात"),
    (topic[1], "जानकारी और सीख"),
    (topic[2], "ऐसी और वीडियो के लिए जुड़े रहें"),
]

def font(size):
    return ImageFont.truetype(FONT, size) if FONT else ImageFont.load_default()

def wrap(draw, text, fnt, max_width):
    lines=[]
    for paragraph in text.split("\n"):
        words=paragraph.split()
        line=""
        for word in words:
            test=(line+" "+word).strip()
            if draw.textbbox((0,0), test, font=fnt)[2] <= max_width:
                line=test
            else:
                if line: lines.append(line)
                line=word
        if line: lines.append(line)
        lines.append("")
    return lines[:-1]

def make_card(title, body, path, index):
    # Plain graphic cards, not stock footage. Use a high-contrast dark background.
    im=Image.new("RGB",(W,H),(18+index*5,35+index*3,52+index*7))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((42,120,W-42,H-120), radius=38, outline=(110,205,160), width=5)
    d.text((70,180), f"DAILY SHORTS  •  {index+1}/3", font=font(25), fill=(150,230,190))
    title_font=font(48)
    body_font=font(38)
    y=300
    for line in wrap(d,title,title_font,W-140):
        d.text((70,y),line,font=title_font,fill="white",stroke_width=1,stroke_fill=(0,0,0)); y+=65
    y=max(y+70,480)
    for line in wrap(d,body,body_font,W-140):
        d.text((70,y),line,font=body_font,fill=(235,240,245)); y+=58
    d.text((70,H-210),"हिंदी • सीखें और साझा करें",font=font(24),fill=(150,230,190))
    im.save(path)

paths=[]
for i,(title,body) in enumerate(slides):
    p=OUT/f"card_{i}.png"; make_card(title,body,p,i); paths.append(p)

# Create a voiceover for the combined narration. Network/service availability is not guaranteed.
narration = f"{topic[0]}. {topic[1]} {topic[2]}"
audio = OUT/"voice.mp3"
gTTS(text=narration, lang="hi").save(str(audio))

# Build an MP4 with FFmpeg; cards have equal durations. Requires ffmpeg in PATH.
concat = OUT/"clips.txt"
with concat.open("w", encoding="utf-8") as f:
    for p in paths:
        f.write(f"file '{p.resolve()}'\nduration 10\n")
    f.write(f"file '{paths[-1].resolve()}'\n")
silent = OUT/"silent.mp4"
subprocess.run([
    "ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),
    "-vf","fps=30,format=yuv420p","-t","30","-an",
    "-c:v","libx264","-pix_fmt","yuv420p",str(silent)
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
final = OUT/"daily_short.mp4"
subprocess.run([
    "ffmpeg","-y","-i",str(silent),"-i",str(audio),
    "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac",
    "-shortest","-t","30","-movflags","+faststart",str(final)
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
Path("output/title.txt").write_text(f"{topic[0]} | हिंदी Short #Shorts", encoding="utf-8")
print(f"Created {final}")
