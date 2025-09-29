import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from PIL import Image

# ---------------------
# BAC CALCULATION
# ---------------------
def calculate_bac(drinks, drink_size_oz, alcohol_percent, weight_lbs, sex, hours_elapsed, metabolism_rate):
    weight_grams = weight_lbs * 453.592
    total_alcohol_g = drinks * drink_size_oz * (alcohol_percent/100) * 29.5735 * 0.789
    r = 0.73 if sex.lower() == "male" else 0.66
    bac = (total_alcohol_g / (weight_grams * r)) * 100
    bac -= metabolism_rate * hours_elapsed
    return max(bac, 0)

# ---------------------
# PLOT FUNCTION
# ---------------------
def plot_bac_curve(current_bac, peak_bac, time_to_zero):
    fig, ax = plt.subplots(figsize=(6,3))

    t = np.linspace(0, time_to_zero, 200)
    bac_curve = np.maximum(current_bac - t * 0.015, 0)

    # Plot BAC curve with color coding
    for i in range(len(t)-1):
        if bac_curve[i] < 0.08:
            color="green"
        elif bac_curve[i] < 0.2:
            color="yellow"
        else:
            color="red"
        ax.plot(t[i:i+2], bac_curve[i:i+2], color=color, linewidth=3)

    # Shaded zones
    ax.axhspan(0.08, 0.2, color="yellow", alpha=0.2)
    ax.axhspan(0.2, 0.4, color="red", alpha=0.2)

    # Horizontal markers
    ax.axhline(0.08, color="orange", linestyle="--", linewidth=1)
    ax.text(time_to_zero*0.95, 0.08, "🚗 Legal Limit", color="orange", va="bottom", ha="right")
    
    ax.axhline(0.3, color="darkred", linestyle="--", linewidth=1)
    ax.text(time_to_zero*0.95, 0.3, "⚠️ High Risk", color="darkred", va="bottom", ha="right")

    # Peak BAC emoji if above legal limit
    if peak_bac >= 0.08:
        ax.text(0.5*time_to_zero, peak_bac, "⚠️", fontsize=16, ha="center", va="bottom")
    
    # Time to legal limit emoji
    time_to_legal = max((current_bac - 0.08)/0.015, 0)
    if current_bac > 0.08:
        ax.plot(time_to_legal, 0.08, "ro")  # red dot
        ax.text(time_to_legal, 0.08, "🚗", ha="center", va="bottom", fontsize=12)

    # ---------------------
    # Safe Driving Bar
    # ---------------------
    bar_height = -0.05  # below x-axis
    for i in range(len(t)-1):
        if bac_curve[i] < 0.08:
            color="green"
        elif bac_curve[i] < 0.2:
            color="yellow"
        else:
            color="red"
        ax.plot(t[i:i+2], [bar_height]*2, color=color, linewidth=6, solid_capstyle='butt')

    # Overlay emojis along bar
    ax.text(0, bar_height, "🚗", ha="center", va="center", fontsize=12)
    stop_time_index = np.argmax(bac_curve > 0.08)
    if stop_time_index > 0:
        ax.text(t[stop_time_index], bar_height, "❌", ha="center", va="center", fontsize=12)

    # Labels and title
    ax.set_xlabel("Hours")
    ax.set_ylabel("BAC (%)")
    ax.set_ylim(bar_height-0.02, max(bac_curve.max(), 0.35))
    ax.set_title("Estimated BAC Over Time with Risk Dashboard")
    
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf

# ---------------------
# RUN FUNCTION
# ---------------------
def run_bac(drinks, drink_size, alcohol_percent, weight, sex, hours_elapsed, metabolism_rate):
    bac_now = calculate_bac(drinks, drink_size, alcohol_percent, weight, sex, hours_elapsed, metabolism_rate)
    peak_bac = calculate_bac(drinks, drink_size, alcohol_percent, weight, sex, 0, metabolism_rate)
    time_to_zero = bac_now / metabolism_rate if metabolism_rate>0 else 0.1
    time_to_legal = max((bac_now - 0.08)/metabolism_rate, 0)

    buf = plot_bac_curve(bac_now, peak_bac, time_to_zero)
    img = Image.open(buf)

    high_risk_warning = "⚠️ High risk!" if peak_bac >= 0.2 else ""
    info_text = (
        f"Current BAC: {bac_now:.3f}%\n"
        f"Peak BAC: {peak_bac:.3f}%\n"
        f"Estimated time to sober: {time_to_zero:.1f} hours\n"
        f"Time to reach legal limit: {time_to_legal:.1f} hours\n"
        f"{high_risk_warning}"
    )
    return img, info_text

# ---------------------
# GRADIO INTERFACE
# ---------------------
with gr.Blocks() as demo:
    gr.Markdown("## 🍺 POSNA's BAC Calculator with Full Risk Dashboard")
    
    with gr.Row():
        drinks = gr.Slider(1, 20, step=1, label="Number of Drinks")
        drink_size = gr.Slider(1, 16, step=1, label="Drink Size (oz)")
        alcohol_percent = gr.Slider(1, 50, step=1, label="Alcohol %")
    
    with gr.Row():
        weight = gr.Number(value=160, label="Weight (lbs)")
        sex = gr.Radio(["Male", "Female"], value="Male", label="Sex")
    
    hours_elapsed = gr.Slider(0, 12, step=0.1, label="Hours Since First Drink")
    metabolism_rate = gr.Slider(0.010, 0.030, step=0.001, value=0.015, label="Metabolism Rate (% per hour)")
    
    plot_output = gr.Image(label="BAC Chart")
    info_output = gr.Textbox(label="BAC Summary")

    btn = gr.Button("Calculate BAC")
    btn.click(
        run_bac,
        inputs=[drinks, drink_size, alcohol_percent, weight, sex, hours_elapsed, metabolism_rate],
        outputs=[plot_output, info_output]
    )

if __name__ == "__main__":
    demo.launch()
