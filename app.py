
from flask import Flask, render_template, request
import requests

app = Flask(__name__)


def get_weather(city):
    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo = requests.get(
            geo_url,
            params={"name": city, "count": 1, "language": "en"},
            timeout=10
        ).json()

        if not geo.get("results"):
            return {"error": "City not found. Try another city."}

        place = geo["results"][0]

        weather_url = "https://api.open-meteo.com/v1/forecast"
        response = requests.get(
            weather_url,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,precipitation",
                "daily": "precipitation_probability_max",
                "timezone": "auto"
            },
            timeout=10
        ).json()

        current = response["current"]
        rain = response.get("daily", {}).get(
            "precipitation_probability_max", [0]
        )[0]

        return {
            "city": place["name"],
            "temperature": current["temperature_2m"],
            "humidity": current["relative_humidity_2m"],
            "rain": current["precipitation"],
            "rain_chance": rain
        }

    except (requests.RequestException, KeyError, ValueError):
        return {"error": "Weather unavailable. Check your internet connection."}


@app.route("/", methods=["GET", "POST"])
def home():
    result = {}
    city = "Chennai"

    if request.method == "POST":
        city = request.form.get("city", "Chennai").strip() or "Chennai"
        crop = request.form.get("crop", "Rice")
        stage = request.form.get("stage", "Growing")
        soil = request.form.get("soil", "Loamy")
        area = request.form.get("area", "1")
        rainfall = request.form.get("rainfall", "10")
        symptoms = request.form.get("symptoms", "None")

        weather = get_weather(city)
        result["weather"] = weather

        fertilizers = {
            "Rice": "Use soil-test-based NPK fertilizer. Split nitrogen application according to crop stage.",
            "Tomato": "Use balanced NPK based on soil testing. Avoid excess nitrogen.",
            "Maize": "Use recommended NPK and split nitrogen applications based on crop stage.",
            "Cotton": "Use soil-test-based NPK and follow local agricultural guidance.",
            "Sugarcane": "Use soil-test-based nutrients and split fertilizer according to crop growth.",
            "Groundnut": "Use recommended phosphorus, calcium and other nutrients based on soil testing."
        }
        result["fertilizer"] = fertilizers.get(
            crop, "Choose fertilizer based on soil testing and local agricultural advice."
        )

        disease_advice = {
            "Yellow leaves": "Yellowing can have several causes, including nutrient deficiency or excess water. Check drainage and leaf patterns.",
            "Brown spots": "Brown spots may indicate a fungal disease or other damage. Avoid wetting leaves and seek local plant-health advice.",
            "White powder": "White powder may indicate a fungal problem such as powdery mildew. Improve airflow and get the crop checked.",
            "Wilting": "Check soil moisture, root health and drainage. Wilting may result from drought, root damage or disease.",
            "Holes in leaves": "Inspect both sides of leaves for insects or caterpillars and seek crop-specific pest advice.",
            "None": "Select a symptom if your crop shows signs of disease."
        }
        result["disease"] = disease_advice.get(
            symptoms, "Select a symptom to get basic guidance."
        )

        try:
            area_value = float(area)
            rainfall_value = float(rainfall)

            if area_value <= 0 or rainfall_value < 0:
                raise ValueError

            water_per_acre = {
                "Rice": 25000,
                "Tomato": 12000,
                "Maize": 15000,
                "Cotton": 18000,
                "Sugarcane": 25000,
                "Groundnut": 10000
            }

            estimated = water_per_acre.get(crop, 15000) * area_value
            reduction = min(rainfall_value * 0.01, 0.5)
            estimated = round(estimated * (1 - reduction))

            result["water"] = estimated
            result["area"] = area_value
            result["water_note"] = (
                "Planning estimate only. Check soil moisture, local rainfall "
                "and agricultural advice before irrigation."
            )
        except ValueError:
            result["water_error"] = "Enter a positive area and valid rainfall amount."

    return render_template("index.html", result=result, city=city)


if __name__ == "__main__":
    app.run(debug=True)
