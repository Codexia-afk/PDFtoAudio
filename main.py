import pyttsx3
from PyPDF2 import PdfReader
from tkinter.filedialog import askopenfilename

book = askopenfilename(
    title="Select PDF",
    filetypes=[("PDF Files", "*.pdf")]
)

reader = PdfReader(book)

text = ""

for page in reader.pages:
    page_text = page.extract_text()
    if page_text:
        text += page_text + "\n"

engine = pyttsx3.init()

engine.save_to_file(text, "audiobook.mp3")
engine.runAndWait()

print("Audiobook saved as audiobook.mp3")