from pathlib import Path

def cargar_cv(ruta: str) -> str:
    """Lee un CV en .txt, .pdf p .docx y devuelve su texto"""
    p = Path(ruta)
    if not p.exists():
        return "CV no disponible"

    ext = p.suffix.lower()
    if ext == ".txt":
        return p.read_text(encoding="utf-8", errors="ignore")
    if ext == ".pdf":
        import pdfplumber
        with pdfplumber.open(p) as pdf:
            return  "\n".join((pag.extract_text() or "") for pag in pdf.pages)
    if ext == ".docx":
        import docx
        documento = docx.Document(str(p))
        return "\n".join(par.text for par in documento.paragraphs)
    raise ValueError(f"Formato de CV no soportado: {ext}")


BASE_DIR = Path(__file__).resolve().parent.parent  # raíz del proyecto (sube desde services/)

def buscar_cv(base: str = "cv") -> str | None:
    carpeta = BASE_DIR / "data"
    # 1) nombre exacto: cv.txt | cv.pdf | cv.docx
    for ext in (".txt", ".pdf", ".docx"):
        f = carpeta / f"{base}{ext}"
        if f.exists():
            return str(f)
    # 2) comodín: cualquier cv*.pdf/docx/txt (p.ej. "cv_ares.pdf")
    for f in sorted(carpeta.glob("cv*.*")):
        if f.suffix.lower() in (".txt", ".pdf", ".docx"):
            return str(f)
    return None

