import re
import logging
import httpx
from dataclasses import dataclass
from typing import List
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class KBSection:
    section: str
    content: str


class KnowledgeBaseTool:
    def __init__(self, kb_url=None):
        self.kb_url = kb_url or settings.KB_URL

    async def fetch_relevant_sections(self, question: str) -> List[KBSection]:
        raw_md = await self._fetch_kb()
        if not raw_md:
            logger.warning("KB retornou conteudo vazio")
            return []
        all_sections = self._parse_sections(raw_md)
        relevant = self._rank_sections(all_sections, question)
        logger.info("KB: %d secoes totais, %d relevantes", len(all_sections), len(relevant))
        return relevant

    async def _fetch_kb(self) -> str:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.kb_url)
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as exc:
            logger.error("Erro HTTP ao buscar KB: %s", exc)
        except httpx.RequestError as exc:
            logger.error("Erro de rede ao buscar KB: %s", exc)
        return ""

    def _parse_sections(self, markdown: str) -> List[KBSection]:
        sections = []
        topic_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
        topic_matches = list(topic_pattern.finditer(markdown))

        if not topic_matches:
            heading_pattern = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
            matches = list(heading_pattern.finditer(markdown))
            if not matches:
                sections.append(KBSection(section="Documento completo", content=markdown.strip()))
                return sections
            for i, match in enumerate(matches):
                title = match.group(1).strip()
                start = match.end()
                end = matches[i+1].start() if i+1 < len(matches) else len(markdown)
                body = markdown[start:end].strip()
                if body:
                    sections.append(KBSection(section=title, content=body))
            return sections

        for i, match in enumerate(topic_matches):
            title = match.group(1).strip()
            start = match.start()
            end = topic_matches[i+1].start() if i+1 < len(topic_matches) else len(markdown)
            body = markdown[start:end].strip()
            if body:
                sections.append(KBSection(section=title, content=body))

        return sections

    def _rank_sections(self, sections, question: str, top_k: int = 3, min_score: int = 1):
        if not sections:
            return []
        stop_words = {
            "como","qual","quais","quando","onde","por","que","para","uma","um",
            "de","do","da","dos","das","the","how","what","when","where","which",
            "who","are","is","in","on","at","to","and","or","not",
        }
        tokens = {
            w.lower() for w in re.findall(r'\b\w+\b', question)
            if len(w) >= 3 and w.lower() not in stop_words
        }
        if not tokens:
            return sections[:top_k]
        scored = []
        for sec in sections:
            haystack = (sec.section + " " + sec.content).lower()
            score = sum(1 for t in tokens if t in haystack)
            if score >= min_score:
                scored.append((score, sec))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [sec for _, sec in scored[:top_k]]
