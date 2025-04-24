# PDF Playground

A comparative analysis tool for different PDF parsing libraries in Python. This project helps evaluate and compare various PDF parsing solutions to understand their strengths and limitations.

## 📚 Supported PDF Parsing Libraries

- PyPDF
- PyMuPDF
- Doctr
- Marker
- Markitdown
- Docling
- SmolDocling
- Unstructured

## 🗂 Project Structure

```
pdf-playground/
├── src/                   # Source code for different PDF parsers
│   ├── docling.py        # Docling implementation
│   ├── doctr.py          # Doctr implementation
│   ├── marker.py         # Marker implementation
│   ├── markitdown.py     # Markitdown implementation
│   ├── pymupdf.py        # PyMuPDF implementation
│   ├── pypdf.py          # PyPDF implementation
│   ├── smoldocling.py    # SmolDocling implementation
│   ├── unstructured.py   # Unstructured implementation
│   ├── save_markdowns.py # Utility for saving results
│   └── settings.py       # Project settings
├── examples/             # Test PDF files
│   ├── academic_paper_figure.pdf
│   ├── attention_paper.pdf
│   ├── complex_layout.pdf
│   ├── french.pdf
│   ├── handwriting_form.pdf
│   ├── invoice.pdf
│   ├── magazine_complex_layout.pdf
│   ├── table.pdf
│   └── ...
├── results/              # Parsed output from different libraries
│   ├── docling_result_text.md
│   ├── doctr_result_text.md
│   ├── marker_result_text.md
│   ├── markitdown_result_text.md
│   ├── pymupdf4llm_result_text.md
│   ├── pypdf_result_text.md
│   ├── smoldocling_result_text.md
│   └── unstrctured_result_text.md
├── debug_data/          # Visual debugging data
│   └── PDF_Parsing_Analysis/
├── requirements.txt     # Project dependencies
└── notebook.ipynb      # Jupyter notebook for analysis
```

## 🚀 Getting Started

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pdf-playground.git
cd pdf-playground
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📄 Usage

1. Place your PDF files in the `examples/` directory
2. Run individual parser implementations from the `src/` directory
3. Check the parsed results in the `results/` directory
4. Use the Jupyter notebook for comparative analysis

## 📊 Example Files

The `examples/` directory contains various PDF files to test different parsing scenarios:
- Academic papers with figures
- Complex magazine layouts
- Tables and merged cells
- Handwriting forms
- Invoices
- Multi-language documents (e.g., French)

## 🔍 Results

Parsing results are saved as markdown files in the `results/` directory. Each implementation has its own output file for easy comparison:
- `docling_result_text.md`
- `doctr_result_text.md`
- `marker_result_text.md`
- And more...

## 🛠 Development

To add a new PDF parser implementation:
1. Create a new Python file in the `src/` directory
2. Implement the parsing logic
3. Use `save_markdowns.py` to save the results
4. Update the notebook to include the new parser in the comparison

## 📝 Requirements

See `requirements.txt` for a full list of dependencies.
