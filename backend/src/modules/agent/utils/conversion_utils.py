from langchain_community.document_loaders import PyPDFLoader


class ConversionUtils:
    @staticmethod
    async def convert_pdf_to_text(pdf_path: str) -> str:
        loader = PyPDFLoader(pdf_path)
        pages = []
        async for page in loader.alazy_load():
            pages.append(page)
        return pages
