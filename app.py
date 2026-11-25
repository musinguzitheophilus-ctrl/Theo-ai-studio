import os
import base64
import requests
from flask import Flask, request, render_template_string, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

HTML = """
<!DOCTYPE html>
<html>
<head>
<link rel="icon" type="image/svg+xml" href="{{ url_for('static', filename='favicon.svg') }}">
<link rel="icon" type="image/png" href="{{ url_for('static', filename='favicon.png') }}"> <title>THEO AI Studio</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
    background: #080b0a;
    color: #00ff88;
    font-family: Arial;
    text-align: center;
    padding: 20px;
}
h1 { font-size: 32px; }
textarea {
    width: 90%;
    height: 120px;
    background: #151b18;
    color: white;
    border: 1px solid #00ff88;
    padding: 12px;
    border-radius: 10px;
}
button {
    background: #00ff88;
    color: black;
    padding: 15px 30px;
    border: none;
    border-radius: 10px;
    font-weight: bold;
    margin-top: 15px;
}
img {
    max-width: 100%;
    border-radius: 12px;
    margin-top: 20px;
}
.error { color: #ff7777; }
</style>
</head>
<body>
<h1>THEO AI</h1>
<p>AI IMAGE STUDIO</p>
<form method="POST">
<textarea name="prompt"
placeholder="Describe the image you want to create..."
required>{{ prompt }}</textarea><br>
<button type="submit">GENERATE IMAGE</button>
</form>
<section style="margin-top:40px; padding:20px; background:#151b18; border:1px solid #00ff88; border-radius:15px;">
    <h2>THEO AI CHAT</h2>
    <div id="chat-box" style="height:250px; overflow-y:auto; text-align:left; color:white; padding:10px;">
        <p>THEO AI: Hello! How can I help you today?</p>
    </div>

    <input id="chat-input" type="text" placeholder="Ask THEO AI anything..."
    style="width:90%; padding:12px; margin-top:10px;">

    <button onclick="sendMessage()">SEND MESSAGE</button>
</section>

<script>
async function sendMessage() {
    const input = document.getElementById("chat-input");
    const box = document.getElementById("chat-box");
    const message = input.value.trim();

    if (!message) return;

    box.innerHTML += "<p>You: " + message + "</p>";
    input.value = "";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: message})
        });

        const data = await response.json();
        box.innerHTML += "<p>THEO AI: " +
            (data.reply || data.error) + "</p>";
        box.scrollTop = box.scrollHeight;
    } catch (error) {
        box.innerHTML += "<p>THEO AI: Connection failed.</p>";
    }
}
</script>
{% if error %}
<p class="error">{{ error }}</p>
{% endif %}
{% if image %}
<h3>Your generated image</h3>
<img src="{{ image }}" alt="AI generated image">
{% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    prompt = ""
    error = None
    image = None

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()

        if not ACCOUNT_ID or not API_TOKEN:
            error = "Cloudflare settings are missing. Check your .env file."
        elif not prompt:
            error = "Please enter an image description."
        else:
            try:
                endpoint = (
                    f"https://api.cloudflare.com/client/v4/accounts/"
                    f"{ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
                )

                response = requests.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {API_TOKEN}"},
                    json={"prompt": prompt},
                    timeout=180
                )
                response.raise_for_status()

                data = response.json()
                encoded_image = data["result"]["image"]
                image_bytes = base64.b64decode(encoded_image)

                os.makedirs("static", exist_ok=True)
                with open("static/generated.jpg", "wb") as f:
                    f.write(image_bytes)

                image = url_for("static", filename="generated.jpg")

            except Exception:
                error = "Image generation failed. Check your internet and Cloudflare settings."

    return render_template_string(
        HTML, prompt=prompt, image=image, error=error
    )

@app.route("/chat", methods=["POST"])
def chat():
    message = request.json.get("message", "").strip()

    if not message:
        return {"error": "Please enter a message."}, 400

    try:
        endpoint = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{ACCOUNT_ID}/ai/run/@cf/qwen/qwen2.5-coder-32b-instruct"
        )

        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {API_TOKEN}"},
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": "You are THEO AI, a helpful and friendly assistant."
                    },
                    {"role": "user", "content": message}
                ]
            },
            timeout=120
        )

        response.raise_for_status()
        data = response.json()

        return {"reply": data["result"]["response"]}

    except Exception:
        return {"error": "THEO AI could not respond. Check your Cloudflare model and API settings."}, 500 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
