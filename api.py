from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

function searchBook() {
  let q = document.getElementById("search").value;

  console.log("sending request:", q);

  fetch("http://127.0.0.1:5000/search?q=" + encodeURIComponent(q))
    .then(res => {
      console.log("response status:", res.status);
      return res.json();
    })
    .then(data => {
      console.log("data received:", data);

      let grouped = {};

      data.forEach(r => {
        if (!grouped[r.city]) grouped[r.city] = {};
        if (!grouped[r.city][r.library]) grouped[r.city][r.library] = [];
        grouped[r.city][r.library].push(r);
      });

      let html = "";

      for (let city in grouped) {

        html += `<div class="card">`;
        html += `<div class="city">📍 ${city}</div>`;

        for (let lib in grouped[city]) {

          html += `<div class="library">🏛 ${lib}</div>`;

          grouped[city][lib].forEach(item => {

            html += `
              <div class="item">
                <img src="${item.cover_image || 'https://via.placeholder.com/60x80'}">
                <div>
                  <div>📘 ${item.publisher}</div>
                  <div>💰 ${item.price}</div>
                </div>
              </div>
            `;
          });

        }

        html += `</div>`;
      }

      document.getElementById("results").innerHTML = html;

    })
    .catch(err => {
      console.log("ERROR:", err);
      document.getElementById("results").innerHTML =
        "خطأ بالاتصال - افتح Console وشوف السبب";
    });
}

@app.route("/search")
def search_api():
    q = request.args.get("q", "")
    return jsonify(search(q))

@app.route("/")
def home():
    return "API is running"

app.run(host="0.0.0.0", port=5000)
