
try:
    import pypdf
    reader = pypdf.PdfReader("Round2.pdf")
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    print(text)
except ImportError:
    print("pypdf not installed")
except Exception as e:
    print(f"Error reading PDF: {e}")
