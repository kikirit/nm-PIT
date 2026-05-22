"""
Newton's Divided Differences Interpolation Method.

This module implements:
1. Generation of the divided difference table.
2. Calculation of the interpolated value at a given target x.
3. Generation of a clean string representation of the Newton polynomial.
"""

def divided_difference_table(x_values, y_values):
    """
    Generates the complete divided difference table.
    
    Parameters:
        x_values (list of float): The x-coordinates of the data points.
        y_values (list of float): The y-coordinates of the data points.
        
    Returns:
        list of list of float/None: A 2D grid of size n x n, representing 
        the divided difference table, where table[i][j] corresponds to 
        the j-th order divided difference starting at x_i. Unused entries 
        are filled with None.
    """
    n = len(x_values)
    # Initialize table with None
    table = [[None for _ in range(n)] for _ in range(n)]
    
    # Column 0 is filled with y values (0th order divided differences)
    for i in range(n):
        table[i][0] = float(y_values[i])
        
    # Calculate divided differences column by column
    for j in range(1, n):
        for i in range(n - j):
            denominator = float(x_values[i + j] - x_values[i])
            if denominator == 0.0:
                raise ValueError(
                    f"Duplicate x value detected at x = {x_values[i]}. "
                    "Cannot compute divided differences due to division by zero."
                )
            table[i][j] = (table[i + 1][j - 1] - table[i][j - 1]) / denominator
            
    return table

def newton_interpolation(x_values, table, x):
    """
    Computes the interpolated y value for a given x using Newton's polynomial.
    
    Parameters:
        x_values (list of float): The x-coordinates of the data points.
        table (list of list of float/None): The divided difference table.
        x (float): The target point to interpolate.
        
    Returns:
        float: The interpolated y value.
    """
    n = len(x_values)
    y = table[0][0]
    term = 1.0
    
    for j in range(1, n):
        term *= (x - x_values[j - 1])
        y += table[0][j] * term
        
    return y

def polynomial_string(x_values, coefficients):
    """
    Generates a LaTeX-formatted Newton interpolating polynomial.
    """

    n = len(x_values)

    if n == 0:
        return "P(x)=0"

    terms = []

    for j in range(n):

        coeff = coefficients[j]

        if coeff is None or abs(coeff) < 1e-12:
            continue

        coeff_rounded = round(coeff, 6)

        # Sign handling
        if j == 0:
            sign = ""
        else:
            sign = "+" if coeff_rounded >= 0 else "-"

        coeff_abs = abs(coeff_rounded)

        # Coefficient formatting
        if coeff_abs == 1 and j != 0:
            coeff_part = ""
        else:
            coeff_part = f"{coeff_abs:g}"

        # Product terms
        factors = []

        for k in range(j):

            xk = x_values[k]

            if xk == 0:
                factors.append("(x)")
            elif xk > 0:
                factors.append(f"(x-{xk:g})")
            else:
                factors.append(f"(x+{abs(xk):g})")

        factor_string = "".join(factors)

        term = f"{sign} {coeff_part}{factor_string}".strip()

        terms.append(term)

    polynomial = " ".join(terms)

    return f"P(x) = {polynomial}"

def generate_steps(x_values, y_values, table):
    """
    Generates readable divided difference calculations.
    """

    n = len(x_values)

    steps = []

    for j in range(1, n):

        order_steps = []

        for i in range(n - j):

            result = table[i][j]

            formula = (
                f"f[x_{{{i}}},\\ldots,x_{{{i+j}}}] = "
                f"\\frac{{{table[i + 1][j - 1]:.4f} - {table[i][j - 1]:.4f}}}"
                f"{{{x_values[i + j]:.4f} - {x_values[i]:.4f}}}"
                f" = {result:.4f}"
            )

            order_steps.append({
                "formula": formula
            })

        steps.append({
            "order": j,
            "calculations": order_steps
        })

    return steps