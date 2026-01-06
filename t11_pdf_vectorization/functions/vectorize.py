import os
import re
from typing import Any, Dict, List

import pymupdf
from sentence_transformers import SentenceTransformer

# ============================================================
# 🔧 SET THIS
# ============================================================
PDF_PATH = "/Users/danieladayev/tutorials/t11_pdf_vectorization/sample-local-pdf.pdf"

# Local embedding model (downloads automatically once)
LOCAL_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dims

# Chunking params (characters)
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
# ============================================================


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_pdf_blocks(pdf_path: str) -> List[Dict[str, Any]]:
    doc = pymupdf.open(pdf_path)
    pages = []

    for i in range(len(doc)):
        page = doc[i]
        blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)

        page_blocks = []
        for b in blocks:
            x0, y0, x1, y1, txt, block_no, block_type = b
            txt = normalize_text(txt)
            if not txt or len(txt) < 3:
                continue
            page_blocks.append({"block_id": int(block_no), "text": txt})

        pages.append({"page": i + 1, "blocks": page_blocks})

    doc.close()
    return pages


def chunk_blocks(blocks: List[Dict[str, Any]], chunk_size: int, chunk_overlap: int):
    chunks = []
    current_text_parts = []
    current_block_ids = []
    current_len = 0
    chunk_index = 0

    def flush():
        nonlocal chunk_index, current_text_parts, current_block_ids, current_len
        if not current_text_parts:
            return

        text = "\n\n".join(current_text_parts).strip()
        if text:
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "block_ids": current_block_ids.copy(),
                    "text": text,
                }
            )
            chunk_index += 1

        # overlap tail
        if chunk_overlap > 0 and text:
            tail = text[-chunk_overlap:]
            current_text_parts = [tail]
            current_block_ids = []
            current_len = len(tail)
        else:
            current_text_parts = []
            current_block_ids = []
            current_len = 0

    for block in blocks:
        block_text = block["text"]
        block_id = block["block_id"]

        # If one block is huge, split it
        if len(block_text) > chunk_size:
            flush()
            start = 0
            while start < len(block_text):
                end = min(start + chunk_size, len(block_text))
                piece = block_text[start:end].strip()
                if piece:
                    chunks.append(
                        {
                            "chunk_index": chunk_index,
                            "block_ids": [block_id],
                            "text": piece,
                        }
                    )
                    chunk_index += 1
                start += chunk_size - chunk_overlap

            current_text_parts = []
            current_block_ids = []
            current_len = 0
            continue

        projected_len = current_len + len(block_text) + 2
        if projected_len > chunk_size:
            flush()

        current_text_parts.append(block_text)
        current_block_ids.append(block_id)
        current_len += len(block_text) + 2

    flush()
    return chunks


def chunk_pdf(pages: List[Dict[str, Any]], chunk_size: int, chunk_overlap: int):
    all_chunks = []
    for p in pages:
        page_num = p["page"]
        blocks = p["blocks"]
        if not blocks:
            continue
        page_chunks = chunk_blocks(blocks, chunk_size, chunk_overlap)
        for c in page_chunks:
            c["page"] = page_num
            all_chunks.append(c)
    return all_chunks


def embed_texts_local(texts: List[str], model_name: str):
    encoder = SentenceTransformer(model_name)
    vectors = encoder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return vectors.tolist()


def main():
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    print(f"\n📄 PDF: {PDF_PATH}")

    # 1) Extract blocks
    pages = read_pdf_blocks(PDF_PATH)
    num_pages = len(pages)
    num_blocks = sum(len(p["blocks"]) for p in pages)

    print(f"✅ Pages: {num_pages}")
    print(f"✅ Blocks extracted: {num_blocks}")

    # 2) Chunk
    chunks = chunk_pdf(pages, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"✅ Chunks created: {len(chunks)}")

    if not chunks:
        print("⚠️ No chunks produced. (PDF may be scanned images with no text layer.)")
        return

    # 3) Embed (local)
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts_local(texts, LOCAL_MODEL)

    print(f"✅ Embeddings created: {len(embeddings)}")
    print(f"✅ Embedding dimension: {len(embeddings[0])}")

    # 4) Show sample output
    print("\n--- SAMPLE CHUNKS ---")
    for i in range(min(2, len(chunks))):
        print(
            f"\n[Chunk {i}] Page={chunks[i]['page']} BlockIDs={chunks[i]['block_ids']}"
        )
        print(chunks[i]["text"][:600] + ("..." if len(chunks[i]["text"]) > 600 else ""))

        emb_preview = embeddings[i][:10]
        print(f"Embedding preview (first 10 dims): {emb_preview}")

    print("\n✅ Done.\n")


if __name__ == "__main__":
    main()
