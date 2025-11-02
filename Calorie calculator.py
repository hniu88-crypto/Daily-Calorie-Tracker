import subprocess
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

# ===== Auto-install missing packages =====
def install_package(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

try:
    import pandas as pd
except ImportError:
    print("pandas not found. Installing...")
    install_package("pandas")
    import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib not found. Installing...")
    install_package("matplotlib")
    import matplotlib.pyplot as plt

# ===== File setup =====
FOOD_FILE = "food_data.csv"
LOG_FILE = "food_log.csv"
PROFILE_FILE = "user_profile.csv"
today = str(date.today())

# ===== User Profile =====
def load_or_create_profile():
    if os.path.exists(PROFILE_FILE):
        df = pd.read_csv(PROFILE_FILE)
        return df.iloc[0].to_dict()
    else:
        print("=== Create Your Profile ===")
        name = input("Name: ").strip() or "User"
        sex = input("Gender (M/F): ").strip().upper()
        height = float(input("Height (cm): "))
        weight = float(input("Weight (kg): "))
        age = int(input("Age: "))

        print("\nActivity Level:")
        print("1. Sedentary (little or no exercise)")
        print("2. Lightly active (1–3 days/week)")
        print("3. Moderately active (3–5 days/week)")
        print("4. Very active (6–7 days/week)")
        print("5. Extra active (physical job or athlete)")
        act_choice = input("Choose activity level (1–5): ").strip()
        activity_factors = {"1":1.2, "2":1.375, "3":1.55, "4":1.725, "5":1.9}
        act_factor = activity_factors.get(act_choice, 1.2)

        profile = {
            "name": name, "sex": sex, "height": height,
            "weight": weight, "age": age, "activity_factor": act_factor
        }
        pd.DataFrame([profile]).to_csv(PROFILE_FILE, index=False)
        return profile

def calculate_tdee(profile):
    """Calculate recommended daily calorie intake (TDEE)"""
    if profile["sex"] == "M":
        bmr = 10 * profile["weight"] + 6.25 * profile["height"] - 5 * profile["age"] + 5
    else:
        bmr = 10 * profile["weight"] + 6.25 * profile["height"] - 5 * profile["age"] - 161
    tdee = bmr * profile["activity_factor"]
    return round(tdee, 1)

profile = load_or_create_profile()
tdee = calculate_tdee(profile)

# ===== Food Database =====
def load_food_data():
    if os.path.exists(FOOD_FILE):
        df = pd.read_csv(FOOD_FILE)
        return {food.lower(): cal for food, cal in zip(df["food"], df["calories_per_100g"])}
    else:
        default_data = {
            "Rice": 116, "Bread": 265, "Chicken breast": 165, "Apple": 52,
            "Egg": 155, "Milk": 60, "Banana": 89, "Potato": 77
        }
        default_data_lower = {k.lower(): v for k, v in default_data.items()}
        pd.DataFrame(list(default_data_lower.items()), columns=["food", "calories_per_100g"]).to_csv(FOOD_FILE, index=False)
        return default_data_lower

def ensure_log_file():
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=["date","food","weight(g)","calories"]).to_csv(LOG_FILE, index=False)

food_data = load_food_data()
ensure_log_file()
df_log = pd.read_csv(LOG_FILE)
today_log = df_log[df_log["date"] == today].copy()

# ===== Functions =====
def save_food_database():
    pd.DataFrame(list(food_data.items()), columns=["food", "calories_per_100g"]).to_csv(FOOD_FILE, index=False)

def add_new_food():
    name = input("Enter new food name: ").strip().lower()
    if not name:
        print("Food name cannot be empty!")
        return
    try:
        kcal = float(input("Enter calories per 100g: "))
    except ValueError:
        print("Invalid calorie value!")
        return
    food_data[name] = kcal
    save_food_database()
    print(f"Added {name.capitalize()} ({kcal} kcal/100g) to database.")

def add_food_entry():
    global today_log, df_log
    food = input("Enter food name: ").strip().lower()
    if food not in food_data:
        print(f"{food.capitalize()} not found in database. Please add it first.")
        return
    try:
        weight = float(input("Enter weight in grams: "))
    except ValueError:
        print("Invalid weight!")
        return
    calories = food_data[food] * weight / 100
    print(f"{food.capitalize()} ({weight}g) = {calories:.2f} kcal")
    today_log = pd.concat([today_log, pd.DataFrame([{
        "date": today,
        "food": food,
        "weight(g)": weight,
        "calories": calories
    }])], ignore_index=True)
    df_log = pd.concat([df_log[df_log["date"] != today], today_log], ignore_index=True)
    df_log.to_csv(LOG_FILE, index=False)

def show_today_log():
    if today_log.empty:
        print("No entries today.")
        print(f"Recommended calorie intake: {tdee:.0f} kcal\n")
        return
    print("\nToday's Food Log:")
    log_display = today_log.copy()
    log_display["food"] = log_display["food"].str.capitalize()
    print(log_display[["food","weight(g)","calories"]].to_string(index=False))
    total = today_log["calories"].sum()
    print(f"Total calories consumed: {total:.2f} kcal")
    print(f"Recommended intake (TDEE): {tdee:.2f} kcal")
    diff = total - tdee
    if diff > 0:
        print(f"⚠️ You exceeded your goal by {diff:.1f} kcal.\n")
    else:
        print(f"✅ You are {abs(diff):.1f} kcal under your goal.\n")

def show_weekly_chart():
    if df_log.empty:
        print("No data to show.")
        return
    df_log["date"] = pd.to_datetime(df_log["date"])
    week_start = pd.to_datetime(date.today()) - pd.Timedelta(days=6)
    weekly = df_log[df_log["date"] >= week_start].groupby("date")["calories"].sum().reset_index()
    if weekly.empty:
        print("No records in the last 7 days.")
        return
    weekly = weekly.sort_values("date")
    plt.figure(figsize=(8,4))
    plt.plot(weekly["date"], weekly["calories"], marker="o", label="Actual intake")
    plt.axhline(y=tdee, color="r", linestyle="--", label="Recommended")
    plt.title("Last 7 Days Calorie Trend")
    plt.xlabel("Date")
    plt.ylabel("Calories (kcal)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def show_profile():
    print("\n=== Current Profile ===")
    for k, v in profile.items():
        print(f"{k.capitalize()}: {v}")
    print(f"Recommended daily intake: {tdee:.0f} kcal")

def main_menu():
    while True:
        print("\n=== Daily Calorie Tracker ===")
        print("1. Add Food Entry")
        print("2. Add New Food to Database")
        print("3. Show Today's Log")
        print("4. Show Last 7 Days Calorie Trend")
        print("5. Show My Profile")
        print("6. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            add_food_entry()
        elif choice == "2":
            add_new_food()
        elif choice == "3":
            show_today_log()
        elif choice == "4":
            show_weekly_chart()
        elif choice == "5":
            show_profile()
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()
