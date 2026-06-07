import pyttsx3
from PyPDF2 import PdfReader
from tkinter.filedialog import askopenfilename

book = askopenfilename(
    title="Select PDF",
    filetypes=[("PDF Files", "*.pdf")]
)

reader = PdfReader(book)

player = pyttsx3.init()

for page in reader.pages:
    text = page.extract_text()
    if text:
        player.say(text)

player.runAndWait()   