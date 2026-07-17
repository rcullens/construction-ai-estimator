"""
Digital Twin generation from construction PDFs.
Produces grounded page-level JSON that downstream agents can reason over.
"""

from __future__ import annotations
import json
import uuid
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

import fitz  # PyMuPDF

from models.models import DocumentMeta, DocumentType


class DigitalTwinBuilder:
    def __init__(self, output_dir: str | Path = "./digital_twins"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _classify_page(self, text: str) -> DocumentType:
        """Heuristic page classification. Can be upgraded with a small LLM call later."""
        lower = text.lower()[:3000]

        if any(k in lower for k in ["addendum", "addenda", "revision no", "bulletin"]):
            return DocumentType.ADDENDUM
        if any(k in lower for k in ["division 0", "division 1", "section 01", "part 1 - general", "general requirements"]):
            return DocumentType.SPECIFICATION
        if any(k in lower for k in ["schedule of", "door schedule", "finish schedule", "equipment schedule"]):
            return DocumentType.SCHEDULE
        if len(text.strip()) < 80:
            return DocumentType.DRAWING
        return DocumentType.DRAWING

    def build_from_pdf(self, pdf_path: str | Path, project_id: Optional[str] = None) -> Tuple[DocumentMeta, Dict[str, Any]]:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        doc_id = str(uuid.uuid4())
        pages_data: List[Dict[str, Any]] = []

        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            text_dict = page.get_text("dict")

            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_filename = f"{doc_id}_p{page_num:03d}.png"
            img_path = self.output_dir / img_filename
            pix.save(str(img_path))

            blocks = []
            for b in text_dict.get("blocks", []):
                if b.get("type") == 0:
                    blocks.append({
                        "bbox": b.get("bbox"),
                        "lines": [
                            {
                                "bbox": line.get("bbox"),
                                "text": "".join([span.get("text", "") for span in line.get("spans", [])])
                            }
                            for line in b.get("lines", [])
                        ]
                    })

            page_data = {
                "page_index": page_num,
                "width": page.rect.width,
                "height": page.rect.height,
                "text": text,
                "image_path": str(img_path),
                "blocks": blocks,
                "rotation": page.rotation,
            }
            pages_data.append(page_data)

        first_text = next((p["text"] for p in pages_data if len(p["text"].strip()) > 50), "")
        doc_type = self._classify_page(first_text)

        twin = {
            "document_id": doc_id,
            "project_id": project_id,
            "filename": pdf_path.name,
            "source_path": str(pdf_path),
            "page_count": len(doc),
            "created_at": datetime.utcnow().isoformat(),
            "pages": pages_data,
            "title_block": None,
            "detected_scale": None,
            "symbols": [],
        }

        twin_path = self.output_dir / f"{doc_id}.json"
        with open(twin_path, "w", encoding="utf-8") as f:
            json.dump(twin, f, indent=2, ensure_ascii=False)

        meta = DocumentMeta(
            document_id=doc_id,
            filename=pdf_path.name,
            type=doc_type,
            page_count=len(doc),
            digital_twin_path=str(twin_path),
        )

        doc.close()
        return meta, twin

    def ingest_package(self, file_paths: List[str | Path], project_id: Optional[str] = None) -> List[DocumentMeta]:
        metas = []
        for path in file_paths:
            meta, _ = self.build_from_pdf(path, project_id=project_id)
            metas.append(meta)
            print(f"  \u2713 Ingested: {Path(path).name} \u2192 {meta.document_id} ({meta.type.value})")
        return metas


def load_digital_twin(twin_path: str | Path) -> Dict[str, Any]:
    with open(twin_path, "r", encoding="utf-8") as f:
        return json.load(f)
