def generate_latex_table_from_lists(rows, caption="", label=""):
    if not rows:
        return "No data provided."

    num_columns = len(rows[0])
    column_format = 'l' * num_columns  # Simple format, all columns left-aligned

    # Start building the LaTeX table code
    latex_table = r"\begin{table}[htb!]" + "\n"
    latex_table += r"    \centering" + "\n"
    latex_table += r"    \begin{tabular}{" + column_format + r"} \hline" + "\n"

    # Add rows to the table
    for row in rows:
        row_data = " & ".join(row)  # Join all elements in the row to form one string
        latex_table += "    " + row_data + r" \\" + "\n"

    # Close the tabular environment and add caption and label
    latex_table += r"    \hline" + "\n"
    latex_table += r"    \end{tabular}" + "\n"
    if caption:
        latex_table += r"    \caption{" + caption + "}" + "\n"
    if label:
        latex_table += r"    \label{" + label + "}" + "\n"
    latex_table += r"\end{table}"

    return latex_table


# Example usage:
# rows = [['Header1', 'Header2', 'Header3'], ['Data1', 'Data2', 'Data3'], ['Data4', 'Data5', 'Data6']]
# latex_code = generate_latex_table_from_lists(rows, caption="Sample Table", label="tab:sample_table")
# print(latex_code)