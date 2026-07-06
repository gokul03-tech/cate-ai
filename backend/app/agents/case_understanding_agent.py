"""
LexOrch-KG — Agent 1: Case Understanding Agent
Handles document parsing, OCR, chunking, and summarization.
"""

import io
import os
import uuid
from typing import Any

from loguru import logger
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import HumanMessage, SystemMessage

from app.agents.base_agent import BaseAgent, AgentResult


class CaseUnderstandingAgent(BaseAgent):
    """
    Agent 1 — Case Understanding
    
    Responsibilities:
    - Extract text from PDF/DOCX/TXT
    - Apply OCR if text extraction fails
    - Split document into semantic chunks
    - Generate AI-powered summary
    - Identify key facts
    """

    def __init__(self) -> None:
        super().__init__("CaseUnderstandingAgent", step=1)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""],
        )

    async def execute(
        self, state: dict[str, Any]
    ) -> tuple[dict[str, Any], AgentResult]:
        """Parse document, extract text, OCR if needed, summarize."""
        file_path: str = state["file_path"]
        file_type: str = state["file_type"]

        # ── Step 1: Extract raw text ────────────────────────────────────────
        raw_text, page_count, ocr_applied = await self._extract_text(
            file_path, file_type
        )
        word_count = len(raw_text.split())
        logger.info(
            f"[CaseUnderstandingAgent] Extracted {word_count} words "
            f"from {page_count} pages | OCR={ocr_applied}"
        )

        # ── Step 2: Chunk the document ──────────────────────────────────────
        chunks = self.text_splitter.create_documents(
            [raw_text],
            metadatas=[{"case_id": str(state["case_id"]), "source": file_path}],
        )
        logger.info(f"[CaseUnderstandingAgent] Created {len(chunks)} chunks")

        # ── Step 3: Generate summary ────────────────────────────────────────
        summary = await self._summarize(raw_text[:8000])  # First 8K chars

        # ── Step 4: Extract key facts ───────────────────────────────────────
        key_facts = await self._extract_key_facts(raw_text[:6000])

        # ── Update state ────────────────────────────────────────────────────
        state.update({
            "raw_text": raw_text,
            "chunks": [
                {
                    "id": str(uuid.uuid4()),
                    "text": chunk.page_content,
                    "metadata": chunk.metadata,
                }
                for chunk in chunks
            ],
            "page_count": page_count,
            "word_count": word_count,
            "ocr_applied": ocr_applied,
            "summary": summary,
            "key_facts": key_facts,
        })

        result = AgentResult(
            agent_name=self.name,
            status="completed",
            output={
                "page_count": page_count,
                "word_count": word_count,
                "chunks_count": len(chunks),
                "ocr_applied": ocr_applied,
                "summary_length": len(summary),
                "key_facts_count": len(key_facts),
            },
        )
        return state, result

    async def _extract_text(
        self, file_path: str, file_type: str
    ) -> tuple[str, int, bool]:
        """
        Extract text from file. Falls back to OCR if native extraction fails.
        
        Returns: (text, page_count, ocr_applied)
        """
        ocr_applied = False

        if file_type == "pdf":
            text, page_count = self._extract_pdf(file_path)
            # Fallback to OCR if extracted text is too short
            if len(text.strip()) < 100:
                logger.warning("PDF text extraction minimal — applying OCR")
                text, page_count = self._ocr_pdf(file_path)
                ocr_applied = True

        elif file_type == "docx":
            text, page_count = self._extract_docx(file_path)

        elif file_type == "txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            page_count = max(1, len(text) // 3000)

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return text, page_count, ocr_applied

    def _extract_pdf(self, file_path: str) -> tuple[str, int]:
        """Extract text using PyMuPDF (fast, native)."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            return "\n".join(text_parts), len(doc)
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return "", 0

    def _ocr_pdf(self, file_path: str) -> tuple[str, int]:
        """Apply Tesseract OCR to scanned PDF pages."""
        try:
            import fitz
            import pytesseract
            from PIL import Image

            doc = fitz.open(file_path)
            text_parts = []
            for page in doc:
                # Render page as image
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                # OCR the image
                ocr_text = pytesseract.image_to_string(img, lang="eng")
                text_parts.append(ocr_text)
            return "\n".join(text_parts), len(doc)
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return "", 0

    def _extract_docx(self, file_path: str) -> tuple[str, int]:
        """Extract text from DOCX files."""
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join(para.text for para in doc.paragraphs)
            # Estimate pages
            page_count = max(1, len(text) // 3000)
            return text, page_count
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return "", 0

    async def _summarize(self, text: str) -> str:
        """Generate an AI-powered legal case summary."""
        system_msg = SystemMessage(content="""You are a senior legal analyst. 
        Summarize the provided legal case document concisely and accurately.
        Focus on: parties involved, charges/claims, key facts, jurisdiction, and current status.
        Keep the summary under 500 words.""")
        human_msg = HumanMessage(content=f"Summarize this legal document:\n\n{text}")

        try:
            response = await self.llm.ainvoke([system_msg, human_msg])
            return response.content
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return "Summary generation failed. Please review the document manually."

    async def _extract_key_facts(self, text: str) -> list[str]:
        """Extract the most important legal facts from the document."""
        system_msg = SystemMessage(content="""You are a legal expert.
        Extract the top 10 most important legal facts from this document.
        Return ONLY a numbered list of facts, one per line.
        Example: 1. The defendant was arrested on January 15, 2024""")
        human_msg = HumanMessage(
            content=f"Extract key legal facts:\n\n{text}"
        )

        try:
            response = await self.llm.ainvoke([system_msg, human_msg])
            lines = response.content.strip().split("\n")
            facts = [
                line.strip().lstrip("0123456789. ").strip()
                for line in lines
                if line.strip() and len(line.strip()) > 10
            ]
            return facts[:10]
        except Exception as e:
            logger.error(f"Key fact extraction failed: {e}")
            return []
