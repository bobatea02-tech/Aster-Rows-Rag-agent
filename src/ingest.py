import os
import re
import yaml
import chromadb

FRONTMATTER_FIELDS_TO_KEEP = [
    "document_id",
    "title",
    "status",
    "effective_date",
    "last_reviewed",
    "audience",
    "policy_authority",
    "supersedes",
    "superseded_by",
    "superseded_date",
]


def parse_markdown_sections(filepath: str):
    """
    Parses YAML front matter and splits the body into sections by heading
    (H1/H2/H3). Each section keeps the filename, heading, and the full
    front-matter metadata for filtering and citation.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    metadata = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1].strip()
            body = parts[2].strip()
            metadata = yaml.safe_load(raw_yaml) if raw_yaml else {}

    filename = os.path.basename(filepath)

    split_pattern = r"(?=(?:^|\n)#{1,3}\s+)"
    raw_chunks = [c.strip() for c in re.split(split_pattern, body) if c.strip()]
    if not raw_chunks:
        raw_chunks = [body]

    sections = []
    for chunk in raw_chunks:
        heading_match = re.match(r"^(#{1,3})\s+(.+)", chunk)
        heading = heading_match.group(2).strip() if heading_match else "General"

        # Skip heading-only chunks with almost no body (e.g. a bare H1
        # title immediately followed by the first H2) — they add retrieval
        # noise without useful content.
        body_only = re.sub(r"^#{1,3}\s+.+", "", chunk, count=1).strip()
        if len(body_only.split()) < 5:
            continue

        doc_meta = {"source": filename, "heading": heading}
        for field in FRONTMATTER_FIELDS_TO_KEEP:
            value = metadata.get(field)
            doc_meta[field] = str(value) if value is not None else ""

        # Guarantee these are always present so where={"status": "active"}
        # filters never silently break on a missing/blank field.
        if not doc_meta.get("status"):
            doc_meta["status"] = "active"
        if not doc_meta.get("audience"):
            doc_meta["audience"] = "customer"

        sections.append((doc_meta, chunk))

    return sections


def build_vector_db(docs_folder: str = "knowledge-base"):
    db_path = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
    client = chromadb.PersistentClient(path=db_path)

    # Rebuild cleanly so edits/removals in the KB don't leave orphaned
    # chunks behind from a previous ingest run.
    try:
        client.delete_collection(name="policies")
    except Exception:
        pass
    collection = client.get_or_create_collection(name="policies")

    target_folder = os.path.join(os.path.dirname(__file__), "..", docs_folder)
    if not os.path.exists(target_folder):
        print(f"Error: Folder '{docs_folder}' not found at {target_folder}")
        return

    print("Ingesting and chunking policy documents...")
    count = 0
    for filename in sorted(os.listdir(target_folder)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(target_folder, filename)
        sections = parse_markdown_sections(filepath)

        for idx, (meta, text) in enumerate(sections):
            doc_id = f"{filename}#sec-{idx}"
            collection.upsert(documents=[text], metadatas=[meta], ids=[doc_id])
            count += 1

        status = sections[0][0]["status"] if sections else "n/a"
        print(f"  -> {filename}: {len(sections)} sections | status={status}")

    print(f"\nIndexed {count} sections in ChromaDB.")


if __name__ == "__main__":
    build_vector_db()