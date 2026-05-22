import os
import io
import uuid
import time
import base64
import matplotlib

# Use non-interactive Agg backend to prevent GUI issues and memory leaks
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np

from flask import Flask, render_template, request, redirect, url_for

from methods.newton_divided import (
    divided_difference_table,
    newton_interpolation,
    polynomial_string
)

app = Flask(__name__)

# Assign app to a variable of the same name for Vercel's WSGI server compatibility
app = app


def cleanup_old_plots():
    """Removes generated plot images older than 5 minutes to manage disk usage."""

    try:

        folder = os.path.join(app.root_path, 'static', 'generated')

        if not os.path.exists(folder):
            return

        now = time.time()

        for filename in os.listdir(folder):

            filepath = os.path.join(folder, filename)

            if os.path.isfile(filepath) and filename.endswith('.png'):

                # 300 seconds = 5 minutes
                if now - os.path.getmtime(filepath) > 300:
                    os.remove(filepath)

    except Exception:
        # Prevent any filesystem permission errors from crashing the app
        pass


@app.route("/")
def home():
    """Renders the main educational calculator page."""
    return render_template("index.html")


@app.route("/examples")
def examples():
    """Renders the worked examples page."""
    return render_template("examples.html")


@app.route("/discussion")
def discussion():
    """Renders the mathematical discussion page."""
    return render_template("discussion.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    """
    Handles interpolation requests.
    Validates inputs, calculates the divided difference table,
    constructs the polynomial, plots the graph,
    and renders the result page.
    """

    # 1. Retrieve raw inputs
    
    x_val_str = request.form.get("x_values", "").strip()
    y_val_str = request.form.get("y_values", "").strip()
    x_target_str = request.form.get("x_target", "").strip()

    error_msg = None

    # 2. Input Validation
    

    if not x_val_str or not y_val_str or not x_target_str:

        error_msg = "All fields are required. Please enter values."

    else:

        try:

            # Parse target interpolation point
            try:
                x_target = float(x_target_str)

            except ValueError:
                raise ValueError(
                    "The interpolation point 'x' must be a valid number."
                )

            # Parse X values
            try:
                x_values = [
                    float(x.strip())
                    for x in x_val_str.split(",")
                    if x.strip()
                ]

            except ValueError:
                raise ValueError(
                    "X values must contain only numbers separated by commas."
                )

            # Parse Y values
            try:
                y_values = [
                    float(y.strip())
                    for y in y_val_str.split(",")
                    if y.strip()
                ]

            except ValueError:
                raise ValueError(
                    "Y values must contain only numbers separated by commas."
                )

            # Check for minimum points
            if len(x_values) < 2:

                raise ValueError(
                    "Please provide at least 2 data points (n >= 2)."
                )

            # Verify arrays are equal in size
            if len(x_values) != len(y_values):

                raise ValueError(
                    f"The number of X values ({len(x_values)}) "
                    f"must match the number of Y values ({len(y_values)})."
                )

            # Check for duplicate X values
            if len(x_values) != len(set(x_values)):

                raise ValueError(
                    "Duplicate X values are not allowed."
                )

        except ValueError as ve:

            error_msg = str(ve)

    # 3. Validation Failed

    if error_msg:

        return render_template(
            "index.html",
            error=error_msg,
            x_val_str=x_val_str,
            y_val_str=y_val_str,
            x_target=x_target_str
        )

    # 4. Perform Calculations

    try:

        table = divided_difference_table(
            x_values,
            y_values
        )

        y_result = newton_interpolation(
            x_values,
            table,
            x_target
        )

        poly_str = polynomial_string(
            x_values,
            table[0]
        )

    except ValueError as ve:

        return render_template(
            "index.html",
            error=str(ve),
            x_val_str=x_val_str,
            y_val_str=y_val_str,
            x_target=x_target_str
        )

    # 5. Generate Matplotlib Plot — premium dark theme matching the redesigned UI
    BG_BASE    = '#06090f'
    BG_SURFACE = '#0d1320'
    C_CURVE    = '#00c4d4'   # teal — polynomial curve
    C_POINTS   = '#0fe0a2'   # emerald — data points
    C_TARGET   = '#fbbf24'   # amber — interpolated star
    C_GRID     = '#1e2d45'
    C_TICK     = '#4a6080'
    C_TEXT     = '#8fa3bf'
    C_TITLE    = '#f1f5f9'

    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor=BG_BASE)
    ax.set_facecolor(BG_SURFACE)
    fig.patch.set_alpha(1.0)

    # Build smooth curve range with margin
    min_x = min(x_values)
    max_x = max(x_values)
    span   = max_x - min_x
    margin = span * 0.18 if span != 0 else 1.0
    x_start = min_x - margin
    x_end   = max_x + margin

    # 400 sample points for a smooth curve
    x_curve = [x_start + i * (x_end - x_start) / 399.0 for i in range(400)]
    y_curve = [newton_interpolation(x_values, table, xc) for xc in x_curve]

    # Curve — dashed teal line with subtle fill
    ax.plot(x_curve, y_curve, color=C_CURVE, linestyle='--',
            linewidth=2.2, alpha=0.9, label='Newton Polynomial P(x)', zorder=2)
    ax.fill_between(x_curve, y_curve, alpha=0.05, color=C_CURVE, zorder=1)

    # Data points — emerald circles
    ax.scatter(x_values, y_values, color=C_POINTS, s=90, zorder=5,
               edgecolors='#ffffff', linewidths=0.8, label='Known data points')

    # Interpolated point — amber star
    ax.scatter([x_target], [y_result], color=C_TARGET, marker='*', s=260,
               zorder=6, edgecolors='#ffffff', linewidths=0.6,
               label=f'P({x_target:.4g}) = {y_result:.6g}')

    # Annotate interpolated point
    ax.annotate(
        f'  ({x_target:.4g}, {y_result:.4g})',
        (x_target, y_result),
        fontsize=8, color=C_TARGET,
        va='bottom', ha='left',
        xytext=(6, 8), textcoords='offset points'
    )

    # Title & axis labels
    ax.set_title("Newton's Divided Differences — Interpolation Curve",
                 color=C_TITLE, fontsize=12, fontweight='bold', pad=14)
    ax.set_xlabel("x", color=C_TEXT, fontsize=10)
    ax.set_ylabel("P(x)", color=C_TEXT, fontsize=10)

    # Spines — only bottom & left
    for spine_name, spine in ax.spines.items():
        if spine_name in ('top', 'right'):
            spine.set_visible(False)
        else:
            spine.set_color(C_GRID)
            spine.set_linewidth(0.8)

    # Horizontal grid only, very subtle
    ax.yaxis.grid(True, color=C_GRID, linestyle='-', linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(colors=C_TICK, which='both', labelsize=8.5)

    # Legend
    leg = ax.legend(facecolor=BG_BASE, edgecolor=C_GRID,
                    fontsize=8.5, framealpha=0.85, loc='best')
    for text in leg.get_texts():
        text.set_color(C_TEXT)

    # Prevent clipping
    plt.tight_layout()

    # 6. Save Plot

    plot_filename = f"plot_{uuid.uuid4().hex}.png"

    generated_dir = os.path.join(
        app.root_path,
        'static',
        'generated'
    )

    # Generate Base64 inline source
    buf = io.BytesIO()

    plt.savefig(
        buf,
        format='png',
        bbox_inches='tight',
        dpi=140
    )

    buf.seek(0)

    plot_base64 = base64.b64encode(
        buf.getvalue()
    ).decode('utf-8')

    plot_url = f"data:image/png;base64,{plot_base64}"

    # Optional local save
    try:

        os.makedirs(generated_dir, exist_ok=True)

        filepath = os.path.join(
            generated_dir,
            plot_filename
        )

        plt.savefig(
            filepath,
            format='png',
            bbox_inches='tight',
            dpi=140
        )

    except Exception:
        pass

    # Close figures to release memory

    plt.clf()
    plt.close('all')

    # Cleanup old plots

    cleanup_old_plots()

    # 7. Render Results

    return render_template(
        "result.html",
        x_target=x_target,
        y_result=y_result,
        x_values=x_values,
        table=table,
        poly_str=poly_str,
        plot_url=plot_url
    )


@app.errorhandler(404)
def page_not_found(e):
    """Fallback redirect to landing page for missing routes."""
    return redirect(url_for('home'))


if __name__ == "__main__":

    # Ensure generated directory exists locally
    os.makedirs(
        os.path.join(app.root_path, 'static', 'generated'),
        exist_ok=True
    )

    app.run(debug=True)
