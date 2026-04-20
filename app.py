from flask import Flask, render_template, request
import pandas as pd
import joblib

app = Flask(__name__)

model = joblib.load("churn_model.pkl")
model_columns = joblib.load("model_columns.pkl")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.form

        input_data = pd.DataFrame({
            "gender": [data.get("gender", "Male")],
            "SeniorCitizen": [int(data.get("SeniorCitizen", 0))],
            "Partner": [data.get("Partner", "No")],
            "Dependents": [data.get("Dependents", "No")],
            "tenure": [int(data.get("tenure", 1))],
            "PhoneService": [data.get("PhoneService", "Yes")],
            "InternetService": [data.get("InternetService", "DSL")],
            "Contract": [data.get("Contract", "Month-to-month")],
            "MonthlyCharges": [float(data.get("MonthlyCharges", 0))],
            "TotalCharges": [float(data.get("TotalCharges", 0))]
        })

        # Feature engineering
        input_data["avg_monthly_spend"] = input_data["TotalCharges"] / (input_data["tenure"] + 1)
        input_data["contract_risk"] = (input_data["Contract"] == "Month-to-month").astype(int)

        # Encoding
        input_data = pd.get_dummies(input_data)
        input_data = input_data.reindex(columns=model_columns, fill_value=0)

        print(input_data.head())  # Debug

        # Prediction
        prediction = model.predict(input_data)[0]
        probs = model.predict_proba(input_data)[0]

        stay_prob = probs[0]
        churn_prob = probs[1]

        if prediction == 1:
            result = f"⚠️ High Risk of Churn ({churn_prob:.2f})"
        else:
            result = f"✅ Customer Likely to Stay ({stay_prob:.2f})"

        return render_template("index.html",
                               prediction_text=result,
                               stay_prob=round(stay_prob, 2),
                               churn_prob=round(churn_prob, 2))

    except Exception as e:
        return render_template("index.html", prediction_text=f"Error: {e}")


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)