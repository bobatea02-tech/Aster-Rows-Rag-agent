import os
import re
import yaml
import chromadb

def parse_markdown_sections(filepath: str):
    """
    Parses frontmatter and splits markdown by top-level or second-level headings (##).
    Preserves heading context for accurate source citations.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    metadata = {}
    body = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            raw_yaml = parts[1].strip()
            body = parts[2].strip()
            metadata = yaml.safe_load(raw_yaml) if raw_yaml else {}

    filename = os.path.basename(filepath)
    sections = []
    
    # Split by markdown headers (# Header or ## Subheader)
    split_pattern = r'(?=(?:^|\n)#{1,3}\s+)'
    chunks = [c.strip() for c in re.split(split_pattern, body) if c.strip()]
    
    if not chunks:
        chunks = [body]

    for chunk in chunks:
        # Extract the heading title
        heading_match = re.match(r'^(#{1,3})\s+(.+)', chunk)
        heading = heading_match.group(2).strip() if heading_match else "General"
        
        doc_meta = {
            "source": filename,
            "heading": heading,
            "status": str(metadata.get("status", "active")),
            "title": str(metadata.get("title", filename))
        }
        sections.append((doc_meta, chunk))

    return sections

def build_vector_db(docs_folder: str = "knowledge-base"):
    db_path = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="policies")
    
    target_folder = os.path.join(os.path.dirname(__file__), "..", docs_folder)
    if not os.path.exists(target_folder):
        print(f"Error: Folder '{docs_folder}' not found at {target_folder}")
        return

    print("Ingesting and chunking policy documents with headings...")
    count = 0
    for filename in os.listdir(target_folder):
        if filename.endswith(".md"):
            filepath = os.path.join(target_folder, filename)
            sections = parse_markdown_sections(filepath)
            
            for idx, (meta, text) in enumerate(sections):
                doc_id = f"{filename}#sec-{idx}"
                collection.upsert(
                    documents=[text],
                    metadatas=[meta],
                    ids=[doc_id]
                )
                count += 1
            print(f"  -> Ingested: {filename} ({len(sections)} sections) | Status: {sections[0][0]['status']}")
            
    print(f"\nSuccessfully indexed {count} policy sections in ChromaDB.")

if __name__ == "__main__":
    build_vector_db()