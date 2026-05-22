import os
import io
import uuid
import time
import base64
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

from flask import Flask, render_template, request, redirect, url_for
from methods.newton_divided import (
    divided_difference_table,
    newton_interpolation,
    polynomial_string
)

app = Flask(__name__)

app = app


def cleanup_old_plots():

    try:
        folder = os.path.join(app.root_path, 'static', 'generated')

        if not os.path.exists(folder):
            return

        now = time.time()

        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)

            if os.path.isfile(filepath) and filename.endswith('.png'):

                if now - os.path.getmtime(filepath) > 300:
                    os.remove(filepath)

    except Exception:
        pass


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/examples")
def examples():
    return render_template("examples.html")


@app.route("/discussion")
def discussion():
    return render_template("discussion.html")


@app.route("/calculate", methods=["POST"])
def calculate():

    x_val_str = request.form.get("x_values", "").strip()
    y_val_str = request.form.get("y_values", "").strip()
    x_target_str = request.form.get("x_target", "").strip()

    error_msg = None

    if not x_val_str or not y_val_str or not x_target_str:
        error_msg = "All fields are required. Please enter values."

    else:

        try:

            try:
                x_target = float(x_target_str)

            except ValueError:
                raise ValueError(
                    "The interpolation point 'x' must be a valid number."
                )

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

            if len(x_values) < 2:
                raise ValueError(
                    "Please provide at least 2 data points (n >= 2)."
                )

            if len(x_values) != len(y_values):
                raise ValueError(
                    f"The number of X values ({len(x_values)}) "
                    f"must match the number of Y values ({len(y_values)})."
                )

            if len(x_values) != len(set(x_values)):
                raise ValueError(
                    "Duplicate X values are not allowed."
                )

        except ValueError as ve:
            error_msg = str(ve)

    if error_msg:

        return render_template(
            "index.html",
            error=error_msg,
            x_val_str=x_val_str,
            y_val_str=y_val_str,
            x_target=x_target_str
        )

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

    fig, ax = plt.subplots(
        figsize=(8, 5),
        facecolor='#0f172a'
    )

    ax.set_facecolor('#111827')

    min_x = min(x_values)
    max_x = max(x_values)

    span = max_x - min_x

    margin = span * 0.15 if span != 0 else 1.0

    x_start = min_x - margin
    x_end = max_x + margin

    x_curve = [
        x_start + i * (x_end - x_start) / 299.0
        for i in range(300)
    ]

    y_curve = [
        newton_interpolation(x_values, table, xc)
        for xc in x_curve
    ]

    line, = ax.plot(
        x_curve,
        y_curve,
        color='#8b5cf6',
        linestyle='-',
        linewidth=3.0,
        label='Newton Polynomial'
    )

    line.set_path_effects([
        pe.Stroke(
            linewidth=8,
            foreground='#8b5cf644'
        ),
        pe.Normal()
    ])

    ax.scatter(
        x_values,
        y_values,
        color='#22c55e',
        edgecolors='white',
        linewidths=1,
        s=90,
        zorder=5,
        label='Data Points'
    )

    ax.scatter(
        [x_target],
        [y_result],
        color='#f43f5e',
        marker='*',
        edgecolors='white',
        linewidths=1,
        s=260,
        zorder=6,
        label=f'P({x_target:.2f}) = {y_result:.2f}'
    )

    ax.set_title(
        "Newton Divided Differences Interpolation",
        color='#e2e8f0',
        fontsize=16,
        fontweight='bold',
        pad=18
    )

    ax.set_xlabel(
        "X Axis",
        color='#cbd5e1',
        fontsize=12
    )

    ax.set_ylabel(
        "Y Axis",
        color='#cbd5e1',
        fontsize=12
    )

    ax.grid(
        True,
        color='#475569',
        linestyle='--',
        linewidth=0.7,
        alpha=0.35
    )

    ax.tick_params(
        colors='#cbd5e1',
        which='both'
    )

    for spine in ax.spines.values():
        spine.set_color('#64748b')
        spine.set_linewidth(1.2)

    legend = ax.legend(
        facecolor='#1e293b',
        edgecolor='#475569',
        fontsize=10
    )

    for text in legend.get_texts():
        text.set_color('#f8fafc')

    legend.get_frame().set_alpha(0.9)

    plot_filename = f"plot_{uuid.uuid4().hex}.png"

    generated_dir = os.path.join(
        app.root_path,
        'static',
        'generated'
    )

    buf = io.BytesIO()

    plt.savefig(
        buf,
        format='png',
        bbox_inches='tight',
        dpi=160
    )

    buf.seek(0)

    plot_base64 = base64.b64encode(
        buf.getvalue()
    ).decode('utf-8')

    plot_url = f"data:image/png;base64,{plot_base64}"

    try:

        os.makedirs(
            generated_dir,
            exist_ok=True
        )

        filepath = os.path.join(
            generated_dir,
            plot_filename
        )

        plt.savefig(
            filepath,
            format='png',
            bbox_inches='tight',
            dpi=160
        )

    except Exception:
        pass

    plt.clf()
    plt.close('all')

    cleanup_old_plots()

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
    return redirect(url_for('home'))


if __name__ == "__main__":

    os.makedirs(
        os.path.join(
            app.root_path,
            'static',
            'generated'
        ),
        exist_ok=True
    )

    app.run(debug=True)