from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
h = svg2rlg("C:/Users/HenryS/Downloads/86548cb347b5acfb41bcb328c89b9bdc.svg")
renderPM.drawToFile(h, "excbg.png", "PNG")
