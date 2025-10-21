from flask import Flask, render_template_string

app = Flask(__name__)

@app.route("/")
def home():
    return render_template_string("""
    <html>
      <head>
        <title>ربات خنگول 🤖</title>
        <meta charset="utf-8"/>
      </head>
      <body style="text-align:center; font-family:sans-serif;">
        <h1>👋 سلام! این سایت رسمی ربات خنگول است</h1>
        <p>ساخته شده توسط <b>@NOORI_NOOR</b></p>
        <p>برای چت با ربات به 
        <a href="https://t.me/Khenqol_bot">@Khenqol_bot</a> بروید.</p>
      </body>
    </html>
    """)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
