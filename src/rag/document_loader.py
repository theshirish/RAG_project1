import asyncio
import subprocess

from abc import ABC, abstractmethod
from pathlib import Path
from docx import Document



from config.logging_config import setup_logger

logger = setup_logger(__name__)


# Template for our file loaders
class BaseDocumentLoader(ABC):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    @abstractmethod
    async def load(self) -> str:
        pass


# Reads .txt file format
class TextLoader(BaseDocumentLoader):

    async def load(self) -> str:
        logger.info(f"Loading text file: {self.path.name}")
        if not self.path.exists():
            logger.error(f"File not found: {self.path.name}")
            raise FileNotFoundError(f"File not found: {self.path.name}")

        loop = asyncio.get_event_loop()

        def _read_file():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading text file {self.path.name}: {e}")
                raise

        return await loop.run_in_executor(None, _read_file)


# Reads .md file format
class MarkdownLoader(BaseDocumentLoader):
    """
    Loads markdown files (.md).
    """

    async def load(self) -> str:
        logger.info(f"Loading markdown file: {self.path.name}")
        if not self.path.exists():
            logger.error(f"File not found: {self.path.name}")
            raise FileNotFoundError(f"File not found: {self.path.name}")

        loop = asyncio.get_event_loop()

        def _read_file():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    # Returns raw markdown. You could add logic here to strip markdown syntax if needed.
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading markdown file {self.path.name}: {e}")
                raise

        return await loop.run_in_executor(None, _read_file)

# Reads .csv file format
class CSVLoader(BaseDocumentLoader):
    """
    Loads CSV files (.csv).
    """

    async def load(self) -> str:
        logger.info(f"Loading CSV file: {self.path.name}")
        if not self.path.exists():
            logger.error(f"File not found: {self.path.name}")
            raise FileNotFoundError(f"File not found: {self.path.name}")

        loop = asyncio.get_event_loop()

        def _read_file():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    # Returns raw CSV. You could add logic here to strip markdown syntax if needed.
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading CSV file {self.path.name}: {e}")
                raise

        return await loop.run_in_executor(None, _read_file)



# TODO: Reads .docx file format
class DocxLoader(BaseDocumentLoader):
    """
    Loads DOCX files (.docx).
    """
    full_text = []
    async def load(self) -> str:
        logger.info(f"Loading DOCX file: {self.path.name}")
        if not self.path.exists():
            logger.error(f"File not found: {self.path.name}")
            raise FileNotFoundError(f"File not found: {self.path.name}")

        loop = asyncio.get_event_loop()

        def _read_file():
            try:
                # with open(self.path, "r", encoding="utf-8") as f:
                    ##################################
                            # Load the document
                doc = Document(self.path)
                
                # Extract text from all paragraphs
                full_text = []
                for paragraph in doc.paragraphs:
                    full_text.append(paragraph.text)
                    
                # Optional: Extract text from tables if present
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            full_text.append(cell.text)
                            
                return '\n'.join(full_text)
                    ##################################
                    # Returns raw CSV. You could add logic here to strip markdown syntax if needed.
                    # return f.read()
            except Exception as e:
                logger.error(f"Error reading doc file {self.path.name}: {e}")
                raise

        return await loop.run_in_executor(None, _read_file)


# TODO: Reads .doc file format
class DocLoader(BaseDocumentLoader):
    """
    Loads DOC files (.doc).
    """

    async def load(self) -> str:
        logger.info(f"Loading DOC file: {self.path.name}")
        if not self.path.exists():
            logger.error(f"File not found: {self.path.name}")
            raise FileNotFoundError(f"File not found: {self.path.name}")

        loop = asyncio.get_event_loop()

        def _read_file():
            try:
                cmd = ['textutil', '-convert', 'txt', '-stdout', self.path]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return '\n'.join(result.stdout)


            except Exception as e:
                logger.error(f"Error reading docx file {self.path.name}: {e}")
                raise

        return await loop.run_in_executor(None, _read_file)


# TODO: Reads .pdf file format
# TODO: Reads .pdfOcr file format


class DocumentLoadFactory:

    @staticmethod
    def get_loader(file_path: str | Path) -> BaseDocumentLoader:
        path = Path(file_path)
        ext = path.suffix.lower()  # extract extention from a path .txt, .md, .doc

        logger.info(f"Creating loader for file: {path.name} with extension: {ext}")

        if ext == ".txt":
            return TextLoader(path)

        if ext == ".md":
            return MarkdownLoader(path)

        if ext == ".csv":
            return CSVLoader(path)

        if ext == ".docx":
            return DocxLoader(path)

        if ext == ".doc":
            return DocLoader(path)

        logger.error(f"Unsupported file extension: {ext} for file {path.name}")
        raise ValueError(f"Unsupported file extension: {ext}")
