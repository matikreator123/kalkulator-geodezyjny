import math
import statistics
import os
import random

# --- Import Danych ---
if os.path.exists("pomiar.txt"):
    print("Plik 'pomiar.txt' został wykryty.")
else:
    print("Plik 'pomiar.txt' nie został wykryty.")
    create_file = input("Czy chcesz utworzyć 'pomiar.txt' z przykładowymi danymi? tak/nie: ").lower()
    if create_file == "tak":
        random_base_number = random.uniform(30.0, 110.0)
        formatted_1 = f"{random_base_number:.4f}"
        formatted_1a = f"{(random_base_number + random.uniform(-0.001, 0.001)+200):.4f}"
        formatted_2 = f"{(random_base_number + random.uniform(-0.001, 0.001)):.4f}"
        formatted_2a = f"{(random_base_number + random.uniform(-0.001, 0.001)+200):.4f}"
        formatted_3 = f"{(random_base_number + random.uniform(-0.001, 0.001)):.4f}"
        formatted_3a = f"{(random_base_number + random.uniform(-0.001, 0.001)+200):.4f}"
        with open("pomiar.txt", "w") as file:
            file.write(f"{formatted_1} {formatted_1a}\n")
            file.write(f"{formatted_2} {formatted_2a}\n")
            file.write(f"{formatted_3} {formatted_3a}")
        print("'pomiar.txt' został utworzony z przykładowymi danymi.")
    else:
        print("Nie można kontynuować bez pliku 'pomiar.txt'. Program zostanie zakończony.")
        exit()

measurements = []
with open("pomiar.txt", "r") as file:
     for line in file:
         measurements.append([float(x) for x in line.split()])

# Obliczenie odchyleń w [cc]
raw_deviations_cc = []
for m in measurements:
    absolute_difference = abs(m[0] - m[1]) - 200
    raw_deviations_cc.append(round((absolute_difference / 2) * 10000, 2))

# --- Wybór trybu ---
print("Proszę wybrać tryb:")
print("1. Wyłącznie kolimacja")
print("2. Wyłącznie inklinacja")
print("3. Znana kolimacja (oblicz inklinację)")
print("4. Znana inklinacja (oblicz kolimację)")
mode = input("Wybór: ").lower()

# --- WARIANT 1: WYŁĄCZNIE KOLIMACJA ---
if mode == "1":
    collimation = round(statistics.mean(raw_deviations_cc), 2)
    print(f"Średnia kolimacja (c): {collimation} [cc]")
    
    residual_v = [round(value - collimation, 2) for value in raw_deviations_cc]
    vv = [round(v**2, 2) for v in residual_v]
    mean_collimation_error = math.sqrt(sum(vv) / (len(measurements) * (len(measurements) - 1)))
    print(f"Średni błąd kolimacji (m_c): \u00B1{round(mean_collimation_error, 2)} [cc]")
    
# --- WARIANT 2: WYŁĄCZNIE INKLINACJA ---
elif mode == "2":
    z_grad = float(input("Wprowadź odległość zenitową (z) w gradach: "))
    z_rad = (z_grad * math.pi) / 200
    
    calc_i_values = []
    for delta in raw_deviations_cc:
        i_val = delta * math.tan(z_rad)
        calc_i_values.append(round(i_val, 2))
    
    inclination = round(statistics.mean(calc_i_values), 2)
    
    residual_v_i = [round(value - inclination, 2) for value in calc_i_values]
    vv_i = [round(v**2, 2) for v in residual_v_i]
    
    mean_inclination_error = math.sqrt(sum(vv_i) / (len(measurements) * (len(measurements) - 1)))
    
    print(f"\nInklinacja (i): {inclination} [cc]")
    print(f"Średni błąd inklinacji (m_i): \u00B1{round(mean_inclination_error, 2)} [cc]")

# --- WARIANT 3: OBLICZANIE INKLINACJI (i) ---
elif mode == "3":
    try:
        z_grad = float(input("Wprowadź odległość zenitową (z) w gradach: "))
        if z_grad % 200 == 0:
            raise ValueError("Odległość zenitowa nie może być wielokrotnością 200g.")
            
        known_c = float(input("Wprowadź znany błąd kolimacji (c) w [cc]: "))
        z_rad = (z_grad * math.pi) / 200
        
        calc_i_values = []
        for delta in raw_deviations_cc:
            # i = (delta - c/sin(z)) * tan(z)
            i_val = (delta - (known_c / math.sin(z_rad))) * math.tan(z_rad)
            calc_i_values.append(i_val)
        
        inclination = statistics.mean(calc_i_values)
        n = len(calc_i_values)
        v_squared_sum = sum((v - inclination)**2 for v in calc_i_values)
        m_i = math.sqrt(v_squared_sum / (n * (n - 1)))
        
        print(f"\nInklinacja (i): {inclination:.2f} [cc]")
        print(f"Średni błąd inklinacji (m_i): ±{m_i:.2f} [cc]")
    except ValueError as e:
        print(f"Błąd danych: {e}")

# --- WARIANT 4: OBLICZANIE KOLIMACJI (c) ---
elif mode == "4":
    z_grad = float(input("Wprowadź odległość zenitową (z) w gradach: "))
    known_i = float(input("Wprowadź znany błąd inklinacji przyrządu (i) w [cc]: "))
    z_rad = (z_grad * math.pi) / 200
    
    # Wzór: c = (delta - i/tan(z)) * sin(z)
    calc_c_values = []
    for delta in raw_deviations_cc:
        c_val = (delta - (known_i / math.tan(z_rad))) * math.sin(z_rad)
        calc_c_values.append(round(c_val, 2))
    
    collimation = round(statistics.mean(calc_c_values), 2)
    residual_v_c = [round(Value - collimation, 2) for Value in calc_c_values]
    vv_c = [round(v**2, 2) for v in residual_v_c]
    mean_collimation_error = math.sqrt(sum(vv_c) / (len(measurements) * (len(measurements) - 1)))
    
    print(f"\nKolimacja (c): {collimation} [cc]")
    print(f"Średni błąd kolimacji (m_c): \u00B1{round(mean_collimation_error, 2)} [cc]")
else:
    print("Nieprawidłowy wybór trybu. Spróbuj ponownie.")