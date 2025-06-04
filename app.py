
import streamlit as st
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from binance.client import Client

# Initialisation Binance (lecture publique)
client = Client()

# Sidebar : paramètres utilisateur
st.sidebar.header("Paramètres de la stratégie")
usdt_amount = st.sidebar.number_input("Montant USDT", min_value=1.0, value=50.0, step=1.0)
profit_target_pct = st.sidebar.slider("Objectif de vente (+%)", min_value=0.5, max_value=10.0, value=2.0, step=0.5) / 100
buyback_drop_pct = st.sidebar.slider("Reprise d'achat (-%)", min_value=1.0, max_value=20.0, value=3.0, step=0.5) / 100
symbol = "ADAUSDT"

# Variables de simulation
state = st.session_state
if "cycle_active" not in state:
    state.cycle_active = False
    state.trade_history = []
    state.price_log = []

st.title("📈 Simulation de trading ADA (Binance)")
st.markdown("**Stratégie** : Achat ADA → Vente +%.2f%% → Rachat -%.2f%%" % (profit_target_pct * 100, buyback_drop_pct * 100))

start_button = st.button("Lancer la simulation", disabled=state.cycle_active)
stop_button = st.button("Arrêter", disabled=not state.cycle_active)

# Fonction pour obtenir le prix ADA
@st.cache_data(ttl=5)
def get_price():
    try:
        return float(client.get_symbol_ticker(symbol=symbol)['price'])
    except:
        return None

# Fonction d’affichage
def display_history():
    if not state.trade_history:
        st.info("Aucune simulation encore enregistrée.")
        return

    df = pd.DataFrame(state.trade_history, columns=["Heure", "Action", "Prix"])
    st.dataframe(df, use_container_width=True)

# Affichage graphique
def display_chart():
    if not state.price_log:
        return
    times = [row[0] for row in state.price_log]
    prices = [row[1] for row in state.price_log]
    plt.figure(figsize=(10, 3))
    plt.plot(times, prices, label="Prix ADA")
    for t in state.trade_history:
        if t[1] == "Achat":
            plt.axhline(y=t[2], color="green", linestyle="--", label="Achat")
        elif t[1] == "Vente":
            plt.axhline(y=t[2], color="red", linestyle=":", label="Vente")
        elif t[1] == "Rachat":
            plt.axhline(y=t[2], color="blue", linestyle="-.", label="Rachat")
    plt.xlabel("Heure")
    plt.ylabel("Prix USDT")
    plt.title("Évolution du prix ADA")
    plt.xticks(rotation=45)
    plt.legend()
    st.pyplot(plt)

# Logique de simulation
if start_button:
    state.cycle_active = True
    buy_price = get_price()
    if buy_price:
        quantity = round(usdt_amount / buy_price, 1)
        sell_target = round(buy_price * (1 + profit_target_pct), 4)
        rebuy_target = round(sell_target * (1 - buyback_drop_pct), 4)

        state.trade_history.append((datetime.now().strftime("%H:%M:%S"), "Achat", buy_price))
        st.success(f"Achat simulé de {quantity} ADA à {buy_price:.4f} USDT")
        st.info(f"Objectif de vente à {sell_target:.4f} (+{profit_target_pct*100:.2f}%)")
        st.info(f"Objectif de rachat à {rebuy_target:.4f} (-{buyback_drop_pct*100:.2f}%)")

        sold = False
        rebought = False

        while state.cycle_active:
            current_price = get_price()
            if current_price is None:
                st.warning("Erreur de connexion Binance")
                break

            now = datetime.now().strftime("%H:%M:%S")
            st.metric("Prix ADA", f"{current_price:.4f} USDT")
            state.price_log.append((now, current_price))

            if not sold and current_price >= sell_target:
                state.trade_history.append((now, "Vente", current_price))
                st.success(f"Vente simulée à {current_price:.4f}")
                sold = True

            elif sold and current_price <= rebuy_target:
                state.trade_history.append((now, "Rachat", current_price))
                st.success(f"Rachat simulé à {current_price:.4f}")
                state.cycle_active = False

            time.sleep(10)
            st.rerun()

if stop_button:
    state.cycle_active = False
    st.warning("Simulation arrêtée")

st.markdown("---")
st.subheader("Historique des actions 🧾")
display_history()
st.subheader("Graphique ADA en temps réel 📊")
display_chart()
