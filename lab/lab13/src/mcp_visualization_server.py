import io
import base64
import matplotlib.pyplot as plt
from typing import Annotated
from fastmcp import FastMCP


mcp = FastMCP("Visualization Server")

@mcp.tool(description="Creates a line plot from data and returns a base64 encoded PNG image.")
def line_plot(
    data: Annotated[list[list[float]], "A list of lists ."],
    title: Annotated[str, "The title of the plot."] = "",
    x_label: Annotated[str, "Label for the X-axis."] = "",
    y_label: Annotated[str, "Label for the Y-axis."] = "",
    show_legend: Annotated[bool, "Whether to display the legend."] = False
) -> str:
    plt.figure(figsize=(10, 6))

    for i, points in enumerate(data):
        label = f"Series {i + 1}"
        plt.plot(points, marker='o', label=label)

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid(True, linestyle='--', alpha=0.7)

    if show_legend:
        plt.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')

    return img_base64



if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8004)