# app/service/processors/txt_processor.py
from .base import BaseProcessor


class TextProcessor(BaseProcessor):
    def extract_text(self, file_path: str) -> str:
        """
        Try common encodings to avoid crashes/garbled text.
        """
        encodings = ["utf-8", "gbk", "utf-16", "latin-1"]

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read().strip()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                # Unknown errors should not crash ingestion.
                print(f"Failed to read text file ({enc}): {e}")
                break

        # Last resort: ignore decode errors.
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        except Exception:
            return ""