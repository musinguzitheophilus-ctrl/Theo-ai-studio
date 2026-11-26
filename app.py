150
150
150
import os
import time
import base64
import requests
from flask import Flask, request, render_template_string, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

HTML = open("new_design.html").read()

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
                filename = f"generated_{int(time.time())}.jpg"
                with open(os.path.join("static", filename), "wb") as f:
                    f.write(image_bytes)

                image = url_for("static", filename=filename)

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
